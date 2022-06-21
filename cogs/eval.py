import asyncio
import io
import multiprocessing
import random
import time
import traceback

import asteval
import discord
from discord.ext import commands

import globals
from utils import to_code_block


async def _evaluate(query: str):
    res = to_code_block(query, 'py')
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
            r = str(queue.get())
            res += to_code_block(r)
    except Exception as e:
        res += to_code_block(str(e))
    return res


class EvalModal(discord.ui.Modal, title='Eval'):
    code = discord.ui.TextInput(
        label='python code',
        style=discord.TextStyle.long,
        placeholder='enter python code here',
        row=4
    )

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(await _evaluate(self.code.value))


class EvalCog(commands.Cog, name='Eval', description='evaluate python expression'):
    @commands.hybrid_command(name='eval', aliases=('solve', 'calc', 'math', 'maths'),
                             description='evaluate python expression')
    async def eval(self, ctx: commands.Context, query: str = None) -> None:
        if query is None:
            if ctx.interaction is None:
                raise RuntimeError('use slash command to access the multiline editor')
            await ctx.interaction.response.send_modal(EvalModal(timeout=None))
            return
        else:
            await ctx.reply(await _evaluate(query))
