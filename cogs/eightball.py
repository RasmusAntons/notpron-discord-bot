import random
from cogs.command import Command, Category


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


class EightballCommand(Command):
    name = '8ball'
    category = Category.UTILITY
    arg_range = (0, 99)
    arg_desc = '[question...]'
    description = 'Answer a yes or no question'

    async def execute(self, args, msg):
        category = random.choice(list(responses.values()))
        response = random.choice(category)
        await msg.reply(response)
