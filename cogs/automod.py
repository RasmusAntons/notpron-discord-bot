import globals
import cogs.softban
from discord.ext import commands
import discord
import datetime

class AutomodListener(commands.Cog):
    def __init__(self):
        self.coll_members = globals.bot.db['automod_members']
        self.coll_members.create_index('uid')

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.type not in [discord.MessageType.default, discord.MessageType.reply]:
            return
        if not isinstance(msg.author, discord.Member):
            return
        multiple_attachments = len(msg.attachments) > 1
        new_member = msg.author.joined_at is not None and msg.author.joined_at > (datetime.datetime.now(datetime.UTC) - datetime.timedelta(days=7))
        past_messages = self.coll_members.find_one({'uid': msg.author.id})
        if past_messages is None:
            self.coll_members.insert_one({'uid': msg.author.id})
            suspicious = multiple_attachments and new_member
            if suspicious:
                await globals.bot.get_cog('Softban').softban_internal(msg.author, globals.bot.user)
                mod_channel = discord.utils.get(msg.author.guild.channels, id=globals.bot.conf.get(globals.bot.conf.keys.MOD_CHANNEL))
                if mod_channel:
                    await mod_channel.send(f'{msg.author.mention} has been automatically softbanned for this message {msg.jump_url}')
