import random

from discord import app_commands
from discord.ext import commands


class RollCog(commands.Cog, name='Roll', description='roll a die'):
    @commands.hybrid_command(name='roll', description='roll a die')
    @app_commands.describe(amount='number of dice to roll', sides='number of sides on each die')
    async def roll(self, ctx: commands.Context, amount: int = 1, sides: int = 6) -> None:
        if amount > 100:
            raise RuntimeError('too many dice >:(')
        rolls = [random.randint(1, sides) for _ in range(amount)]
        res = f'{sum(rolls)}'
        if amount > 1:
            rolls_s = [str(roll) for roll in rolls]
            res += f' ({" + ".join(rolls_s)})'
        await ctx.reply(res)
