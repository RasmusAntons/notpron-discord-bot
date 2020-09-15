import discord
import re
import asyncio
from gtts import gTTS
from queue import Queue
from markov import Markov
import time
import api
import random
import datetime
import weather
import json
import pyowm.commons.exceptions
import quantities
from PIL import Image
import imagine


class DiscordConnection(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.playing = False
        self.markov = Markov(self, config)
        self.tts_n = 0
        self.post_tts_delay = None
        self.tts_queue = Queue()
        self.api_server = api.ApiServer(self, config)
        self.word_prompt = None
        self.correct_word = None
        self.word_guesses = {}
        self.num_reacts = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']
        self.name_check = None
        self.rr = 0

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!hint | !antihint"))
        print('I\'m in.')
        await self.markov.load_model('all')
        self.loop.create_task(self.background_task())

    async def background_task(self):
        while True:
            ts = datetime.datetime.utcnow()
            if self.name_check is None or ts.hour != self.name_check.hour:
                for id, names in self.config.get_names().items():
                    new_name = names.get(str(ts.hour))
                    if new_name:
                        try:
                            guild = self.get_guild(self.config.get_guild())
                            member = await guild.fetch_member(int(id))
                            await member.edit(nick=new_name)
                        except discord.HTTPException as e:
                            print(e)
            self.name_check = ts
            await asyncio.sleep(10)

    async def on_message(self, msg):
        if msg.channel.id not in self.config.get_channels() or msg.author.id == self.user.id:
            return
        #if '<:tyteok:743847838097866842>' in msg.content:
        #    user = await self.fetch_user(305983034799161344)
        #    dm_channel = user.dm_channel
        #    if dm_channel is None:
        #        dm_channel = await user.create_dm()
        #    if dm_channel is not None:
        #        await dm_channel.send('ok')
        if msg.author.id == 704372346995081246:
            if random.randint(0, 500) == 0:
                await msg.channel.send('get some sleep, Alessa')
        if self.user.mentioned_in(msg):
            if '@everyone' not in msg.content and '@here' not in msg.content:
                await self.markov.talk(msg.channel)
        elif msg.content.startswith("!imitate ") or msg.content.startswith('!regenerate'):
            cmd = msg.content[1:].strip()
            await self.markov.on_command(msg, cmd)
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
        elif msg.content.startswith('!thread'):
            n = msg.content[7:].strip().replace('-', 'minus ')
            thread = self.config.get_thread(n)
            if thread is None:
                res = "No thread with that name found"
            else:
                res = f'Level {n}: {thread}'
            dm_channel = msg.author.dm_channel
            if dm_channel is None:
                dm_channel = await msg.author.create_dm()
            if dm_channel is not None:
                await dm_channel.send(res)
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
        elif msg.content.startswith('!weather'):
            if len(msg.content) < 10:
                return
            query = msg.content[9:]
            try:
                await msg.channel.send(embed=weather.get_weather_msg(query, self.config.get_owm_key()))
            except pyowm.commons.exceptions.NotFoundError:
                await msg.channel.send(f'{msg.author.mention} I don\'t know that place')
        elif msg.content == '!botpronpleasestartthemultiplechoicewordguessinggame':
            await self.start_word_game(msg)
        elif msg.content == '!rr':
            loadtxt = ' loads one bullet into the revolver and' if self.rr == 0 else ''
            await msg.channel.send(f'{msg.author.display_name}{loadtxt} slowly pulls the trigger...')
            await msg.channel.trigger_typing()
            await asyncio.sleep(1)
            if random.randrange(6 - self.rr) == 0:
                await msg.channel.send(f'{msg.author.display_name} **died**')
                try:
                    await msg.author.edit(nick=f'dead')
                except:
                    pass
                self.rr = 0
            else:
                self.rr += 1
                await msg.channel.send(f'*click* - empty chamber. {msg.author.display_name} will live another day. Who\'s next? Misses since last death: {self.rr}')
        elif msg.content.startswith('!conv'):
            try:
                _, amount, origin, destination = msg.content.split(' ')
            except ValueError:
                await msg.channel.send('use !convert <amount> <origin unit> <destination unit>')
                return
            try:
                amount = float(amount)
                q = quantities.Quantity(amount, origin)
                ou = str(q.units)[4:]
                q.units = destination
                r = q.item()
                du = str(q.units)[4:]
                await msg.channel.send(f'{amount}{ou} = {r}{du}')
            except ValueError as e:
                await msg.channel.send(str(e))
            except LookupError as e:
                await msg.channel.send(str(e))
        elif msg.content.startswith('!colour ') or msg.content.startswith('!color '):
            try:
                col = msg.content.split(' ')[1].replace('#', '')
                if len(col) != 6:
                    await msg.channel.send('Use !colour #000000')
                    return
                col = int(col, 16)
                im = Image.new("RGB", (128, 128), f'#{col:06X}')
                im.save('colour.png')
                await msg.channel.send(file=discord.File('colour.png', filename=f'{col:06x}.png'))
            except ValueError as e:
                await msg.channel.send('Use !colour #000000')
        elif msg.content.startswith('!solver '):
            if self.config.get_mod_role() not in [role.id for role in msg.author.roles]:
                await msg.channel.send('Gotta have the moderator role to do this, sorry.')
                return
            params = msg.content[8:].split(' ')
            if len(params) != 2:
                await msg.channel.send('Use !solver <user id> <solver number>')
                return
            try:
                guild = self.get_guild(self.config.get_guild())
                solver = await guild.fetch_member(int(params[0]))
                solver_nr = int(params[1])
                ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
                description = f'Congratulations {solver.mention}, the {ordinal(solver_nr)} person to complete Notpron.'
                embed = discord.Embed(title=f'New Solver', description=description, color=0xa6ce86)
                embed.set_thumbnail(url=solver.avatar_url_as(size=128))
                await self.get_channel(self.config.get_announcements_channel()).send(embed=embed)
            except discord.HTTPException as e:
                await msg.channel.send(str(e))
            except ValueError as e:
                await msg.channel.send(str(e))
        elif msg.content.startswith('!imagine '):
            keyword = msg.content[9:].strip() + ' -notpron'
            adult = msg.channel.is_nsfw()
            if not re.match(r'^[A-Za-z0-9 ÄÖÜaöäß]+$', keyword):
                return await msg.channel.send(f'{msg.author.mention} please give me words like /^[A-Za-z0-9 ÄÖÜaöäß]+$/')
            print(f'Searching for "{keyword}"')
            img_path = await imagine.rv_image(keyword, adult)
            if not img_path:
                excuses = ['I cannot imagine that', 'I don\'t even know what that is']
                return await msg.channel.send(f'{msg.author.mention} {random.choice(excuses)}')
            await msg.channel.send(file=discord.File(img_path, f'{keyword}.jpg'))

    async def start_word_game(self, orig_msg):
        if self.word_prompt:
            await orig_msg.channel.send('STFU AND WAIT FOR THE OLD ROUND TO END')
            return
        txt = 'WHAT IS THIS WORD?????? U HAVE 30 SECONDS!!!'
        lines = [line for line in open('res/uwuwords.txt')]
        words = [random.choice(lines).split(';') for _ in range(4)]
        self.correct_word = random.randint(0, 3)
        embed = discord.Embed(title=f'{words[self.correct_word][0]}', color=0xa6ce86)
        for i, word in enumerate(words):
            embed.add_field(name=f'{i + 1}', value=f'{word[1]}', inline=False)
        embed.set_footer(text=f'difficulty {words[self.correct_word][4]}')
        self.word_prompt = await orig_msg.channel.send(txt, embed=embed)
        self.word_guesses = {}
        for reaction in self.num_reacts:
            await self.word_prompt.add_reaction(reaction)
        await asyncio.sleep(30)
        txt = f'GAME OVER!! CORRECT GUESSES: '
        for uid, guess in self.word_guesses.items():
            if guess == self.correct_word:
                txt += f'{self.get_user(uid).display_name} '
        await orig_msg.channel.send(txt)
        self.word_prompt = None

    async def on_reaction_add(self, reaction, user):
        if user.id == self.user.id or not self.word_prompt or reaction.message.id != self.word_prompt.id:
            return
        try:
            guess = self.num_reacts.index(reaction.emoji)
            if user.id not in self.word_guesses.keys():
                self.word_guesses[user.id] = guess
        except ValueError:
            print(f'what is this emoji? {reaction.emoji}')
        print(self.word_guesses)

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
