import discord
import re
import asyncio
from gtts import gTTS
from queue import Queue
import time


class DiscordConnection(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.playing = False
        self.tts_n = 0
        self.post_tts_delay = None
        self.tts_queue = Queue()

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!hint | !antihint"))
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
        elif msg.content.startswith('!tts ') or msg.content.startswith('!tts_'):
            lang='de'
            off=5
            if msg.content.startswith('!tts_'):
                lang = msg.content.split(' ')[0][5:]
                off = len(msg.content.split(' ')[0]) + 1
            print(f'generating tts for {msg.author.display_name}')
            text = f'{msg.author.display_name}: {msg.content[off:]}'
            tts = gTTS(text=text, lang=lang)
            tts.save(f'voice_{self.tts_n}.mp3')
            self.tts_queue.put(f'voice_{self.tts_n}.mp3')
            self.tts_n += 1
            print('added voice to queue')

    async def on_voice_state_update(self, member, before, after):
        if member.id != self.user.id and after.channel:
            print(f'{member.name} switched from {before} to {after}')
            ch = after.channel
            if ch.id in self.config.get_music_channels() and not self.playing:
                print(f'It\'s my music channel and I am not playing, connecting...')
                for old_vc in self.voice_clients:
                    print(f'Found old vc, trying to disconnect: {old_vc}')
                    await old_vc.disconnect()
                vc = await ch.connect()
                print(vc)
                self.playing = True
                self.post_tts_delay = 15
                def on_finished(err):
                    print('finshed playing')
                    if len(ch.members) > 1:
                        print('there is still someone here, playing again')
                        while not self.tts_queue.empty():
                            print(f'found something in the tts queue')
                            vc.play(discord.FFmpegPCMAudio(self.tts_queue.get()), after=on_finished)
                            self.post_tts_delay = 15
                        if self.post_tts_delay:
                            self.post_tts_delay -= 1
                            time.sleep(0.5)
                        vc.play(discord.FFmpegPCMAudio('res/mus1.mp3'), after=on_finished)
                    else:
                        print('all alone, I\'ll go too')
                        self.playing = False
                        asyncio.run_coroutine_threadsafe(vc.disconnect(), vc.loop)

                vc.play(discord.FFmpegPCMAudio('res/mus1.mp3'), after=on_finished)
        elif member.id == self.user.id and not after.channel:
            self.playing = False
