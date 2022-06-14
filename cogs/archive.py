import discord
from discord.ext import commands

import globals
from utils import get_channel


class ArchiveCog(commands.Cog, name='Archive', description='archive channels'):
    def __init__(self):
        coll_messages = globals.bot.db['archive']
        coll_messages.create_index('id', unique=True)
        coll_messages.create_index('channel')
        coll_messages.create_index('created_at')
        coll_channels = globals.bot.db['archive_channels']
        coll_channels.create_index('id')

    @commands.hybrid_command(name='archive', description='archive all messages in this channel')
    async def archive(self, ctx: commands.Context, channel: discord.TextChannel) -> None:
        print(f'Archiving {channel.name}')
        progress_msg = await ctx.reply(f'Archiving of {channel.mention} in progress...')
        n = 0
        async for n in ArchiveCog.reindex_channel(channel):
            await progress_msg.edit(content=f'Archiving of {channel.mention} in progress...\n{n} messages archived.')
        await progress_msg.edit(content=f'Archived {channel.mention}.\n{n} messages archived.')
        globals.bot.db['archive_channels'].replace_one({'id': channel.id}, {
            'id': channel.id, 'guild': channel.guild.id, 'guild_name': channel.guild.name, 'name': channel.name,
            'topic': channel.topic,
            'users': [member.id for member in channel.members]}, upsert=True)

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        for channel_id in globals.conf.get(globals.conf.keys.ARCHIVE_CHANNELS, []):
            channel = await get_channel(channel_id)
            coll = globals.bot.db['archive']
            last_message = next(
                coll.find({'channel': channel_id}, {'_id': 0, 'created_at': 1}).sort([('created_at', -1)]).limit(1),
                None)
            last_timestamp = last_message['created_at'] if last_message is not None else None
            async for message in channel.history(after=last_timestamp):
                coll.insert_one(self.message_to_dict(message))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if globals.conf.list_contains(globals.conf.keys.ARCHIVE_CHANNELS, message.channel.id):
            globals.bot.db['archive'].insert_one(self.message_to_dict(message))

    @commands.Cog.listener()
    async def on_message_edit(self, before: discord.Message | discord.PartialMessage, after: discord.Message) -> None:
        if globals.conf.list_contains(globals.conf.keys.ARCHIVE_CHANNELS, after.channel.id):
            globals.bot.db['archive'].replace_one({'id': after.id}, self.message_to_dict(after), upsert=True)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message | discord.PartialMessage) -> None:
        if globals.conf.list_contains(globals.conf.keys.ARCHIVE_CHANNELS, message.id):
            globals.bot.db['archive'].delete_one({'id': message.id})

    @staticmethod
    async def reindex_channel(channel: discord.TextChannel, limit=None, before=None, after=None) -> None:
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
    def attachment_to_dict(attachment: discord.Attachment) -> dict:
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
    def message_to_dict(message: discord.Message) -> dict:
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
