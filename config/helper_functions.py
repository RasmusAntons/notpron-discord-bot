import globals
from utils import get_member, get_guild
from discord.ext import commands
import discord


def is_admin(user):
    return globals.conf.list_contains(globals.conf.keys.ADMIN_USERS, user.id)


def check_bot_admin(msg='permission denied'):
    async def is_bot_admin(ctx: commands.Context):
        if not is_admin(ctx.author):
            await ctx.send(msg, ephemeral=True)
            return False
        return True
    return commands.check(is_bot_admin)


async def get_main_guild():
    guild_id = globals.bot.conf.get(globals.conf.keys.GUILD)
    return await get_guild(guild_id)


async def is_mod(user):
    mod_roles = globals.bot.conf.get(globals.conf.keys.MOD_ROLES)
    if isinstance(user, discord.Member):
        member = user
    else:
        member = await get_member(user)
    if member is None:
        return False
    for role in member.roles:
        if role.id in mod_roles:
            return True
    return False


def check_mod(msg='permission denied'):
    async def _is_mod(ctx: commands.Context):
        if not await is_mod(ctx.author):
            await ctx.send(msg, ephemeral=True)
            return False
        return True
    return commands.check(_is_mod)


async def is_trusted_user(user):
    mod_roles = globals.bot.conf.get(globals.conf.keys.TRUSTED_USER_ROLES)
    if isinstance(user, discord.Member):
        member = user
    else:
        member = await get_member(user)
    if member is None:
        return False
    for role in member.roles:
        if role.id in mod_roles:
            return True
    return False
