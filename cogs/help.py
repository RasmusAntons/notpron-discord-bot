from cogs.command import Command, Category
import discord
from discord.utils import escape_markdown
import globals


class HelpCommand(Command):
    name = 'help'
    category = Category.UTILITY
    arg_range = (0, 1)
    description = 'list available commands'
    arg_desc = '[category]'

    async def execute(self, args, msg):
        categories = {category.value: [] for category in Category}
        embed_colour = globals.bot.conf.get(globals.bot.conf.keys.EMBED_COLOUR, 0)
        prefix = globals.bot.conf.get(globals.bot.conf.keys.PREFIX)
        for cmd in globals.bot.commands_flat:
            if await cmd.is_admin([], msg, test=True):
                categories[cmd.category.value].append(cmd)
        embed = None
        if len(args) == 1:
            commands = categories.get(args[0].lower())
            if commands:
                embed = discord.Embed(title=f'{globals.bot.user.name} {args[0].title()} Commands', color=embed_colour)
                for cmd in commands:
                    desc = f'*{escape_markdown(cmd.description)}*' if cmd.description else '-'
                    if cmd.arg_desc:
                        desc += f'\n`{prefix}{cmd.name} {cmd.arg_desc}`'
                    embed.add_field(name=cmd.name, value=desc, inline=False)
        if embed is None:
            embed = discord.Embed(title=f'{globals.bot.user.name} Command Categories', color=embed_colour)
            for category, commands in categories.items():
                if commands:
                    embed.add_field(name=category, value=f'{len(commands)} commands.', inline=False)
            embed.set_footer(text=f'Use `{prefix}{self.name} [category]` to see the commands.')
        await msg.channel.send(embed=embed)
