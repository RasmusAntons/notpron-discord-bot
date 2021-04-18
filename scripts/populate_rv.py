import datetime
from sqlitedict import SqliteDict
import globals


def populate_rv():
    coll = globals.bot.db['rv']
    coll_logs = globals.bot.db['rv_logs']
    coll_stats = globals.bot.db['rv_stats']
    with SqliteDict('rv/db.sqlite') as rvdb:
        for key, value in rvdb.items():
            if key == 'log':
                for log_entry in value:
                    log_entry['t_start'] = datetime.datetime.utcfromtimestamp(log_entry['t_start'])
                    log_entry['t_end'] = datetime.datetime.utcfromtimestamp(log_entry['t_end'])
                    coll_logs.insert_one(log_entry)
            elif key == 'stats':
                for uid, stats_entry in value.items():
                    stats_entry['uid'] = int(uid)
                    coll_stats.insert_one(stats_entry)
            else:
                value['uid'] = int(key)
                value['t_start'] = datetime.datetime.utcfromtimestamp(value['t_start'])
                coll.insert_one(value)
