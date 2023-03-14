import io
import sys
import time
import traceback

from discord.ext import commands
import pymongo

import api
from cogs import *
from config import Config
from listeners import *
from mongodb_markov import MongodbMarkov
from utils import *


class DiscordConnection(commands.Bot):
    ENABLED_COGS = [ColourCog, ConfigCog, NotpronCog, ArchiveCog, PurgeCog, ConvertCog, CovidCog, EightballCog, EvalCog,
                    ExifCog, FontCog, HighlightCog, ImagineCog, MagiceyeCog, MarkovCog, EnigmaticsCog, RemindmeCog,
                    RenameCog, RolesCog, RollCog, RrCog, RvCog, TranslateCog, WeatherCog, WhosaiditCog, WordgameCog,
                    WordnikCog, OpenAICog]

    ENABLED_LISTENERS = [ArchiveListener, AmongUsListener, BotReactionListener, DmRelayListener]

    def __init__(self, config_file):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True
        super().__init__(intents=intents, command_prefix='!')
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
        self.markov_office = MongodbMarkov(db_client=self._db_client, db_name='office_markov')
        self.api_server = api.ApiServer()
        # self.commands = {}
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

    async def setup_hook(self):
        self.loop.create_task(self.api_server.coro)
        for cog in self.ENABLED_COGS:
            cog_instance = cog()
            await self.add_cog(cog_instance, guilds=[discord.Object(id=416666891055005706)])
            if hasattr(cog_instance, 'app_commands'):
                for app_command in cog_instance.app_commands:
                    self.tree.add_command(app_command)
        # self.tree.copy_global_to(guild=discord.Object(id=416666891055005706))
        # await self.tree.sync(guild=discord.Object(id=416666891055005706))
        await self.tree.sync()
        self.add_check(self.check, call_once=True)
        # print(self.get_cog('ColourCommand').get_commands())

    async def on_ready(self):
        if not self.initialised:
            self.initialised = True
            print('I\'m in.')
            for ready_listener in self.ready_listeners:
                await ready_listener.on_ready()
        else:
            print('Reconnected.')

    async def report_error(self, exc=None, method='unknown', args=None):
        if exc is not None:
            if sys.version_info >= (3, 10):
                tb = ''.join(traceback.format_exception(exc))
            else:
                tb = ''.join(traceback.format_exception(type(exc), exc, exc.__traceback__))
        else:
            tb = traceback.format_exc()
        control_channel_id = globals.conf.get(globals.conf.keys.CONTROL_CHANNEL)
        print(tb, file=sys.stderr)
        if control_channel_id:
            ch = await get_channel(control_channel_id)
            text = '\n'.join([
                f'Error in `{method}` {inline_code(str(args))}:',
                to_code_block(tb, lang='py'),
            ])
            if len(text) < 2000:
                self.loop.create_task(ch.send(text))
            else:
                file = discord.File(io.StringIO(text), filename=f'error_details.txt')
                self.loop.create_task(ch.send(f'Error in `{method}`', file=file))

    async def on_error(self, event_method, *args, **kwargs):
        await self.report_error(method=event_method, args=args)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.context.Context, error):
        if ctx.cog and ctx.cog.has_error_handler():
            return
        if isinstance(error, (commands.CommandNotFound, commands.errors.CheckFailure)):
            return
        while hasattr(error, 'original') and getattr(error, 'original'):
            error = getattr(error, 'original')
        try:
            msg = str(error) or error.__class__.__name__
            await ctx.reply(msg)
        except discord.NotFound:
            pass
        await self.report_error(exc=error, method=f'{ctx.cog.__class__.__name__}:{ctx.command}', args=ctx.args[2:])

    async def check_ratelimit(self, ctx: commands.Context):
        if ctx.channel.permissions_for(ctx.author).manage_messages:
            return True
        limit = self.conf.dict_get(self.conf.keys.RATELIMITS, ctx.channel.id, 0)
        if limit > 0:
            if ctx.channel.id not in self.ratelimit:
                self.ratelimit[ctx.channel.id] = {}
            if ctx.author.id not in self.ratelimit[ctx.channel.id]:
                self.ratelimit[ctx.channel.id][ctx.author.id] = [0] * limit
            t_now = time.time()
            t_hist = self.ratelimit[ctx.channel.id][ctx.author.id]
            if t_now - t_hist[0] < 60 * 60:
                return False
            else:
                self.ratelimit[ctx.channel.id][ctx.author.id] = t_hist[1:] + [t_now]
                return True
        else:
            return True

    async def check(self, ctx: commands.Context):
        if not self.conf.list_contains(self.conf.keys.CHANNELS, ctx.channel.id):
            if ctx.interaction is not None:
                await ctx.reply('commands are not enabled in this channel', ephemeral=True)
            return False
        if ctx.command.qualified_name != 'help' and not await self.check_ratelimit(ctx):
            msg = 'Ratelimit exceeded! :robot: Please avoid using too many bot commands in the improper ' \
                  'channels and use #bots-and-spam instead!'
            if ctx.interaction is not None:
                await ctx.reply(msg, ephemeral=True)
            else:
                dm_channel = await self.get_dm_channel(ctx.author)
                await dm_channel.send(msg)
                for emoji in ['👉', '#️⃣', '🤖']:
                    await ctx.message.add_reaction(emoji)
            return False
        return True

    async def get_dm_channel(self, user):
        return user.dm_channel or await user.create_dm()

    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        cached_message = discord.utils.get(self.cached_messages, id=payload.message_id)
        if cached_message is None:
            ch = await get_channel(payload.channel_id)
            message = await ch.fetch_message(payload.message_id)
            reaction = None
            for other in message.reactions:
                if (type(other.emoji) == str and other.emoji == payload.emoji.name) or (
                        isinstance(other.emoji, discord.Emoji) and other.emoji.id == payload.emoji.id):
                    reaction = other
                    break
            user = ch.guild.get_member(payload.user_id) or await ch.guild.fetch_member(payload.user_id)
            for cog in self.cogs.values():
                cog_listeners = dict(cog.get_listeners())
                if 'on_reaction_add' in cog_listeners:
                    await cog_listeners['on_reaction_add'](reaction, user)

    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        cached_message = discord.utils.get(self.cached_messages, id=payload.message_id)
        if cached_message is None:
            ch = await get_channel(payload.channel_id)
            message = await ch.fetch_message(payload.message_id)
            reaction = None
            for other in message.reactions:
                if (type(other.emoji) == str and other.emoji == payload.emoji.name) or (
                        isinstance(other.emoji, discord.Emoji) and other.emoji.id == payload.emoji.id):
                    reaction = other
                    break
            if reaction is None:
                data = {'count': 0, 'me': False, 'emoji': payload.emoji}
                emoji = payload.emoji.name if payload.emoji.id is None else payload.emoji
                reaction = discord.Reaction(message=message, data=data, emoji=emoji)
            user = ch.guild.get_member(payload.user_id) or await ch.guild.fetch_member(payload.user_id)
            for cog in self.cogs.values():
                cog_listeners = dict(cog.get_listeners())
                if 'on_reaction_remove' in cog_listeners:
                    await cog_listeners['on_reaction_remove'](reaction, user)

    async def on_raw_message_edit(self, payload: discord.RawMessageUpdateEvent) -> None:
        if payload.cached_message is None:
            ch = await get_channel(payload.channel_id)
            before = discord.PartialMessage(channel=ch, id=payload.message_id)
            after = await ch.fetch_message(payload.message_id)
            for cog in self.cogs.values():
                cog_listeners = dict(cog.get_listeners())
                if 'on_message_edit' in cog_listeners:
                    await cog_listeners['on_message_edit'](before, after)

    async def on_raw_message_delete(self, payload: discord.RawMessageDeleteEvent) -> None:
        if payload.cached_message is None:
            ch = await get_channel(payload.channel_id)
            message = discord.PartialMessage(channel=ch, id=payload.message_id)
            for cog in self.cogs.values():
                cog_listeners = dict(cog.get_listeners())
                if 'on_message_delete' in cog_listeners:
                    await cog_listeners['on_message_delete'](message)

    async def on_raw_bulk_message_delete(self, payload):
        ch = await get_channel(payload.channel_id)
        messages = dict.fromkeys(payload.message_ids, None)
        for cached_message in payload.cached_messages:
            messages[cached_message.id] = cached_message
        for message_id in messages.keys():
            if messages[message_id] is None:
                messages[message_id] = discord.PartialMessage(channel=ch, id=message_id)
        for cog in self.cogs.values():
            cog_listeners = dict(cog.get_listeners())
            if 'on_message_delete' in cog_listeners:
                for message in messages.values():
                    await cog_listeners['on_message_delete'](message)
