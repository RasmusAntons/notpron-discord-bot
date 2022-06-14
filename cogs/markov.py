from cogs.command import Command, Category
import config
import globals
import time
import numpy as np
from discord.utils import escape_mentions
import asyncio


class MarkovAddChannelCommand(Command):
    name = 'markov_add_channel'
    category = Category.ADMIN
    arg_range = (1, 2)
    description = 'Add messages from a channel to the text generation.'
    arg_desc = '<#text_channel> [message_limit]'

    async def check(self, args, msg, test=False):
        return await super().check(args, msg, test) and config.is_admin(msg.author)

    async def execute(self, args, msg):
        limit = int(args[1]) if len(args) == 2 else 10**5
        if len(msg.channel_mentions) != 1:
            raise Exception('Mention a channel with this command.')
        ch = msg.channel_mentions[0]
        progress_msg = await msg.channel.send(f'Adding {ch.mention} to text generation...')
        count = 0
        t_last_update = time.time()
        async for old_msg in ch.history(limit=limit):
            if not old_msg.author.bot:
                count += 1
                text = old_msg.clean_content
                globals.bot.markov.insert_text(text, tag=str(old_msg.author.id))
            if t_last_update + 10 < time.time():
                t_last_update = time.time()
                await progress_msg.edit(content=f'Adding {ch.mention} to text generation...\n{count} messages added.')
        await progress_msg.edit(content=f'Added {ch.mention} to text generation.\n{count} messages added.')


class ImitateCommand(Command):
    name = 'imitate'
    category = Category.UTILITY
    arg_range = (1, 1)
    description = 'Generate text imitating a user.'
    arg_desc = '<@user>'

    async def execute(self, args, msg):
        if len(msg.mentions) != 1:
            raise Exception('Mention a user with this command.')
        elif msg.mentions[0].bot:
            raise Exception('Cannot imitate bot users.')
        for n in range(np.random.geometric(0.5)):
            text = globals.bot.markov.generate_forwards(tag=str(msg.mentions[0].id))
            if text is None:
                await msg.reply(f'I don\' know {msg.mentions[0].display_name} well enough.')
                return
            async with msg.channel.typing():
                await asyncio.sleep(0.04 * len(text))
                await msg.channel.send(escape_mentions(text))
