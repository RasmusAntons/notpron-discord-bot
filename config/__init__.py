import yaml
from .key_models import *
import sys
from .conf_keys import Key
from .helper_functions import *
import globals


class Config:
    keys = Key

    def __init__(self, yaml_file):
        self._conf = {}
        self.yaml_file = yaml_file
        self.load_yaml()
        self._coll_name = 'config'

    def load_yaml(self, override=False):
        try:
            with open(self.yaml_file, 'r') as f:
                yaml_cfg = yaml.load(f, Loader=yaml.CLoader or yaml.Loader)
        except FileNotFoundError:
            self._create_yaml(self.yaml_file)
            print(f'New config file created in {self.yaml_file}, please enter required values.', file=sys.stderr)
            sys.exit(-1)
        for enum_item in self.keys:
            key = enum_item.value.key
            if key in yaml_cfg and key is not None and (override or key not in self._conf):
                self._conf[key] = yaml_cfg[key]
            elif enum_item.value.default is not None:
                self._conf[key] = enum_item.value.default

    def load_db(self, override=True):
        for enum_item in self.keys:
            key = enum_item.value.key
            coll = globals.bot.db[self._coll_name]
            coll.create_index('key', unique=True)
            result = coll.find_one({'key': key})
            if result is not None and (override or key not in self._conf):
                self._conf[key] = result['value']

    def _create_yaml(self, yaml_file):
        yaml_parts = []
        for enum_item in self.keys:
            key = enum_item.value
            if key.help_text:
                yaml_parts.append(f'# {key.help_text}')
            escape = '# ' if not key.required else ''
            yaml_repr = yaml.dump(key.default_or_empty).rstrip('...\n')
            if type(key.default_or_empty) in (list, dict):
                yaml_repr = '\n' + '\n'.join((f'{escape}  {line}' for line in yaml_repr.split('\n')))
            yaml_parts.append(f'{escape}{key.key}: {yaml_repr}\n')
        with open(yaml_file, 'w') as f:
            f.write('\n'.join(yaml_parts))

    def get(self, key, default=None, *, bypass_protected=False):
        value = self._conf.get(key.value.key)
        if value is None:
            return default
        if key.value.protected and not bypass_protected:
            value = key.value.protected_val
        return value

    def set(self, key, value):
        assert value is None or type(value) == key.value.datatype.value
        self._conf[key.value.key] = value
        coll = globals.bot.db[self._coll_name]
        coll.replace_one({'key': key.value.key}, {'key': key.value.key, 'value': value}, upsert=True)

    def unset(self, key, ignore_required=False):
        if key.value.required and not ignore_required:
            raise RuntimeError(f'Config key {key.value.key} cannot be unset.')
        del self._conf[key.value.key]
        coll = globals.bot.db[self._coll_name]
        coll.delete_one({'key': key.value.key})

    def reset(self, key):
        self.unset(key, ignore_required=True)
        self.load_yaml(override=False)

    def list_contains(self, key, value, *, bypass_protected=False):
        assert type(value) == key.value.list_item_type.value
        if key.value.protected and not bypass_protected:
            return False
        value_list = self.get(key, bypass_protected=True)
        return value_list and value in value_list

    def list_add(self, key, value):
        assert type(value) == key.value.list_item_type.value
        value_list = self.get(key, [])
        if value in value_list:
            return False
        value_list.append(value)
        self.set(key, value_list)
        return True

    def list_remove(self, key, value):
        assert type(value) == key.value.list_item_type.value
        value_list = self.get(key)
        if value_list is None or value not in value_list:
            return False
        value_list.remove(value)
        self.set(key, value_list)
        return True

    def dict_get(self, key, sub_key, default=None, *, bypass_protected=False):
        assert type(sub_key) == key.value.key_type.value
        if key.value.protected and not bypass_protected:
            return default
        value_dict = self.get(key, bypass_protected=True)
        if value_dict is None:
            return default
        return value_dict.get(sub_key, default)

    def dict_set(self, key, sub_key, value):
        assert type(sub_key) == key.value.key_type.value
        assert type(value) == key.value.value_type.value
        value_dict = self.get(key, {})
        value_dict[sub_key] = value
        self.set(key, value_dict)

    def dict_unset(self, key, sub_key):
        assert type(sub_key) == key.value.key_type.value
        value_dict = self.get(key, {})
        if sub_key not in value_dict:
            return False
        del value_dict[sub_key]
        self.set(key, value_dict)
        return True

    def dump(self, full=False):
        res = []
        for enum_item in self.keys:
            lhs = f'{enum_item.value.key}: {enum_item.value.datatype.value.__name__}'
            value = self.get(enum_item)
            if full or value is not None:
                res.append(f'{lhs:28s} = {value}')
        return '\n'.join(res)
