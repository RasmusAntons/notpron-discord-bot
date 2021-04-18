from enum import Enum


class ConfigDatatype(Enum):
    STRING = str
    INT = int
    LIST = list
    DICT = dict


class ConfigKey:
    protected_val = '********'

    def __init__(self, key, datatype, *, required=False, default=None, protected=False, help_text=None):
        self.key = key
        self.datatype = datatype
        self.required = required
        self.default = default
        self.protected = protected
        self.help_text = help_text

    @property
    def default_or_empty(self):
        return self.default if self.default is not None else self.datatype.value()


class ConfigListKey(ConfigKey):
    protected_val = ['********']

    def __init__(self, key, list_item_type, *, required=False, default=None, protected=False, help_text=None):
        super().__init__(key, ConfigDatatype.LIST, required=required, default=default, protected=protected,
                         help_text=help_text)
        self.list_item_type = list_item_type

    @property
    def default_or_empty(self):
        return self.default if self.default is not None else [self.list_item_type.value()]


class ConfigDictKey(ConfigKey):
    protected_val = {'********': '********'}

    def __init__(self, key, key_type, value_type, *, required=False, default=None, protected=False, help_text=None):
        super().__init__(key, ConfigDatatype.DICT, required=required, default=default, protected=protected,
                         help_text=help_text)
        self.key_type = key_type
        self.value_type = value_type

    @property
    def default_or_empty(self):
        key_value = self.key_type.value() if self.key_type.value != str else ' '
        return self.default if self.default is not None else {key_value: self.value_type.value()}
