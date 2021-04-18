from commands.command import Command, Category
import globals


class AntiHintCommand(Command):
    name = 'antihint'
    category = Category.NOTPRON
    arg_range = (1, 1)
    description = 'request a DM with an antihint for a level'
    arg_desc = '<level name>'

    def __init__(self):
        super().__init__()
        globals.bot.db['antihints'].create_index('level', unique=True)

    async def execute(self, args, msg):
        hint = None
        n = -1
        try:
            n = int(args[0])
            coll = globals.bot.db['antihints']
            result = coll.find_one({'level': str(n)})
            if result:
                hint = result['value']
        except ValueError:
            pass
        if hint is None:
            res = ['Type !hint <level number from 1-79> for a level specific hint. No hints for 80 and beyond!']
        else:
            res = ['Official antihints for Notpron.', 'These are not REAL hints, just from non-walkthrough.',
                   'In other words, for fun, not for real help.']
            for line in hint:
                res.append(f'{n}: {line}')
        dm_channel = await globals.bot.get_dm_channel(msg.author)
        for line in res:
            await dm_channel.send(line)
