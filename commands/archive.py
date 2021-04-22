import discord
from commands.command import Command, Category
import globals
from utils import get_channel
from listeners import ArchiveListener
import config


class ArchiveCommand(Command):
    name = 'archive'
    category = Category.ADMIN
    arg_range = (1, 1)
    description = 'Store all messages from a channel in the database.'
    arg_desc = '<channel>'

    async def check(self, args, msg, test=False):
        return await super().check(args, msg, test) and config.is_admin(msg.author)

    async def execute(self, args, msg):
        if len(msg.channel_mentions) == 1:
            ch = msg.channel_mentions[0]
        else:
            try:
                chid = int(args[0])
                ch = await get_channel(chid)
            except (ValueError, discord.HTTPException):
                raise RuntimeError('Channel not found.')
        print(f'Archiving {ch.name}')
        progress_msg = await msg.channel.send(f'Archiving of {ch.mention} in progress...')
        n = 0
        async for n in ArchiveListener.reindex_channel(ch):
            await progress_msg.edit(content=f'Archiving of {ch.mention} in progress...\n{n} messages archived.')
        await progress_msg.edit(content=f'Archived {ch.mention}.\n{n} messages archived.')
        globals.bot.db['archive_channels'].replace_one({'id': ch.id}, {
            'id': ch.id, 'guild': ch.guild.id, 'guild_name': ch.guild.name, 'name': ch.name, 'topic': ch.topic,
            'users': [member.id for member in ch.members]}, upsert=True)
