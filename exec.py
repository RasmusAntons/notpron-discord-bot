import argparse
from config import Config
import discord
# from scripts.populate_hints import populate_hints
# from scripts.populate_word_game import populate_word_game
# from scripts.populate_highlights import populate_highlights
# from scripts.populate_underage import populate_underage
# from scripts.populate_rv import populate_rv
# from scripts.weekly_notify import weekly_notify
# from scripts.send_embed import send_embed
# from scripts.emoji_stat import emoji_stat
# from scripts.fix_weekly_solver_v2 import fix_weekly_solver_v2
# from scripts.fix_games_role import fix_games_role
# from scripts.quarantine_perms import quarantine_perms
# from scripts.brat import brat
from scripts.weeklies_channels import create_weeklies_channels
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
        # await send_embed()
        # await weekly_notify()
        # await emoji_stat()
        # await fix_weekly_solver_v2()
        # await fix_games_role()
        # await quarantine_perms()
        # await brat()
        await create_weeklies_channels()

        # ch = self.get_channel(776099352962793503)
        # msg = await ch.fetch_message(883092891046645791)
        # await msg.reply(':pensive:')

        print('done')
        await self.close()


def run_bot(config):
    bot = ExecDiscordConnection(config)
    bot.run(bot.conf.get(bot.conf.keys.DISCORD_TOKEN, bypass_protected=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='config.yaml', help='Config yaml file.')
    args = parser.parse_args()
    run_bot(args.config)
