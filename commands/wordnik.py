import wordnik.swagger
import wordnik.WordApi
from commands.command import Command, Category
import globals


class WordnikCommand(Command):
    name = 'wordnik'
    category = Category.UTILITY
    aliases = ['define']
    arg_range = (1, 99)
    description = 'define a word'
    arg_desc = 'define|frequency <word>'

    async def send_usage(self):
        pass

    async def execute(self, args, msg):
        api_key = globals.conf.get(globals.conf.keys.WORDNIK_API_KEY, bypass_protected=True)
        wordnik_client = wordnik.swagger.ApiClient(api_key, 'https://api.wordnik.com/v4')
        word_api = wordnik.WordApi.WordApi(wordnik_client)
        for subcmd in ['define']:
            if msg.content.split(' ')[0][1:] == subcmd:
                args.insert(0, subcmd)
        if args[0] == 'define':
            if len(args) != 2:
                return False
            definitions = word_api.getDefinitions(args[1], limit=2)
            await msg.reply(definitions[1].text)
        elif args[0] == 'frequency':
            if len(args) != 2:
                return False
            frequency = word_api.getWordFrequency(args[1])
            await msg.reply(str(frequency))
        else:
            return False
        return True
