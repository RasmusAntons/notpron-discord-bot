import logging
import random
import uuid

import discord
from discord import app_commands
from discord.ext import commands
import string
import openai

import globals
import utils
from utils import escape_discord


class GuiserCog(commands.GroupCog, name='guiser', description='social interaction game'):
    def __init__(self):
        coll_guiser = globals.bot.db['guiser']
        coll_guiser.create_index('game_id', unique=False)

    @app_commands.command(name='start')
    async def guiser_start(self, interaction: discord.Interaction, topic: str = None):
        coll_guiser = globals.bot.db['guiser']
        embed = discord.Embed(title='Guiser Game')
        if topic is not None:
            embed.add_field(name='Topic', value=topic, inline=False)
        embed.add_field(name='Players', value=f'<@{interaction.user.id}>', inline=False)
        game_id = uuid.uuid4().hex
        start_menu = StartMenu(game_id=game_id)
        await interaction.response.send_message(embed=embed, view=start_menu)
        coll_guiser.insert_one({'game_id': game_id, 'owner': interaction.user.id})
        coll_guiser.insert_one({'game_id': game_id, 'player': interaction.user.id, 'alive': True})
        message: discord.Message = await interaction.original_response()
        coll_guiser.insert_one({'game_id': game_id, 'menu_ch': interaction.channel.id, 'menu_msg': message.id})
        coll_guiser.insert_one({'game_id': game_id, 'state': 'setup'})
        logging.error(f'{game_id=}')
        prompt = await generate_user_prompt(topic=topic)
        logging.error(f'{prompt=}')
        coll_guiser.insert_one({'game_id': game_id, 'prompt': prompt})


async def generate_user_prompt(topic=None):
    openai.organization = globals.conf.get(globals.conf.keys.OPENAI_ORGANIZATION, bypass_protected=True)
    openai.api_key = globals.conf.get(globals.conf.keys.OPENAI_API_KEY, bypass_protected=True)
    prompt = 'Write a short question as a fun prompt for discussion in a party game. The question should give the players an opportunity to talk about their personal beliefs and preferences.'
    if topic is not None:
        prompt += f' The Question should be about the following topic: {topic}.'
    result = await openai.Completion.acreate(
        model='text-davinci-003',
        prompt=prompt,
        max_tokens=50,
        temperature=0.5
    )
    return result.choices[0].text.strip()[:100]


async def update_menu_message(menu_ch, menu_msg, game_id):
    coll_guiser = globals.bot.db['guiser']
    ch = await utils.get_channel(menu_ch)
    msg = await ch.fetch_message(menu_msg)
    embed = msg.embeds[0]
    players = list(doc['player'] for doc in coll_guiser.find({'game_id': game_id, 'player': {'$exists': True}}))
    embed.remove_field(len(embed.fields)-1)
    embed.add_field(name='Players', value='\n'.join(f'<@{player}>' for player in players))
    logging.error(f'{players=}')
    await msg.edit(embed=embed)


class StartMenu(discord.ui.View):
    def __init__(self, game_id, *, timeout=None):
        self.game_id = game_id
        self.coll_guiser = globals.bot.db['guiser']
        super().__init__(timeout=timeout)

    @discord.ui.button(label='Join', style=discord.ButtonStyle.primary)
    async def join_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.coll_guiser.find_one({'game_id': self.game_id, 'player': interaction.user.id}) is not None:
            await interaction.response.defer(ephemeral=True, thinking=False)
            return
        if self.coll_guiser.find_one({'game_id': self.game_id, 'state': 'setup'}) is None:
            await interaction.response.defer(ephemeral=True, thinking=False)
            return
        self.coll_guiser.insert_one({'game_id': self.game_id, 'player': interaction.user.id, 'alive': True})
        menu_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'menu_ch': {'$exists': True}, 'menu_msg': {'$exists': True}})
        menu_ch = menu_doc['menu_ch']
        menu_msg = menu_doc['menu_msg']
        await interaction.response.defer(ephemeral=True, thinking=False)
        await update_menu_message(menu_ch=menu_ch, menu_msg=menu_msg, game_id=self.game_id)

    @discord.ui.button(label='Leave', style=discord.ButtonStyle.secondary)
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.coll_guiser.find_one({'game_id': self.game_id, 'player': interaction.user.id}) is None:
            await interaction.response.defer(ephemeral=True, thinking=False)
            return
        if self.coll_guiser.find_one({'game_id': self.game_id, 'state': 'setup'}) is None:
            await interaction.response.defer(ephemeral=True, thinking=False)
            return
        self.coll_guiser.delete_one({'game_id': self.game_id, 'player': interaction.user.id})
        menu_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'menu_ch': {'$exists': True}, 'menu_msg': {'$exists': True}})
        menu_ch = menu_doc['menu_ch']
        menu_msg = menu_doc['menu_msg']
        await interaction.response.defer(ephemeral=True, thinking=False)
        await update_menu_message(menu_ch=menu_ch, menu_msg=menu_msg, game_id=self.game_id)

    @discord.ui.button(label='Start', style=discord.ButtonStyle.red)
    async def start_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        owner_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'owner': {'$exists': True}})
        if interaction.user.id != owner_doc['owner']:
            await interaction.response.defer(ephemeral=True, thinking=False)
            return
        if self.coll_guiser.find_one({'game_id': self.game_id, 'state': 'setup'}) is None:
            await interaction.response.defer(ephemeral=True, thinking=False)
            return
        players = list(doc['player'] for doc in self.coll_guiser.find({'game_id': self.game_id, 'player': {'$exists': True}}))
        embed = discord.Embed(title='Guiser Game', description=f'0/{len(players)}')
        prompt_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'prompt': {'$exists': True}})
        if prompt_doc:
            embed.add_field(name='Prompt', value=prompt_doc['prompt'], inline=False)
        game_menu = GameMenu(game_id=self.game_id)
        await interaction.response.send_message(embed=embed, view=game_menu)
        self.coll_guiser.insert_one({'game_id': self.game_id, 'guiser': random.choice(players)})
        self.coll_guiser.update_one({'game_id': self.game_id, 'state': {'$exists': True}}, {'$set': {'state': 'answer'}})
        message: discord.Message = await interaction.original_response()
        self.coll_guiser.insert_one({'game_id': self.game_id, 'game_ch': interaction.channel.id, 'game_msg': message.id})


class GameMenu(discord.ui.View):
    def __init__(self, game_id, *, timeout=None):
        self.game_id = game_id
        self.coll_guiser = globals.bot.db['guiser']
        super().__init__(timeout=timeout)

    @discord.ui.button(label='Chat', style=discord.ButtonStyle.primary)
    async def chat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        players = list(doc['player'] for doc in self.coll_guiser.find({'game_id': self.game_id, 'player': {'$exists': True}}))
        guiser = self.coll_guiser.find_one({'game_id': self.game_id, 'guiser': {'$exists': True}})['guiser']
        guised_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'guised': {'$exists': True}})
        guised = guised_doc['guised'] if guised_doc else None
        if interaction.user.id not in players:
            await interaction.response.defer(ephemeral=True, thinking=False)
            return
        if interaction.user.id == guiser and guised is None:
            await interaction.response.send_message('Select user to disguise at.', view=GuiserView(game_id=self.game_id, players=players, guiser=guiser), ephemeral=True)
        else:
            guised_user = None
            if guised:
                guised_user = interaction.guild.get_member(guised) or await interaction.guild.fetch_member(guised)
            await interaction.response.send_modal(ChatModal(game_id=self.game_id, player=interaction.user.id, guised_user=guised_user))


class ReplyMenu(discord.ui.View):
    def __init__(self, game_id, replying_to: discord.Message, replying_author, *, timeout=None):
        self.game_id = game_id
        self.replying_to = replying_to
        self.replying_author = replying_author
        self.coll_guiser = globals.bot.db['guiser']
        super().__init__(timeout=timeout)

    @discord.ui.button(label='Reply', style=discord.ButtonStyle.primary)
    async def chat_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        players = list(doc['player'] for doc in self.coll_guiser.find({'game_id': self.game_id, 'player': {'$exists': True}}))
        guised_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'guised': {'$exists': True}})
        guised = guised_doc['guised'] if guised_doc else None
        if interaction.user.id not in players:
            await interaction.response.defer(ephemeral=True, thinking=False)
            return
        if not self.coll_guiser.find_one({'game_id': self.game_id, 'player': interaction.user.id, 'alive': True}):
            await interaction.response.send_message('you are dead', ephemeral=True)
            return
        guised_user = interaction.guild.get_member(guised) or await interaction.guild.fetch_member(guised)
        await interaction.response.send_modal(ChatModal(game_id=self.game_id, player=interaction.user.id, guised_user=guised_user, replying_to=self.replying_to))

    @discord.ui.button(label='Kill', style=discord.ButtonStyle.red)
    async def kill_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        guiser = self.coll_guiser.find_one({'game_id': self.game_id, 'guiser': {'$exists': True}})['guiser']
        guised = self.coll_guiser.find_one({'game_id': self.game_id, 'guised': {'$exists': True}})['guised']
        if interaction.user.id == guiser:
            await interaction.response.defer(ephemeral=True, thinking=False)
            return
        if not self.coll_guiser.find_one({'game_id': self.game_id, 'player': interaction.user.id, 'alive': True}):
            await interaction.response.send_message('you are dead', ephemeral=True)
            return
        if self.replying_author == guised:
            await interaction.response.send_message(f'{interaction.user.mention} won the game by killing <@{guiser}>')
            self.coll_guiser.update_one({'game_id': self.game_id, 'state': {'$exists': True}}, {'$set': {'state': 'over'}})
        elif not self.coll_guiser.find_one({'game_id': self.game_id, 'player': self.replying_author, 'alive': True}):
            await interaction.response.send_message('that player is already dead', ephemeral=True)
        else:
            player_docs = list(self.coll_guiser.find({'game_id': self.game_id, 'player': {'$exists': True}}))
            self.coll_guiser.update_one({'game_id': self.game_id, 'player': interaction.user.id}, {'$set': {'alive': False}})
            self.coll_guiser.update_one({'game_id': self.game_id, 'player': self.replying_author}, {'$set': {'alive': False}})
            player_docs_alive = list(filter(lambda doc: doc.get('alive'), player_docs))
            await interaction.response.send_message(f'{interaction.user.mention} killed <@{self.replying_author}> but they were innocent, so both died')
            if len(player_docs_alive) < 3:
                self.coll_guiser.update_one({'game_id': self.game_id, 'state': {'$exists': True}}, {'$set': {'state': 'over'}})
                await interaction.channel.send(f'<@{guiser}> won the game by being one of the last two players alive')

class GuiserView(discord.ui.View):
    def __init__(self, game_id, players, guiser):
        super().__init__()
        self.coll_guiser = globals.bot.db['guiser']
        self.game_id = game_id
        self.players = players
        self.guiser = guiser

    @discord.ui.select(cls=discord.ui.UserSelect)
    async def select_target(self, interaction: discord.Interaction, select: discord.ui.UserSelect):
        guised_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'guised': {'$exists': True}})
        if guised_doc:
            guised = guised_doc['guised']
            await interaction.response.send_message(f'already disguised as <@{guised}>', ephemeral=True)
            return
        selected = select.values[0]
        if selected.id not in self.players:
            await interaction.response.send_message('that player is not in the game', ephemeral=True)
            return
        if selected.id == interaction.user.id:
            await interaction.response.send_message('you cannot disguise as yourself', ephemeral=True)
            return
        self.coll_guiser.insert_one({'game_id': self.game_id, 'guised': selected.id})
        self.coll_guiser.update_one({'game_id': self.game_id, 'player': selected.id}, {'$set': {'alive': False}})
        await interaction.response.send_modal(ChatModal(game_id=self.game_id, player=interaction.user.id, guised_user=selected))


class ChatModal(discord.ui.Modal):
    chat = discord.ui.TextInput(
        label='Write something here.',
        style=discord.TextStyle.long,
        row=4
    )

    def __init__(self, game_id, player, guised_user, replying_to=None):
        super().__init__(title='')
        self.coll_guiser = globals.bot.db['guiser']
        self.game_id = game_id
        self.player = player
        prompt_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'prompt': {'$exists': True}})
        self.replying_to = replying_to
        self.guild = None
        if replying_to:
            self.chat.placeholder = replying_to.embeds[0].description
        elif prompt_doc is not None:
            self.chat.placeholder = prompt_doc['prompt']
        self.guiser = self.coll_guiser.find_one({'game_id': self.game_id, 'guiser': {'$exists': True}})['guiser']
        guised_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'guised': {'$exists': True}})
        self.guised = guised_doc['guised'] if guised_doc else None
        if self.player != self.guiser:
            self.title = 'Chat as yourself'
        else:
            self.title = f'Chat as {guised_user.display_name}'

    async def send_chat(self, ch, message, player):
        guised = self.coll_guiser.find_one({'game_id': self.game_id, 'guised': {'$exists': True}})['guised']
        if not self.coll_guiser.find_one({'game_id': self.game_id, 'player': player, 'alive': True}):
            return
        elif player == self.guiser:
            player = guised
        author = self.guild.get_member(player) or await self.guild.fetch_member(player)
        embed = discord.Embed()
        icon_url = author.avatar.url if author.avatar else None
        embed.set_author(name=author.display_name, icon_url=icon_url)
        embed.description = message
        embed.colour = author.colour
        if self.replying_to is None:
            msg = await ch.send(embed=embed)
        else:
            msg = await self.replying_to.reply(embed=embed)
        await msg.edit(view=ReplyMenu(game_id=self.game_id, replying_to=msg, replying_author=player))

    async def update_game_message(self):
        game_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'game_ch': {'$exists': True}, 'game_msg': {'$exists': True}})
        player_docs = list(self.coll_guiser.find({'game_id': self.game_id, 'player': {'$exists': True}}))
        n_messages = len([player_doc for player_doc in player_docs if 'messages' in player_doc])
        ch = await utils.get_channel(game_doc['game_ch'])
        message = await ch.fetch_message(game_doc['game_msg'])
        embed = message.embeds[0]
        embed.description = f'{n_messages}/{len(player_docs)}'
        await message.edit(embed=embed)
        if n_messages == len(player_docs):
            self.coll_guiser.update_one({'game_id': self.game_id, 'state': {'$exists': True}}, {'$set': {'state': 'chat'}})
            random.shuffle(player_docs)
            for player_doc in player_docs:
                await self.send_chat(ch, player_doc['messages'][0], player_doc['player'])

    async def on_submit(self, interaction: discord.Interaction):
        state = self.coll_guiser.find_one({'game_id': self.game_id, 'state': {'$exists': True}})['state']
        player_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'player': self.player})
        self.guild = interaction.guild
        if state == 'answer':
            if 'messages' in player_doc:
                await interaction.response.send_message('please wait for everyone to answer the original prompt', ephemeral=True)
            else:
                self.coll_guiser.update_one({'game_id': self.game_id, 'player': self.player}, {'$set': {'messages': [self.chat.value]}})
                await interaction.response.defer(ephemeral=True, thinking=False)
                await self.update_game_message()
        elif state == 'chat':
            await interaction.response.defer(ephemeral=True, thinking=False)
            game_doc = self.coll_guiser.find_one({'game_id': self.game_id, 'game_ch': {'$exists': True}, 'game_msg': {'$exists': True}})
            ch = await utils.get_channel(game_doc['game_ch'])
            await self.send_chat(ch, self.chat.value, interaction.user.id)
