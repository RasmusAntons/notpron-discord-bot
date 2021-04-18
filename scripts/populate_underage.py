import json
import globals
import time


def populate_underage():
    with open('blocked_users.json') as f:
        underage = json.load(f)
    new_values = [{'uid': k, 'until': v} for k, v in underage.items()]
    new_values = filter(lambda e: e['until'] > time.time(), new_values)
    coll = globals.bot.db['underage']
    coll.insert_many(new_values)
