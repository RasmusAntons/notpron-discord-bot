import asyncio
import json
import traceback

import discord.utils

import globals
import utils
from utils import get_guild, escape_discord


class ApiServer:
    def __init__(self):
        self.coro = asyncio.start_server(self.handle_request, '0.0.0.0',
                                         globals.bot.conf.get(globals.bot.conf.keys.API_PORT))
        """
        'type': 'puzzle_submission',
        'name': puzzle_submission.name,
        'short_name': puzzle_submission.short_name,
        'description': puzzle_submission.description,
        'submitter': puzzle_submission.submitter.username
        """
        self.functions = {
            'raw': {'f': self.send_raw, 'p': {'chid': int, 'message': str}},
            'react_message': {'f': self.react_message, 'p': {'chid': int, 'mid': int, 'emoji': str}},
            'update_roles': {'f': self.update_roles, 'p': {'uid': int, 'gid': int, 'add': list, 'remove': list}},
            'weekly_solve': {'f': self.send_weekly_solve, 'p': {'chid': int, 'uid': int, 'name': str, 'week': int}},
            'event_solve': {'f': self.send_halloween_solve, 'p': {'chid': int, 'uid': int, 'name': str}},
            'weekly_announce': {'f': self.send_weekly_announce,
                                'p': {'chid': int, 'title': str, 'uids': list, 'names': list, 'icon': str, 'week': int,
                                      'solved': list}},
            'puzzle_submission': {'f': self.send_puzzle_submission,
                                  'p': {'name': str, 'short_name': str, 'description': str, 'submitter': str}},
            'puzzle_edit_suggestion': {'f': self.send_puzzle_edit_suggestion,
                                       'p': {'name': str, 'suggestion_id': str, 'suggestion': str, 'submitter': str}},
        }

    async def handle_request(self, reader, writer):
        try:
            data = (await reader.read(8192)).decode('utf-8')
            print('api request', data)
        except UnicodeDecodeError:
            writer.close()
            return
        try:
            req = json.loads(data)
            req_type = req.get('type')
        except (json.decoder.JSONDecodeError, AttributeError):
            writer.write(json.dumps('invalid request').encode('utf-8'))
            await writer.drain()
            writer.close()
            return
        res = {'status': 'ok'}
        if req_type in self.functions:
            function = self.functions[req_type]['f']
            params = self.functions[req_type]['p']
            for param, expected_type in params.items():
                provided = req.get(param)
                if provided is None:
                    res = {'error': f'missing parameter {param}'}
                    break
                elif type(provided) != expected_type:
                    res = {'error': f'wrong type for {param}: expected {expected_type}, got {type(provided)}'}
                    break
            else:
                if req.get("async"):
                    globals.bot.loop.create_task(function(*(req.get(param) for param in params)))
                else:
                    try:
                        function_res = await function(*(req.get(param) for param in params))
                        if function_res is not None:
                            res |= function_res
                    except Exception as e:
                        traceback.print_exc()
                        res = {'error': str(e)}
        else:
            res = {'error': 'invalid request type'}
        writer.write(json.dumps(res).encode('utf-8'))
        await writer.drain()
        writer.close()

    async def send_raw(self, channel, message):
        ch = globals.bot.get_channel(channel)
        await ch.send(message)

    async def react_message(self, chid: int, mid: int, emoji: str):
        channel = await utils.get_channel(chid)
        message = await channel.fetch_message(mid)
        await message.add_reaction(emoji)

    async def update_roles(self, uid, gid, add, remove):
        guild = await get_guild(gid)
        member = guild.get_member(uid) or await guild.fetch_member(uid)
        if add:
            await member.add_roles(*(guild.get_role(rid) for rid in add))
        if remove:
            actually_remove = [role.id for role in member.roles if role.id in remove]
            await member.remove_roles(*(guild.get_role(rid) for rid in actually_remove))

    async def _get_mention(self, ch, uid, same_server=False, default='?????'):
        try:
            member = ch.guild.get_member(uid) or await ch.guild.fetch_member(uid)
            return member.mention
        except (discord.NotFound, discord.HTTPException):
            if same_server:
                return default
            try:
                user = globals.bot.get_user(uid) or await globals.bot.fetch_user(uid)
                return user.name
            except (discord.NotFound, discord.HTTPException):
                return default

    async def send_weekly_solve(self, chid, uid, name, week):
        ch = globals.bot.get_channel(chid) or await globals.bot.fetch_channel(chid)
        mention = await self._get_mention(ch, uid, same_server=True, default=name)
        if uid:
            weekly_solver_rid = globals.conf.get(globals.conf.keys.WEEKLY_SOLVER_ROLE)
            try:
                weekly_solver_role = discord.utils.get(ch.guild.roles, id=weekly_solver_rid)
                member = ch.guild.get_member(uid) or await ch.guild.fetch_member(uid)
                await member.add_roles(weekly_solver_role)
            except (discord.NotFound, discord.Forbidden, AttributeError):
                traceback.print_exc()
        await ch.send(f'Congratulations {mention} for solving the weekly puzzle!')

    async def send_halloween_solve(self, chid, uid, name):
        ch = globals.bot.get_channel(chid)
        mention = await self._get_mention(ch, uid, same_server=True, default=name)
        await ch.send(f'Congratulations {mention} for completing the Halloween event! :jack_o_lantern: :ghost:')

    async def send_weekly_announce(self, chid, title, uids, names, icon, week, solved):
        ch_announce = globals.bot.get_channel(chid)
        guild = ch_announce.guild
        mentions = []
        for i in range(min(len(uids), len(names))):
            mentions.append(await self._get_mention(ch_announce, uids[i], same_server=True, default=names[i]))
        mention = ', '.join(mentions)
        title = title.replace('`', '')
        description = f'`{title}` by {mention}'
        embed = discord.Embed(title='ɴᴇᴡ ᴡᴇᴇᴋʟʏ ᴘᴜᴢᴢʟᴇ', description=description,
                              color=globals.bot.conf.get(globals.bot.conf.keys.EMBED_COLOUR),
                              url='https://weeklies.enigmatics.org/')
        embed.set_thumbnail(url=icon)
        # embed.set_footer(text='To learn how to turn these notifications off, look at the message above.')
        # await ch_announce.purge(limit=1, check=lambda m: m.author == globals.bot.user)
        msg = await ch_announce.send('@everyone', embed=embed)
        if ch_announce.is_news():
            await msg.publish()
        channel_admin_rid = globals.conf.get(globals.conf.keys.WEEKLIES_CHANNEL_ADMIN_ROLE)
        if channel_admin_rid is None:
            return
        channel_admin_role = discord.utils.get(guild.roles, id=channel_admin_rid)
        own_member = guild.get_member(globals.bot.user.id) or await guild.fetch_member(globals.bot.user.id)
        weekly_solver_rid = globals.conf.get(globals.conf.keys.WEEKLY_SOLVER_ROLE)
        weekly_solver_role = discord.utils.get(guild.roles, id=weekly_solver_rid)
        await own_member.add_roles(channel_admin_role)
        previous_weekly_chid = globals.conf.dict_get(globals.conf.keys.WEEKLIES_CHANNELS, str(week - 1))
        if previous_weekly_chid is not None:
            previous_weekly_ch = globals.bot.get_channel(previous_weekly_chid) or await globals.bot.fetch_channel(
                previous_weekly_chid)
            for member in previous_weekly_ch.members:
                if member.id == globals.bot.user.id:
                    continue
                await previous_weekly_ch.set_permissions(member, read_messages=True)
                await member.remove_roles(weekly_solver_role)
            await previous_weekly_ch.set_permissions(weekly_solver_role, read_messages=False)
        current_weekly_chid = globals.conf.dict_get(globals.conf.keys.WEEKLIES_CHANNELS, str(week))
        current_weekly_ch = globals.bot.get_channel(current_weekly_chid) or await globals.bot.fetch_channel(
            current_weekly_chid)
        await current_weekly_ch.set_permissions(weekly_solver_role, read_messages=True)
        await own_member.remove_roles(channel_admin_role)
        for solved_uid in solved:
            try:
                member = guild.get_member(solved_uid) or await guild.fetch_member(solved_uid)
                await member.add_roles(weekly_solver_role)
            except (discord.NotFound, discord.Forbidden, AttributeError):
                traceback.print_exc()

    async def send_puzzle_submission(self, name, short_name, description, submitter):
        chid = globals.conf.get(globals.conf.keys.MOD_CHANNEL)
        if chid is None:
            raise RuntimeError('No control channel configured')
        ch = globals.bot.get_channel(chid)
        embed = discord.Embed(title=f'New puzzle submission from {submitter}',
                              description=f'[link](https://enigmatics.org/puzzles/submissions/{short_name})')
        embed.add_field(name='Name', value=escape_discord(name), inline=False)
        if description:
            embed.add_field(name='Description', value=escape_discord(description), inline=False)
        msg = await ch.send(f'@everyone', embed=embed)
        return {'chid': msg.channel.id, 'mid': msg.id}

    async def send_puzzle_edit_suggestion(self, name, suggestion_id, suggestion, submitter):
        chid = globals.conf.get(globals.conf.keys.MOD_CHANNEL)
        if chid is None:
            raise RuntimeError('No control channel configured')
        ch = globals.bot.get_channel(chid)
        embed = discord.Embed(title=f'New puzzle edit suggestion from {submitter}',
                              description=f'[link](https://enigmatics.org/puzzles/edit_suggestion/{suggestion_id})')
        embed.add_field(name='Name', value=escape_discord(name), inline=False)
        if suggestion:
            embed.add_field(name='Suggestion', value=escape_discord(suggestion), inline=False)
        msg = await ch.send(f'@everyone', embed=embed)
        return {'chid': msg.channel.id, 'mid': msg.id}
