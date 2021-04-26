from commands.command import Command, Category
from listeners import MessageListener
import json
import discord
from utils import get_member
import globals
from pymongo.errors import DuplicateKeyError
from bson.objectid import ObjectId
import pymongo


class HighlightCommand(Command, MessageListener):
    name = 'highlight'
    category = Category.UTILITY
    aliases = ['hl']
    arg_range = (1, 99)
    description = 'manage notifications for words or phrases'
    arg_desc = 'add <regular expression...> | list | remove <highlight_id>'

    def __init__(self):
        super(HighlightCommand, self).__init__()
        coll = globals.bot.db['highlights']
        coll.create_index('uid')
        coll.create_index([('uid', pymongo.ASCENDING), ('pattern', pymongo.ASCENDING)], unique=True)

    @staticmethod
    def inline_code(text):
        while '``' in text:
            text = text.replace('``', '`​`')
        return f'``{text}``'

    async def execute(self, args, msg):
        coll = globals.bot.db['highlights']
        if len(args) >= 2 and args[0] == 'add':
            new_hl = ' '.join(args[1:])
            try:
                insert_result = coll.insert_one({'uid': msg.author.id, 'pattern': new_hl})
                valid = coll.find_one({'_id': insert_result.inserted_id, '$where': f'try {{new RegExp(this.pattern)}} catch(e) {{return false}} return true'})
                if valid is None:
                    coll.delete_one({'_id': insert_result.inserted_id})
                    raise RuntimeError('Not valid JavaScript JSON.')
            except DuplicateKeyError:
                raise RuntimeError(f'That highlight already exists.')
            await msg.reply(f'added highlight {self.inline_code(new_hl)}')
            return True
        elif len(args) == 1 and args[0] == 'list':
            user_hl = coll.find({'uid': msg.author.id})
            embed = discord.Embed(colour=globals.bot.conf.get(globals.bot.conf.keys.EMBED_COLOUR))
            text = [f'{msg.author.mention}']
            for i, hl in enumerate(user_hl):
                text.append(f'{self.inline_code(hl["pattern"])} ({hl["_id"]})')
            if len(text) == 1:
                text.append(f'None')
            embed.add_field(name='Highlights', value='\n'.join(text), inline=False)
            await msg.channel.send(embed=embed)
            return True
        elif len(args) == 2 and args[0] in ('remove', 'delete'):
            delete_result = coll.delete_one({'_id': ObjectId(args[1]), 'uid': msg.author.id})
            if delete_result.deleted_count == 1:
                await msg.channel.send(f'Removed highlight {args[1]}.')
            else:
                await msg.channel.send(f'Cannot find highlight {args[1]}.')
            return True
        return False

    async def on_message(self, msg):
        if msg.author.bot:
            return
        coll = globals.bot.db['highlights']
        matches = coll.find({'$where': f'new RegExp(this.pattern).test({json.dumps(msg.content)})'})
        notified = set()
        for match in matches:
            try:
                member = await get_member(match['uid'])
            except discord.NotFound:
                continue
            if not member or not msg.channel.permissions_for(member).read_messages or member.id == msg.author.id:
                continue
            if member.id in notified:
                continue
            ch = await globals.bot.get_dm_channel(member)
            embed = discord.Embed()
            embed.set_author(name=f'{msg.author.display_name}', icon_url=f'{msg.author.avatar_url_as(size=32)}')
            link = f'\n[link]({msg.jump_url})'
            if len(msg.content) > (1024 - len(link)):
                text = f'{msg.content[:(1021 - len(link))]}...{link}'
            else:
                text = f'{msg.content}{link}'
            embed.add_field(name=f'#{msg.channel.name}', value=text, inline=False)
            embed.set_footer(text=f'matched this rule: {match["pattern"]}')
            try:
                await ch.send(embed=embed)
                notified.add(member.id)
            except discord.HTTPException:
                pass
