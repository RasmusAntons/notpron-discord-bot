import discord
import discord.utils
import globals


def to_code_block(text, lang=''):
    while '```' in text:
        text = text.replace('```', '`\u200c`\u200c`')
    return f'```{lang}{text}```'


def escape_discord(text):
    return discord.utils.escape_markdown(discord.utils.escape_mentions(str(text)))


async def get_guild(gid):
    return globals.bot.get_guild(gid) or await globals.bot.fetch_guild(gid)


async def get_user(uid):
    return globals.bot.get_user(uid) or await globals.bot.fetch_user(uid)


async def get_member(user):
    guild_id = globals.bot.conf.get(globals.bot.conf.keys.GUILD)
    if isinstance(user, discord.Member) and user.guild.id == guild_id:
        return user
    elif isinstance(user, discord.User) or isinstance(user, discord.Member):
        user = user.id
    guild = await get_guild(guild_id)
    return guild.get_member(user) or await guild.fetch_member(user)


async def get_channel(chid):
    return globals.bot.get_channel(chid) or await globals.bot.fetch_channel(chid)
