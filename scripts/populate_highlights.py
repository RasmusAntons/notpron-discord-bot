import json

import pymongo

import globals


def populate_highlights():
    with open('highlights.json', 'r') as f:
        highlights = json.load(f)

    coll = globals.bot.db['highlights']
    new_highlights = []
    for uid, patterns in highlights.items():
        for pattern in patterns:
            new_highlights.append({'uid': int(uid), 'pattern': pattern})
    coll.insert_many(new_highlights)
    coll.delete_many({'$where': f'try {{new RegExp(this.pattern)}} catch(e) {{return true}} return false'})
