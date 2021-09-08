import asyncio
import contextlib
import datetime
import traceback
import discord
import pymongo
import dateutil.parser
import pytimeparse.timeparse

from commands.command import Command, Category
from listeners import ReactionListener, ReadyListener
from bson.objectid import ObjectId
from utils import inline_code
import globals


class RemindmeCommand(Command, ReactionListener, ReadyListener):
    name = 'remindme'
    category = Category.UTILITY
    description = 'set a reminder'
    aliases = ['reminder']
    arg_range = (1, 99)
    arg_desc = '<in|at|list|cancel> time [message...]'
    bg_event = asyncio.Event()

    def __init__(self):
        super(RemindmeCommand, self).__init__()
        coll = globals.bot.db['reminders']
        coll.create_index('uid')
        coll.create_index([('ts', pymongo.ASCENDING)])

    async def execute(self, args, msg):
        coll = globals.bot.db['reminders']
        if len(args) >= 2 and args[0] in ('in', 'at'):
            if args[0] == 'in':
                relative_time = pytimeparse.timeparse.timeparse(args[1])
                if relative_time is None:
                    await msg.reply('Invalid time format.')
                    return True
                ts = datetime.datetime.now() + datetime.timedelta(seconds=relative_time)
            else:
                try:
                    ts = dateutil.parser.parse(args[1])
                except (ValueError, OverflowError) as e:
                    await msg.reply('Invalid time format.')
                    return True
            message = ' '.join(args[2:]) if len(args) > 2 else None
            coll.insert_one({'uid': msg.author.id, 'ts': ts, 'message': message})
            self.bg_event.set()
            await msg.reply(f'Set a reminder for {ts.isoformat()}.')
            return True
        elif args[0] == 'list':
            embed = discord.Embed(colour=globals.bot.conf.get(globals.bot.conf.keys.EMBED_COLOUR))
            text = []
            user_reminders = coll.find({'uid': msg.author.id})
            for user_reminder in user_reminders:
                ts: datetime.datetime
                ts = user_reminder['ts'].astimezone(datetime.timezone.utc).replace(microsecond=0)
                escaped_message = inline_code(user_reminder['message']) if user_reminder['message'] else 'None'
                text.append(f'{inline_code(ts.isoformat())} {escaped_message} ({user_reminder["_id"]})')
            if len(text) == 0:
                text.append('None')
            embed.add_field(name='Reminders', value='\n'.join(text), inline=False)
            await msg.reply(embed=embed)
            return True
        elif len(args) == 2 and args[0] in ('cancel', 'remove', 'delete'):
            delete_result = coll.delete_one({'_id': ObjectId(args[1]), 'uid': msg.author.id})
            if delete_result.deleted_count == 1:
                await msg.reply(f'Removed reminder {args[1]}.')
            else:
                await msg.reply(f'Cannot find reminder {args[1]}.')
            return True
        return False

    async def background_task(self):
        coll = globals.bot.db['reminders']
        while True:
            self.bg_event.clear()
            next_event = coll.find().sort('ts', pymongo.ASCENDING).limit(1)
            now = datetime.datetime.now()
            event = next(next_event, None)
            if event:
                ts = event['ts']
                if ts <= now:
                    try:
                        user = globals.bot.get_user(event['uid']) or await globals.bot.fetch_user(event['uid'])
                        ch = await globals.bot.get_dm_channel(user)
                        embed = discord.Embed(colour=globals.bot.conf.get(globals.bot.conf.keys.EMBED_COLOUR))
                        embed.title = 'Reminder'
                        embed.description = event.get('message')
                        await ch.send(embed=embed)
                    except Exception as e:
                        traceback.print_exc()
                    coll.delete_one({'_id': event['_id']})
                else:
                    seconds_left = (ts - now).total_seconds()
                    with contextlib.suppress(asyncio.TimeoutError):
                        await asyncio.wait_for(self.bg_event.wait(), timeout=seconds_left)
            else:
                await self.bg_event.wait()

    async def on_ready(self):
        globals.bot.loop.create_task(self.background_task())

    async def on_reaction_add(self, reaction, user):
        pass

    async def on_reaction_remove(self, reaction, user):
        pass
