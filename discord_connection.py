import discord
import asyncio
from markov import Markov
import api
import time
import datetime
import random
from discord.utils import escape_markdown, escape_mentions
from commands.hint import HintCommand
from commands.antihint import AntiHintCommand
from commands.thread import ThreadCommand
from commands.rr import RrCommand
from commands.help import HelpCommand
from commands.convert import ConvertCommand
from commands.weather import WeatherCommand
from commands.colour import ColourCommand
from commands.solver import SolverCommand
from commands.imagine import ImagineCommand
from commands.guessing_game import GuessingGameCommand
from commands.tts import TtsCommand, NpCommand
from commands.font import FontCommand
from commands.rv import RvCommand
from commands.hw import HwCommand
from commands.translate import TranslateCommand
from commands.roles import UnderageCommand
from commands.highlight import HighlightCommand
from commands.eval import EvalCommand
from commands.purge import PurgeCommand
import reactions


class DiscordConnection(discord.Client):
    ENABLED_COMMANDS = [HintCommand, AntiHintCommand, ThreadCommand, RrCommand, HelpCommand, ConvertCommand,
                        WeatherCommand, ColourCommand, SolverCommand, ImagineCommand, GuessingGameCommand, TtsCommand,
                        FontCommand, RvCommand, HwCommand, NpCommand, TranslateCommand, UnderageCommand,
                        HighlightCommand, EvalCommand, PurgeCommand]

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.markov = Markov(self, config)
        self.api_server = api.ApiServer(self, config)
        self.name_check = None
        self.prefix = self.config.get_prefix()
        self.commands = {}
        self.commands_flat = []
        self.reaction_listeners = set()
        self.raw_reaction_listeners = set()
        self.voice_state_listeners = set()
        self.message_listeners = set()
        self.ratelimit = {}
        # self.ENABLED_COMMANDS.sort(key=lambda e: e.name) # todo: idk, should they be sorted?
        for cmd in self.ENABLED_COMMANDS:
            cmd(self).register()

    async def on_ready(self):
        listening = self.config.get_listening()
        if listening:
            await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name=listening))
        print('I\'m in.')
        await self.markov.load_model('all')
        self.loop.create_task(self.background_task())

    async def background_task(self):
        while True:
            ts = datetime.datetime.utcnow()
            if self.name_check is None or ts.hour != self.name_check.hour:
                for id, names in self.config.get_names().items():
                    new_name = names.get(str(ts.hour))
                    if new_name:
                        try:
                            guild = self.get_guild(self.config.get_guild())
                            member = await guild.fetch_member(int(id))
                            await member.edit(nick=new_name)
                        except discord.HTTPException as e:
                            pass
            self.name_check = ts
            await asyncio.sleep(10)

    async def on_message(self, msg):
        if msg.channel.id not in self.config.get_channels() or msg.author.id == self.user.id:
            return
        # todo: remove when Among Us is over
        if not msg.content.startswith('!') and 'sus' in msg.content.split(' ') and len(msg.mentions) == 1:
            if '@everyone' not in msg.content and '@here' not in msg.content and msg.channel.guild.id == 363692038002180097:
                await msg.channel.send(self.sus_resp(msg.mentions[0].name))

        try:
            await reactions.on_message(self, msg)
            for message_listener in self.message_listeners:
                await message_listener.on_message(msg)
        except Exception as e:
            await msg.channel.send(escape_markdown(escape_mentions(str(e))))
            raise e

        async def check_limit():
            for role in msg.author.roles:
                if role.name.lower() in ['moderator', 'tech support', 'undercover cop', 'admin']:
                    return True
            limit = self.config.get_ratelimit(msg.channel.id)
            if limit > 0:
                if msg.channel.id not in self.ratelimit:
                    self.ratelimit[msg.channel.id] = {}
                if msg.author.id not in self.ratelimit[msg.channel.id]:
                    self.ratelimit[msg.channel.id][msg.author.id] = [0] * limit
                t_now = time.time()
                t_hist = self.ratelimit[msg.channel.id][msg.author.id]
                if t_now - t_hist[0] < 60 * 60:
                    dm_channel = await self.get_dm_channel(msg.author)
                    await dm_channel.send('Ratelimit exceeded! :robot: Please avoid using too many bot commands in the improper channels and use #bots-and-spam instead!')
                    for emoji in ['👉', '#️⃣', '🤖']:
                        await msg.add_reaction(emoji)
                    return False
                else:
                    self.ratelimit[msg.channel.id][msg.author.id] = t_hist[1:] + [t_now]
                    return True
            else:
                return True
        if self.user.mentioned_in(msg):
            if '@everyone' not in msg.content and '@here' not in msg.content:
                if not await check_limit():
                    return
                await self.markov.talk(msg.channel, query=msg.content)
        elif msg.content.startswith("!imitate ") or msg.content.startswith('!regenerate'):
            if not await check_limit():
                return
            cmd = msg.content[1:].strip()
            await self.markov.on_command(msg, cmd)

        if msg.content.startswith(self.prefix):
            content = msg.content[len(self.prefix):].split(' ')
            cmd = content[0]
            args = content[1:]
            command = self.commands.get(cmd)
            if command:
                if not await check_limit():
                    return
                if command.arg_range[0] <= len(args) <= command.arg_range[1]:
                    try:
                        if await command.check(args, msg):
                            await command.execute(args, msg)
                        else:
                            await msg.channel.send(f'{msg.author.mention} please don\'t do that')
                    except Exception as e:
                        await msg.channel.send(escape_markdown(escape_mentions(str(e))))
                        raise e
                else:
                    usage = f'Usage: `{self.prefix}{command.name}'
                    if command.arg_desc:
                        usage += f' {command.arg_desc}'
                    usage += '`'
                    await msg.channel.send(usage)

    async def get_dm_channel(self, user):
        # todo: check if user has dms disabled
        dm_channel = user.dm_channel
        if dm_channel is None:
            dm_channel = await user.create_dm()
        if dm_channel is None:
            raise RuntimeError('Failed to create dm channel')
        return dm_channel

    async def on_reaction_add(self, reaction, user):
        if user.id == self.user.id:
            return
        for reaction_listener in self.reaction_listeners:
            if reaction_listener.on_reaction_add:
                await reaction_listener.on_reaction_add(reaction, user)

    async def on_reaction_remove(self, reaction, user):
        if user.id == self.user.id:
            return
        for reaction_listener in self.reaction_listeners:
            if reaction_listener.on_reaction_remove:
                await reaction_listener.on_reaction_remove(reaction, user)

    async def on_raw_reaction_add(self, payload):
        ch = self.get_channel(payload.channel_id)
        user = ch.guild.get_member(payload.user_id) or await ch.guild.fetch_member(payload.user_id)
        for raw_reaction_listener in self.raw_reaction_listeners:
            if raw_reaction_listener.on_raw_reaction_add:
                await raw_reaction_listener.on_raw_reaction_add(ch, user, payload)

    async def on_raw_reaction_remove(self, payload):
        ch = self.get_channel(payload.channel_id)
        user = ch.guild.get_member(payload.user_id) or await ch.guild.fetch_member(payload.user_id)
        for raw_reaction_listener in self.raw_reaction_listeners:
            if raw_reaction_listener.on_raw_reaction_remove:
                await raw_reaction_listener.on_raw_reaction_remove(ch, user, payload)

    def sus_resp(self, userName):
        fChoice = random.randint(1, 2)
        sChoice = random.randint(0, 1)
        n = max(1, (len(userName) - 8) // 2)
        choice = [f"""
    . 　　　。　　　　•　 　ﾟ　　。 　　.

    　　　.　　　 　　.　　　　　。　　 。　. 　

    .　　 。　　　　　 ඞ 。 . 　　 • 　　　　•

{"    　　ﾟ　　  "[:-n]}{userName} was not {"An" if fChoice == 2 else "The"} Impostor.{"　 。　."[:-n]}

    　　'　　　 {fChoice} Impostor{"s" if fChoice == 2 else ""} remain{"s" if fChoice != 2 else ""} 　 　　。

    　　ﾟ　　　.　　　. ,　　　　.　 .
    """,
                  f"""
    . 　　　。　　　　•　 　ﾟ　　。 　　.

    　　　.　　　 　　.　　　　　。　　 。　. 　

    .　　 。　　　　　 ඞ 。 . 　　 • 　　　　•

{"    　　ﾟ　　  "[:-n]}{userName} was {"An" if sChoice == 1 else "The"} Impostor.{"　 。　."[:-n]}

    　　'　　　 {sChoice} Impostor remains 　 　　。

    　　ﾟ　　　.　　　. ,　　　　.　 .
    """]
        return random.choice(choice)

    async def on_voice_state_update(self, member, before, after):
        for vc_listener in self.voice_state_listeners:
            await vc_listener.on_voice_state_update(member, before, after)
