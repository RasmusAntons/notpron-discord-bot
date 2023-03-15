import datetime

import discord
import openai
from discord.ext import commands

import globals
import utils


RATELIMIT_MINUTES = 60 * 6
RATELIMIT_BURST = 20
RATELIMIT_BURST_OVERRIDE = {
    'image': 5
}


class OpenAICog(commands.Cog, name='ai', description='get an image for your query'):

    def __init__(self):
        self.coll = globals.bot.db['ai_ratelimit']
        self.coll.create_index('uid', unique=True)

    def check_ratelimit(self, uid, tag=''):
        user_info = self.coll.find_one({'uid': uid})
        if user_info and len(user_info.get(f'ts_{tag}', [])) >= RATELIMIT_BURST_OVERRIDE.get(tag, RATELIMIT_BURST):
            ts = user_info.get(f'ts_{tag}')
            time_left = datetime.timedelta(minutes=RATELIMIT_MINUTES) - (datetime.datetime.now() - ts[0])
            if time_left > datetime.timedelta():
                raise Exception(f'Ratelimit exceeded, try again in {time_left}')

    def insert_ratelimit(self, uid, tag=''):
        user_info = self.coll.find_one({'uid': uid})
        if user_info is None:
            user_info = {'uid': uid}
        ts = user_info.get(f'ts_{tag}', [])
        ts.append(datetime.datetime.now())
        ts = ts[:RATELIMIT_BURST]
        user_info[f'ts_{tag}'] = ts
        self.coll.replace_one({'uid': uid}, user_info, upsert=True)

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
            'Current Chat:',
        ]
        current_chat = [
            'Chat bot:'
        ]
        if query is not None:
            current_chat.insert(0, f'{username}: ' + query)
        message_ptr = message
        while message_ptr is not None:
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
        response = openai.ChatCompletion.create(
            model='gpt-3.5-turbo',
            messages=messages,
            max_tokens=250,
            temperature=0.5
        )
        return response.choices[0].message.content

    async def generate_image(self, query: str = None):
        openai.organization = globals.conf.get(globals.conf.keys.OPENAI_ORGANIZATION, bypass_protected=True)
        openai.api_key = globals.conf.get(globals.conf.keys.OPENAI_API_KEY, bypass_protected=True)
        response = openai.Image.create(
            prompt=query,
            size='1024x1024'
        )
        return response.data[0].url

    @commands.hybrid_command(name='ai', description='get actually useful responses')
    async def ai(self, ctx: commands.Context, query: str) -> None:
        self.check_ratelimit(ctx.author.id, tag='chat')
        if ctx.interaction:
            await ctx.interaction.response.defer()
            prefix = f'> {discord.utils.escape_mentions(query)}\n\n'
            res = prefix + await self.respond_chat(query=query, username=ctx.author.display_name)
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
            self.check_ratelimit(msg.author.id)
            async with msg.channel.typing():
                response = await self.respond_chat(message=msg, username=msg.author.display_name)
                await msg.reply(response)
            self.insert_ratelimit(msg.author.id)
