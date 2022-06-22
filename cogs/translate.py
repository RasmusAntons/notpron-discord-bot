import discord
from discord import app_commands
from discord.ext import commands
import pycountry
import translators

import globals
from utils import escape_discord


class TranslateCog(commands.Cog, name='Translate', description='translate text'):
    subst_google = {
        'he': 'iw'
    }
    subst_pycountry = {
        'iw': 'he'
    }

    def __init__(self):
        self.app_commands = [self.context_translate]

    @staticmethod
    def _translate(text: str, source: str = None, dest: str = 'en'):
        if source:
            source = TranslateCog.subst_google.get(source.lower(), source.lower())
        dest = TranslateCog.subst_google.get(dest.lower(), dest.lower())
        if source:
            r = translators.google(text, from_language=source, to_language=dest, is_detail_result=True)
        else:
            r = translators.google(text, to_language=dest, is_detail_result=True)
        r_src = r[1][3]
        r_dst = r[1][1]
        r_text = ' '.join([x[0] for x in r[1][0][0][5]])

        real_src = pycountry.languages.get(alpha_2=TranslateCog.subst_pycountry.get(r_src, r_src))
        src_str = f'{real_src.name} ({real_src.alpha_2})' if real_src else f'{r_src}'
        real_dest = pycountry.languages.get(alpha_2=TranslateCog.subst_pycountry.get(r_dst, r_dst))
        dest_str = f'{real_dest.name} ({real_dest.alpha_2})' if real_dest else f'{r_dst}'
        embed = discord.Embed(color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
        embed.add_field(name=src_str, value=escape_discord(text), inline=False)
        embed.add_field(name=dest_str, value=escape_discord(r_text), inline=False)
        return embed

    @commands.hybrid_command(name='translate', aliases=('t',), description='translate text')
    @app_commands.describe(text='text to translate',
                           source='source language code, default: detect automatically',
                           dest='target language code, default: en')
    async def translate(self, ctx: commands.Context, text: str, source: str = None, dest: str = 'en') -> None:
        await ctx.defer()
        embed = self._translate(text, source, dest)
        await ctx.reply('result', embed=embed)

    @staticmethod
    @app_commands.context_menu(name='translate')
    async def context_translate(interaction: discord.Interaction, message: discord.Message):
        await interaction.response.defer()
        try:
            embed = TranslateCog._translate(message.clean_content)
        except Exception as e:
            await interaction.followup.send(str(e), ephemeral=True)
            await globals.bot.report_error(e, 'context_translate')
            return
        await interaction.followup.send(embed=embed)
