import markovify
import os
import random
import asyncio
from discord.utils import escape_mentions
import re
from globals import bot
import globals
from utils import get_user


FILENAME = 'markov/{}.json'
TXT_FILE = 'markov/{}.txt'


class Markov:
    def __init__(self):
        self.models = {}

    async def load_model(self, key):
        fn = FILENAME.format(key)
        if os.path.exists(fn):
            with open(fn, 'r') as f:
                self.models[key] = markovify.Text.from_json(f.read())

    async def regenerate(self, orig_msg):
        msgs = {'all': []}
        n = 0
        markov_channels = globals.conf.get(globals.conf.keys.MARKOV_CHANNELS)
        for i, channel in enumerate(markov_channels):
            await orig_msg.channel.send(f'reading channel {i + 1}/{len(markov_channels)}')
            async for msg in globals.bot.get_channel(channel).history(limit=10**5):
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
        for uid in re.findall(r'<@!?(\d+)>', m):
            usr = await get_user(int(uid))
            m = m.replace(f'<@{uid}>', usr.name or '??????')
            m = m.replace(f'<@!{uid}>', usr.name or '??????')
        return m

    def get_sentence(self):
        model = self.models.get('all')
        for i in range(100):
            m = model.make_sentence()
            if m:
                return m
        return ''

    async def talk(self, channel, user='all', cont_chance=0.5, query=None):
        model = self.models.get(user)
        if model is None:
            await self.load_model(user)
            model = self.models.get(user)
        if model is None:
            return
        keep_talking = True
        while keep_talking:
            for i in range(100):
                if query:
                    query = re.sub(r'<@!?\d+>', '', query)
                    query = re.sub(r'[\'":;,\.?]', '', query)
                    query = re.sub(r'\s+', ' ', query).strip()
                    lcw = model.least_common_word(query)
                    if lcw:
                        m = model.make_sentence_that_contains(lcw)
                        query = query.replace(lcw, '')
                    else:
                        m = model.make_sentence()
                else:
                    m = model.make_sentence()
                if m:
                    m = await self.replace_mentions(m)
                    m = escape_mentions(m)
                    await channel.trigger_typing()
                    await asyncio.sleep(0.04 * len(m))
                    await channel.send(m)
                    break
            keep_talking = random.random() < cont_chance
