from commands.command import Command
from pytimeparse.timeparse import timeparse
import discord
import json
import time


class UnderageCommand(Command):
    name = 'underagepersonidentified'
    aliases = ['underage']
    arg_range = (2, 2)
    description = 'block user from nsfw channels'
    arg_desc = '<userid> <duration>'

    def __init__(self, bot):
        super().__init__(bot)
        bot.raw_reaction_listeners.add(self)

    async def check(self, args, msg):
        for role in msg.author.roles:
            if role.name.lower() in ['moderator', 'tech support', 'dj']:
                return True
        return False

    async def execute(self, args, msg):
        try:
            user = await msg.guild.fetch_member(int(args[0]))
            t = timeparse(' '.join(args[1:]))
            self.add_blocked_user(user.id, t)
            for rid in [721469067680022541, 768857774573617153]:
                await user.remove_roles(discord.utils.get(msg.guild.roles, id=rid))
            await msg.channel.send(f'blocked {user.display_name} from nsfw channels for {t} seconds')
        except (discord.HTTPException, ValueError) as e:
            await msg.channel.send(str(e))

    def add_blocked_user(self, uid, t):
        with open('blocked_users.json') as f:
            blocked_users = json.load(f)
        until = time.time() + t
        blocked_users[str(uid)] = until
        with open('blocked_users.json', 'w') as f:
            json.dump(blocked_users, f)

    def is_user_blocked(self, uid):
        with open('blocked_users.json') as f:
            blocked_users = json.load(f)
        until = blocked_users.get(str(uid))
        if until:
            print(f'{uid} blocked until {until} ({until - time.time()} more s)')
            if until > time.time():
                return True
            else:
                del blocked_users[str(uid)]
                with open('blocked_users.json', 'w') as f:
                    json.dump(blocked_users, f)
                return False
        else:
            return False

    async def on_raw_reaction_add(self, channel, user, payload):  # todo: use config file
        if channel.id == 721487932606906399:
            if payload.emoji.is_custom_emoji():
                if payload.emoji.id == 721206165605974019:  # mc
                    role = discord.utils.get(channel.guild.roles, id=721461067334680626)
                    await user.add_roles(role)
            elif payload.emoji.name == '🤖':  # tech
                role = discord.utils.get(channel.guild.roles, id=769767161258311741)
                await user.add_roles(role)
            elif payload.emoji.name == '☕':  # adult-lounge
                if self.is_user_blocked(user.id):
                    msg = await channel.fetch_message(payload.message_id)
                    await msg.remove_reaction('☕', user)
                else:
                    role = discord.utils.get(channel.guild.roles, id=768857774573617153)
                    await user.add_roles(role)
            elif payload.emoji.name == '🤢':  # wasteland
                if self.is_user_blocked(user.id):
                    msg = await channel.fetch_message(payload.message_id)
                    await msg.remove_reaction('🤢', user)
                else:
                    role = discord.utils.get(channel.guild.roles, id=721469067680022541)
                    await user.add_roles(role)
            elif payload.emoji.name == '🇧🇷':  # pt
                role = discord.utils.get(channel.guild.roles, id=722963391316230194)
                await user.add_roles(role)

    async def on_raw_reaction_remove(self, channel, user, payload):
        if channel.id == 721487932606906399:
            if payload.emoji.is_custom_emoji():
                if payload.emoji.id == 721206165605974019:  # mc
                    role = discord.utils.get(channel.guild.roles, id=721461067334680626)
                    await user.remove_roles(role)
            elif payload.emoji.name == '🤖':  # tech
                role = discord.utils.get(channel.guild.roles, id=769767161258311741)
                await user.remove_roles(role)
            elif payload.emoji.name == '☕':  # adult-lounge
                role = discord.utils.get(channel.guild.roles, id=768857774573617153)
                await user.remove_roles(role)
            elif payload.emoji.name == '🤢':  # wasteland
                role = discord.utils.get(channel.guild.roles, id=721469067680022541)
                await user.remove_roles(role)
                await user.remove_roles(role)
            elif payload.emoji.name == '🇧🇷':  # pt
                role = discord.utils.get(channel.guild.roles, id=722963391316230194)
                await user.remove_roles(role)
