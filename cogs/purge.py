import datetime

import discord
from discord.ext import commands
from pytimeparse.timeparse import timeparse

import config
import globals
from utils import escape_discord


class PurgeCog(commands.Cog, name='Purge', description='purge messages'):
    unconfirmed = {}

    @staticmethod
    async def check(ctx: commands.Context):
        if not await config.is_mod(ctx.author) or not ctx.channel.permissions_for(ctx.author).manage_messages:
            await ctx.reply('permission denied', ephemeral=True)
            return False
        return True

    @commands.hybrid_command(name='purge', description='purge messages')
    @commands.check(check)
    async def purge(self, ctx: commands.Context, amount_or_duration: str, member: discord.Member = None) -> None:
        td = None
        n = None
        t = datetime.datetime.now()
        try:
            n = int(amount_or_duration)
            if n > 100:
                raise ValueError(f'I\'m not allowed to delete more than 100 messages')
            quantifier = f'the last {n} messages'
        except ValueError:
            tds = timeparse(amount_or_duration)
            if tds:
                td = datetime.timedelta(seconds=tds)
                if tds > 1800:
                    raise ValueError(f'I\'m not allowed to delete more than 30 minutes')
                quantifier = f'messages of the last {td}'
            else:
                quantifier = 'all messages (up to 100)'
        if ctx.message.mentions:
            user_str = ' by ' + ', '.join([user.display_name for user in ctx.message.mentions])
        else:
            if not n and not td:
                await ctx.channel.send(f'{ctx.author.mention}, please mention users, the number or time interval of '
                                       f'messages to purge')
                return
            user_str = ''
        text = f'do you want to purge {quantifier}{user_str}?'
        prompt = await ctx.reply(text)
        await prompt.add_reaction('✅')
        await prompt.add_reaction('❌')
        self.unconfirmed[prompt.id] = {'author': ctx.author, 'users': ctx.message.mentions, 'td': td, 'n': n, 't': t}

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User):
        try:
            confirming = self.unconfirmed.get(reaction.message.id)
            if confirming and user.id == confirming.get('author').id:
                if reaction.emoji == '❌':
                    del self.unconfirmed[reaction.message.id]
                    await reaction.message.delete()
                elif reaction.emoji == '✅':
                    if confirming.get('n') and confirming.get('n') < 0:
                        for _ in range(-confirming.get('n')):
                            await globals.bot.markov.talk(reaction.message.channel, cont_chance=0)
                    else:
                        users = confirming.get('users')
                        after = confirming.get('t') - confirming.get('td') if confirming.get('td') else None
                        limit = confirming.get('n') if confirming.get('n') is not None else 100
                        print(f'purging: {limit=}, {users=}, {after=}, {confirming.get("t")=}')
                        await reaction.message.channel.purge(limit=limit,
                                                             check=lambda m: not users or m.author in users,
                                                             after=after, before=confirming.get('t'))
                    del self.unconfirmed[reaction.message.id]
                    await reaction.message.delete()
                else:
                    await reaction.message.channel.send(f'that\'s a stupid emoji???')
        except Exception as e:
            await reaction.message.channel.send(escape_discord(str(e)))
            raise e
