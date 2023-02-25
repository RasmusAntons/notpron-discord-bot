import io
import math
import os
from urllib.parse import urlparse
import urllib.request

from PIL import Image
import discord
from discord import app_commands
from discord.ext import commands
import numpy as np

import globals


def _magiceye(url):
    req = urllib.request.Request(url, data=None, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'
    })
    in_file = io.BytesIO(urllib.request.urlopen(req).read())
    image = Image.open(in_file).convert("RGB")
    image1 = np.array(image, dtype=int)
    image2 = image.convert("L")
    image2 = np.array(image2, dtype=int)
    image2 = image2[::image.height // 10, :]
    height, width = image2.shape
    uwu = math.inf
    iwi = 0
    for i in range(10, width // 2):
        owo = (np.sum(np.abs(image2 - np.roll(image2, i, 1))))
        if owo < uwu:
            uwu = owo
            iwi = i
    out_file = io.BytesIO()
    Image.fromarray(np.uint8(np.abs(image1 - np.roll(image1, iwi, 1))), mode="RGB").save(out_file, 'PNG')
    out_file.seek(0)
    return out_file


class MagiceyeCog(commands.Cog, name='Magiceye', description='solve magiceye image'):
    def __init__(self):
        self.ctx_menu = app_commands.ContextMenu(name='magiceye', callback=self.context_magiceye)
        self.app_commands = [] # self.ctx_menu]

    @commands.hybrid_command(name='magiceye', description='solve magiceye image')
    async def magiceye(self, ctx: commands.Context, file: discord.Attachment) -> None:
        if ctx.interaction:
            await ctx.interaction.response.defer()
            out_file = _magiceye(file.url)
        else:
            async with ctx.channel.typing():
                out_file = _magiceye(file.url)
        await ctx.reply(file=discord.File(out_file, filename=f'{file.filename}.png', spoiler=True))

    async def context_magiceye(self, interaction: discord.Interaction, message: discord.Message):
        url = None
        name = None
        if message.attachments:
            file = message.attachments[0]
            url = file.url
            name = file.filename
        elif message.embeds:
            for embed in message.embeds:
                if embed.url:
                    url = embed.url
                    parsed_url = urlparse(url)
                    name = os.path.basename(parsed_url.path)
                    break
        if url:
            await interaction.response.defer()
            try:
                out_file = _magiceye(url)
                await interaction.followup.send(file=discord.File(out_file, filename=f'{name}.png', spoiler=True))
            except Exception as e:
                await interaction.followup.send(str(e), ephemeral=True)
                await globals.bot.report_error(e, 'context_magiceye')
        else:
            await interaction.response.send_message('cannot find a file in that message', ephemeral=True)
