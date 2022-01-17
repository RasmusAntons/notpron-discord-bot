import random

from listeners import MessageListener, MessageEditListener, MessageDeleteListener
import globals
import numpy as np
from discord.utils import escape_mentions
import asyncio


class MarkovListener(MessageListener, MessageEditListener, MessageDeleteListener):
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
                        await msg.channel.trigger_typing()
                        await asyncio.sleep(0.04 * len(text))
                        await msg.channel.send(escape_mentions(text))
        if globals.conf.list_contains(globals.conf.keys.CHANNELS, msg.channel.id):
            if (random.random() * 1000) < globals.conf.get(globals.conf.keys.MARKOV_CHANCE):
                member = msg.channel.guild.get_member(globals.bot.user.id) or \
                         await msg.channel.guild.fetch_member(globals.bot.user.id)
                seed = msg.clean_content.replace(f'@{member.display_name}', '')
                for text in globals.bot.markov.generate_multiple_from_least_common(seed):
                    await msg.channel.trigger_typing()
                    await asyncio.sleep(0.04 * len(text))
                    await msg.reply(escape_mentions(text))
        if globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, msg.channel.id):
            globals.bot.markov.insert_text(msg.clean_content, tag=str(msg.author.id))

    async def on_message_edit(self, message, cached_message=None):
        if cached_message and globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, message.channel.id):
            globals.bot.markov.delete_text(cached_message.clean_content)
            globals.bot.markov.insert_text(message.clean_content, tag=str(message.author.id))

    async def on_message_delete(self, message_id, channel, guild, cached_message=None):
        if cached_message and globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, cached_message.channel.id):
            globals.bot.markov.delete_text(cached_message.clean_content, tag=str(cached_message.author.id))
