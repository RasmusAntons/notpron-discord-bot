from commands.command import Command
from PIL import Image, ImageDraw, ImageFont
import discord


class FontCommand(Command):
    name = 'font'
    arg_range = (1, 99)
    description = 'generate an image with text'
    arg_desc = '<text...>'
    guilds = [363692038002180097]  # todo: enigmatics font?

    async def execute(self, args, msg):
        await msg.channel.trigger_typing()
        font = ImageFont.truetype('res/actionj.ttf', 64)
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
