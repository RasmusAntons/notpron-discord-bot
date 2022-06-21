from PIL import Image, ImageDraw, ImageFont
import discord
import globals
import os.path
import io
from discord.ext import commands


class FontCog(commands.Cog, name='Font', description='generate an image with text'):
    @commands.hybrid_command(name='font', description='generate an image with text')
    async def font(self, ctx: commands.Context, text: str) -> None:
        async with ctx.channel.typing():
            font_name = globals.conf.get(globals.conf.keys.FONT)
            if font_name is None or not os.path.exists(f'res/{font_name}.ttf'):
                font_name = 'actionj'
            font = ImageFont.truetype(f'res/{font_name}.ttf', 64)
            im_test = Image.new('RGBA', (100, 100), (255, 255, 255, 0))
            draw = ImageDraw.Draw(im_test)
            size = draw.textsize(text, font=font)
            im = im_test.resize(size)
            draw = ImageDraw.Draw(im)
            draw.text((0, 0), text, font=font)
            out_file = io.BytesIO()
            im.save(out_file, 'PNG')
            out_file.seek(0)
            await ctx.reply(file=discord.File(out_file, filename='font.png'))
