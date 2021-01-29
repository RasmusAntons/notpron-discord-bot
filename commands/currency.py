from commands.command import Command
from forex_python.converter import CurrencyRates, CurrencyCodes
from decimal import Decimal


class CurrencyCommand(Command):
    name = 'currency'
    aliases = ['cc']
    arg_range = (3, 3)
    description = 'convert between currencies'
    arg_desc = '<amount> <origin currency> <destination currency>'

    def currency_code_and_symbol(self, code_or_symbol):
        c = CurrencyCodes()
        symbol = c.get_symbol(code_or_symbol)
        if symbol:
            return code_or_symbol, symbol
        code = c.get_currency_code_from_symbol(code_or_symbol)
        if code:
            return code, code_or_symbol
        return None

    async def execute(self, args, msg):
        amount, origin, destination = args
        amount = Decimal(amount)
        o_code, o_symbol = self.currency_code_and_symbol(origin)
        d_code, d_symbol = self.currency_code_and_symbol(destination)
        c = CurrencyRates()
        res = c.convert(o_code, d_code, amount)
        await msg.channel.send(f'{amount} {o_code} = {res} {d_code}')
