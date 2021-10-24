from commands.command import Command, Category
from listeners import ReactionListener
import globals
import random
import pymongo.errors
import asyncio


class WhoSaidItCommand(Command, ReactionListener):
    name = 'whosaidit'
    category = Category.UTILITY
    arg_range = (0, 2)
    description = 'who said it'
    arg_desc = '[addme | add @user]'
    num_reacts = ['0️⃣', '1️⃣', '2️⃣', '3️⃣', '4️⃣', '5️⃣', '6️⃣', '7️⃣', '8️⃣', '9️⃣']
    n_hints = 5
    delay_between_hints = 10

    def __init__(self):
        super(WhoSaidItCommand, self).__init__()
        coll_enabled = globals.bot.db['whosaidit_enabled']
        coll_enabled.create_index('uid', unique=True)
        self.running = {}

    def format_msg(self, selection, hints, outcome=None):
        res = ['Who said it?', '']
        for i, hint in enumerate(hints):
            res.append(f'Hint {i + 1}:')
            res.append(hint)
        res.append('')
        res.append('•'.join(f'{self.num_reacts[i]} {selection[i].display_name}' for i in range(len(selection))))
        if outcome is not None:
            res.append('')
            res.append(outcome)
        return '\n'.join(res)

    async def execute(self, args, msg):
        coll_enabled = globals.bot.db['whosaidit_enabled']
        if len(args) == 0:
            enabled_users = [user['uid'] for user in coll_enabled.find()]
            selection_uids = random.sample(enabled_users, min(len(enabled_users), 10))
            selection_users = [globals.bot.get_user(uid) or globals.bot.fetch_user(uid) for uid in selection_uids]
            target_user = random.choice(selection_users)
            game_msg = await msg.channel.send(self.format_msg(selection_users, []))
            game_state = {'selection': selection_users, 'target': target_user, 'hints': [], 'guesses': {}, 'ended': False}
            self.running[game_msg.id] = game_state
            for i in range(len(selection_uids)):
                await game_msg.add_reaction(self.num_reacts[i])
            for hint_nr in range(self.n_hints):
                await asyncio.sleep(self.delay_between_hints)
                if game_state['ended']:
                    break
                hint = globals.bot.markov.generate_forwards(tag=str(target_user.id))
                if hint is None:
                    await game_msg.reply(f'I picked {target_user.display_name} but I don\'t know them well enough to imitate them.')
                    return
                game_state['hints'].append(hint)
                await game_msg.edit(content=self.format_msg(selection_users, game_state['hints']))
            await asyncio.sleep(self.delay_between_hints)
            if not game_state['ended']:
                await game_msg.edit(content=self.format_msg(selection_users, game_state['hints'], 'Nobody solved.'))
            del self.running[game_msg.id]
            return True
        if len(args) == 1 and args[0] == 'addme':
            try:
                coll_enabled.insert_one({'uid': msg.author.id})
                await msg.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            except pymongo.errors.DuplicateKeyError:
                await msg.add_reaction('😠')
            return True
        elif len(args) == 2 and args[0] == 'add' and len(msg.mentions) > 0:
            try:
                coll_enabled.insert_one({'uid': msg.mentions[0].id})
                await msg.add_reaction('\N{WHITE HEAVY CHECK MARK}')
            except pymongo.errors.DuplicateKeyError:
                await msg.add_reaction('😠')
            return True
        return False

    async def on_reaction_add(self, reaction, user):
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
                await reaction.message.edit(content=self.format_msg(game_state['selection'], game_state['hints'], f'{user.mention} solved'))

    async def on_reaction_remove(self, reaction, user):
        pass
