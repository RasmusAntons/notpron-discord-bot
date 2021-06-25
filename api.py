import asyncio
import json
import discord.utils
import globals
from utils import get_guild
from utils import escape_discord


class ApiServer:
    def __init__(self):
        self.coro = asyncio.start_server(self.handle_request, 'localhost', globals.bot.conf.get(globals.bot.conf.keys.API_PORT))
        globals.bot.loop.create_task(self.coro)
        """
        'type': 'puzzle_submission',
        'name': puzzle_submission.name,
        'short_name': puzzle_submission.short_name,
        'description': puzzle_submission.description,
        'submitter': puzzle_submission.submitter.username
        """
        self.functions = {
            'raw': {'f': self.send_raw, 'p': {'chid': int, 'message': str}},
            'update_roles': {'f': self.update_roles, 'p': {'uid': int, 'gid': int, 'add': list, 'remove': list}},
            'weekly_solve': {'f': self.send_weekly_solve, 'p': {'chid': int, 'uid': int, 'name': str, 'week': int}},
            'event_solve': {'f': self.send_halloween_solve, 'p': {'chid': int, 'uid': int, 'name': str}},
            'weekly_announce': {'f': self.send_weekly_announce, 'p': {'chid': int, 'title': str, 'uid': int, 'name': str, 'icon': str}},
            'puzzle_submission': {'f': self.send_puzzle_submission, 'p': {'name': str, 'short_name': str, 'description': str, 'submitter': str}}
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
        res = 'ok'
        if req_type in self.functions:
            function = self.functions[req_type]['f']
            params = self.functions[req_type]['p']
            for param, expected_type in params.items():
                provided = req.get(param)
                if provided is None:
                    res = f'missing parameter {param}'
                    break
                elif type(provided) != expected_type:
                    res = f'wrong type for {param}: expected {expected_type}, got {type(provided)}'
                    break
            else:
                if req.get("async"):
                    globals.bot.loop.create_task(function(*(req.get(param) for param in params)))
                else:
                    try:
                        await function(*(req.get(param) for param in params))
                    except Exception as e:
                        res = str(e)
        else:
            res = 'invalid request type'
        writer.write(json.dumps(res).encode('utf-8'))
        await writer.drain()
        writer.close()

    async def send_raw(self, channel, message):
        ch = globals.bot.get_channel(channel)
        await ch.send(message)

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
        ch = globals.bot.get_channel(chid)
        mention = await self._get_mention(ch, uid, same_server=True, default=name)
        weeklies_chid = globals.conf.get(globals.conf.keys.WEEKLIES_CHANNELS, str(week))
        if weeklies_chid is not None:
            weeklies_ch = globals.bot.get_channel(weeklies_chid)
            weeklies_ch: discord.TextChannel
            member = weeklies_ch.guild.get_member(uid) or await weeklies_ch.guild.fetch_member(uid)
            if member:
                await weeklies_ch.set_permissions(member, read_messages=True)
        await ch.send(f'Congratulations {mention} for solving the weekly puzzle!')

    async def send_halloween_solve(self, chid, uid, name):
        ch = globals.bot.get_channel(chid)
        mention = await self._get_mention(ch, uid, same_server=True, default=name)
        await ch.send(f'Congratulations {mention} for completing the Halloween event! :jack_o_lantern: :ghost:')

    async def send_weekly_announce(self, chid, title, uid, name, icon):
        ch = globals.bot.get_channel(chid)
        mention = await self._get_mention(ch, uid, same_server=True, default=name)
        title = title.replace('`', '')
        description = f'`{title}` by {mention}'
        embed = discord.Embed(title='ɴᴇᴡ ᴡᴇᴇᴋʟʏ ᴘᴜᴢᴢʟᴇ', description=description,
                              color=globals.bot.conf.get(globals.bot.conf.keys.EMBED_COLOUR))
        embed.set_thumbnail(url=icon)
        embed.set_footer(text='To learn how to turn these notifications off, look at the message above.')
        await ch.purge(limit=1, check=lambda m: m.author == globals.bot.user)
        msg = await ch.send('@everyone', embed=embed)
        if ch.is_news():
            await msg.publish()

    async def send_puzzle_submission(self, name, short_name, description, submitter):
        chid = globals.conf.get(globals.conf.keys.CONTROL_CHANNEL)
        if chid is None:
            raise RuntimeError('No control channel configured')
        ch = globals.bot.get_channel(chid)
        embed = discord.Embed(title=f'New puzzle submission from {submitter}',
                              description=f'[link](https://enigmatics.org/puzzles/submissions/{short_name})')
        embed.add_field(name='Name', value=escape_discord(name), inline=False)
        if description:
            embed.add_field(name='Description', value=escape_discord(description), inline=False)
        await ch.send(f'@admin', embed=embed)
