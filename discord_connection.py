import discord
import pymongo
from config import Config
import globals
from markov import Markov
import api
import time
import random
from utils import escape_discord
from commands import *
import reactions


class DiscordConnection(discord.Client):
    ENABLED_COMMANDS = [HintCommand, AntiHintCommand, ThreadCommand, RrCommand, HelpCommand, ConvertCommand,
                        WeatherCommand, ColourCommand, SolverCommand, ImagineCommand, GuessingGameCommand,
                        FontCommand, RvCommand, TranslateCommand, UnderageCommand,
                        HighlightCommand, EvalCommand, PurgeCommand, CovidCommand, CurrencyCommand, MagiceyeCommand,
                        ExifCommand, RollCommand, ConfigCommand]

    def __init__(self, config_file):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        globals.bot = self
        self.conf = Config(config_file)
        self._db_client = pymongo.MongoClient(self.conf.get(self.conf.keys.DB_URL))
        self.db = self._db_client[self.conf.get(self.conf.keys.INSTANCE)]
        self.conf.load_db()
        globals.conf = self.conf
        self.markov = Markov()
        self.api_server = api.ApiServer()
        self.name_check = None
        self.commands = {}
        self.commands_flat = []
        self.reaction_listeners = set()
        self.raw_reaction_listeners = set()
        self.voice_state_listeners = set()
        self.message_listeners = set()
        self.ratelimit = {}
        # self.ENABLED_COMMANDS.sort(key=lambda e: e.name) # todo: idk, should they be sorted?
        blacklist_categories = globals.conf.get(globals.conf.keys.BLACKLIST_CATEGORIES)
        for cmd in self.ENABLED_COMMANDS:
            cmd().register()

    async def on_ready(self):
        listening = self.conf.get(self.conf.keys.LISTENING)
        if listening is not None:
            if listening != '':
                await self.change_presence(
                    activity=discord.Activity(type=discord.ActivityType.listening, name=listening))
            else:
                await self.change_presence(activity=None)
        print('I\'m in.')
        await self.markov.load_model('all')

    async def on_message(self, msg):
        prefix = globals.conf.get(globals.conf.keys.PREFIX)
        if not self.conf.list_contains(self.conf.keys.CHANNELS, msg.channel.id) or msg.author.id == self.user.id:
            return
        # todo: remove when Among Us is over
        if not msg.content.startswith(prefix) and 'sus' in msg.content.split(' ') and len(msg.mentions) == 1:
            if '@everyone' not in msg.content and '@here' not in msg.content:
                await msg.channel.send(self.sus_resp(msg.mentions[0].name))

        try:
            await reactions.on_message(self, msg)
            for message_listener in self.message_listeners:
                await message_listener.on_message(msg)
        except Exception as e:
            await msg.reply(escape_discord(f'{type(e).__name__}: {str(e)}'))
            raise e

        async def check_limit():
            for role in msg.author.roles:
                if role.name.lower() in ['moderator', 'tech support', 'undercover cop', 'admin']:
                    return True
            limit = self.conf.dict_get(self.conf.keys.RATELIMITS, msg.channel.id, 0)
            if limit > 0:
                if msg.channel.id not in self.ratelimit:
                    self.ratelimit[msg.channel.id] = {}
                if msg.author.id not in self.ratelimit[msg.channel.id]:
                    self.ratelimit[msg.channel.id][msg.author.id] = [0] * limit
                t_now = time.time()
                t_hist = self.ratelimit[msg.channel.id][msg.author.id]
                if t_now - t_hist[0] < 60 * 60:
                    dm_channel = await self.get_dm_channel(msg.author)
                    await dm_channel.send(
                        'Ratelimit exceeded! :robot: Please avoid using too many bot commands in the improper channels and use #bots-and-spam instead!')
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
        elif msg.content.startswith(f"{prefix}imitate ") or msg.content.startswith(f'{prefix}regenerate'):
            if not await check_limit():
                return
            cmd = msg.content[len(prefix):].strip()
            await self.markov.on_command(msg, cmd)

        if msg.content.startswith(prefix):
            content = msg.content[len(prefix):].split(' ')
            cmd = content[0]
            args = content[1:]
            command = self.commands.get(cmd)
            if command:
                if command.category.value in globals.conf.get(globals.conf.keys.BLACKLIST_CATEGORIES, []):
                    return
                if command.guilds and self.conf.get(self.conf.keys.GUILD) not in command.guilds:
                    return
                if not await check_limit():
                    return
                if command.arg_range[0] <= len(args) <= command.arg_range[1]:
                    try:
                        if await command.check(args, msg):
                            if await command.execute(args, msg) is False:
                                await msg.channel.send(command.usage_str(prefix))
                        else:
                            await msg.reply(f'Permission check failed.')
                    except Exception as e:
                        await msg.reply(escape_discord(f'{type(e).__name__}: {str(e)}'))
                        raise e
                else:
                    await msg.channel.send(command.usage_str(prefix))

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

    async def on_member_join(self, member):
        print(f'{member.name} joined')
        if member.guild.id == 363692038002180097:  # notpron
            role = discord.utils.get(member.guild.roles, id=364055272991490059)  # adventurer
            print(f'assigning {role.name} role')
            await member.add_roles(role)

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
