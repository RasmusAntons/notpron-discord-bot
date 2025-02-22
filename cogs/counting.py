import time
import traceback

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
        self.coll_messages = globals.bot.db['counting_messages']
        self.coll_messages.create_index('mid')
        self.coll_highscores = globals.bot.db['counting_highscores']
        self.coll_silenced = globals.bot.db['counting_silenced']
        self.coll_punishment = globals.bot.db['counting_punishment']
        self.coll_punishment.create_index('uid')

    @commands.Cog.listener()
    async def on_ready(self):
        self.unsilence.start()

    @app_commands.command(name='silenced', description='list silenced users')
    async def silenced(self, interaction: discord.Interaction):
        lines = []
        for silenced in self.coll_silenced.find({}):
            ts = silenced.get('ts')
            member = await interaction.guild.fetch_member(silenced.get('uid'))
            if member is None:
                continue
            lines.append(f'{member.mention} will be unsilenced <t:{int(ts)}:R>')
        msg = f'silenced users:\n{"\n".join(lines)}' if lines else 'no silenced users'
        await interaction.response.send_message(msg)

    def _is_counting_channel(self, channel):
        counting_channel = globals.conf.get(globals.conf.keys.COUNTING_CHANNEL)
        return counting_channel is not None and counting_channel == channel.id

    def _get_punishment(self, uid):
        entry = self.coll_punishment.find_one({'uid': uid})
        return entry.get('factor') if entry is not None else 1

    def _update_punishment(self, uid, failure):
        current_factor = self._get_punishment(uid)
        new_factor = current_factor * 2 if failure else max(1, current_factor - 1)
        self.coll_punishment.replace_one({'uid': uid}, {'factor': new_factor}, upsert=True)

    async def _on_failure(self, state, member, channel, progress, msg=None, deleted=None):
        highscore = self.coll_highscores.find_one({})
        self.coll.delete_one({'chid': channel.id})
        self.coll_messages.delete_many({})
        started_by = state.get('started_by', member.id) if state is not None else member.id
        if highscore is None or highscore.get('score') < progress:
            self.coll_highscores.replace_one({}, {'uid': member.id, 'score': progress,
                                                  'started_by': started_by, 'broken_by': member.id}, upsert=True)
        if msg is not None:
            await msg.add_reaction('❌')
        if deleted is not None:
            await channel.send(f'-# {member.mention} deleted their number {deleted}')
        if progress >= 3:
            if member.id == globals.bot.user.id:
                if msg is not None:
                    await msg.reply('# aw fuck')
                else:
                    await channel.send('# aw fuck')
            else:
                reply_msg = f'# <:angrymeepers2:1255963929184567306> {progress} streak broken by {member.mention}'
                if self._is_counting_channel(channel):
                    silenced_role_id = globals.conf.get(globals.conf.keys.SILENCED_ROLE)
                    if silenced_role_id is not None:
                        silenced_role = member.guild.get_role(silenced_role_id)
                        if silenced_role is not None:
                            punishment_factor = self._get_punishment(member.id)
                            silence_duration = (3/2) * (progress * punishment_factor) ** (2/3)
                            reply_msg += f' who has been silenced for {silence_duration:.2f} hours'
                            await member.add_roles(silenced_role)
                            self.coll_silenced.insert_one(
                                {'uid': member.id, 'ts': int(time.time()) + silence_duration * 60 * 60,
                                 'gid': member.guild.id})
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
                if msg is not None:
                    await msg.reply(reply_msg, allowed_mentions=discord.AllowedMentions.none())
                else:
                    await channel.send(reply_msg, allowed_mentions=discord.AllowedMentions.none())
                self._update_punishment(member.id, True)

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.interaction or isinstance(msg.channel, discord.channel.DMChannel):
            return
        state = self.coll.find_one({'chid': msg.channel.id})
        valid = False
        progress = 0
        if state is not None:
            progress = state.get('progress')
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
            self.coll_messages.insert_one({'mid': msg.id, 'gid': msg.guild.id, 'chid': msg.channel.id, 'uid': msg.author.id, 'progress': progress + 1})
            await msg.add_reaction('✅')
            self._update_punishment(msg.author.id, False)
        elif state is not None and (msg.author.id == globals.bot.user.id or msg.is_system()) and self._is_counting_channel(msg.channel):
            await msg.add_reaction('🤷')
        elif state is not None:
            await self._on_failure(state=state, member=msg.author, channel=msg.channel, progress=progress, msg=msg)

    @commands.Cog.listener()
    async def on_message_delete(self, message: discord.Message | discord.PartialMessage) -> None:
        current_msg_info = self.coll_messages.find_one({'mid': message.id})
        if current_msg_info is None:
            return
        state = self.coll.find_one({'chid': current_msg_info.get('chid')})
        if state is None:
            return
        guild = globals.bot.get_guild(current_msg_info.get('gid'))
        channel = await guild.fetch_channel(current_msg_info.get('chid'))
        member = await guild.fetch_member(current_msg_info.get('uid'))
        await self._on_failure(member=member, channel=channel, state=state, progress=state.get('progress'), deleted=current_msg_info.get('progress'))

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self.coll_silenced.find_one({'uid': member.id}) is not None:
            silenced_role_id = globals.conf.get(globals.conf.keys.SILENCED_ROLE)
            if silenced_role_id is None:
                return
            silenced_role = member.guild.get_role(silenced_role_id)
            if silenced_role is None:
                return
            await member.add_roles(silenced_role, reason=f'{member.name} is still silenced')

    @tasks.loop(seconds=60)
    async def unsilence(self):
        while (silenced := self.coll_silenced.find_one_and_delete({'ts': {'$lte': time.time()}})) is not None:
            try:
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
            except Exception:
                traceback.print_exc()
