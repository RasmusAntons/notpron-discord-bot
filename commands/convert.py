from commands.command import Command
import quantities


class ConvertCommand(Command):
    name = 'convert'
    aliases = ['conv']
    arg_range = (3, 3)
    description = 'convert between two units'
    arg_desc = '<amount> <origin unit> <destination unit>'

    async def execute(self, args, msg):
        amount, origin, destination = args
        amount = float(amount)
        q = quantities.Quantity(amount, origin)
        ou = str(q.units)[4:]
        q.units = destination
        r = q.item()
        du = str(q.units)[4:]
        await msg.channel.send(f'{amount}{ou} = {r}{du}')
