from enum import Enum
from abc import ABC, abstractmethod
import globals


class Category(Enum):
    ADMIN = 'admin'
    UTILITY = 'utility'
    NOTPRON = 'notpron'
    UNDEFINED = 'undefined'


class Command(ABC):
    @property
    @abstractmethod
    def name(self):
        pass

    @property
    @abstractmethod
    def arg_range(self):
        pass

    aliases = []
    description = None
    arg_desc = None
    category = Category.UNDEFINED
    guilds = []

    def register(self):
        names = [self.name] + self.aliases
        for name in names:
            if name in globals.bot.commands.keys():
                raise RuntimeError(f'Duplicate command: {name} is already registered')
            globals.bot.commands[name] = self
        globals.bot.commands_flat.append(self)

    async def check(self, args, msg, test=False):
        return self.category.value not in globals.conf.get(globals.conf.keys.BLACKLIST_CATEGORIES, [])

    def usage_str(self, prefix):
        usage = [f'Usage: `{prefix}{self.name}']
        if self.arg_desc:
            usage.append(f' {self.arg_desc}')
        usage.append('`')
        return ''.join(usage)

    @abstractmethod
    async def execute(self, args, msg):
        pass
