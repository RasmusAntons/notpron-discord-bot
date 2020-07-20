import asyncio
import json
import discord.utils


class ApiServer:
    def __init__(self, client, config):
        self.client = client
        self.config = config
        self.coro = asyncio.start_server(self.handle_request, 'localhost', config.get_api_port())

    async def handle_request(self, reader, writer):
        data = (await reader.read(8192)).decode('utf-8')
        req = json.loads(data)
        res = "ok"
        if req.get('type') == 'raw':
            if type(req.get('chid')) == int and type(req.get('message')) == str:
                writer.write(json.dumps(res).encode('utf-8'))
                await writer.drain()
                writer.close()
                await self.send_raw(req.get('chid'), req.get('message'))
                return
            else:
                res = "invalid signature for raw"
        elif req.get('type') == 'weekly_solve':
            if type(req.get('chid')) == int and type(req.get('uid')) == str:
                writer.write(json.dumps(res).encode('utf-8'))
                await writer.drain()
                writer.close()
                await self.send_weekly_solve(req.get('chid'), req.get('uid'))
                return
            else:
                res = "invalid signature for weekly_solve"
        elif req.get('type') == 'weekly_announce':
            if type(req.get('chid')) == int and type(req.get('title')) == str and type(req.get('uid')) == str and type(req.get('icon')) == str:
                writer.write(json.dumps(res).encode('utf-8'))
                await writer.drain()
                writer.close()
                await self.send_weekly_announce(req.get('chid'), req.get('title'), req.get('uid'), req.get('icon'))
                return
            else:
                res = "invalid signature for weekly_announce"
        else:
            req = "invalid type"
        writer.write(json.dumps(res).encode('utf-8'))
        await writer.drain()
        writer.close()

    async def send_raw(self, channel, message):
        ch = self.client.get_channel(channel)
        await ch.send(message)

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

    async def send_weekly_announce(self, chid, title, uid, icon):
        ch = self.client.get_channel(chid)
        mention = await self._get_mention(ch, uid)
        title = title.replace('`', '')
        description = f'`{title}` by {mention}'
        embed = discord.Embed(title='ɴᴇᴡ ᴡᴇᴇᴋʟʏ ᴘᴜᴢᴢʟᴇ', description=description, color=0xa6ce86)
        embed.set_thumbnail(url=icon)
        embed.set_footer(text='To learn how to turn these notifications off, look at the message above.')
        await ch.purge(limit=1, check=lambda m: m.author == self.client.user)
        await ch.send('@everyone', embed=embed)
