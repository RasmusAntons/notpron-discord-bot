from commands.command import Command, Category
import asyncio
import random
import discord
import globals
import datetime


class RrCommand(Command):
    name = 'rr'
    category = Category.NOTPRON
    arg_range = (0, 0)
    description = 'play a round of russian roulette'

    def __init__(self):
        super(RrCommand, self).__init__()
        coll = globals.bot.db['russian_roulette']
        if not coll.find_one({}):
            coll.insert_one({'streak': 0, 'max_streak': 0, 'uid': None, 'date': None, 'misses': 0, 'deaths': 0})

    async def execute(self, args, msg):
        await msg.channel.send(f'*{msg.author.display_name} loads one bullet into the revolver and slowly pulls the trigger...*')
        async with msg.channel.typing():
            await asyncio.sleep(1)
            coll = globals.bot.db['russian_roulette']
            if random.randrange(6) == 0:
                await msg.channel.send(f'{msg.author.display_name} **died**')
                coll.update_one({}, {'$inc': {'deaths': 1}, '$set': {'streak': 0}})
                try:
                    await msg.author.edit(nick=f'dead')
                except discord.HTTPException:
                    pass
            else:
                stats = coll.find_one({})
                stats['streak'] += 1
                stats['misses'] += 1
                if stats['streak'] > stats['max_streak']:
                    stats['max_streak'] = stats['streak']
                    stats['uid'] = msg.author.id
                    stats['date'] = datetime.datetime.now()
                coll.replace_one({}, stats)
                await msg.channel.send(
                    f'*click* - empty chamber. {msg.author.display_name} will live another day. Who\'s next? Misses since last death: {stats["streak"]}')
