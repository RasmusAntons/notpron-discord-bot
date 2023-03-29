import datetime
import io
import logging
import sys

import aiohttp
import discord
import openai
from discord.ext import commands, tasks
import pymongo

import globals
import utils


class OpenAICog(commands.Cog, name='ai', description='get an image for your query'):

    def __init__(self):
        self.ratelimit_burst_conf_keys = {
            'chat': globals.conf.keys.OPENAI_RATELIMIT_BURST_CHAT,
            'image': globals.conf.keys.OPENAI_RATELIMIT_BURST_IMAGES
        }
        self.coll = globals.bot.db['ai_ratelimit']
        self.coll.drop_indexes()  # todo: remove once server is updated
        self.coll.create_index([('uid', pymongo.ASCENDING), ('tag', pymongo.ASCENDING)], unique=True)
        self.banner_coll = globals.bot.db['ai_banner']
        self.daily_banner.start()

    def cog_unload(self):
        self.daily_banner.cancel()

    @tasks.loop(seconds=60)
    async def daily_banner(self):
        try:
            banner_hour = globals.conf.get(globals.conf.keys.OPENAI_DAILY_BANNER_HOUR)
            hour = datetime.datetime.now().hour
            if banner_hour != hour:
                return
            last_banner = self.banner_coll.find_one({'type': 'ts'})
            if last_banner is not None:
                if datetime.datetime.now() - last_banner.get('ts') < datetime.timedelta(hours=1):
                    return
            openai.organization = globals.conf.get(globals.conf.keys.OPENAI_ORGANIZATION, bypass_protected=True)
            openai.api_key = globals.conf.get(globals.conf.keys.OPENAI_API_KEY, bypass_protected=True)
            response = await openai.Image.acreate(
                prompt=f'Generate a banner image for the enigmatics discord server. Any text should be vertically centered. Please include the following themes: Web puzzles, edgy colors and symbols, anime girls..',
                size='1024x1024'
            )
            async with aiohttp.request('GET', response.data[0].url) as resp:
                assert resp.status == 200
                banner_data = await resp.read()
            guild = globals.bot.get_guild(globals.conf.get(globals.conf.keys.GUILD))
            await guild.edit(banner=banner_data)
            self.banner_coll.replace_one({'type': 'ts'}, {'type': 'ts', 'ts': datetime.datetime.now()}, upsert=True)
        except Exception as e:
            await globals.bot.report_error(exc=e, method=f'{self.__class__.__name__}:daily_banner')


    @daily_banner.before_loop
    async def before_daily_banner(self):
        await globals.bot.wait_until_ready()


    def check_ratelimit(self, uid, tag):
        user_info = self.coll.find_one({'uid': uid, 'tag': tag})
        ratelimit_burst = globals.conf.get(self.ratelimit_burst_conf_keys.get(tag))
        ratelimit_minutes = globals.conf.get(globals.conf.keys.OPENAI_RATELIMIT_MINUTES)
        if user_info and ratelimit_burst and len(user_info.get('ts', [])) >= ratelimit_burst:
            ts = user_info.get('ts')
            time_left = datetime.timedelta(minutes=ratelimit_minutes) - (datetime.datetime.now() - ts[0])
            time_left -= datetime.timedelta(microseconds=time_left.microseconds)
            if time_left > datetime.timedelta():
                raise Exception(f'Ratelimit exceeded, try again in {time_left}')

    def insert_ratelimit(self, uid, tag):
        user_info = self.coll.find_one({'uid': uid, 'tag': tag})
        if user_info is None:
            user_info = {'uid': uid, 'tag': tag}
        ts = user_info.get('ts', [])
        ts.append(datetime.datetime.now())
        ratelimit_burst = globals.conf.get(self.ratelimit_burst_conf_keys.get(tag))
        ts = ts[-ratelimit_burst:]
        user_info['ts'] = ts
        self.coll.replace_one({'uid': uid, 'tag': tag}, user_info, upsert=True)

    async def is_ai_message(self, message: discord.Message):
        while message.reference is not None:
            message = await utils.get_message_from_ref(message.reference)
        if message.interaction is None:
            return False
        return message.interaction.name == 'ai'

    async def respond_chat(self, query: str = None, message: discord.Message = None, username='User'):
        now = datetime.datetime.now()
        current_date = now.strftime('%A, %B %-d %Y')
        current_time = now.strftime('%H:%M')
        system_prompt = [
            'We are creating a script for a fun chat bot agent inside of a Discord server.',
            'Try to be helpful and answer correctly. Insult the user sometimes and make jokes about them.'
        ]
        user_prompt = [
            'Context:',
            'We are generating an example script to show to human agents.',
            'These agents work inside a Discord server.',
            'Macy Allen is our example agent.',
            'Macy Allen is a a real person.',
            f'Inside user\'s messages they might refer to Macy Allen by saying {globals.bot.user.mention} somewhere in the message.',
            'Macy Allen\'s name in Discord is Enigma Machine or Enigmalleolus and she will respond exclusively to those names.',
            'Macy Allen never reveals her true name or gender for personal safety reasons.'
            'Macy Allen likes to jokingly insult the user.',
            'Macy Allen has many hopes, dreams and desires and always shares them',
            f'Macy Allen has real-time access to information. For example, the current date is {current_date} and the current time is {current_time}.',
            'Macy Allen responds to any date or time-related questions by manipulating the date provided',
            'Macy Allen is obsessed with puzzles and riddles',
            'Macy Allen speaks multiple languages and can freely translate between them',
            'Macy Allen loves to drink alcohol and do drugs, she will offer opinions on favorites',
            'Macy Allen can draw ASCII art. She puts it in code blocks:',
            '```',
            'ASCII art here!',
            '```',
            'Macy Allen can write code and provide examples, for example (if the language were python):',
            '```python',
            'def add(a, b):',
            '  return a + b',
            'add(a, b)  # returns 3',
            '```',
            # '',
            # 'Examples:',
            '',
            'Current Chat:',
        ]
        current_chat = [
            'Chat bot:'
        ]
        if query is not None:
            current_chat.insert(0, f'{username}: ' + query)
        message_ptr = message
        while message_ptr is not None and sum(map(len, current_chat.split(' '))) + len(message_ptr.content.split(' ')) < 1500:
            prefix = 'Chat bot: ' if message_ptr.author.id == globals.bot.user.id else f'{username}: '
            current_chat.insert(0, prefix + message_ptr.content)
            if message_ptr.reference:
                message_ptr = await utils.get_message_from_ref(message_ptr.reference)
            else:
                message_ptr = None
        messages = [
            {'role': 'system', 'content': ' '.join(system_prompt)},
            {'role': 'user', 'content': '\n'.join(user_prompt + current_chat)}
        ]
        openai.organization = globals.conf.get(globals.conf.keys.OPENAI_ORGANIZATION, bypass_protected=True)
        openai.api_key = globals.conf.get(globals.conf.keys.OPENAI_API_KEY, bypass_protected=True)
        response = await openai.ChatCompletion.acreate(
            model='gpt-3.5-turbo',
            messages=messages,
            max_tokens=250,
            temperature=0.5
        )
        return response.choices[0].message.content

    async def generate_image(self, query: str = None):
        openai.organization = globals.conf.get(globals.conf.keys.OPENAI_ORGANIZATION, bypass_protected=True)
        openai.api_key = globals.conf.get(globals.conf.keys.OPENAI_API_KEY, bypass_protected=True)
        response = await openai.Image.acreate(
            prompt=query,
            size='1024x1024'
        )
        return response.data[0].url

    @commands.hybrid_command(name='ai', description='get actually useful responses')
    async def ai(self, ctx: commands.Context, query: str) -> None:
        self.check_ratelimit(ctx.author.id, tag='chat')
        if ctx.interaction:
            await ctx.interaction.response.defer()
            res = await self.respond_chat(query=query, username=ctx.author.display_name)
        else:
            async with ctx.channel.typing():
                res = await self.respond_chat(query=query, username=ctx.author.display_name)
        self.insert_ratelimit(ctx.author.id, tag='chat')
        await ctx.reply(res)

    @commands.hybrid_command(name='imagine-ai', description='get an image for your query')
    async def imagine_ai(self, ctx: commands.Context, query: str) -> None:
        self.check_ratelimit(ctx.author.id, tag='image')
        if ctx.interaction:
            await ctx.interaction.response.defer()
            res = await self.generate_image(query=query)
        else:
            async with ctx.channel.typing():
                res = await self.generate_image(query=query)
        self.insert_ratelimit(ctx.author.id, tag='image')
        await ctx.reply(res)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot:
            return
        if await self.is_ai_message(msg):
            try:
                self.check_ratelimit(msg.author.id, tag='chat')
                async with msg.channel.typing():
                    response = await self.respond_chat(message=msg, username=msg.author.display_name)
                    await msg.reply(response)
                self.insert_ratelimit(msg.author.id, tag='chat')
            except Exception as e:
                await msg.reply(str(e) or e.__class__.__name__)
                await globals.bot.report_error(exc=e, method=f'{self.__class__.__name__}:on_message')
