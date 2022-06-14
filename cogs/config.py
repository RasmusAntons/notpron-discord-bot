import io
import json

import discord
from discord import app_commands
from discord.ext import commands
import emoji

import config
import globals
from utils import to_code_block, escape_discord


class ConfigCog(commands.Cog, name='Config', description='manage bot configuration'):
    @commands.hybrid_group(name='config', description='manage bot configuration')
    async def config_grp(self, ctx):
        return None

    @config_grp.command(name='dump', description='dump bot configuration')
    async def dump(self, ctx: commands.Context) -> None:
        file = discord.File(io.StringIO(globals.conf.dump()), filename=f'{globals.bot.user.name}_config.txt')
        await ctx.reply(file=file)

    @config_grp.command(name='get', description='get a config value')
    async def get(self, ctx: commands.Context, key: str) -> None:
        config_key = self.get_config_key(key)
        await self.handle_get(ctx, config_key)

    @config_grp.command(name='set', desctiption='set a config value')
    @config.check_bot_admin()
    async def set(self, ctx: commands.Context, key: str, value: str) -> None:
        config_key = self.get_config_key(key)
        value = self.parse_value(value, config_key)
        globals.conf.set(config_key, value)
        await self.handle_get(ctx, config_key)

    @config_grp.command(name='unset', description='unset a config value')
    @config.check_bot_admin()
    async def unset(self, ctx: commands.Context, key: str) -> None:
        config_key = self.get_config_key(key)
        globals.conf.unset(config_key)
        await self.handle_get(ctx, config_key)

    @config_grp.command(name='reset', description='reset a config value to the .yaml file')
    @config.check_bot_admin()
    async def reset(self, ctx: commands.Context, key: str) -> None:
        config_key = self.get_config_key(key)
        globals.conf.reset(config_key)
        await self.handle_get(ctx, config_key)

    @config_grp.command(name='list_contains', description='check if list entry contains value')
    async def list_contains(self, ctx: commands.Context, key: str, value: str) -> None:
        config_key = self.get_config_key(key)
        value = self.parse_value(value, config_key, override_dtype=config_key.value.list_item_type.value)
        if globals.conf.list_contains(config_key, value):
            await ctx.reply(f'{escape_discord(value)} is in {config_key.value.key}.')
        else:
            await ctx.reply(f'{escape_discord(value)} is not in {config_key.value.key}.')

    @config_grp.command(name='list_add', description='add value to list entry')
    @config.check_bot_admin()
    async def list_add(self, ctx: commands.Context, key: str, value: str) -> None:
        config_key = self.get_config_key(key)
        value = self.parse_value(value, config_key, override_dtype=config_key.value.list_item_type.value)
        if globals.conf.list_add(config_key, value):
            await ctx.reply(f'Added {escape_discord(value)} to {config_key.value.key}.')
        else:
            await ctx.reply(f'{escape_discord(value)} is already in {config_key.value.key}.')

    @config_grp.command(name='list_remove', description='remove value from list entry')
    @config.check_bot_admin()
    async def list_remove(self, ctx: commands.Context, key: str, value: str) -> None:
        config_key = self.get_config_key(key)
        value = self.parse_value(value, config_key, override_dtype=config_key.value.list_item_type.value)
        if globals.conf.list_remove(config_key, value):
            await ctx.reply(f'Removed {escape_discord(value)} from {config_key.value.key}.')
        else:
            await ctx.reply(f'{escape_discord(value)} is not in {config_key.value.key}.')

    @config_grp.command(name='dict_get', description='get value from dict entry')
    async def dict_get(self, ctx: commands.Context, key: str, sub_key: str) -> None:
        config_key = self.get_config_key(key)
        sub_key = self.parse_value(sub_key, config_key, override_dtype=config_key.value.key_type.value, emojize=True)
        value = globals.conf.dict_get(config_key, sub_key)
        f_value = f'{config_key.value.key}[{sub_key}]: {config_key.value.value_type.value.__name__} = {value}'
        await ctx.reply(to_code_block(f_value))

    @config_grp.command(name='dict_set', description='set value in dict entry')
    @config.check_bot_admin()
    async def dict_set(self, ctx: commands.Context, key: str, sub_key: str, value: str) -> None:
        config_key = self.get_config_key(key)
        sub_key = self.parse_value(sub_key, config_key, override_dtype=config_key.value.key_type.value, emojize=True)
        value = self.parse_value(value, config_key, override_dtype=config_key.value.value_type.value)
        globals.conf.dict_set(config_key, sub_key, value)
        await ctx.reply(f'Set {config_key.value.key}[{escape_discord(sub_key)}] to {escape_discord(value)}.')

    @config_grp.command(name='dict_unset', description='unset value in dict entry')
    @config.check_bot_admin()
    async def dict_unset(self, ctx: commands.Context, key: str, sub_key: str) -> None:
        config_key = self.get_config_key(key)
        sub_key = self.parse_value(sub_key, config_key, override_dtype=config_key.value.key_type.value, emojize=True)
        if globals.conf.dict_unset(config_key, sub_key):
            await ctx.reply(f'Unset {config_key.value.key}[{escape_discord(sub_key)}].')
        else:
            await ctx.reply(f'{escape_discord(sub_key)} is not a key in {config_key.value.key}.')

    @get.autocomplete('key')
    @set.autocomplete('key')
    @unset.autocomplete('key')
    @reset.autocomplete('key')
    @list_contains.autocomplete('key')
    @list_add.autocomplete('key')
    @list_remove.autocomplete('key')
    @dict_get.autocomplete('key')
    @dict_set.autocomplete('key')
    @dict_unset.autocomplete('key')
    async def key_autocomplete(self, interaction: discord.Interaction, key: str) -> None:
        choices = []
        for config_key in globals.conf.keys:
            if key.lower() in config_key.name.lower():
                choices.append(app_commands.Choice(name=config_key.name, value=config_key.name.lower()))
            if len(choices) == 25:
                break
        return choices

    @staticmethod
    async def handle_get(ctx: commands.Context, config_key: str):
        value = globals.conf.get(config_key)
        f_value = f'{config_key.value.key}: {config_key.value.datatype.value.__name__} = {value}'
        await ctx.reply(to_code_block(f_value))

    @staticmethod
    def parse_value(value_str, config_key, override_dtype=None, emojize=False):
        dtype = override_dtype or config_key.value.datatype.value
        if dtype == str:
            return value_str if not emojize else emoji.emojize(value_str)
        elif dtype == int:
            return int(value_str, 0)
        elif dtype == list:
            dtype_list = config_key.value.list_value.value
            try:
                value_list = json.loads(value_str)
                assert type(value_list) == list
                for value in value_list:
                    assert type(value) == dtype_list
            except (json.JSONDecodeError, AssertionError):
                raise RuntimeError(f'Enter a list of {dtype_list.__name__} as JSON.')
            return value_list
        elif dtype == dict:
            dtype_key = config_key.value.key_type.value
            dtype_value = config_key.value.value_type.value
            try:
                value_dict = json.loads(value_str)
                assert type(value_dict) == dict
                for key, value in value_dict.items():
                    assert type(key) == dtype_key and type(value) == dtype_value
            except (json.JSONDecodeError, AssertionError):
                raise RuntimeError(f'Enter a dict of {dtype_key.__name__} -> {dtype_value.__name__} as JSON.')
            return value_dict

    @staticmethod
    def get_config_key(key):
        for enum_item in globals.conf.keys:
            if enum_item.value.key == key:
                return enum_item
        raise RuntimeError(f'Config key {key} does not exist.')
