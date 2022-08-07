import discord
from discord.ext import commands

import globals


class NotpronCog(discord.ext.commands.Cog, name='Notpron',
                 description='get notpron level hints, antihints and threads'):
    guild_ids = [363692038002180097]

    def __init__(self):
        globals.bot.db['hints'].create_index('level', unique=True)
        globals.bot.db['antihints'].create_index('level', unique=True)
        globals.bot.db['threads'].create_index('level', unique=True)

    @staticmethod
    async def check(ctx: commands.Context):
        return ctx.guild.id in NotpronCog.guild_ids

    async def _hint(self, ctx: commands.Context, level: str, antihint=False):
        hint = None
        n = None
        result = None
        try:
            n = int(level)
            coll = globals.bot.db['hints' if not antihint else 'antihints']
            result = coll.find_one({'level': str(n)})
            if result:
                hint = result['value']
        except ValueError:
            pass
        if hint is None:
            res = ['Type !hint <level number from 1-79> for a level specific hint. No hints for 80 and beyond!']
        else:
            if not antihint:
                res = ['Official hints for Notpron']
            else:
                res = ['Official antihints for Notpron.', 'These are not REAL hints, just from non-walkthrough.',
                       'In other words, for fun, not for real help.']
            for line in hint:
                res.append(f'{n}: {line}')
        if ctx.interaction is not None:
            await ctx.reply(f'{n}' if result is not None else '‍')
            await ctx.reply('\n'.join(res), ephemeral=True)
        else:
            dm_channel = await globals.bot.get_dm_channel(ctx.author)
            for line in res:
                await dm_channel.send(line)

    @discord.ext.commands.hybrid_command(name='hint', description='get the official hint for a level')
    @commands.check(check)
    async def hint(self, ctx: commands.Context, level: str) -> None:
        await self._hint(ctx, level)

    @discord.ext.commands.hybrid_command(name='antihint', description='get the antihint for a level')
    @commands.check(check)
    async def antihint(self, ctx: commands.Context, level: str) -> None:
        await self._hint(ctx, level, antihint=True)

    @discord.ext.commands.hybrid_command(name='thread', description='get a link to the forum thread to a level')
    @commands.check(check)
    async def thread(self, ctx: commands.Context, level: str) -> None:
        n = level.replace('-', 'minus ')
        coll = globals.bot.db['threads']
        result = coll.find_one({'level': n})
        if result is None:
            res = "No thread with that name found"
        else:
            thread = result['value']
            res = f'Level {n}: {thread}'
        if ctx.interaction is not None:
            await ctx.reply(f'{level}' if result is not None else '‍')
            await ctx.reply(res, ephemeral=True)
        else:
            dm_channel = await globals.bot.get_dm_channel(ctx.author)
            await dm_channel.send(res)
