import asyncio
import json
import discord.utils


class ApiServer:
    def __init__(self, client, config, loop):
        self.client = client
        self.config = config
        self.loop = loop
        self.coro = asyncio.start_server(self.handle_request, 'localhost', config.get_api_port())
        self.loop.create_task(self.coro)

    async def handle_request(self, reader, writer):
        data = (await reader.read(8192)).decode('utf-8')
        try:
            req = json.loads(data)
            req_type = req.get('type')
        except (json.decoder.JSONDecodeError, AttributeError):
            writer.write(json.dumps('invalid request').encode('utf-8'))
            await writer.drain()
            writer.close()
            return
        res = "ok"
        if req_type == 'raw':
            if type(req.get('chid')) == int and type(req.get('message')) == str:
                writer.write(json.dumps(res).encode('utf-8'))
                await writer.drain()
                writer.close()
                self.loop.create_task(self.send_raw(req.get('chid'), req.get('message')))
                return
            else:
                res = "invalid signature for raw"
        elif req_type == 'update_roles':
            try:
                self.loop.create_task(
                    self.update_roles(int(req.get('uid')),
                                      int(req.get('gid')),
                                      [int(role) for role in req.get('add') or ()],
                                      [int(role) for role in req.get('remove') or ()])
                )
            except (ValueError, TypeError) as e:
                print(e)
                res = 'invalid signature for update_roles'
        elif req_type == 'weekly_solve':
            if type(req.get('chid')) == int and type(req.get('uid')) == str:
                writer.write(json.dumps(res).encode('utf-8'))
                await writer.drain()
                writer.close()
                self.loop.create_task(self.send_weekly_solve(req.get('chid'), req.get('uid')))
                return
            else:
                res = "invalid signature for weekly_solve"
        elif req_type == 'event_solve':
            if type(req.get('chid')) == int and type(req.get('uid')) == str:
                writer.write(json.dumps(res).encode('utf-8'))
                await writer.drain()
                writer.close()
                self.loop.create_task(self.send_halloween_solve(req.get('chid'), req.get('uid')))
                return
            else:
                res = "invalid signature for event_solve"
        elif req_type == 'weekly_announce':
            if type(req.get('chid')) == int and type(req.get('title')) == str and type(req.get('uid')) == str and type(req.get('icon')) == str:
                writer.write(json.dumps(res).encode('utf-8'))
                await writer.drain()
                writer.close()
                self.loop.create_task(self.send_weekly_announce(req.get('chid'), req.get('title'), req.get('uid'), req.get('icon')))
                return
            else:
                res = "invalid signature for weekly_announce"
        else:
            res = "invalid type"
        writer.write(json.dumps(res).encode('utf-8'))
        await writer.drain()
        writer.close()

    async def send_raw(self, channel, message):
        ch = self.client.get_channel(channel)
        await ch.send(message)

    async def update_roles(self, uid, gid, add, remove):
        guild = self.client.get_guild(gid) or await self.client.fetch_guild(gid)
        member = guild.get_member(uid) or await guild.fetch_member(uid)
        if add:
            await member.add_roles(*(guild.get_role(rid) for rid in add))
        if remove:
            actually_remove = [role.id for role in member.roles if role.id in remove]
            await member.remove_roles(*(guild.get_role(rid) for rid in actually_remove))

    async def _get_mention(self, ch, uid):
        try:
            member = await ch.guild.fetch_member(uid)
            return member.mention
        except:
            try:
                user = await self.client.fetch_user(uid)
                return user.name
            except:
                return '?????'

    async def send_weekly_solve(self, chid, uid):
        ch = self.client.get_channel(chid)
        mention = await self._get_mention(ch, uid)
        await ch.send(f'Congratulations {mention} for solving the weekly riddle!')

    async def send_halloween_solve(self, chid, uid):
        ch = self.client.get_channel(chid)
        mention = await self._get_mention(ch, uid)
        await ch.send(f'Congratulations {mention} for completing the Halloween event! :jack_o_lantern: :ghost:')

    async def send_weekly_announce(self, chid, title, uid, icon):
        ch = self.client.get_channel(chid)
        mention = await self._get_mention(ch, uid)
        title = title.replace('`', '')
        description = f'`{title}` by {mention}'
        embed = discord.Embed(title='ɴᴇᴡ ᴡᴇᴇᴋʟʏ ᴘᴜᴢᴢʟᴇ', description=description, color=0xa6ce86)
        embed.set_thumbnail(url=icon)
        embed.set_footer(text='To learn how to turn these notifications off, look at the message above.')
        await ch.purge(limit=1, check=lambda m: m.author == self.client.user)
        msg = await ch.send('@everyone', embed=embed)
        if ch.is_news():
            await msg.publish()
