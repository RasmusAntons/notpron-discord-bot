from listeners import ReadyListener
import discord
import globals


class StatusListener(ReadyListener):
    async def on_ready(self):
        listening = globals.conf.get(globals.conf.keys.LISTENING)
        if listening is not None:
            if listening != '':
                await globals.bot.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.listening, name=listening))
            else:
                await globals.change_presence(activity=None)
