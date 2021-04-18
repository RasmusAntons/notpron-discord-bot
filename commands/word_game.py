from commands.command import Command, Category
import random
import discord
import asyncio
import globals
import utils
from utils import escape_discord
from pymongo.errors import DuplicateKeyError


class GuessingGameCommand(Command):
    name = 'wordgame'
    aliases = ['botpronpleasestartthemultiplechoicewordguessinggame', 'wg']
    category = Category.UTILITY
    arg_range = (0, 99)
    description = 'Start a word game.'
    arg_desc = '[language] | add <language> <word> <definition...> | remove <language> <word>'
    word_prompt = None
    correct_word = None
    word_guesses = {}
    num_reacts = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

    def __init__(self):
        super().__init__()
        globals.bot.reaction_listeners.add(self)
        coll = globals.bot.db['word_game']
        coll.create_index('question', unique=True)
        coll.create_index('language')

    async def execute(self, args, msg):
        if len(args) == 0:
            await self.start_word_game(msg)
            return True
        elif len(args) == 1:
            await self.start_word_game(msg, args[0])
            return True
        elif len(args) >= 4 and args[0] == 'add':
            coll = globals.bot.db['word_game']
            try:
                coll.insert_one({'language': args[1], 'question': args[2], 'answer': ' '.join(args[3:])})
                await msg.channel.send(f'Added {escape_discord(args[1])} word "{escape_discord(args[2])}".')
            except DuplicateKeyError:
                await msg.channel.send(f'"{escape_discord(args[2])}" already exists for {escape_discord(args[2])}.')
            return True
        elif len(args) >= 3 and args[0] in ('remove', 'delete'):
            coll = globals.bot.db['word_game']
            deleted_count = coll.delete_one({'language': args[1], 'question': args[2]}).deleted_count
            if deleted_count:
                await msg.channel.send(f'Removed {escape_discord(args[1])} word "{escape_discord(args[2])}".')
            else:
                await msg.channel.send(f'Cannot find {escape_discord(args[1])} word "{escape_discord(args[2])}".')
            return True
        return False

    async def start_word_game(self, orig_msg, lang='english'):
        if self.word_prompt:
            await orig_msg.reply('Please wait for the round to end.')
            return
        txt = 'What is this word? You have 30 seconds!'
        coll = globals.bot.db['word_game']
        words = list(coll.aggregate([{'$match': {'language': lang}}, {'$sample': {'size': 4}}]))
        if len(words) < 4:
            raise RuntimeError(f'There are {len(words)} {lang} words, at least 4 are needed for the word game.')
        self.correct_word = random.randint(0, 3)
        embed = discord.Embed(title=words[self.correct_word]['question'], color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
        for i, word in enumerate(words):
            embed.add_field(name=f'{i + 1}', value=escape_discord(word['answer']), inline=False)
        difficulty = words[self.correct_word].get('difficulty')
        if difficulty:
            embed.set_footer(text=f'difficulty {difficulty}')
        self.word_prompt = await orig_msg.channel.send(txt, embed=embed)
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

    async def on_reaction_add(self, reaction, user):
        if user.id == globals.bot.user.id or not self.word_prompt or reaction.message.id != self.word_prompt.id:
            return
        try:
            guess = self.num_reacts.index(reaction.emoji)
            if user.id not in self.word_guesses.keys():
                self.word_guesses[user.id] = guess
        except ValueError:
            pass

    async def on_reaction_remove(self, reaction, user):
        pass
