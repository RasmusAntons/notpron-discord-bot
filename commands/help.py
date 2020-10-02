from commands.command import Command
import discord
from discord.utils import escape_markdown


class HelpCommand(Command):
    name = 'help'
    arg_range = (0, 0)
    description = 'list available commands'

    async def execute(self, args, msg):
        embed = discord.Embed(title='Botpron Commands', color=self.bot.config.get_embed_colour())
        for cmd in self.bot.ENABLED_COMMANDS:
            desc = f'*{escape_markdown(cmd.description)}*' if cmd.description else '-'
            if cmd.arg_desc:
                desc += f'\n`{self.bot.prefix}{cmd.name} {cmd.arg_desc}`'
            embed.add_field(name=cmd.name, value=desc, inline=False)
        await msg.channel.send(embed=embed)