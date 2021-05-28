from listeners import MessageListener
import string
import random
import globals


class BotReactionListener(MessageListener):
    punct = str.maketrans(dict.fromkeys(string.punctuation))

    async def on_message(self, msg):
        if not globals.conf.list_contains(globals.conf.keys.CHANNELS, msg.channel.id):
            return
        content_lower = msg.content.lower().translate(self.punct)
        words_lower = content_lower.split()
        if globals.conf.get(globals.conf.keys.INSTANCE) == 'notpron':
            if 'norway' in words_lower:
                await msg.add_reaction('<:tyteok:743847838097866842>')
            if 'rv' in words_lower:
                chance = random.random()
                if chance < 0.15:
                    await msg.add_reaction('<:rv:609873514161373337>')
                elif random.random() < 0.20:
                    await msg.add_reaction('<:tiredrv:754151962097877034>')
            if 'uwu' in words_lower:
                if random.random() < 0.2:
                    await msg.add_reaction('<:uwu:743223746760015932>')
            if 'owo' in words_lower:
                if random.random() < 0.2:
                    await msg.add_reaction('<:owo:743223746520678462>')
            if msg.author.id == 441958578962694144:
                for word in ['kill', 'murder', 'euthanize', 'assassinate', 'slaughter', 'exterminate', 'death']:
                    if word in words_lower:
                        await msg.add_reaction('<:cleaver:744968925023961119>')
            if 'botpron' in words_lower:
                await msg.add_reaction('<:iwanttodie:489169265497210900>')
            for phrase in ['hardest riddle', 'harder than notpron', 'better than notpron', 'notpron2', 'notpron 2',
                           'notpron two']:
                if phrase in content_lower:
                    await msg.add_reaction('<:cipher:745115170245836891>')
                    break
