import random

from discord.ext import commands

from utils import escape_discord

responses = {
    'positive': [
        'It is certain',
        'Without a doubt',
        'You may rely on it',
        'Yes definitely',
        'It is decidedly so',
        'As I see it, yes',
        'Most likely', 'Yes',
        'Outlook good',
        'Signs point to yes',
    ],
    'neutral': [
        'Reply hazy try again',
        'Better not tell you now',
        'Ask again later',
        'Cannot predict now',
        'Concentrate and ask again',
    ],
    'negative': [
        'Don’t count on it',
        'Outlook not so good',
        'My sources say no',
        'Very doubtful',
        'My reply is no',
    ]
}


class EightballCog(commands.Cog, name='Eightball', description='answer a yes or no question'):
    @commands.hybrid_command(name='8ball', aliases=('eightball',), description='answer a yes or no question')
    async def eightball(self, ctx: commands.Context, question: str) -> None:
        category = random.choice(list(responses.values()))
        response = random.choice(category)
        if ctx.interaction:
            response = f'> {escape_discord(question)}\n{response}'
        await ctx.reply(response)
