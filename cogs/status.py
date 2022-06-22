import discord
from discord.ext import commands

import globals


class StatusCog(commands.Cog, name='Status', description='set status when logging in'):
    @commands.Cog.listener()
    async def on_ready(self):
        listening = globals.conf.get(globals.conf.keys.LISTENING)
        if listening is not None:
            if listening != '':
                await globals.bot.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.listening, name=listening))
            else:
                await globals.bot.change_presence(activity=None)
