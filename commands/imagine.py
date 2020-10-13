from commands.command import Command
from bing_image_downloader import downloader
import glob
import random
import discord
import re
import os


class ImagineCommand(Command):
    name = 'imagine'
    arg_range = (1, 99)
    description = 'get an image for your query'
    arg_desc = '<query...>'
    state = {}

    async def rv_image(self, keyword, adult=False):
        n = (self.state.get(keyword, 0) % 9) + 1
        self.state[keyword] = n
        fn = f'download/{keyword}/Image_{n}'
        if os.path.isfile(fn):
            return fn
        downloader.download(keyword, limit=9, output_dir='download', adult_filter_off=adult, force_replace=True,
                            timeout=10)
        if os.path.isfile(fn):
            return fn
        files = glob.glob(f'download/{keyword}/Image_*')
        if len(files) > 0:
            return files[-1]
        return None

    async def execute(self, args, msg):
        keyword = msg.content[9:].strip() + ' -notpron'
        adult = msg.channel.is_nsfw()
        if not re.match(r'^[A-Za-z0-9 \-+ÄÖÜäöüß]+$', keyword):
            return await msg.channel.send(f'{msg.author.mention} please give me words like /^[A-Za-z0-9 ÄÖÜäöüß]+$/')
        await msg.channel.trigger_typing()
        print(f'Searching for "{keyword}"')
        img_path = await self.rv_image(keyword, adult)
        if not img_path:
            excuses = ['I cannot imagine that', 'I don\'t even know what that is']
            return await msg.channel.send(f'{msg.author.mention} {random.choice(excuses)}')
        await msg.channel.send(file=discord.File(img_path, f'{keyword}.jpg'))
