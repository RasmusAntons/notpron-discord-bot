from commands.command import Command
import random


class RollCommand(Command):
    name = 'roll'
    aliases = []
    arg_range = (0, 2)
    description = 'roll a die'
    arg_desc = '[amount] [d[sides]]'

    async def execute(self, args, msg):
        sides = 6
        amount = 1
        for arg in args:
            if arg.startswith('d') or arg.startswith('D'):
                sides = int(arg[1:])
            else:
                amount = int(arg)
        if amount > 100:
            raise RuntimeError('too many dice >:(')
        rolls = [random.randint(1, sides) for _ in range(amount)]
        res = f'{sum(rolls)}'
        if amount > 1:
            rolls_s = [str(roll) for roll in rolls]
            res += f' ({" + ".join(rolls_s)})'
        await msg.reply(res)
