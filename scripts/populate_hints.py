import json
import globals


def populate_hints():
    with open('scripts/hints.json', 'r') as f:
        hints = json.load(f)

    for coll_name in ('hints', 'antihints', 'threads'):
        coll = globals.bot.db[coll_name]
        for level, value in hints[coll_name].items():
            coll.insert_one({'level': level, 'value': value})
            print(level, value)
