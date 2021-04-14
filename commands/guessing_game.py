from commands.command import Command
import random
import discord
import asyncio


class GuessingGameCommand(Command):
    name = 'botpronpleasestartthemultiplechoicewordguessinggame'
    arg_range = (0, 0)
    description = 'start a word game'
    word_prompt = None
    correct_word = None
    word_guesses = {}
    guilds = [363692038002180097]
    num_reacts = ['1️⃣', '2️⃣', '3️⃣', '4️⃣']

    def __init__(self, bot):
        super().__init__(bot)
        bot.reaction_listeners.add(self)

    async def execute(self, args, msg):
        await self.start_word_game(msg)

    async def start_word_game(self, orig_msg):
        if self.word_prompt:
            await orig_msg.channel.send('STFU AND WAIT FOR THE OLD ROUND TO END')
            return
        txt = 'WHAT IS THIS WORD?????? U HAVE 30 SECONDS!!!'
        lines = [line for line in open('res/uwuwords.txt')]
        words = [random.choice(lines).split(';') for _ in range(4)]
        self.correct_word = random.randint(0, 3)
        embed = discord.Embed(title=f'{words[self.correct_word][0]}', color=self.bot.config.get_embed_colour())
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
                txt += f'{self.bot.get_user(uid).display_name} '
        await orig_msg.channel.send(txt)
        self.word_prompt = None

    async def on_reaction_add(self, reaction, user):
        if user.id == self.bot.user.id or not self.word_prompt or reaction.message.id != self.word_prompt.id:
            return
        try:
            guess = self.num_reacts.index(reaction.emoji)
            if user.id not in self.word_guesses.keys():
                self.word_guesses[user.id] = guess
        except ValueError:
            print(f'what is this emoji? {reaction.emoji}')
        print(self.word_guesses)

    async def on_reaction_remove(self, reaction, user):
        pass
