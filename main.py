import argparse
from discord_connection import DiscordConnection


def run_bot(config_file):
    bot = DiscordConnection(config_file)
    bot.run(bot.conf.get(bot.conf.keys.DISCORD_TOKEN, bypass_protected=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='config.yaml', help='Config yaml file.')
    args = parser.parse_args()
    run_bot(args.config)
