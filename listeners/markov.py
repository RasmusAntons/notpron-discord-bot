from listeners import MessageListener, MessageEditListener, MessageDeleteListener
import globals
import numpy as np
from utils import escape_discord
import asyncio


class MarkovListener(MessageListener, MessageEditListener, MessageDeleteListener):
    async def on_message(self, msg):
        if msg.author.bot:
            return
        if not globals.conf.list_contains(globals.conf.keys.CHANNELS, msg.channel.id):
            return
        if globals.bot.user.mentioned_in(msg):
            if '@everyone' not in msg.content and '@here' not in msg.content:
                await msg.channel.trigger_typing()
                n = np.random.geometric(0.5)
                for text in globals.bot.markov.generate_multiple_from_least_common(msg.clean_content, n):
                    await asyncio.sleep(0.04 * len(text))
                    await msg.channel.send(escape_discord(text))
        if globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, msg.channel.id):
            globals.bot.markov.insert_text(msg.clean_content)

    async def on_message_edit(self, message, cached_message=None):
        if cached_message is not None:
            globals.bot.markov.delete_text(cached_message.clean_content)
            globals.bot.markov.insert_text(message.clean_content)

    async def on_message_delete(self, message_id, channel, guild, cached_message=None):
        if cached_message:
            globals.bot.markov.delete_text(cached_message.clean_content)
