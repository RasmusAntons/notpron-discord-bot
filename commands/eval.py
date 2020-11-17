from commands.command import Command
import asteval
import discord
import io
import multiprocessing
import time
from discord.utils import escape_markdown, escape_mentions


class EvalCommand(Command):
    name = 'eval'
    aliases = ['evaluate', 'solve', 'math', 'maths']
    arg_range = (0, 99)
    description = 'evaluate expression'
    arg_desc = '<expression...>'

    async def execute(self, args, msg):
        query = ' '.join(args)
        try:
            queue = multiprocessing.Queue()
            start = time.time()

            def thread():
                stderr = io.StringIO()
                aeval = asteval.Interpreter(err_writer=stderr, no_print=True)
                r = aeval(query)
                stderr.seek(0)
                err = stderr.read()
                if err:
                    r = err
                queue.put(r)
            t = multiprocessing.Process(target=thread)
            t.start()
            while t.is_alive():
                if time.time() - start > 0.25:
                    t.terminate()
                    res = 'Runtime exceeded :angry:'
                    break
            else:
                res = queue.get()
                res = str(res)
        except Exception as e:
            res = str(e)
        embed = discord.Embed(color=self.bot.config.get_embed_colour())
        embed.add_field(name=escape_mentions(escape_markdown(query)), value=escape_markdown(escape_mentions(res)),
                        inline=False)
        await msg.channel.send(embed=embed)
