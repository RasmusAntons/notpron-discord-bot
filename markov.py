import markovify
import os
import random
from config import Config
import asyncio
import re


FILENAME = 'markov/{}.json'
TXT_FILE = 'markov/{}.txt'


class Markov:
    def __init__(self, bot, config: Config):
        self.bot = bot
        self.config = config
        self.models = {}

    async def load_model(self, key):
        fn = FILENAME.format(key)
        if os.path.exists(fn):
            with open(fn, 'r') as f:
                self.models[key] = markovify.Text.from_json(f.read())

    async def on_command(self, msg, cmd):
        if cmd == "regenerate" and msg.channel.id == self.config.get_control_channel():
            n = await self.regenerate(msg)
            await msg.channel.send(f"finished regenerating, using {n} messages")
        elif cmd.startswith("imitate "):
            if msg.mentions:
                await self.talk(msg.channel, user=int(msg.mentions[0].id))
            else:
                uname = cmd[8:]
                user = msg.channel.guild.get_member_named(uname)
                if user:
                    await self.talk(msg.channel, user=user.id)
                else:
                    try:
                        uid = int(cmd[8:])
                        if 100000000000000 <= uid <= 9999999999999999999:
                            await self.talk(msg.channel, user=uid)
                    except:
                        pass

    async def regenerate(self, orig_msg):
        msgs = {'all': []}
        n = 0
        for i, channel in enumerate(self.config.get_markov_channels()):
            await orig_msg.channel.send(f'reading channel {i + 1}/{len(self.config.get_markov_channels())}')
            async for msg in self.bot.get_channel(channel).history(limit=10**5):
                if not msg.author.bot:
                    n += 1
                    text = msg.content
                    msgs['all'].append(text)
                    if msg.author.id not in msgs:
                        msgs[msg.author.id] = [text]
                    else:
                        msgs[msg.author.id].append(text)
        for key, texts in msgs.items():
            if len(texts) < 20:
                continue
            with open(TXT_FILE.format(key), 'w') as f:
                f.write('\n'.join(texts))
            try:
                model = markovify.NewlineText('\n'.join(texts), retain_original=False)
                self.models[key] = model.compile(inplace=True)
                with open(FILENAME.format(key), 'w') as f:
                    f.write(self.models[key].to_json())
            except KeyError as e:
                await orig_msg.channel.send(str(e))
        return n

    async def replace_mentions(self, m):
        for uid in re.findall(r'<@!(\d+)>', m):
            usr = await self.bot.fetch_user(int(uid))
            m = m.replace(f'<!@{uid}>', usr.name or '??????')
        return m

    async def talk(self, channel, user='all', cont_chance=0.5):
        model = self.models.get(user)
        if model is None:
            await self.load_model(user)
            model = self.models.get(user)
        if model is None:
            return
        keep_talking = True
        while keep_talking:
            for i in range(100):
                m = model.make_sentence()
                if m:
                    m = await self.replace_mentions(m)
                    await channel.trigger_typing()
                    await asyncio.sleep(0.04 * len(m))
                    await channel.send(m)
                    break
            keep_talking = random.random() < cont_chance
