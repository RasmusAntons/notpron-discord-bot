import asyncio
import random
import time

import discord
from discord.ext import commands
from discord.utils import escape_mentions
import numpy as np

import config
import globals


class MarkovCog(commands.Cog, name='Markov', description='text generation using markov chains'):
    @commands.hybrid_group(name='markov', description='manage markov text generation')
    async def markov_grp(self, ctx):
        return None

    @markov_grp.command(name='add', description='add messages from a channel to the text generation')
    @config.check_bot_admin()
    async def add(self, ctx: commands.Context, channel: discord.TextChannel, message_limit: int = 10 ** 5) -> None:
        progress_msg = await ctx.reply(f'Adding {channel} to text generation...')
        count = 0
        t_last_update = time.time()
        async for old_msg in channel.history(limit=message_limit):
            if not old_msg.author.bot:
                count += 1
                text = old_msg.clean_content
                globals.bot.markov.insert_text(text, tag=str(old_msg.author.id))
            if t_last_update + 10 < time.time():
                t_last_update = time.time()
                await progress_msg.edit(
                    content=f'Adding {channel.mention} to text generation...\n{count} messages added.')
        await progress_msg.edit(content=f'Added {channel.mention} to text generation.\n{count} messages added.')

    @commands.hybrid_command(name='imitate', description='generate text imitating a user')
    async def imitate(self, ctx: commands.Context, user: discord.Member) -> None:
        if user.bot:
            raise Exception('Cannot imitate bot users.')
        if ctx.interaction:
            await ctx.interaction.response.defer()
        texts = [globals.bot.markov.generate_forwards(tag=str(user.id)) for _ in range(np.random.geometric(0.5))]
        if None in texts:
            raise RuntimeError(f'I don\' know {user.display_name} well enough.')
        text = '\n'.join(texts)[:2000]
        delay = 0.04 * len(text)
        if ctx.interaction:
            await ctx.interaction.followup.send(text)
        else:
            async with ctx.channel.typing():
                await asyncio.sleep(delay)
                await ctx.reply(escape_mentions(text))

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        if globals.conf.list_contains(globals.conf.keys.CHANNELS, msg.channel.id):
            if globals.bot.user.mentioned_in(msg):
                if '@everyone' not in msg.content and '@here' not in msg.content:
                    member = msg.channel.guild.get_member(globals.bot.user.id) or \
                             await msg.channel.guild.fetch_member(globals.bot.user.id)
                    seed = msg.clean_content.replace(f'@{member.display_name}', '')
                    n = np.random.geometric(0.5)
                    for text in globals.bot.markov.generate_multiple_from_least_common(seed, n):
                        async with msg.channel.typing():
                            await asyncio.sleep(0.04 * len(text))
                            await msg.channel.send(escape_mentions(text))
        if globals.conf.list_contains(globals.conf.keys.CHANNELS, msg.channel.id):
            if (random.random() * 1000) < globals.conf.get(globals.conf.keys.MARKOV_CHANCE):
                member = msg.channel.guild.get_member(globals.bot.user.id) or \
                         await msg.channel.guild.fetch_member(globals.bot.user.id)
                seed = msg.clean_content.replace(f'@{member.display_name}', '')
                for text in globals.bot.markov.generate_multiple_from_least_common(seed):
                    async with msg.channel.typing():
                        await asyncio.sleep(0.04 * len(text))
                        await msg.reply(escape_mentions(text))
        if globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, msg.channel.id):
            globals.bot.markov.insert_text(msg.clean_content, tag=str(msg.author.id))

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message | discord.PartialMessage, after: discord.Message) -> None:
        if not isinstance(before, discord.Message):
            return
        if globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, after.channel.id):
            globals.bot.markov.delete_text(before.clean_content)
            globals.bot.markov.insert_text(after.clean_content, tag=str(after.author.id))

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message | discord.PartialMessage) -> None:
        if not isinstance(message, discord.Message):
            return
        if globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, message.channel.id):
            globals.bot.markov.delete_text(message.clean_content, tag=str(message.author.id))
