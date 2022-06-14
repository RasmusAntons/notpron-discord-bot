from cogs.command import Command, Category
from listeners import RawReactionListener
from pytimeparse.timeparse import timeparse
import discord
import time
import globals
import config


class UnderageCommand(Command, RawReactionListener):
    name = 'underagepersonidentified'
    category = Category.ADMIN
    aliases = ['underage']
    arg_range = (2, 2)
    description = 'block user from nsfw channels'
    arg_desc = '<userid> <duration>'

    def __init__(self):
        super(UnderageCommand, self).__init__()
        globals.bot.db['underage'].create_index('uid', unique=True)

    async def check(self, args, msg, test=False):
        return await super().check(args, msg, test) and await config.is_mod(msg.author)

    async def execute(self, args, msg):
        try:
            user = await msg.guild.fetch_member(int(args[0]))
            t = timeparse(' '.join(args[1:]))
            coll = globals.bot.db['underage']
            coll.replace_one({'uid': user.id}, {'uid': user.id, 'until':  time.time() + t}, upsert=True)
            for rid in globals.conf.get(globals.conf.keys.ADULT_ROLES, []):
                await user.remove_roles(discord.utils.get(msg.guild.roles, id=rid))
            await msg.channel.send(f'blocked {user.display_name} from nsfw channels for {t} seconds')
        except (discord.HTTPException, ValueError) as e:
            await msg.channel.send(str(e))

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

    async def on_raw_reaction_add(self, channel, member, payload):
        if channel.id == globals.conf.get(globals.conf.keys.ROLE_CHANNEL):
            msg = await channel.fetch_message(payload.message_id)
            if payload.emoji.is_custom_emoji():
                emoji = str(payload.emoji.id)
            else:
                emoji = payload.emoji.name
            rid = globals.conf.dict_get(globals.conf.keys.ASSIGN_ROLES, emoji)
            if rid:
                if rid in globals.conf.get(globals.conf.keys.ADULT_ROLES, []):
                    if self.is_user_blocked(member.id):
                        await msg.remove_reaction(payload.emoji, member)
                        return
                role = discord.utils.get(channel.guild.roles, id=rid)
                await member.add_roles(role)
                exrs = globals.conf.get(globals.conf.keys.EXCLUSIVE_ROLES)
                if role and exrs and rid in exrs:
                    exrs_o = [discord.utils.get(channel.guild.roles, id=rid) for rid in exrs if rid != role.id]
                    await member.remove_roles(*exrs_o)
                    for reaction in msg.reactions:
                        if reaction.emoji != payload.emoji:
                            await reaction.remove(member)

    async def on_raw_reaction_remove(self, channel, member, payload):
        if channel.id == globals.conf.get(globals.conf.keys.ROLE_CHANNEL):
            if payload.emoji.is_custom_emoji():
                emoji = str(payload.emoji.id)
            else:
                emoji = payload.emoji.name
            rid = globals.conf.dict_get(globals.conf.keys.ASSIGN_ROLES, emoji)
            if rid:
                role = discord.utils.get(channel.guild.roles, id=rid)
                await member.remove_roles(role)
