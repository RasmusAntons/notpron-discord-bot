from commands.command import Command, Category
from utils import to_code_block, escape_discord
import globals
import config
import json
import emoji


class ConfigCommand(Command):
    name = 'config'
    aliases = ['conf']
    category = Category.ADMIN
    arg_range = (1, 99)
    description = 'View and edit the bot configuration. Enter lists and dicts as JSON.'
    arg_desc = 'dump | get <key> | set <key> <value> | unset <key> | reset <key> | list_contains <key> <value> ' \
               '| list_add <key> <value> | list_remove <value> | dict_get <key> <sub_key> ' \
               '| dict_set <key> <sub_key> <value> | dict_unset <key> <sub_key>'

    async def check(self, args, msg, test=False):
        return await super().check(args, msg, test) and config.is_admin(msg.author)

    async def handle_get(self, config_key, msg):
        value = globals.conf.get(config_key)
        f_value = f'{config_key.value.key}: {config_key.value.datatype.value.__name__} = {value}'
        await msg.channel.send(to_code_block(f_value))

    async def execute(self, args, msg):
        if len(args) == 1:
            if args[0] == 'dump':
                await msg.channel.send(f'**{globals.bot.user.name} Config Dump**\n{to_code_block(globals.conf.dump())}')
                return True
            else:
                return False
        config_key = self.get_config_key(args[1].lower())
        if len(args) == 2 and args[0] == 'get':
            await self.handle_get(config_key, msg)
        elif len(args) >= 3 and args[0] == 'set':
            value = self.parse_value(' '.join(args[2:]), config_key)
            globals.conf.set(config_key, value)
            await self.handle_get(config_key, msg)
        elif len(args) == 2 and args[0] == 'unset':
            globals.conf.unset(config_key)
            await self.handle_get(config_key, msg)
        elif len(args) == 2 and args[0] == 'reset':
            globals.conf.reset(config_key)
            await self.handle_get(config_key, msg)
        elif len(args) >= 3 and args[0] == 'list_contains':
            value = self.parse_value(' '.join(args[2:]), config_key, override_dtype=config_key.value.list_item_type.value)
            if globals.conf.list_contains(config_key, value):
                await msg.channel.send(f'{escape_discord(value)} is in {config_key.value.key}.')
            else:
                await msg.channel.send(f'{escape_discord(value)} is not in {config_key.value.key}.')
        elif len(args) >= 3 and args[0] == 'list_add':
            value = self.parse_value(' '.join(args[2:]), config_key, override_dtype=config_key.value.list_item_type.value)
            if globals.conf.list_add(config_key, value):
                await msg.channel.send(f'Added {escape_discord(value)} to {config_key.value.key}.')
            else:
                await msg.channel.send(f'{escape_discord(value)} is already in {config_key.value.key}.')
        elif len(args) >= 3 and args[0] == 'list_remove':
            value = self.parse_value(' '.join(args[2:]), config_key, override_dtype=config_key.value.list_item_type.value)
            if globals.conf.list_add(config_key, value):
                await msg.channel.send(f'Removed {escape_discord(value)} from {config_key.value.key}.')
            else:
                await msg.channel.send(f'{escape_discord(value)} is not in {config_key.value.key}.')
        elif len(args) == 3 and args[0] == 'dict_get':
            sub_key = self.parse_value(args[2], config_key, override_dtype=config_key.value.key_type.value, emojize=True)
            value = globals.conf.dict_get(config_key, sub_key)
            f_value = f'{config_key.value.key}[{sub_key}]: {config_key.value.value_type.value.__name__} = {value}'
            await msg.channel.send(to_code_block(f_value))
        elif len(args) >= 4 and args[0] == 'dict_set':
            sub_key = self.parse_value(args[2], config_key, override_dtype=config_key.value.key_type.value, emojize=True)
            value = self.parse_value(' '.join(args[3:]), config_key, override_dtype=config_key.value.value_type.value)
            globals.conf.dict_set(config_key, sub_key, value)
            await msg.channel.send(f'Set {config_key.value.key}[{escape_discord(sub_key)}] to {escape_discord(value)}.')
        elif len(args) == 3 and args[0] == 'dict_unset':
            sub_key = self.parse_value(args[2], config_key, override_dtype=config_key.value.key_type.value, emojize=True)
            if globals.conf.dict_unset(config_key, sub_key):
                await msg.channel.send(f'Unset {config_key.value.key}[{escape_discord(sub_key)}].')
            else:
                await msg.channel.send(f'{escape_discord(sub_key)} is not a key in {config_key.value.key}.')
        else:
            return False
        return True

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
