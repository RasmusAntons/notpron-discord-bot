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
        try:
            amount = Decimal(amount)
        except Exception as _:
            raise ValueError(f'Cannot parse decimal: {amount}')
        try:
            o_code, o_symbol = self.currency_code_and_symbol(origin)
        except TypeError:
            raise ValueError(f'Unknown currency: {origin}')
        try:
            d_code, d_symbol = self.currency_code_and_symbol(destination)
        except TypeError:
            raise ValueError(f'Unknown currency: {destination}')
        c = CurrencyRates()
        res = c.convert(o_code, d_code, amount)
        await msg.channel.send(f'{amount} {o_code} = {res} {d_code}')
