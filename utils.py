from discord.utils import escape_markdown, escape_mentions
from discord import User, Member
import globals


def to_code_block(text, lang=''):
    while '```' in text:
        text = text.replace('```', '`\u200c`\u200c`')
    return f'```{lang}{text}```'


def escape_discord(text):
    return escape_markdown(escape_mentions(str(text)))


async def get_guild(gid):
    return globals.bot.get_guild(gid) or await globals.bot.fetch_guild(gid)


async def get_user(uid):
    return globals.bot.get_user(uid) or await globals.bot.fetch_user(uid)


async def get_member(user):
    guild_id = globals.bot.conf.get(globals.bot.conf.keys.GUILD)
    if isinstance(user, Member) and user.guild.id == guild_id:
        return user
    elif isinstance(user, User) or isinstance(user, Member):
        user = user.id
    guild = await get_guild(guild_id)
    return guild.get_member(user) or await guild.fetch_member(user)
