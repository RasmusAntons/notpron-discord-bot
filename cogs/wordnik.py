import wordnik.swagger
import wordnik.WordApi
from discord.ext import commands
import globals
import discord
import pandas as pd
import matplotlib.pyplot as plt
import io
import urllib

import utils


class WordnikCog(commands.Cog, name='Wordnik', description='wordnik'):
    @commands.hybrid_command(name='define', description='define a word')
    async def define(self, ctx: commands.Context, word: str, limit: int = 1) -> None:
        api_key = globals.conf.get(globals.conf.keys.WORDNIK_API_KEY, bypass_protected=True)
        wordnik_client = wordnik.swagger.ApiClient(api_key, 'https://api.wordnik.com/v4')
        word_api = wordnik.WordApi.WordApi(wordnik_client)
        dictionaries = 'all'
        try:
            definitions = word_api.getDefinitions(word, limit=(limit + 5), sourceDictionaries=dictionaries)
            definitions = list(filter(lambda d: d.text, definitions))[:limit]
        except urllib.error.HTTPError:
            definitions = None
        if definitions:
            embed = discord.Embed(description=utils.escape_discord(word),
                                  color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
            for definition in definitions:
                text = utils.escape_discord(definition.text)
                text = text.replace('<xref>', '*').replace('</xref>', '*').replace('<em>', '**').replace('</em>', '**')
                embed.add_field(name=definition.partOfSpeech, value=text, inline=False)
            await ctx.reply(embed=embed)
        else:
            await ctx.reply('no definition found')

    @commands.hybrid_command(name='wordfrequency', description='show usage of a word in history')
    async def wordfrequency(self, ctx: commands.Context, word: str, start: int = 1800, end: int = 2022) -> None:
        api_key = globals.conf.get(globals.conf.keys.WORDNIK_API_KEY, bypass_protected=True)
        wordnik_client = wordnik.swagger.ApiClient(api_key, 'https://api.wordnik.com/v4')
        word_api = wordnik.WordApi.WordApi(wordnik_client)
        try:
            frequency = word_api.getWordFrequency(word, startYear=start, endYear=end)
        except urllib.error.HTTPError:
            return await ctx.reply('word not found')
        df = pd.DataFrame(((point.year, point.count) for point in frequency.frequency), columns=['year', 'count'])
        embed = discord.Embed(description=utils.escape_discord(word),
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
        await ctx.reply(file=file, embed=embed)
