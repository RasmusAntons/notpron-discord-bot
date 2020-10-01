import discord
import asyncio
from markov import Markov
import api
import datetime
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
from commands.tts import TtsCommand


class DiscordConnection(discord.Client):
    ENABLED_COMMANDS = [HintCommand, AntiHintCommand, ThreadCommand, RrCommand, HelpCommand, ConvertCommand,
                        WeatherCommand, ColourCommand, SolverCommand, ImagineCommand, GuessingGameCommand, TtsCommand]

    def __init__(self, config):
        super().__init__()
        self.config = config
        self.markov = Markov(self, config)
        self.api_server = api.ApiServer(self, config)
        self.name_check = None
        self.prefix = self.config.get_prefix()
        self.commands = {}
        self.reaction_listeners = set()
        self.voice_state_listeners = set()
        # self.ENABLED_COMMANDS.sort(key=lambda e: e.name) # todo: idk, should they be sorted?
        for cmd in self.ENABLED_COMMANDS:
            cmd(self).register()

    async def on_ready(self):
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.listening, name="!hint | !antihint"))
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
        if self.user.mentioned_in(msg):
            if '@everyone' not in msg.content and '@here' not in msg.content:
                await self.markov.talk(msg.channel)
        elif msg.content.startswith("!imitate ") or msg.content.startswith('!regenerate'):
            cmd = msg.content[1:].strip()
            await self.markov.on_command(msg, cmd)

        if msg.content.startswith(self.prefix):
            content = msg.content[len(self.prefix):].split(' ')
            cmd = content[0]
            args = content[1:]
            command = self.commands.get(cmd)
            if command:
                if command.arg_range[0] <= len(args) <= command.arg_range[1]:
                    try:
                        if await command.check(args, msg):
                            await command.execute(args, msg)
                    except Exception as e:
                        await msg.channel.send(escape_markdown(escape_mentions(str(e))))
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
            dm_channel = await user.author.create_dm()
        if dm_channel is None:
            raise RuntimeError('Failed to create dm channel')
        return dm_channel

    async def on_reaction_add(self, reaction, user):
        if user.id == self.user.id:
            return
        for reaction_listener in self.reaction_listeners:
            await reaction_listener.on_reaction_add(reaction, user)

    async def on_voice_state_update(self, member, before, after):
        for vc_listener in self.voice_state_listeners:
            await vc_listener.on_voice_state_update(member, before, after)
