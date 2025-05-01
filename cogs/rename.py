import io
import re

import discord
from discord import app_commands
from discord.ext import commands

import config
import globals


class RenameCog(commands.Cog, name='Rename', description='mass rename nerds'):
    def __init__(self):
        self.groups_coll = globals.bot.db['rename_groups']
        self.groups_coll.create_index('name', unique=True)
        self.users_coll = globals.bot.db['rename_users']
        self.users_coll.create_index('uid', unique=True)

    @commands.hybrid_group(name='rename', description='mass rename nerds')
    async def rename_grp(self, ctx):
        return None

    @rename_grp.command(name='creategroup', description='add a renaming group')
    @config.check_bot_admin()
    async def creategroup(self, ctx: commands.Context, name: str) -> None:
        self.groups_coll.insert_one({'name': name, 'users': []})
        return await ctx.reply(f'created group {name}')

    @rename_grp.command(name='deletegroup', description='delete a renaming group')
    @config.check_bot_admin()
    async def deletegroup(self, ctx: commands.Context, group: str) -> None:
        self.groups_coll.delete_one({'name': group})
        return await ctx.reply(f'deleted group {group}')

    @rename_grp.command(name='listgroups', description='list renaming groups')
    @config.check_bot_admin()
    async def listgroups(self, ctx: commands.Context) -> None:
        groups = self.groups_coll.find({}, {'name': True})
        response = '**rename groups:**\n' + '\n'.join((group['name'] for group in groups))
        return await ctx.reply(response)

    @rename_grp.command(name='showgroup', description='show a renaming group')
    @config.check_bot_admin()
    async def showgroup(self, ctx: commands.Context, group: str) -> None:
        group_obj = self.groups_coll.find_one({'name': group})
        if group_obj is None:
            raise RuntimeError('That group does not exist')
        usernames = []
        invalid_uids = []
        for uid in group_obj['users']:
            user = globals.bot.get_user(int(uid))
            if user is not None:
                usernames.append(f'{user.name}#{user.discriminator}')
            else:
                invalid_uids.append(uid)
        out_file = io.StringIO()
        for username in usernames:
            out_file.write(f'{username}\n')
        for invalid_uid in invalid_uids:
            out_file.write(f'user not found: {invalid_uid}\n')
        out_file.seek(0)
        return await ctx.reply(f'**{group}**\n', file=discord.File(out_file, filename=f'{group}.txt'))

    @rename_grp.command(name='addto', description='add users to renaming group')
    @config.check_bot_admin()
    async def addto(self, ctx: commands.Context, group: str, role: discord.Role = None, user: discord.User = None,
                    user01: discord.User = None, user02: discord.User = None, user03: discord.User = None,
                    user04: discord.User = None, user05: discord.User = None, user06: discord.User = None,
                    user07: discord.User = None, user08: discord.User = None, user09: discord.User = None,
                    user10: discord.User = None, user11: discord.User = None, user12: discord.User = None,
                    user13: discord.User = None, user14: discord.User = None, user15: discord.User = None,
                    user16: discord.User = None, user17: discord.User = None, user18: discord.User = None,
                    user19: discord.User = None, user20: discord.User = None, user21: discord.User = None,
                    user22: discord.User = None) -> None:
        group_obj = self.groups_coll.find_one({'name': group})
        if group_obj is None:
            raise RuntimeError('That group does not exist')
        update_count = 0
        users = [user, user01, user02, user03, user04, user05, user06, user07, user08, user09, user10, user11, user12,
                 user13, user14, user15, user16, user17, user18, user19, user20, user21, user22]
        for user in users:
            if user and str(user.id) not in group_obj['users']:
                group_obj['users'].append(str(user.id))
                update_count += 1
        if role is not None:
            for member in role.members:
                if str(member.id) not in group_obj['users']:
                    group_obj['users'].append(str(member.id))
                    update_count += 1
        if update_count:
            self.groups_coll.update_one({'name': group}, {'$set': {'users': group_obj['users']}})
        return await ctx.reply(f'added {update_count} users to group {group}')

    @rename_grp.command(name='removefrom', description='remove users from renaming group')
    @config.check_bot_admin()
    async def removefrom(self, ctx: commands.Context, group: str, user: discord.User, user01: discord.User = None,
                         user02: discord.User = None, user03: discord.User = None, user04: discord.User = None,
                         user05: discord.User = None, user06: discord.User = None, user07: discord.User = None,
                         user08: discord.User = None, user09: discord.User = None, user10: discord.User = None,
                         user11: discord.User = None, user12: discord.User = None, user13: discord.User = None,
                         user14: discord.User = None, user15: discord.User = None, user16: discord.User = None,
                         user17: discord.User = None, user18: discord.User = None, user19: discord.User = None,
                         user20: discord.User = None, user21: discord.User = None, user22: discord.User = None,
                         user23: discord.User = None) -> None:
        group_obj = self.groups_coll.find_one({'name': group})
        if group_obj is None:
            raise RuntimeError('That group does not exist')
        update_count = 0
        users = [user, user01, user02, user03, user04, user05, user06, user07, user08, user09, user10, user11, user12,
                 user13, user14, user15, user16, user17, user18, user19, user20, user21, user22, user23]
        for user in users:
            if user and str(user.id) in group['users']:
                group_obj['users'].remove(str(user.id))
                update_count += 1
        if update_count:
            self.groups_coll.update_one({'name': group}, {'$set': {'users': group_obj['users']}})
        return await ctx.reply(f'removed {update_count} users from group {group}')

    async def _rename(self, ctx: commands.Context, group_name: str, names: str = None, revert=False):
        group = self.groups_coll.find_one({'name': group_name})
        if group is None:
            raise RuntimeError('That group does not exist')
        await ctx.defer()
        new_name_choices = names.split('|') if names is not None else ['']
        count = 0
        invalid_uids = []
        failed_renames = []
        for i, uid in enumerate(group['users']):
            user = globals.bot.get_user(int(uid))
            if user is not None:
                member = ctx.guild.get_member(int(uid))
                renamed_user = self.users_coll.find_one({'uid': uid})
                old_name = member.nick
                new_name = new_name_choices[i % len(new_name_choices)]
                if renamed_user is not None:
                    if renamed_user['new_name'] == member.nick:
                        old_name = renamed_user['old_name']
                try:
                    if not revert:
                        if member.nick != new_name:
                            await member.edit(nick=new_name)
                            count += 1
                        self.users_coll.update_one({'uid': uid},
                                                   {'$set': {'uid': uid, 'old_name': old_name, 'new_name': new_name}},
                                                   upsert=True)
                    else:
                        if member.nick != old_name:
                            await member.edit(nick=old_name)
                            count += 1
                        self.users_coll.delete_one({'uid': uid})
                except discord.HTTPException:
                    failed_renames.append(member.mention)
            else:
                invalid_uids.append(uid)
        response = f'renamed {count} users'
        if invalid_uids:
            response += '\n failed to find the following users: ' + ' '.join(invalid_uids)
        if failed_renames:
            response += '\n failed to rename the following users: ' + ' '.join(failed_renames)
        return await ctx.reply(response)

    @rename_grp.command(name='renamegroup', description='rename everyone in a group')
    @config.check_bot_admin()
    async def renamegroup(self, ctx: commands.Context, group: str, names: str) -> None:
        await self._rename(ctx, group, names=names)

    @rename_grp.command(name='revertgroup', description='revert names for everyone in a group')
    @config.check_bot_admin()
    async def revertgroup(self, ctx: commands.Context, group: str) -> None:
        await self._rename(ctx, group, revert=True)

    @showgroup.autocomplete('group')
    @addto.autocomplete('group')
    @removefrom.autocomplete('group')
    @renamegroup.autocomplete('group')
    @revertgroup.autocomplete('group')
    @deletegroup.autocomplete('group')
    async def group_autocomplete(self, interaction: discord.Interaction, group: str) -> None:
        if group:
            pat = re.compile(re.escape(group), re.I)
            res = self.groups_coll.find({'name': {'$regex': pat}}, {'name': True}, limit=25)
        else:
            res = self.groups_coll.find(limit=25)
        return [app_commands.Choice(name=grp['name'], value=grp['name']) for grp in res]
