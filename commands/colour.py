from commands.command import Command
from PIL import Image
import discord


class ColourCommand(Command):
    name = 'colour'
    aliases = ['color']
    arg_range = (1, 1)
    description = 'display a 6-digit hex colour'
    arg_desc = '<hex colour>'

    async def execute(self, args, msg):
        col = args[0].replace('#', '')
        if len(col) != 6:
            raise ValueError('I need a 6-digit hex value')
        col = int(col, 16)
        im = Image.new("RGB", (128, 128), f'#{col:06X}')
        im.save('colour.png')
        await msg.channel.send(file=discord.File('colour.png', filename=f'{col:06x}.png'))
