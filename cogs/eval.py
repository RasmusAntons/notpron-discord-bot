from cogs.command import Command, Category
import asteval
import asyncio
import discord
import io
import multiprocessing
import time
import random
import globals
from utils import escape_discord


class EvalCommand(Command):
    name = 'eval'
    category = Category.UTILITY
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
                stdout = io.StringIO()
                stderr = io.StringIO()
                aeval = asteval.Interpreter(writer=stdout, err_writer=stderr, use_numpy=False)
                del aeval.symtable['open']
                aeval.symtable['random'] = random.random
                aeval.symtable['choice'] = random.choice
                aeval.symtable['randrange'] = random.randrange
                r = aeval(query)
                for stream in (stdout, stderr):
                    stream.seek(0)
                    err = stream.read()
                    if err:
                        r = err
                queue.put(r)
            timeout = globals.conf.get(globals.conf.keys.EVAL_TIMEOUT, 250) / 1000
            t = multiprocessing.Process(target=thread)
            t.start()
            while t.is_alive():
                time_left = start + timeout - time.time()
                if time_left < 0:
                    t.terminate()
                    res = 'Runtime exceeded :angry:'
                    break
                await asyncio.sleep(max(0.25, time_left))
            else:
                res = queue.get()
                res = str(res)
        except Exception as e:
            res = str(e)
        embed = discord.Embed(color=globals.conf.get(globals.conf.keys.EMBED_COLOUR, 0))
        embed.add_field(name=escape_discord(query), value=escape_discord(res), inline=False)
        await msg.channel.send(embed=embed)
