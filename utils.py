import discord
import discord.utils
import discord.errors
import globals


def to_code_block(text, lang=''):
    while '```' in text:
        text = text.replace('```', '`\u200c`\u200c`')
    return f'```{lang}\n{text}```'


def inline_code(text):
    while '``' in text:
        text = text.replace('``', '`​`')
    return f'``{text}``'


def escape_discord(text):
    return discord.utils.escape_markdown(discord.utils.escape_mentions(str(text)))


async def get_guild(gid):
    if gid is None:
        return None
    try:
        return globals.bot.get_guild(gid) or await globals.bot.fetch_guild(gid)
    except discord.errors.NotFound:
        return None


async def get_user(uid):
    try:
        return globals.bot.get_user(uid) or await globals.bot.fetch_user(uid)
    except discord.errors.NotFound:
        return None


async def get_member(user):
    guild_id = globals.bot.conf.get(globals.bot.conf.keys.GUILD)
    if isinstance(user, discord.Member) and user.guild.id == guild_id:
        return user
    elif isinstance(user, discord.User) or isinstance(user, discord.Member):
        user = user.id
    guild = await get_guild(guild_id)
    try:
        return guild.get_member(user) or await guild.fetch_member(user)
    except discord.errors.NotFound:
        return None


async def get_channel(chid: int) -> discord.TextChannel:
    try:
        return globals.bot.get_channel(chid) or await globals.bot.fetch_channel(chid)
    except discord.errors.NotFound:
        return None
