import re
import globals
import random
from listeners import MessageListener


class AnagramListener(MessageListener):
    def __init__(self):
        super().__init__()
        self.min_len = 8
        self.max_len = 20
        self.emoji = ['😄', '😆', '😉', '😮', '😔', '🙂', '😋', '🤓']
        self.words = {}
        for line in open('res/anagram_wordlist.txt'):
            if not line:
                continue
            word = line.strip()
            key = ''.join(sorted(word))
            if key in self.words:
                self.words[key].append(word)
            else:
                self.words[key] = [word]

    async def on_message(self, msg):
        if msg.author.id == globals.bot.user.id:
            return
        if not globals.conf.list_contains(globals.conf.keys.CHANNELS, msg.channel.id):
            return
        if not self.min_len <= len(msg.content) <= self.max_len * 2:
            return
        letters = re.sub(r'\W', '', msg.content).lower()
        if self.min_len <= len(letters) <= self.max_len:
            key = ''.join(sorted(letters))
            words = self.words.get(key)
            if words and letters in words:
                words.remove(letters)
            if words:
                if len(words) == 1:
                    text = f'I found an anagram for your message {random.choice(self.emoji)}: {words[0]}'
                else:
                    words_str = ', '.join(words)
                    text = f'I found {len(words)} anagrams for your message {random.choice(self.emoji)}: {words_str}'
                await msg.reply(text)
