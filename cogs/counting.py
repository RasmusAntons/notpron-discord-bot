import discord
from discord import app_commands
from discord.ext import commands

import globals
import logging

class CountingCog(commands.Cog):
    def __init__(self):
        self.coll = globals.bot.db['counting']
        self.coll.create_index('chid')

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.interaction:
            return
        state = self.coll.find_one({'chid': msg.channel.id})
        valid = False
        progress = 0
        if state is not None:
            progress = state.get('progress')
            content = msg.content
            valid = progress is not None and content.isnumeric() and int(content) == progress + 1 and state.get('last_uid') != msg.author.id
        elif msg.content.isnumeric() and int(msg.content) == 1:
            valid = True
        if valid:
            self.coll.replace_one({'chid': msg.channel.id}, {'chid': msg.channel.id, 'last_uid': msg.author.id, 'progress': progress + 1}, upsert=True)
            await msg.add_reaction('✅')
        elif state is not None:
            self.coll.delete_one({'chid': msg.channel.id})
            await msg.add_reaction('❌')
            if progress >= 3:
                if msg.author.id == globals.bot.user.id:
                    await msg.reply('# aw fuck')
                else:
                    await msg.reply('# nopers <:angrymeepers2:1255963929184567306>')
