from commands.command import Command, Category
from forex_python.converter import CurrencyRates, CurrencyCodes
from forex_python.bitcoin import BtcConverter
from decimal import Decimal
import math


class CurrencyCommand(Command):
    name = 'currency'
    aliases = ['cc']
    category = Category.UTILITY
    arg_range = (3, 3)
    description = 'convert between currencies'
    arg_desc = '<amount> <origin currency> <destination currency>'

    @staticmethod
    def format_number(number, significant, min_precision=0):
        round_to = max(min_precision, significant - math.floor(math.log10(number)) - 1)
        return f'{round(number, round_to):.{round_to}f}'.rstrip('.0')

    def currency_code_and_symbol(self, code_or_symbol):
        if code_or_symbol.upper() in ('BTC', '₿'):
            return 'BTC', '₿'
        c = CurrencyCodes()
        code = c.get_currency_code_from_symbol(code_or_symbol)
        if code:
            return code, code_or_symbol
        code_or_symbol = code_or_symbol.upper()
        symbol = c.get_symbol(code_or_symbol)
        if symbol:
            return code_or_symbol, symbol
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
        if o_code == 'BTC':
            b = BtcConverter()
            res = b.convert_btc_to_cur(amount, 'USD')
            if d_code != 'USD':
                res = c.convert('USD', d_code, res)
        elif d_code == 'BTC':
            b = BtcConverter()
            if o_code != 'USD':
                amount = c.convert(o_code, 'USD', amount)
            res = b.convert_to_btc(amount, o_code)
        else:
            res = c.convert(o_code, d_code, amount)
        res = self.format_number(res, 4, 2)
        await msg.channel.send(f'{amount: f} {o_code} = {res or 0} {d_code}')
