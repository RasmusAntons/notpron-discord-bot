import re
import globals
import random
from discord.ext import commands


class AnagramListener(commands.Cog):
    def __init__(self):
        super().__init__()
        self.max_len = 0
        self.emoji = ['😄', '😆', '😉', '😮', '🥺', '🙂', '😋', '🤓']
        self.words = {}
        for line in open('res/anagram_wordlist.txt'):
            if not line:
                continue
            word = line.strip()
            if len(word) > self.max_len:
                self.max_len = len(word)
            key = ''.join(sorted(word))
            if key in self.words:
                self.words[key].append(word)
            else:
                self.words[key] = [word]

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.id == globals.bot.user.id:
            return
        if not globals.conf.list_contains(globals.conf.keys.CHANNELS, msg.channel.id):
            return
        min_len = globals.conf.get(globals.conf.keys.ANAGRAM_MIN_LENGTH)
        if not min_len <= len(msg.content) <= 50:
            return
        letters = re.sub(r'\W', '', msg.content).lower()
        if min_len <= len(letters):
            key = ''.join(sorted(letters))
            words = self.words.get(key)
            if words and letters in words:
                words.remove(letters)
            if words:
                if len(words) == 1:
                    await msg.reply(f'{random.choice(self.emoji)} anagram: {words[0]}')
