import requests
import wordnik.swagger
import wordnik.WordApi
from commands.command import Command, Category
import globals
import discord
import pandas as pd
import matplotlib.pyplot as plt
import io
import urllib

import utils


class WordnikCommand(Command):
    name = 'wordnik'
    category = Category.UTILITY
    aliases = ['define']
    arg_range = (1, 99)
    description = 'define a word'
    arg_desc = '(define <query...> [limit=<n>])|(frequency <query...> [start=<n>] [end=<n>])'

    async def send_usage(self):
        pass

    async def execute(self, args, msg):
        api_key = globals.conf.get(globals.conf.keys.WORDNIK_API_KEY, bypass_protected=True)
        wordnik_client = wordnik.swagger.ApiClient(api_key, 'https://api.wordnik.com/v4')
        word_api = wordnik.WordApi.WordApi(wordnik_client)
        for subcmd in ['define']:
            if msg.content.split(' ')[0][1:] == subcmd:
                args.insert(0, subcmd)
        if args[0] == 'define':
            query = []
            limit = 1
            for arg in args[1:]:
                if arg.startswith('limit='):
                    limit = int(arg[6:])
                else:
                    query.append(arg)
            query = ' '.join(query)
            if not query:
                return False
            return await self.define(word_api, msg, query, limit)
        elif args[0] == 'frequency':
            query = []
            start = 1800
            end = 2022
            for arg in args[1:]:
                if arg.startswith('start='):
                    start = int(arg[6:])
                elif arg.startswith('end='):
                    end = int(arg[4:])
                else:
                    query.append(arg)
            query = ' '.join(query)
            if not query:
                return False
            await self.frequency(word_api, msg, query, start=start, end=end)
        else:
            return False
        return True

    async def define(self, word_api, msg, query, limit=1):
        dictionaries = 'all'
        try:
            definitions = word_api.getDefinitions(query, limit=limit + 5, sourceDictionaries=dictionaries)
            definitions = list(filter(lambda d: d.text, definitions))[:limit]
        except urllib.error.HTTPError:
            definitions = None
        if definitions:
            embed = discord.Embed(description=utils.escape_discord(query),
                                  color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
            for definition in definitions:
                text = utils.escape_discord(definition.text)
                text = text.replace('<xref>', '*').replace('</xref>', '*').replace('<em>', '**').replace('</em>', '**')
                embed.add_field(name=definition.partOfSpeech, value=text, inline=False)
            await msg.reply(embed=embed)
        else:
            await msg.reply('no definition found')

    async def frequency(self, word_api, msg, query, start=1800, end=2022):
        try:
            frequency = word_api.getWordFrequency(query, startYear=start, endYear=end)
        except urllib.error.HTTPError:
            return await msg.reply('word not found')
        df = pd.DataFrame(((point.year, point.count) for point in frequency.frequency), columns=['year', 'count'])
        embed = discord.Embed(description=utils.escape_discord(query),
                              color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
        p = df.plot(x='year', y='count', kind='line', grid=True, figsize=(7.5, 4.1), color='#a6ce86', legend=False)
        p.set_facecolor('#2f3136')
        p.get_figure().set_facecolor('#2f3136')
        p.get_figure().subplots_adjust(top=0.95, bottom=0.16, right=0.98, left=.11)
        for spine in p.spines.values():
            spine.set_color('#b0b0b0')
        p.xaxis.label.set_color('white')
        p.set_ylabel('count', color='white')
        p.tick_params(axis='x', colors='white')
        p.tick_params(axis='y', colors='white')
        p.title.set_color('white')
        out_file = io.BytesIO()
        plt.savefig(out_file)
        plt.close()
        out_file.seek(0)
        file = discord.File(out_file, filename=f'frequency.png')
        embed.set_image(url=f'attachment://frequency.png')
        await msg.reply(file=file, embed=embed)
