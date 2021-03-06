from commands.command import Command
import glob
import os
from discord.utils import escape_markdown
import youtube_dl
import asyncio
import re


class HwCommand(Command):
    name = 'hw'
    arg_range = (1, 2)
    description = 'manage halloween music queue'
    arg_desc = 'list | remove <list index> | yt <youtube url>'
    guilds = [363692038002180097]  # todo: enigmatics music? fix

    async def check(self, args, msg):
        if not msg.channel.guild.id in self.guilds:
            return False
        for role in msg.author.roles:
            if role.name.lower() in ['moderator', 'tech support', 'dj']:
                return True
        else:
            return False

    async def execute(self, args, msg):
        songs = glob.glob('res/halloween/*')
        if args[0] == 'list':
            text = 'Halloween Queue:\n```' + '\n'.join([f'{i:2d}. {song[14:]}' for i, song in enumerate(songs)]) + '```'
            await msg.channel.send(text)
        elif args[0] == 'remove':
            n = int(args[1])
            song = songs[n]
            os.remove(song)
            await msg.channel.send(f'{msg.author.mention} deleted {escape_markdown(song[14:])}')
        elif args[0] == 'yt':
            bot = self.bot
            message = await msg.channel.send(f'starting download...')

            def my_hook(d):
                if d['status'] == 'downloading':
                    txt = f'{d["status"]}: {d["_percent_str"]}'
                if d['status'] == 'finished':
                    txt = f'done 😺'
                asyncio.run_coroutine_threadsafe(message.edit(content=txt), bot.loop)

            ydl_opts = {
                'format': 'bestaudio/best',
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '140',
                }],
                'progress_hooks': [my_hook],
                'outtmpl': 'res/halloween/%(title)s.%(ext)s'
            }
            with youtube_dl.YoutubeDL(ydl_opts) as ydl:
                ydl.download([args[1]])
