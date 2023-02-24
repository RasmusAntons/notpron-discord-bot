import asyncio
import random

import discord
from discord.ext import commands
import pymongo
from pymongo.errors import DuplicateKeyError

import globals
import utils
from utils import escape_discord


class WordgameCog(commands.Cog, name='Wordgame', description='word game'):
    word_prompt = None
    correct_word = None
    word_guesses = {}
    num_reacts = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

    def __init__(self):
        self.coll = globals.bot.db['word_game']
        self.coll.create_index([('question', pymongo.ASCENDING), ('language', pymongo.ASCENDING)], unique=True)
        self.coll.create_index('language')

    @commands.hybrid_group(name='wordgame', description='word game')
    async def wordgame_grp(self, ctx):
        return None

    @wordgame_grp.command(name='start', description='start a word game')
    async def start(self, ctx: commands.Context, language: str = 'english') -> None:
        if self.word_prompt:
            await ctx.reply('Please wait for the round to end.')
            return
        txt = 'What is this word? You have 30 seconds!'
        words = list(self.coll.aggregate([{'$match': {'language': language}}, {'$sample': {'size': 4}}]))
        if len(words) < 4:
            raise RuntimeError(f'There are {len(words)} {language} words, at least 4 are needed for the word game.')
        self.correct_word = random.randint(0, 3)
        embed = discord.Embed(title=words[self.correct_word]['question'],
                              color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
        for i, word in enumerate(words):
            embed.add_field(name=f'{i + 1}', value=escape_discord(word['answer']), inline=False)
        difficulty = words[self.correct_word].get('difficulty')
        if difficulty:
            embed.set_footer(text=f'difficulty {difficulty}')
        self.word_prompt = await ctx.reply(txt, embed=embed)
        self.word_guesses = {}
        for reaction in self.num_reacts:
            await self.word_prompt.add_reaction(reaction)
        await asyncio.sleep(30)
        txt = f'Game over! Correct answers: '
        for uid, guess in self.word_guesses.items():
            if guess == self.correct_word:
                txt += f'{(await utils.get_user(uid)).display_name} '
        await self.word_prompt.reply(txt)
        self.word_prompt = None

    @wordgame_grp.command(name='addword', description='add a word')
    async def addword(self, ctx: commands.Context, word: str, definition: str, language: str = 'english') -> None:
        try:
            self.coll.insert_one({'language': language, 'question': word, 'answer': definition})
            await ctx.reply(f'Added {escape_discord(language)} word "{escape_discord(word)}".')
        except DuplicateKeyError:
            await ctx.reply(f'"{escape_discord(word)}" already exists for {escape_discord(language)}.')

    @wordgame_grp.command(name='removeword', description='remove a word')
    async def removeword(self, ctx: commands.Context, word: str, language: str = 'english') -> None:
        deleted_count = self.coll.delete_one({'language': language, 'question': word}).deleted_count
        if deleted_count:
            await ctx.reply(f'Removed {escape_discord(language)} word "{escape_discord(word)}".')
        else:
            await ctx.reply(f'Cannot find {escape_discord(language)} word "{escape_discord(word)}".')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.id == globals.bot.user.id or not self.word_prompt or reaction.message.id != self.word_prompt.id:
            return
        try:
            guess = self.num_reacts.index(reaction.emoji)
            if user.id not in self.word_guesses.keys():
                self.word_guesses[user.id] = guess
        except ValueError:
            pass
