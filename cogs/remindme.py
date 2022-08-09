import asyncio
import contextlib
import datetime
import sys
import traceback

from bson.objectid import ObjectId
import dateutil.parser
import discord
from discord.ext import commands
import pymongo
import pytimeparse.timeparse

import globals
from utils import inline_code


class ReminderModal(discord.ui.Modal, title='Cancel Reminder'):
    def __init__(self, coll, options, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.coll = coll
        self.code.options = options

    code = discord.ui.Select(
        options=[],
        placeholder='select reminder to cancel'
    )

    async def on_submit(self, interaction: discord.Interaction):
        object_id = self.code.values[0]
        delete_result = self.coll.delete_one({'_id': ObjectId(object_id), 'uid': interaction.user.id})
        if delete_result.deleted_count == 1:
            await interaction.response.send_message(f'Cancelled reminder {object_id}.')
        else:
            await interaction.response.send_message(f'Cannot find reminder {object_id}.')


class RemindmeCog(commands.Cog, name='Remindme', description='set a reminder'):
    def __init__(self):
        self.coll = globals.bot.db['reminders']
        self.coll.create_index('uid')
        self.coll.create_index([('ts', pymongo.ASCENDING)])
        self.bg_event = None if sys.version_info < (3, 10, 0) else asyncio.Event()

    @commands.hybrid_group(name='remindme', description='set a reminder')
    async def remindme_grp(self, ctx):
        return None

    async def _remindme(self, ctx: commands.Context, ts: datetime.datetime, text: str):
        self.coll.insert_one({'uid': ctx.author.id, 'ts': ts, 'message': text})
        self.bg_event.set()
        await ctx.reply(f'Set a reminder for <t:{int(ts.timestamp())}>.')

    @remindme_grp.command(name='in', description='set a reminder in a certain time')
    async def remindme_in(self, ctx: commands.Context, relative_time: str, text: str = None) -> None:
        relative_time = pytimeparse.timeparse.timeparse(relative_time)
        if relative_time is None:
            raise RuntimeError('Invalid time format.')
        ts = datetime.datetime.now().replace(microsecond=0) + datetime.timedelta(seconds=relative_time)
        await self._remindme(ctx, ts, text)

    @remindme_grp.command(name='at', description='set a reminder at a certain time')
    async def remindme_at(self, ctx: commands.Context, absolute_time: str, text: str = None) -> None:
        try:
            ts = dateutil.parser.parse(absolute_time)
            ts = ts.replace(tzinfo=ts.tzinfo or datetime.timezone.utc)
        except (ValueError, OverflowError) as e:
            raise RuntimeError('Invalid time format')
        await self._remindme(ctx, ts, text)

    @remindme_grp.command(name='list', description='list reminders')
    async def list(self, ctx: commands.Context) -> None:
        embed = discord.Embed(colour=globals.bot.conf.get(globals.bot.conf.keys.EMBED_COLOUR))
        text = []
        user_reminders = self.coll.find({'uid': ctx.author.id})
        for user_reminder in user_reminders:
            ts: datetime.datetime = user_reminder['ts'].astimezone(datetime.timezone.utc)
            escaped_message = inline_code(user_reminder['message'][:25]) if user_reminder['message'] else 'None'
            text.append(f'<t:{int(ts.timestamp())}> {escaped_message} ({user_reminder["_id"]})')
        if len(text) == 0:
            text.append('None')
        embed.add_field(name='Reminders', value='\n'.join(text), inline=False)
        await ctx.reply(embed=embed)

    @remindme_grp.command(name='cancel', description='cancel a reminder')
    async def cancel(self, ctx: commands.Context, object_id: str = None):
        if object_id is None:
            if ctx.interaction is None:
                raise RuntimeError('uses slash command or specify reminder id')
            options = []
            user_reminders = self.coll.find({'uid': ctx.author.id})
            for user_reminder in user_reminders:
                if len(options) == 25:
                    break
                ts: datetime.datetime = user_reminder['ts'].astimezone(datetime.timezone.utc)
                options.append(discord.SelectOption(label=ts.isoformat(),
                                                    description=user_reminder['message'][:100],
                                                    value=str(user_reminder['_id'])))
            options = options[:25]
            if not options:
                raise RuntimeError('no reminders to cancel')
            await ctx.interaction.response.send_modal(ReminderModal(coll=self.coll, options=options, timeout=None))
            return
        delete_result = self.coll.delete_one({'_id': ObjectId(object_id), 'uid': ctx.author.id})
        if delete_result.deleted_count == 1:
            await ctx.reply(f'Cancelled reminder {object_id}.')
        else:
            await ctx.reply(f'Cannot find reminder {object_id}.')
        return True

    @commands.Cog.listener()
    async def on_ready(self):
        if sys.version_info < (3, 10, 0):
            self.bg_event = asyncio.Event(loop=globals.bot.loop)
        globals.bot.loop.create_task(self.background_task())

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
