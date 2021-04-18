from commands.command import Command, Category
import covid19
import discord
from millify import millify, prettify
import matplotlib.pyplot as plt
import datetime
import re
import io
import globals


class CovidCommand(Command):
    name = 'covid'
    category = Category.UTILITY
    arg_range = (0, 99)
    description = 'show covid-19 data for a location'
    arg_desc = '[location...]'

    async def execute(self, args, msg):
        key = globals.bot.conf.get(globals.bot.conf.keys.GMAPS_API_KEY, bypass_protected=True)
        if key is None:
            raise RuntimeError('Google maps API key not set.')
        query = ' '.join(args)
        res = covid19.data(query, key=key)
        colour = globals.bot.conf.get(globals.bot.conf.keys.EMBED_COLOUR)
        embed = discord.Embed(title=f'COVID-19 data for {res.region or query}', color=colour)
        embed.add_field(name='Total Cases', value=prettify(res.cum_cases))
        embed.add_field(name='Total Deaths', value=prettify(res.cum_deaths))
        if res.pop is not None:
            embed.add_field(name='Population', value=millify(res.pop, precision=2))
            embed.add_field(name='7 day average cases per million', value=f'{res.sda_cpm: .2f}')
            embed.add_field(name='7 day average deaths per million', value=f'{res.sda_dpm: .2f}')
        source = f'[{res.source}]({res.source_url})' if res.source_url else res.source
        embed.add_field(name='Source', value=source)

        dfm = res.df.rolling(7, on='date').mean()
        p = dfm.plot(x='date', y='new_cases', kind='line', grid=True, figsize=(7.5, 4.1), color='#a6ce86', legend=False)
        p.set_facecolor('#2f3136')
        p.get_figure().set_facecolor('#2f3136')
        xticks = list(dfm.date[::len(dfm.date)//8])
        if type(xticks[0]) == str:
            xlabels = list(map(lambda e: datetime.datetime.strptime(e, '%Y-%m-%d').date(), xticks))
            xticks = range(0, len(dfm.date), len(dfm.date)//8)
        else:
            xlabels = xticks
        p.set_xticks(xticks)
        p.set_xticklabels(map(lambda e: e.strftime('%Y-%m-%d'), xlabels), rotation=25)
        p.get_figure().subplots_adjust(top=0.95, bottom=0.16, right=0.98, left=.11)
        for spine in p.spines.values():
            spine.set_color('#b0b0b0')
        p.xaxis.label.set_color('white')
        p.set_ylabel('new cases (7 day average)', color='white')
        p.tick_params(axis='x', colors='white', labelrotation=15)
        p.tick_params(axis='y', colors='white')
        p.title.set_color('white')
        out_file = io.BytesIO()
        plt.savefig(out_file)
        plt.close()
        out_file.seek(0)
        region = re.sub(r'[^a-zA-Z0-9_]+', '_', res.region).strip('_')
        file = discord.File(out_file, filename=f'{region}.png')
        embed.set_image(url=f'attachment://{region}.png')
        await msg.channel.send(file=file, embed=embed)
