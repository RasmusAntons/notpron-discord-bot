from commands.command import Command
import discord
import urllib.request
import exiftool
from discord.utils import escape_markdown, escape_mentions
import os
import io


class ExifCommand(Command):
    name = 'exif'
    aliases = []
    arg_range = (0, 0)
    description = 'solve magiceye image'

    async def execute(self, args, msg):
        attachments = msg.attachments
        if len(attachments) == 0:
            if msg.reference:
                ref = msg.reference.cached_message or await msg.channel.fetch_message(msg.reference.message_id)
                if len(ref.attachments) > 0:
                    attachments = ref.attachments
                else:
                    raise RuntimeError('The referenced message does not have a file attached')
            else:
                raise RuntimeError('Please upload or reference a file with this command')
        attachment = attachments[0]
        req = urllib.request.Request(attachment.url, data=None, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'})
        with open('exif_tmp', 'wb') as f:
            f.write(urllib.request.urlopen(req).read())

        with exiftool.ExifTool() as et:
            metadata = et.get_metadata('exif_tmp')

        os.remove('exif_tmp')

        text = [f'**{escape_markdown(escape_mentions(attachment.filename))}**', '```']
        for key, value in metadata.items():
            key = key.split(':')[-1]
            if key in ('SourceFile', 'FileName', 'Directory', 'FilePermissions'):
                continue
            nextline = f'{key: <24}: {value}'
            while '```' in nextline:
                nextline = nextline.replace('```', '`\u200c`\u200c`')
            text.append(nextline)
        text.append('```')

        res = '\n'.join(text)
        if len(res) <= 2000:
            await msg.channel.send(res)
        else:
            await msg.channel.send(text[0], file=discord.File(io.StringIO('\n'.join(text[2:-1])), f'{attachment.filename}.exif.txt'))