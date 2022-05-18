import io
import sys
import traceback
import pymongo
from config import Config
from mongodb_markov import MongodbMarkov
import api
import time
from utils import *
from commands import *
from listeners import *


class DiscordConnection(discord.Client):
    ENABLED_COMMANDS = [HintCommand, AntiHintCommand, ThreadCommand, RrCommand, HelpCommand, ConvertCommand,
                        WeatherCommand, ColourCommand, SolverCommand, ImagineCommand, GuessingGameCommand,
                        FontCommand, RvCommand, TranslateCommand, UnderageCommand,
                        HighlightCommand, EvalCommand, PurgeCommand, CovidCommand, CurrencyCommand, MagiceyeCommand,
                        ExifCommand, RollCommand, ConfigCommand, ArchiveCommand, MarkovAddChannelCommand,
                        ImitateCommand, RemindmeCommand, WhoSaidItCommand, WordnikCommand, ProfileCommand]

    ENABLED_LISTENERS = [ArchiveListener, AmongUsListener, DefaultRoleListener, BotReactionListener, DmRelayListener,
                         MarkovListener]

    def __init__(self, config_file):
        intents = discord.Intents.default()
        intents.members = True
        super().__init__(intents=intents)
        globals.bot = self
        self.conf = Config(config_file)
        self._db_client = pymongo.MongoClient(
            self.conf.get(self.conf.keys.DB_URL),
            unicode_decode_error_handler='ignore'
        )
        self.db = self._db_client[self.conf.get(self.conf.keys.INSTANCE)]
        self.conf.load_db()
        globals.conf = self.conf
        self.markov = MongodbMarkov(db_client=self._db_client, db_name=self.db.name)
        self.api_server = api.ApiServer()
        self.commands = {}
        self.commands_flat = []
        self.message_listeners = set()
        self.reaction_listeners = set()
        self.raw_reaction_listeners = set()
        self.message_edit_listeners = set()
        self.message_delete_listeners = set()
        self.voice_state_listeners = set()
        self.ready_listeners = set()
        self.member_join_listeners = set()
        self.ratelimit = {}
        self.initialised = False
        self.ENABLED_COMMANDS.sort(key=lambda e: e.name)
        for entity in self.ENABLED_COMMANDS + self.ENABLED_LISTENERS:
            entity()

    async def on_ready(self):
        if not self.initialised:
            self.initialised = True
            print('I\'m in.')
            for ready_listener in self.ready_listeners:
                await ready_listener.on_ready()
        else:
            print('Reconnected.')

    async def on_error(self, event_method, *args, **kwargs):
        control_channel_id = globals.conf.get(globals.conf.keys.CONTROL_CHANNEL)
        exception_txt = traceback.format_exc()
        print(exception_txt, file=sys.stderr)
        if control_channel_id:
            ch = await get_channel(control_channel_id)
            text = '\n'.join([
                f'Error in `{event_method}`',
                to_code_block(exception_txt),
                to_code_block(str(args))
            ])
            if len(text) < 2000:
                self.loop.create_task(ch.send(text))
            else:
                file = discord.File(io.StringIO(text), filename=f'error_details.txt')
                self.loop.create_task(ch.send(f'Error in `{event_method}`', file=file))

    async def on_message(self, msg):
        for message_listener in self.message_listeners:
            await message_listener.on_message(msg)
        prefix = globals.conf.get(globals.conf.keys.PREFIX)

        if not self.conf.list_contains(self.conf.keys.CHANNELS, msg.channel.id) or msg.author.id == self.user.id:
            return

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
                        traceback.print_exc()
                else:
                    await msg.channel.send(command.usage_str(prefix))

    async def get_dm_channel(self, user):
        return user.dm_channel or await user.create_dm()

    async def on_reaction_add(self, reaction, user):
        if user.id == self.user.id:
            return
        for reaction_listener in self.reaction_listeners:
            await reaction_listener.on_reaction_add(reaction, user)

    async def on_reaction_remove(self, reaction, user):
        if user.id == self.user.id:
            return
        for reaction_listener in self.reaction_listeners:
            await reaction_listener.on_reaction_remove(reaction, user)

    async def on_raw_reaction_add(self, payload):
        ch = await get_channel(payload.channel_id)
        member = await get_member(payload.user_id)
        for raw_reaction_listener in self.raw_reaction_listeners:
            await raw_reaction_listener.on_raw_reaction_add(ch, member, payload)

    async def on_raw_reaction_remove(self, payload):
        ch = await get_channel(payload.channel_id)
        member = await get_member(payload.user_id)
        for raw_reaction_listener in self.raw_reaction_listeners:
            await raw_reaction_listener.on_raw_reaction_remove(ch, member, payload)

    async def on_member_join(self, member):
        for member_join_listener in self.member_join_listeners:
            await member_join_listener.on_member_join(member)

    async def on_raw_message_edit(self, payload):
        ch = await get_channel(payload.channel_id)
        ch: discord.TextChannel
        message = await ch.fetch_message(payload.message_id)
        for message_edit_listener in self.message_edit_listeners:
            message_edit_listener: MessageEditListener
            await message_edit_listener.on_message_edit(message, payload.cached_message)

    async def on_raw_message_delete(self, payload):
        ch = await get_channel(payload.channel_id)
        guild = await get_guild(payload.guild_id) if payload.guild_id else None
        for message_delete_listener in self.message_delete_listeners:
            await message_delete_listener.on_message_delete(payload.message_id, ch, guild, payload.cached_message)

    async def on_raw_bulk_message_delete(self, payload):
        ch = await get_channel(payload.channel_id)
        guild = await get_guild(payload.guild_id) if payload.guild_id else None
        messages = dict.fromkeys(payload.message_ids, None)
        for cached_message in payload.cached_messages:
            messages[cached_message.id] = cached_message
        for message_id, cached_message in messages.items():
            for message_delete_listener in self.message_delete_listeners:
                await message_delete_listener.on_message_delete(message_id, ch, guild, cached_message)

    async def on_voice_state_update(self, member, before, after):
        for vc_listener in self.voice_state_listeners:
            await vc_listener.on_voice_state_update(member, before, after)
