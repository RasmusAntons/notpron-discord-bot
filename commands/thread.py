from commands.command import Command, Category
import globals


class ThreadCommand(Command):
    name = 'thread'
    category = Category.NOTPRON
    arg_range = (1, 2)
    description = 'request a DM with a link to the forum thread to a level'
    arg_desc = '<level name>'

    def __init__(self):
        super().__init__()
        globals.bot.db['threads'].create_index('level', unique=True)

    async def execute(self, args, msg):
        n = ''.join(args).replace('-', 'minus ')
        coll = globals.bot.db['threads']
        result = coll.find_one({'level': n})
        if result is None:
            res = "No thread with that name found"
        else:
            thread = result['value']
            res = f'Level {n}: {thread}'
        dm_channel = await globals.bot.get_dm_channel(msg.author)
        await dm_channel.send(res)
