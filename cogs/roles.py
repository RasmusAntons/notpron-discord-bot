import time

import discord
from discord.ext import commands
from pytimeparse.timeparse import timeparse

import config
import globals


class RolesCog(commands.Cog, name='Roles', description='display a 6-digit hex colour'):
    def __init__(self):
        self.coll = globals.bot.db['underage']
        self.coll.create_index('uid', unique=True)

    @commands.hybrid_command(name='underagepersonidentified', aliases=('underage',),
                             description='block user from nsfw channels')
    @config.check_mod()
    async def underagepersonidentified(self, ctx: commands.Context, member: discord.Member, duration: str) -> None:
        t = timeparse(duration)
        self.coll.replace_one({'uid': member.id}, {'uid': member.id, 'until': time.time() + t}, upsert=True)
        for rid in globals.conf.get(globals.conf.keys.ADULT_ROLES, []):
            await member.remove_roles(discord.utils.get(ctx.guild.roles, id=rid))
        await ctx.reply(f'blocked {member.display_name} from nsfw channels for {t} seconds')

    def is_user_blocked(self, uid):
        coll = globals.bot.db['underage']
        result = coll.find_one({'uid': uid})
        if result:
            until = result['until']
            print(f'{uid} blocked until {until} ({until - time.time()} more s)')
            if until > time.time():
                return True
            else:
                coll.delete_one({'uid': uid})
                return False
        else:
            return False

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, member: discord.Member):
        if member.id == globals.bot.user.id:
            return
        channel = reaction.message.channel
        if channel.id == globals.conf.get(globals.conf.keys.ROLE_CHANNEL):
            print('in role channel')
            if reaction.is_custom_emoji():
                emoji = str(reaction.emoji.id)
            else:
                emoji = reaction.emoji
            print(f'{emoji=}')
            rid = globals.conf.dict_get(globals.conf.keys.ASSIGN_ROLES, emoji)
            print(f'{rid=}')
            if rid:
                if rid in globals.conf.get(globals.conf.keys.ADULT_ROLES, []):
                    if self.is_user_blocked(member.id):
                        await reaction.message.remove_reaction(reaction.emoji, member)
                        return
                role = discord.utils.get(channel.guild.roles, id=rid)
                await member.add_roles(role)
                exrs = globals.conf.get(globals.conf.keys.EXCLUSIVE_ROLES)
                if role and exrs and rid in exrs:
                    exrs_o = [discord.utils.get(channel.guild.roles, id=rid) for rid in exrs if rid != role.id]
                    await member.remove_roles(*exrs_o)
                    for other in reaction.message.reactions:
                        if other.emoji != reaction.emoji:
                            await other.remove(member)

    @commands.Cog.listener()
    async def on_reaction_remove(self, reaction: discord.Reaction, member: discord.Member):
        if member.id == globals.bot.user.id:
            return
        channel = reaction.message.channel
        if channel.id == globals.conf.get(globals.conf.keys.ROLE_CHANNEL):
            if reaction.is_custom_emoji():
                emoji = str(reaction.emoji.id)
            else:
                emoji = reaction.emoji
            rid = globals.conf.dict_get(globals.conf.keys.ASSIGN_ROLES, emoji)
            if rid:
                role = discord.utils.get(channel.guild.roles, id=rid)
                await member.remove_roles(role)

    @commands.Cog.listener()
    async def on_member_join(self, member):
        default_role_id = globals.conf.get(globals.conf.keys.DEFAULT_ROLE)
        if default_role_id:
            role = discord.utils.get(member.guild.roles, id=default_role_id)
            if role is None:
                return
            await member.add_roles(role)
