from commands.command import Command, Category
import quantities
import math


class ConvertCommand(Command):
    name = 'convert'
    category = Category.UTILITY
    aliases = ['conv']
    arg_range = (3, 3)
    description = 'convert between two units'
    arg_desc = '<amount> <origin unit> <destination unit>'

    @staticmethod
    def format_number(number, significant, min_precision=0):
        round_to = max(min_precision, significant - math.floor(math.log10(number)) - 1)
        return f'{round(number, round_to):.{round_to}f}'.rstrip('.0')

    async def execute(self, args, msg):
        amount, origin, destination = args
        amount = float(amount)
        q = quantities.Quantity(amount, origin)
        ou = str(q.units)[4:]
        q.units = destination
        r = self.format_number(q.item(), 4)
        du = str(q.units)[4:]
        await msg.channel.send(f'{self.format_number(amount, 4)} {ou} = {r} {du}')
