from commands.command import Command, Category
import discord
import urllib.request
import exiftool
from utils import escape_discord, to_code_block
import os
import io

important_tags = ['XMP:Location', 'XMP:Title', 'XMP:Creator', 'Photoshop:SlicesGroupName', 'IPTC:By-line',
                  'IPTC:ObjectName', 'IPTC:Sub-location', 'EXIF:XPComment', 'EXIF:UserComment',
                  'Composite:GPSPosition', 'PNG:AnimationFrames', 'GIF:FrameCount', 'GIF:Duration',
                  'EXIF:Model', 'XMP:DateCreated', 'CreationTime', 'File:FileModifyDate',
                  'File:FileAccessDate', 'File:FileType', 'Composite:ImageSize']


class ExifCommand(Command):
    name = 'exif'
    category = Category.UTILITY
    arg_range = (0, 1)
    arg_desc = '[all]'
    description = 'show file file metadata'

    async def execute(self, args, msg):
        attachments = msg.attachments
        if len(args) == 1:
            if args[0].endswith('all'):
                all_tags = True
            else:
                raise RuntimeError('Invalid argument:')
        else:
            all_tags = False
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
        req = urllib.request.Request(attachment.url, data=None, headers={
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'})
        with open('exif_tmp', 'wb') as f:
            f.write(urllib.request.urlopen(req).read())

        with exiftool.ExifTool() as et:
            if all_tags:
                metadata = et.get_metadata('exif_tmp')
            else:
                metadata = et.get_tags(important_tags, 'exif_tmp')

        os.remove('exif_tmp')

        text = [f'**{escape_discord(attachment.filename)}**', '```']
        for key, value in metadata.items():
            key = key.split(':')[-1]
            if key in ('SourceFile', 'FileName', 'Directory', 'FilePermissions'):
                continue
            nextline = f'{key: <24}: {value}'
            while '```' in nextline:
                nextline = nextline.replace('```', '`\u200c`\u200c`')
            text.append(nextline)
        text.append('```' + ('Use "exif all" to see all tags.' if not all_tags else ''))

        res = '\n'.join(text)
        if len(res) <= 2000:
            await msg.channel.send(res)
        else:
            await msg.channel.send(text[0], file=discord.File(io.StringIO('\n'.join(text[2:-1])),
                                                              f'{attachment.filename}.exif.txt'))
