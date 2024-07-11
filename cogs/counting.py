import time

import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks

import globals
import logging

class CountingCog(commands.Cog):
    def __init__(self):
        self.coll = globals.bot.db['counting']
        self.coll.create_index('chid')
        self.coll_highscores = globals.bot.db['counting_highscores']
        self.coll_silenced = globals.bot.db['counting_silenced']

    @commands.Cog.listener()
    async def on_ready(self):
        self.unsilence.start()

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.interaction:
            return
        state = self.coll.find_one({'chid': msg.channel.id})
        valid = False
        progress = 0
        highscore = None
        if state is not None:
            progress = state.get('progress')
            highscore = self.coll_highscores.find_one({})
            content = msg.content
            try:
                valid = progress is not None and content.isnumeric() and int(content) == progress + 1 and state.get('last_uid') != msg.author.id
            except ValueError:
                valid = False
        elif msg.content.isnumeric() and int(msg.content) == 1:
            valid = True
        if valid:
            started_by = state.get('started_by', msg.author.id) if state is not None else msg.author.id
            self.coll.replace_one({'chid': msg.channel.id}, {'chid': msg.channel.id, 'last_uid': msg.author.id, 'progress': progress + 1, 'started_by': started_by}, upsert=True)
            await msg.add_reaction('✅')
        elif state is not None:
            self.coll.delete_one({'chid': msg.channel.id})
            started_by = state.get('started_by', msg.author.id) if state is not None else msg.author.id
            self.coll_highscores.replace_one({}, {'message': msg.jump_url, 'uid': msg.author.id, 'score': progress + 1, 'started_by': started_by, 'broken_by': msg.author.id}, upsert=True)
            await msg.add_reaction('❌')
            if progress >= 3:
                if msg.author.id == globals.bot.user.id:
                    await msg.reply('# aw fuck')
                else:
                    reply_msg = f'# <:angrymeepers2:1255963929184567306> {progress} streak broken by {msg.author.mention}'
                    counting_channel = globals.conf.get(globals.conf.keys.COUNTING_CHANNEL)
                    if counting_channel is not None and counting_channel == msg.channel.id:
                        silenced_role_id = globals.conf.get(globals.conf.keys.SILENCED_ROLE)
                        if silenced_role_id is not None:
                            silenced_role = msg.author.guild.get_role(silenced_role_id)
                            if silenced_role is not None:
                                reply_msg += f' who has been silenced for {progress * 10} minutes'
                                await msg.author.add_roles(silenced_role)
                                self.coll_silenced.insert_one({'uid': msg.author.id, 'ts': int(time.time()) + progress * 10 * 60, 'gid': msg.author.guild.id})
                            else:
                                logging.error('silenced_role is None')
                        else:
                            logging.error('silenced_role_id is None')
                    if highscore is not None:
                        previous_score = highscore.get('score')
                        previous_started_uid = highscore.get('started_by')
                        previous_broken_uid = highscore.get('broken_by')
                        previous = 'previous ' if progress > previous_score else ''
                        reply_msg += f'\n{previous}record: {previous_score} (started by <@{previous_started_uid}>, broken by <@{previous_broken_uid}>)'
                    await msg.reply(reply_msg)

    @tasks.loop(seconds=60)
    async def unsilence(self):
        while (silenced := self.coll_silenced.find_one_and_delete({'ts': {'$lte': time.time()}})) is not None:
            logging.error(f'unsilencing <@{silenced.get("uid")}>')
            guild = globals.bot.get_guild(silenced.get('gid'))
            if guild is None:
                logging.error('guild is None')
                continue
            member = await guild.fetch_member(silenced.get('uid'))
            if member is None:
                logging.error('member is None')
                continue
            silenced_role_id = globals.conf.get(globals.conf.keys.SILENCED_ROLE)
            if silenced_role_id is None:
                logging.error('silenced_role_id is None')
                continue
            silenced_role = member.guild.get_role(silenced_role_id)
            if silenced_role is None:
                logging.error('silenced_role is None')
                continue
            await member.remove_roles(silenced_role)
