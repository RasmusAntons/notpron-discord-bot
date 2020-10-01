from commands.command import Command
from gtts import gTTS
from queue import Queue
import discord
import time
import asyncio


class TtsCommand(Command):
    name = 'tts'
    arg_range = (1, 99999)
    description = 'speak in mus1.mp3-on-repeat'
    arg_desc = '<language code> <text...>'
    tts_queue = Queue()
    tts_n = 0
    playing = False
    post_tts_delay = None

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

    async def on_voice_state_update(self, member, before, after):
        if member.id != self.bot.user.id and after.channel:
            print(f'{member.name} switched from {before} to {after}')
            ch = after.channel
            if ch.id in self.bot.config.get_music_channels() and not self.playing:
                print(f'It\'s my music channel and I am not playing, connecting...')
                for old_vc in self.bot.voice_clients:
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
        elif member.id == self.bot.user.id and not after.channel:
            self.playing = False
