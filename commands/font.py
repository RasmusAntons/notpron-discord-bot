from commands.command import Command, Category
from PIL import Image, ImageDraw, ImageFont
import discord
import globals
import os.path


class FontCommand(Command):
    name = 'font'
    category = Category.UTILITY
    arg_range = (1, 99)
    description = 'Generate an image with text.'
    arg_desc = '<text...>'

    async def execute(self, args, msg):
        async with msg.channel.typing():
            font_name = globals.conf.get(globals.conf.keys.FONT)
            if font_name is None or not os.path.exists(f'res/{font_name}.ttf'):
                font_name = 'actionj'
            font = ImageFont.truetype(f'res/{font_name}.ttf', 64)
            text = ' '.join(args)
            im_test = Image.new('RGBA', (100, 100), (255, 255, 255, 0))
            draw = ImageDraw.Draw(im_test)
            size = draw.textsize(text, font=font)
            print(size)
            im = im_test.resize(size)
            draw = ImageDraw.Draw(im)
            draw.text((0, 0), text, font=font)
            im.save('font.png')
            await msg.channel.send(file=discord.File('font.png', filename='font.png'))
