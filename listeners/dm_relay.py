from listeners import MessageListener, MessageEditListener, MessageDeleteListener
import discord
import discord.errors
import globals
from utils import get_channel, get_user
import datetime


class DmRelayListener(MessageListener, MessageEditListener, MessageDeleteListener):
    image_types = ('image/jpeg', 'image/png', 'image/gif')

    def __init__(self):
        super(DmRelayListener, self).__init__()
        globals.bot.db['db_relay'].create_index('dm_message')
        globals.bot.db['db_relay'].create_index('relayed_message')

    def create_embed(self, msg):
        embed = discord.Embed(colour=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
        embed.set_author(name=f'{msg.author.display_name}', icon_url=f'{msg.author.avatar_url_as(size=32)}')
        embed.description = msg.content
        image_set = False
        for attachment in msg.attachments:
            if attachment.content_type in self.image_types and not image_set:
                embed.set_image(url=attachment.url)
                image_set = True
            else:
                embed.add_field(name='Attachment', value=f'[{attachment.filename}]({attachment.url})')
        return embed

    async def on_message(self, msg):
        if msg.author.id == globals.bot.user.id:
            return
        dm_relay_channel_id = globals.conf.get(globals.conf.keys.DM_RELAY_CHANNEL)
        if type(msg.channel) == discord.DMChannel:
            coll = globals.bot.db['db_relay']
            if dm_relay_channel_id:
                ch = await get_channel(dm_relay_channel_id)
                relayed_message = await ch.send(embed=self.create_embed(msg))
                coll.insert_one({'dm_message': msg.id, 'relayed_message': relayed_message.id, 'uid': msg.author.id})
        elif dm_relay_channel_id and msg.channel.id == dm_relay_channel_id:
            if msg.reference:
                coll = globals.bot.db['db_relay']
                relayed_pair = coll.find_one({'relayed_message': msg.reference.message_id})
                if not relayed_pair:
                    return
                user = await get_user(relayed_pair['uid'])
                if not user:
                    raise RuntimeError(f'Cannot find user {relayed_pair["uid"]}.')
                ch = await globals.bot.get_dm_channel(user)
                files = [await attachment.to_file() for attachment in msg.attachments]
                response = await ch.send(msg.content, files=files)
                coll.insert_one({'dm_message': response.id, 'relayed_message': msg.id,  'uid': user.id})

    async def on_message_edit(self, message, cached_message=None):
        if message.author.id == globals.bot.user.id:
            return
        dm_relay_channel_id = globals.conf.get(globals.conf.keys.DM_RELAY_CHANNEL)
        if type(message.channel) == discord.DMChannel:
            coll = globals.bot.db['db_relay']
            relayed_pair = coll.find_one({'dm_message': message.id})
            if not relayed_pair:
                return
            relay_channel = await get_channel(dm_relay_channel_id)
            relayed_message = await relay_channel.fetch_message(relayed_pair['relayed_message'])
            if not relayed_message:
                return
            await relayed_message.edit(embed=self.create_embed(message))
        elif message.channel.id == dm_relay_channel_id:
            coll = globals.bot.db['db_relay']
            relayed_pair = coll.find_one({'relayed_message': message.id})
            if not relayed_pair:
                return
            user = await get_user(relayed_pair['uid'])
            if not user:
                return
            ch = await globals.bot.get_dm_channel(user)
            dm_message = await ch.fetch_message(relayed_pair['dm_message'])
            await dm_message.edit(content=message.content)

    async def on_message_delete(self, message_id, channel, guild, cached_message=None):
        coll = globals.bot.db['db_relay']
        relayed_pair = coll.find_one({'$or': [{'dm_message': message_id}, {'relayed_message': message_id}]})
        if not relayed_pair:
            return
        if relayed_pair['dm_message'] == message_id:
            dm_relay_channel_id = globals.conf.get(globals.conf.keys.DM_RELAY_CHANNEL)
            relay_channel = await get_channel(dm_relay_channel_id)
            try:
                relayed_message = await relay_channel.fetch_message(relayed_pair['relayed_message'])
            except discord.errors.NotFound:
                return
            if relayed_message.author.id != globals.bot.user.id:
                return
            if len(relayed_message.embeds) == 0:
                return
            embed = relayed_message.embeds[0]
            embed.set_footer(text=f'Message deleted at {datetime.datetime.utcnow().replace(microsecond=0)}.')
            await relayed_message.edit(embed=embed)
        elif relayed_pair['relayed_message'] == message_id:
            user = await get_user(relayed_pair['uid'])
            if not user:
                return
            ch = await globals.bot.get_dm_channel(user)
            try:
                dm_message = await ch.fetch_message(relayed_pair['dm_message'])
            except discord.errors.NotFound:
                return
            if dm_message.author.id != globals.bot.user.id:
                return
            await dm_message.delete()
