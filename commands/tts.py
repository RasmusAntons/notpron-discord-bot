from commands.command import Command
from gtts import gTTS
from queue import Queue
import discord
import time
import asyncio
import random
import glob


class TtsCommand(Command):
    name = 'tts'
    arg_range = (1, 99999)
    description = 'speak in mus1.mp3-on-repeat'
    arg_desc = '<language code> <text...>'
    tts_queue = Queue()
    tts_n = 0
    playing = None
    post_tts_delay = None
    vc = None
    halloween_state = 0

    def __init__(self, bot):
        super().__init__(bot)
        bot.voice_state_listeners.add(self)

    async def execute(self, args, msg):
        lang = args[0]
        print(f'generating tts for {msg.author.display_name}')
        text = f'{msg.author.display_name}: {" ".join(args[1:])}'
        tts = gTTS(text=text, lang=lang)
        tts.save(f'voice_{self.tts_n}.mp3')
        self.tts_queue.put(f'voice_{self.tts_n}.mp3')
        self.tts_n += 1
        print('added voice to queue')

    def get_halloween_song(self):
        songs = glob.glob(f'res/halloween/*')
        self.halloween_state = (self.halloween_state + 1) % len(songs)
        return songs[self.halloween_state]

    async def on_voice_state_update(self, member, before, after):
        mus1_ch = self.bot.get_channel(self.bot.config.get_music_channels()[0])
        halloween_ch = self.bot.get_channel(self.bot.config.get_music_channels()[-1])
        if member.id != self.bot.user.id:
            print(f'{member.name} switched from {before.channel} to {after.channel}')
            ch = after.channel

            def on_finished(err):
                print('stopped playing')
                for mus_ch in [mus1_ch, halloween_ch]:
                    if self.playing != mus_ch and len(mus_ch.members) > 0:
                        asyncio.run_coroutine_threadsafe(self.vc.move_to(mus_ch), self.vc.loop)
                        self.playing = mus_ch
                        break
                    elif self.playing == mus_ch and len(mus_ch.members) > 1:
                        break
                else:
                    self.playing = None
                    asyncio.run_coroutine_threadsafe(self.vc.disconnect(), self.vc.loop)
                    self.vc = None
                    return
                print('there is still someone here, playing again')
                while not self.tts_queue.empty():
                    print(f'found something in the tts queue')
                    self.vc.play(discord.FFmpegPCMAudio(self.tts_queue.get()), after=on_finished)
                    self.post_tts_delay = 15
                if self.post_tts_delay:
                    self.post_tts_delay -= 1
                    time.sleep(0.5)
                next_fn = 'res/mus1.mp3' if self.playing == mus1_ch else self.get_halloween_song()

                async def play():
                    await asyncio.sleep(1)
                    self.vc.play(discord.FFmpegPCMAudio(next_fn), after=on_finished)
                asyncio.run_coroutine_threadsafe(play(), self.vc.loop)

            print(f'{self.playing=}')
            if self.playing:
                print(f'{self.playing.members=}')
            if self.playing and ch == self.playing:
                return
            elif self.vc and ch == mus1_ch:
                if self.playing:
                    self.vc.stop()
            elif self.playing and len(self.playing.members) <= 1:
                self.vc.stop()
            elif ch and ch.id in self.bot.config.get_music_channels() and not self.playing:
                print(f'It\'s my music channel and I am not playing, connecting...')
                for old_vc in self.bot.voice_clients:
                    print(f'Found old vc, trying to disconnect: {old_vc}')
                    await old_vc.disconnect()
                self.vc = await ch.connect()
                self.playing = ch
                self.post_tts_delay = 15
                fn = 'res/mus1.mp3' if ch == mus1_ch else self.get_halloween_song()
                self.vc.play(discord.FFmpegPCMAudio(fn), after=on_finished)
        elif member.id == self.bot.user.id and not after.channel:
            self.playing = None
            if self.vc:
                await self.vc.disconnect()
                self.vc = None
