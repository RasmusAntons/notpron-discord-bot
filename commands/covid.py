from commands.command import Command
from covid19.bin import run as covid19
import discord
from millify import millify, prettify


class CovidCommand(Command):
    name = 'covid'
    arg_range = (0, 99)
    description = 'show covid-19 data for a location'
    arg_desc = '[location...]'

    async def execute(self, args, msg):
        key = self.bot.config.get_geocode_api_key()
        query = ' '.join(args)
        res = covid19.main(query, key=key)
        colour = self.bot.config.get_embed_colour()
        embed = discord.Embed(title=f'COVID-19 data for {res.region or query}', color=colour)
        embed.add_field(name='Total Cases', value=prettify(res.cum_cases))
        embed.add_field(name='Total Deaths', value=prettify(res.cum_deaths))
        embed.add_field(name='Population', value=millify(res.pop, precision=2))
        embed.add_field(name='7 day average cases per million', value=f'{res.sda_cpm: .2f}')
        embed.add_field(name='7 day average deaths per million', value=f'{res.sda_dpm: .2f}')
        source = f'[{res.source}]({res.source_url})' if res.source_url else res.source
        embed.add_field(name='Source', value=source)
        await msg.channel.send(embed=embed)
