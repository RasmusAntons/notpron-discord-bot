from decimal import Decimal
import math

from discord.ext import commands
from forex_python.bitcoin import BtcConverter
from forex_python.converter import CurrencyRates, CurrencyCodes
import quantities


class ConvertCog(commands.Cog, name='Convert', description='convert values'):
    @staticmethod
    def format_number(number, significant, min_precision=0):
        round_to = max(min_precision, significant - math.floor(math.log10(number)) - 1)
        return f'{round(number, round_to):.{round_to}f}'.removesuffix('.0')

    @commands.hybrid_command(name='convert', aliases=('conv',), description='convert between two units')
    async def convert(self, ctx: commands.Context, amount: float, origin: str, destination: str) -> None:
        q = quantities.Quantity(amount, origin)
        ou = str(q.units)[4:]
        q.units = destination
        r = self.format_number(q.item(), 4)
        du = str(q.units)[4:]
        await ctx.reply(f'{self.format_number(amount, 4)} {ou} = {r} {du}')

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

    @commands.hybrid_command(name='currency', aliases=('cc',), description='convert between currencies')
    async def currency(self, ctx: commands.Context, amount: float, origin: str, destination: str) -> None:
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
        await ctx.reply(f'{self.format_number(amount, 2, 2)} {o_code} = {res or 0} {d_code}')
