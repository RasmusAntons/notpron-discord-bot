from commands.command import Command
import discord
from PIL import Image
import numpy as np
import math
import urllib.request
import io


class MagiceyeCommand(Command):
    name = 'magiceye'
    aliases = []
    arg_range = (0, 0)
    description = 'solve magiceye image'

    async def execute(self, args, msg):
        attachments = msg.attachments
        if len(attachments) != 1:
            raise RuntimeError('Please upload an image (png/gif/jpg) with this command')
        attachment = attachments[0]
        if attachment.filename[-4:] not in ('.png', '.gif', '.jpg'):
            raise RuntimeError('Only .png, .gif and .jpg images are supported')
        req = urllib.request.Request(attachment.url, data=None, headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0'})
        in_file = io.BytesIO(urllib.request.urlopen(req).read())
        image = Image.open(in_file).convert("L")
        image1 = np.array(image, dtype=int)
        image2 = image.copy()
        image2.thumbnail((400, 400))
        image2 = np.array(image2, dtype=int)

        height, width = image2.shape
        uwu = math.inf
        iwi = 0

        for i in range(10, width // 2):
            owo = (np.sum(np.abs(image2 - np.roll(image2, i, 1))))
            if owo < uwu:
                uwu = owo
                iwi = i

        iwi = iwi * image.width // width
        uwu = math.inf

        for i in range(iwi - image.width // width, iwi + image.width // width):
            owo = (np.sum(np.abs(image - np.roll(image, i, 1))))
            if owo < uwu:
                uwu = owo
                iwi = i

        out_file = io.BytesIO()
        Image.fromarray(np.uint8(np.abs(image1 - np.roll(image1, iwi, 1))), mode="L").save(out_file, 'PNG')
        out_file.seek(0)
        await msg.channel.send(f'I solved your magiceye, {msg.author.mention}', file=discord.File(out_file, filename=f'{attachment.filename}.png', spoiler=True))
