import json
import re

import discord
from discord import app_commands
from discord.ext import commands
import pymongo
from pymongo.errors import DuplicateKeyError

import globals
from utils import inline_code


class HighlightCog(commands.Cog, name='Highlight', description='manage notifications for words or phrases'):
    def __init__(self):
        self.coll = globals.bot.db['highlights']
        self.coll.create_index('uid')
        self.coll.create_index([('uid', pymongo.ASCENDING), ('pattern', pymongo.ASCENDING)], unique=True)

    @commands.hybrid_group(name='highlight', aliases=('hl',), description='manage notifications for words or phrases')
    async def highlight_grp(self, ctx):
        return None

    @highlight_grp.command(name='add', description='add a highlight')
    async def add(self, ctx: commands.Context, pattern: str) -> None:
        try:
            insert_result = self.coll.insert_one({'uid': ctx.author.id, 'pattern': pattern})
            clause = f'try {{new RegExp(this.pattern)}} catch(e) {{return false}} return true'
            valid = self.coll.find_one({'_id': insert_result.inserted_id, '$where': clause})
            if valid is None:
                self.coll.delete_one({'_id': insert_result.inserted_id})
                raise RuntimeError('Not valid JavaScript regex.')
        except DuplicateKeyError:
            raise RuntimeError(f'That highlight already exists.')
        await ctx.reply(f'added highlight {inline_code(pattern)}')

    @highlight_grp.command(name='list', description='list highlights')
    async def list(self, ctx: commands.Context) -> None:
        user_hl = self.coll.find({'uid': ctx.author.id})
        embed = discord.Embed(colour=globals.bot.conf.get(globals.bot.conf.keys.EMBED_COLOUR))
        text = []
        for hl in user_hl:
            text.append(inline_code(hl["pattern"]))
        if len(text) == 0:
            text.append(f'None')
        embed.add_field(name='Highlights', value='\n'.join(text), inline=False)
        await ctx.reply(embed=embed)

    @highlight_grp.command(name='remove')
    async def remove(self, ctx: commands.Context, pattern: str):
        delete_result = self.coll.delete_one({'uid': ctx.author.id, 'pattern': pattern})
        if delete_result.deleted_count == 1:
            await ctx.reply(f'Removed highlight {inline_code(pattern)}.')
        else:
            await ctx.reply(f'Cannot find highlight {inline_code(pattern)}.')

    @remove.autocomplete('pattern')
    async def key_autocomplete(self, interaction: discord.Interaction, pattern: str) -> None:
        if pattern:
            pat = re.compile(re.escape(pattern), re.I)
            res = self.coll.find({'uid': interaction.user.id, 'pattern': {'$regex': pat}}, limit=25)
        else:
            res = self.coll.find({'uid': interaction.user.id}, limit=25)
        return [app_commands.Choice(name=hl['pattern'], value=hl['pattern']) for hl in res]

    @commands.Cog.listener()
    async def on_message(self, msg):
        if msg.author.bot:
            return
        matches = self.coll.find({'$where': f'new RegExp(this.pattern).test({json.dumps(msg.content)})'})
        notified = set()
        for match in matches:
            try:
                member = msg.guild.get_member(int(match['uid'])) or await msg.guild.fetch_member(match['uid'])
            except discord.NotFound:
                continue
            if (not member) or (not msg.channel.permissions_for(member).read_messages) or member.id == msg.author.id:
                continue
            if member.id in notified:
                continue
            ch = await globals.bot.get_dm_channel(member)
            embed = discord.Embed()
            embed.set_author(name=f'{msg.author.display_name}',
                             icon_url=f'{msg.author.display_avatar.url.replace("?size=1024", "?size=32")}')
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
