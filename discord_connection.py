import discord
import re
import asyncio


class DiscordConnection(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.playing = False

    async def on_ready(self):
        print('I\'m in.')

    async def on_message(self, msg):
        if msg.channel.id not in self.config.get_channels() or msg.author.id == self.user.id:
            return
        if msg.content.startswith('!hint') or msg.content.startswith('!antihint'):
            hint = None
            m = re.match(r'^!(?P<anti>anti)?hint (?P<level>\d\d?)$', msg.content)
            if (m):
                n = int(m.group('level'))
                a = bool(m.group('anti'))
                hint = self.config.get_hint(n) if not a else self.config.get_antihint(n)
            if hint is None:
                res = ['Type !hint <level number from 1-79> for a level specific hint. No hints for 80 and beyond!']
            else:
                if not a:
                    res = ['Official hints for Notpron']
                else:
                    res = ['Official antihints for Notpron.', 'These are not REAL hints, just from non-walkthrough.', 'In other words, for fun, not for real help.']
                for line in hint:
                    res.append(f'{n}: {line}')
            dm_channel = msg.author.dm_channel
            if dm_channel is None:
                dm_channel = await msg.author.create_dm()
            if dm_channel is not None:
                for line in res:
                    await dm_channel.send(line)
            else:
                await msg.channel.send(f'{msg.author.mention} failed to send dm, please check your settings')

    async def on_voice_state_update(self, member, before, after):
        if member.id != self.user.id and after.channel:
            ch = after.channel
            if ch.id in self.config.get_music_channels() and not self.playing:
                for old_vc in self.voice_clients:
                    await old_vc.disconnect()
                vc = await ch.connect()
                print(vc)
                self.playing = True
                def on_finished(err):
                    if len(ch.members) > 1:
                        vc.play(discord.FFmpegPCMAudio('res/mus1.mp3'), after=on_finished)
                    else:
                        self.playing = False
                        asyncio.run_coroutine_threadsafe(vc.disconnect(), vc.loop)

                vc.play(discord.FFmpegPCMAudio('res/mus1.mp3'), after=on_finished)
        elif member.id == self.user.id and not after.channel:
            self.playing = False
