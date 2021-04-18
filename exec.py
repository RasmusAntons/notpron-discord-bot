import argparse
from config import Config
import discord
from scripts.populate_hints import populate_hints
from scripts.populate_word_game import populate_word_game
from scripts.populate_highlights import populate_highlights
from scripts.populate_underage import populate_underage
from scripts.populate_rv import populate_rv
import pymongo
import globals


class ExecDiscordConnection(discord.Client):
    def __init__(self, config_file):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        globals.bot = self
        self.conf = Config(config_file)
        globals.conf = self.conf
        self._db_client = pymongo.MongoClient(self.conf.get(self.conf.keys.DB_URL))
        self.db = self._db_client[self.conf.get(self.conf.keys.INSTANCE)]
        self.conf.load_db()

    async def on_ready(self):
        print('I\'m in.')
        # populate_hints()
        # populate_word_game()
        # populate_highlights()
        # populate_underage()
        # populate_rv()

        print('done')
        await self.close()


def run_bot(config):
    bot = ExecDiscordConnection(config)
    bot.loop.run_until_complete(bot.login(bot.conf.get(bot.conf.keys.DISCORD_TOKEN, bypass_protected=True)))
    bot.loop.run_until_complete(bot.connect())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='config.yaml', help='Config yaml file.')
    args = parser.parse_args()
    run_bot(args.config)
