import discord
from listeners.listener import MessageListener, MessageEditListener, MessageDeleteListener, ReadyListener
import globals
from utils import get_channel
import time


class ArchiveListener(MessageListener, MessageEditListener, MessageDeleteListener, ReadyListener):
    def __init__(self):
        super(ArchiveListener, self).__init__()
        coll_messages = globals.bot.db['archive']
        coll_messages.create_index('id', unique=True)
        coll_messages.create_index('channel')
        coll_messages.create_index('created_at')
        coll_channels = globals.bot.db['archive_channels']
        coll_channels.create_index('id')

    async def on_ready(self):
        for channel_id in globals.conf.get(globals.conf.keys.MARKOV_CHANNELS, []):
            channel = await get_channel(channel_id)
            coll = globals.bot.db['archive']
            last_message = next(
                coll.find({'channel': channel_id}, {'_id': 0, 'created_at': 1}).sort([('created_at', -1)]).limit(1),
                None)
            last_timestamp = last_message['created_at'] if last_message is not None else None
            async for message in channel.history(after=last_timestamp):
                coll.insert_one(self.message_to_dict(message))

    async def on_message(self, message):
        if globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, message.channel.id):
            globals.bot.db['archive'].insert_one(self.message_to_dict(message))

    async def on_message_edit(self, message, cached_message=None):
        if globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, message.channel.id):
            globals.bot.db['archive'].replace_one({'id': message.id}, self.message_to_dict(message), upsert=True)

    async def on_message_delete(self, message_id, channel, guild, cached_message=None):
        if globals.conf.list_contains(globals.conf.keys.MARKOV_CHANNELS, message_id):
            globals.bot.db['archive'].delete_one({'id': message_id})

    @staticmethod
    async def reindex_channel(channel, limit=None, before=None, after=None):
        coll = globals.bot.db['archive']
        coll.delete_many({'channel': channel.id})
        count = 0
        t_last_update = time.time()
        async for message in channel.history(limit=limit, before=before, after=after):
            coll.insert_one(ArchiveListener.message_to_dict(message))
            count += 1
            if t_last_update + 10 < time.time():
                t_last_update = time.time()
                yield count
        yield count

    @staticmethod
    def attachment_to_dict(attachment):
        attachment: discord.Attachment
        return {
            'id': attachment.id,
            'size': attachment.size,
            'height': attachment.height,
            'width': attachment.width,
            'filename': attachment.filename,
            'url': attachment.url,
            'proxy_url': attachment.proxy_url,
            'content_type': attachment.content_type
        }

    @staticmethod
    def message_to_dict(message):
        message: discord.Message
        return {
            'id': message.id,
            'guild': message.guild.id,
            'channel': message.channel.id,
            'author': message.author.id,
            'author_name': message.author.display_name,
            'created_at': message.created_at,
            'edited_at': message.edited_at,
            'content': message.clean_content,
            'pinned': message.pinned,
            'type': message.type.name,
            'embeds': [embed.to_dict() for embed in message.embeds],
            'attachments': [ArchiveListener.attachment_to_dict(attachment) for attachment in message.attachments],
            'url': message.jump_url
        }
