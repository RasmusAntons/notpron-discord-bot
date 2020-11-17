from commands.command import Command
import asteval
import discord
import io
from discord.utils import escape_markdown, escape_mentions


class EvalCommand(Command):
    name = 'eval'
    aliases = ['evaluate', 'solve', 'math', 'maths']
    arg_range = (0, 99)
    description = 'evaluate expression'
    arg_desc = '<expression...>'

    async def execute(self, args, msg):
        stderr = io.StringIO()
        aeval = asteval.Interpreter(err_writer=stderr, no_print=True)
        query = ' '.join(args)
        try:
            res = aeval(query)
            res = str(res) if res else ''
            stderr.seek(0)
            err = stderr.read()
            if err:
                res = (res + '\n' + err).strip()
        except Exception as e:
            res = str(e)
        embed = discord.Embed(color=self.bot.config.get_embed_colour())
        embed.add_field(name=escape_mentions(escape_markdown(query)), value=escape_markdown(escape_mentions(res)),
                        inline=False)
        await msg.channel.send(embed=embed)
