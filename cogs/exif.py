import io
import os
import urllib.request

import discord
from discord.app_commands import context_menu
from discord.ext import commands
import exiftool
from urllib.parse import urlparse

from utils import escape_discord

skip_keys = ['SourceFile', 'FileName', 'Directory', 'FilePermissions', 'FileModifyDate', 'FileAccessDate',
             'FileInodeChangeDate']


def _exif(url):
    req = urllib.request.Request(url, data=None, headers={
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'})
    with open('exif_tmp', 'wb') as f:
        f.write(urllib.request.urlopen(req).read())
    with exiftool.ExifToolHelper() as et:
        metadata = et.get_metadata('exif_tmp')
    os.remove('exif_tmp')
    attrs = []
    for key, value in metadata[0].items():
        key = key.split(':')[-1]
        if key in skip_keys:
            continue
        attrs.append(f'{key: <24}: {value}')
    return '\n'.join(attrs)


class ExifCog(commands.Cog, name='Exif', description='show file file metadata'):
    def __init__(self):
        self.app_commands = [self.context_exif]

    @commands.hybrid_command(name='exif', description='show file file metadata')
    async def exif(self, ctx: commands.Context, file: discord.Attachment) -> None:
        res = _exif(file.url)
        res_file = discord.File(io.StringIO(res), f'{name}.exif.txt')
        await ctx.reply(f'**{escape_discord(file.filename)}**', file=res_file)

    @staticmethod
    @context_menu(name='exif')
    async def context_exif(interaction: discord.Interaction, message: discord.Message):
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
            res = _exif(url)
            res_file = discord.File(io.StringIO(res), f'{name}.exif.txt')
            await interaction.response.send_message(f'**{escape_discord(name)}**', file=res_file)
        else:
            await interaction.response.send_message('cannot find a file in that message', ephemeral=True)
