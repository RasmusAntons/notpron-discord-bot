import asyncio
import datetime
import random

import discord
from discord.ext import commands

import globals
import utils


class RrCog(commands.Cog, name='Rr', description='play a round of russian roulette'):
    def __init__(self):
        self.coll = globals.bot.db['russian_roulette']
        if not self.coll.find_one({}):
            self.coll.insert_one({'streak': 0, 'max_streak': 0, 'uid': None, 'date': None, 'misses': 0, 'deaths': 0})
        self.current_users = set()

    @commands.hybrid_command(name='rr', description='play a round of russian roulette')
    async def rr(self, ctx: commands.Context) -> None:
        if ctx.author.id in self.current_users:
            await ctx.reply('wait for the previous rr to finish', ephemeral=True)
        self.current_users.add(ctx.author.id)
        await ctx.reply(
            f'*{ctx.author.display_name} loads one bullet into the revolver and slowly pulls the trigger...*'
        )
        async with ctx.channel.typing():
            await asyncio.sleep(1)
            if random.randrange(6) == 0:
                await ctx.channel.send(f'{ctx.author.display_name} **died**')
                self.coll.update_one({}, {'$inc': {'deaths': 1}, '$set': {'streak': 0}})
                try:
                    await ctx.author.edit(nick=f'dead')
                except discord.HTTPException:
                    pass
            else:
                stats = self.coll.find_one({})
                stats['streak'] += 1
                stats['misses'] += 1
                if stats['streak'] > stats['max_streak']:
                    stats['max_streak'] = stats['streak']
                    stats['uid'] = ctx.author.id
                    stats['date'] = datetime.datetime.now()
                self.coll.replace_one({}, stats)
                await ctx.channel.send(
                    f'*click* - empty chamber. {ctx.author.display_name} will live another day. Who\'s '
                    f'next? Misses since last death: {stats["streak"]}'
                )
        self.current_users.remove(ctx.author.id)

    @commands.hybrid_command(name='rrstats', description='see russian roulette stats')
    async def rrstats(self, ctx: commands.Context) -> None:
        stats = self.coll.find_one({})
        max_streak = stats['max_streak']
        uid = stats['uid']
        user = await utils.get_user(uid)
        username = user.display_name if user else uid
        date = stats['date']
        if date:
            date = date.strftime('%b %d %Y')
        await ctx.reply(f'longest streak was {max_streak} by {username} on {date}')
