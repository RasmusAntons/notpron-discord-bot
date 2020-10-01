from abc import ABC, abstractmethod


class Command(ABC):

    def __init__(self, bot):
        self.bot = bot

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

    def register(self):
        names = [self.name] + self.aliases
        for name in names:
            if name in self.bot.commands.keys():
                raise RuntimeError(f'Duplicate command: {name} is already registered')
            self.bot.commands[name] = self

    async def check(self, args, msg):
        return True

    @abstractmethod
    async def execute(self, args, msg):
        pass
