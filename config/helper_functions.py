import globals
from utils import get_member, get_guild


def is_admin(user):
    return globals.conf.list_contains(globals.conf.keys.ADMIN_USERS, user.id)


async def get_main_guild():
    guild_id = globals.bot.conf.get(globals.conf.keys.GUILD)
    return await get_guild(guild_id)


async def is_mod(user):
    mod_roles = globals.bot.conf.get(globals.conf.keys.MOD_ROLES)
    member = await get_member(user)
    if member is None:
        return False
    for role in member.roles:
        if role.id in mod_roles:
            return True
    return False
