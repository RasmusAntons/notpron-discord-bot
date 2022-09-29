import asyncio
import random
from collections import namedtuple

import discord
from discord.ext import commands
import pymongo.errors

import config
import globals


class WhosaiditCog(commands.Cog, name='Whosaidit', description='who said it'):
    num_reacts = ['1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣', '🔟']
    n_clues = 5
    delay_before_start = 3
    delay_between_clues = 10

    def __init__(self):
        self.coll_enabled = globals.bot.db['whosaidit_enabled']
        self.coll_enabled.create_index('uid', unique=True)
        self.running = {}

    def format_msg(self, selection, clues, outcome=None):
        embed = discord.Embed(title='who said this:', color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
        for i, hint in enumerate(clues):
            embed.add_field(name=f'------------', value=hint, inline=False)
        selection_text = ' • '.join(f'{i + 1} {selection[i].display_name}' for i in range(len(selection)))
        embed.set_footer(text=selection_text)
        if outcome is not None:
            embed.add_field(name='game over', value=outcome, inline=False)
        return embed

    @commands.hybrid_group(name='whosaidit', description='who said it')
    async def whosaidit_grp(self, ctx):
        return None

    @whosaidit_grp.command(name='start', description='start a game')
    async def start(self, ctx: commands.Context) -> None:
        enabled_users = [user['uid'] for user in self.coll_enabled.find()]
        selection_uids = random.sample(enabled_users, min(len(enabled_users), 10))
        selection_users = [globals.bot.get_user(uid) or await globals.bot.fetch_user(uid) for uid in selection_uids]
        selection_users = sorted(selection_users, key=lambda u: u.display_name)
        target_user = random.choice(selection_users)
        game_msg = await ctx.reply(embed=self.format_msg(selection_users, []))
        game_state = {'selection': selection_users, 'target': target_user, 'clues': [], 'guesses': {}, 'ended': False}
        self.running[game_msg.id] = game_state
        for i in range(len(selection_uids)):
            await game_msg.add_reaction(self.num_reacts[i])
        await asyncio.sleep(self.delay_before_start)
        for hint_nr in range(self.n_clues):
            if game_state['ended']:
                break
            hint = globals.bot.markov.generate_forwards(tag=str(target_user.id))
            if hint is None:
                await game_msg.reply(
                    f'I picked {target_user.display_name} but I don\'t know them well enough to imitate them.')
                return
            game_state['clues'].append(hint)
            await game_msg.edit(embed=self.format_msg(selection_users, game_state['clues']))
            await asyncio.sleep(self.delay_between_clues)
        if not game_state['ended']:
            await game_msg.edit(embed=self.format_msg(selection_users, game_state['clues'],
                                                      f'nobody guessed {target_user.display_name}'))
        del self.running[game_msg.id]

    @whosaidit_grp.command(name='theoffice', description='start a game with the office characters')
    async def start(self, ctx: commands.Context) -> None:
        characters = {'Dealer', 'Man 1', 'Seth Mayers', 'Pam', 'Woman 1', 'Darryl', 'Woman 2', 'All', 'Senator Lipton',
                      'Man', 'Clark', 'Woman 3', 'Robert California', 'Creed', 'Hank', 'Phyllis', 'Camera', 'Stripper',
                      'Malcolm', 'Carol Stills', 'Stanley', 'Ravi', 'Nellie Bertram', 'Val', 'Brandon', 'Bob', 'Warren',
                      'Dwight', 'Holly', 'Everyone', 'Todd Packer', 'Michael', 'Hunter', 'Jordan', 'Robert', 'Billy',
                      'Jan', 'Receptionist', 'Dakota', 'Woman over speakerphone', 'Ryan',
                      'Pam as “ninth-biggest client”', 'Jakey', 'Ed', 'Nellie', 'Minister', 'Oscar', 'Meredith', 'Jo',
                      'David Brent', 'Others', 'Andy', 'Photographer', 'Roy', 'Gabe', 'Zeke', 'Mose', 'Joan', 'Hide',
                      'Moderator', 'Angela', 'Usher', 'Rachel', 'Kendall', 'Billy’s Girlfriend',
                      'Vance Refrigeration guy', 'Woman 4', 'Pam as “fourth-biggest client”', 'Realtor', 'Erin',
                      'Man 3', 'Nurse', 'Fred Henry', 'Woman', 'Woman from Buffalo', 'Warren Buffett', 'David',
                      'Casey Dean', 'Kelly', 'Pete', 'Charles', 'Kevin', 'Jada', 'Fred', 'Jim', 'Katy', 'Bill Hader',
                      'Toby', 'Finger Lakes Guy', 'Troy', 'Bob Vance', 'Crowd', 'Co-workers', 'Man 2', 'Merv', 'Holy',
                      'Jake', 'Carol', 'Rolph', 'AJ', 'Karen', 'Sasha', 'Meredith’s Vet', 'David Wallace', 'Calvin',
                      'Both', 'Man from Buffalo', 'Nick', 'Buyer', 'Merv Bronte', 'Guy', 'Someone'}
        Character = namedtuple('Character', ['display_name', 'id'])
        selection_names = random.sample(characters, min(len(characters), 10))
        selection_chars = [Character(display_name=name, id=name.lower()) for name in selection_names]
        selection_chars = sorted(selection_chars, key=lambda u: u.display_name)
        target_char = random.choice(selection_chars)
        game_msg = await ctx.reply(embed=self.format_msg(selection_chars, []))
        game_state = {'selection': selection_chars, 'target': target_char, 'clues': [], 'guesses': {}, 'ended': False}
        self.running[game_msg.id] = game_state
        for i in range(len(selection_chars)):
            await game_msg.add_reaction(self.num_reacts[i])
        await asyncio.sleep(self.delay_before_start)
        for hint_nr in range(self.n_clues):
            if game_state['ended']:
                break
            hint = globals.bot.markov_office.generate_forwards(tag=str(target_char.id))
            if hint is None:
                await game_msg.reply(
                    f'I picked {target_user.display_name} but I don\'t know them well enough to imitate them.')
                return
            game_state['clues'].append(hint)
            await game_msg.edit(embed=self.format_msg(selection_chars, game_state['clues']))
            await asyncio.sleep(self.delay_between_clues)
        if not game_state['ended']:
            await game_msg.edit(embed=self.format_msg(selection_chars, game_state['clues'],
                                                      f'nobody guessed {target_char.display_name}'))
        del self.running[game_msg.id]

    @whosaidit_grp.command(name='adduser', description='add user to the game')
    async def adduser(self, ctx: commands.Context, user: discord.User = None):
        if user is None:
            user = ctx.author
        if user.id != ctx.author.id and not await config.is_mod(ctx.author):
            await ctx.reply('you can only add yourself', ephemeral=True)
            return
        try:
            self.coll_enabled.insert_one({'uid': user.id})
            await ctx.reply(f'added {user.mention} to the game')
        except pymongo.errors.DuplicateKeyError:
            await ctx.reply(f'that user is already in the game')

    @whosaidit_grp.command(name='removeuser', description='remove user from the game')
    async def adduser(self, ctx: commands.Context, user: discord.User = None):
        if user is None:
            user = ctx.author
        if user.id != ctx.author.id and not await config.is_mod(ctx.author):
            await ctx.reply('you can only remove yourself', ephemeral=True)
            return
        res = self.coll_enabled.delete_one({'uid': user.id})
        if res.deleted_count:
            await ctx.reply(f'removed {user.mention} from the game')
        else:
            await ctx.reply(f'that user is not in the game')

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction, user):
        if user.id == globals.bot.user.id:
            return
        if reaction.message.id in self.running and reaction.emoji in self.num_reacts:
            game_state = self.running[reaction.message.id]
            if game_state['ended'] or user.id in game_state['guesses']:
                return
            guess_idx = self.num_reacts.index(reaction.emoji)
            if len(game_state['selection']) <= guess_idx:
                return
            game_state['guesses'][user.id] = guess_idx
            if game_state['selection'][guess_idx].id == game_state['target'].id:
                game_state['ended'] = True
                correct_guess = game_state['target'].display_name
                await reaction.message.edit(embed=self.format_msg(game_state['selection'], game_state['clues'],
                                                                  f'{user.mention} solved by guessing {correct_guess}'))
