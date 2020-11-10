from commands.command import Command
from googletrans import Translator
import discord
import pycountry
from discord.utils import escape_markdown, escape_mentions


class TranslateCommand(Command):
    name = 'translate'
    aliases = ['t']
    arg_range = (0, 99)
    description = 'translate text'
    arg_desc = '<text...> [src=<language>] [dest=<language>]'
    subst_google = {
        'he': 'iw'
    }
    subst_pycountry = {
        'iw': 'he'
    }

    async def execute(self, args, msg):
        src = None
        dest = 'en'
        text = []
        for arg in args:
            if arg.startswith('src='):
                src = self.subst_google.get(arg[4:]) or arg[4:]
            elif arg.startswith('dest='):
                dest = self.subst_google.get(arg[5:]) or arg[5:]
                if src in self.subst_google:
                    src = self.subst_google[src]
            else:
                text.append(arg)
        text = ' '.join(text)
        for i in range(100):
            try:
                translator = Translator()
                if src is not None:
                    r = translator.translate(text, src=src, dest=dest)
                else:
                    r = translator.translate(text, dest=dest)
                break
            except AttributeError:
                pass
        else:
            raise RuntimeError('Failed to google translate 100 times :sob:')

        real_src = pycountry.languages.get(alpha_2=self.subst_pycountry.get(r.src) or r.src)
        src_str = f'{real_src.name} ({real_src.alpha_2})' if real_src else f'{r.src}'
        real_dest = pycountry.languages.get(alpha_2=self.subst_pycountry.get(r.dest) or r.dest)
        dest_str = f'{real_dest.name} ({real_dest.alpha_2})' if real_dest else f'{r.dest}'
        embed = discord.Embed(color=self.bot.config.get_embed_colour())
        embed.add_field(name=src_str, value=escape_markdown(escape_mentions(text)), inline=False)
        embed.add_field(name=dest_str, value=escape_markdown(escape_mentions(r.text)), inline=False)
        confidence = r.extra_data.get('confidence')
        possible_mistakes = r.extra_data.get('possible-mistakes')
        if type(possible_mistakes) == list and len(possible_mistakes) >= 2:
            possible_mistakes = possible_mistakes[1]
        ft = f'confidence: {confidence}, possible mistakes: {possible_mistakes}'
        embed.set_footer(text=ft)
        await msg.channel.send(embed=embed)
