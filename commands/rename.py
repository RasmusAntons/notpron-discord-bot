import random

import discord
import pymongo.collection

from commands.command import Command, Category
import config
import globals


class RenameCommand(Command):
    name = 'rename'
    category = Category.ADMIN
    arg_range = (2, 99)
    description = 'mass rename nerds'
    arg_desc = 'group create <group_name> | group list | group show <group_name> | group add <group_name> [mentions...] | rename <group_name> [new names (| separated)...] | revert <group_name>'

    def __init__(self):
        super(RenameCommand, self).__init__()
        groups_coll = globals.bot.db['rename_groups']
        groups_coll.create_index('name', unique=True)
        users_coll = globals.bot.db['rename_users']
        users_coll.create_index('uid', unique=True)

    async def check(self, args, msg, test=False):
        return await super().check(args, msg, test) and config.is_admin(msg.author)

    async def execute(self, args, msg):
        groups_coll: pymongo.collection.Collection = globals.bot.db['rename_groups']
        users_coll: pymongo.collection.Collection = globals.bot.db['rename_users']
        if args[0] == 'group':
            if args[1] == 'create':
                group_name = args[2]
                groups_coll.insert_one({'name': group_name, 'users': []})
                return await msg.reply(f'created group {group_name}')
            elif args[1] == 'list':
                groups = groups_coll.find({}, {'name': True})
                response = '**rename groups:**\n' + '\n'.join((group['name'] for group in groups))
                return await msg.reply(response)
            elif args[1] == 'show':
                group_name = args[2]
                group = groups_coll.find_one({'name': group_name})
                if group is None:
                    raise RuntimeError('That group does not exist')
                usernames = []
                invalid_uids = []
                for uid in group['users']:
                    user = globals.bot.get_user(int(uid))
                    if user is not None:
                        usernames.append(user.mention)
                    else:
                        invalid_uids.append(uid)
                return await msg.reply(f'**{group_name}**\n' + '\n'.join(usernames) + '\n' + '\n'.join(invalid_uids))
            elif args[1] == 'add':
                group_name = args[2]
                group = groups_coll.find_one({'name': group_name})
                if group is None:
                    raise RuntimeError('That group does not exist')
                update_count = 0
                for member in msg.mentions:
                    if str(member.id) not in group['users']:
                        group['users'].append(str(member.id))
                        update_count += 1
                if update_count:
                    groups_coll.update_one({'name': group_name}, {'$set': {'users': group['users']}})
                return await msg.reply(f'added {update_count} users to group {group_name}')
            elif args[1] == 'remove':
                group_name = args[2]
                group = groups_coll.find_one({'name': group_name})
                if group is None:
                    raise RuntimeError('That group does not exist')
                update_count = 0
                for member in msg.mentions:
                    if str(member.id) in group['users']:
                        group['users'].remove(str(member.id))
                        update_count += 1
                if update_count:
                    groups_coll.update_one({'name': group_name}, {'$set': {'users': group['users']}})
                return await msg.reply(f'removed {update_count} users from group {group_name}')
        elif args[0] in ('rename', 'revert'):
            group_name = args[1]
            group = groups_coll.find_one({'name': group_name})
            if group is None:
                raise RuntimeError('That group does not exist')
            new_name_choices = ' '.join(args[2:]).split('|')
            count = 0
            invalid_uids = []
            failed_renames = []
            for uid in group['users']:
                user = globals.bot.get_user(int(uid))
                if user is not None:
                    member = msg.guild.get_member(int(uid))
                    renamed_user = users_coll.find_one({'uid': uid})
                    old_name = member.nick
                    new_name = random.choice(new_name_choices)
                    if renamed_user is not None:
                        if renamed_user['new_name'] == member.nick:
                            old_name = renamed_user['old_name']
                    try:
                        if args[0] == 'rename':
                            if member.nick != new_name:
                                await member.edit(nick=new_name)
                                count += 1
                            users_coll.update_one({'uid': uid}, {'$set': {'uid': uid, 'old_name': old_name, 'new_name': new_name}}, upsert=True)
                        elif args[0] == 'revert':
                            if member.nick != old_name:
                                await member.edit(nick=old_name)
                                count += 1
                            users_coll.delete_one({'uid': uid})
                    except discord.HTTPException:
                        failed_renames.append(member.mention)
                else:
                    invalid_uids.append(uid)
            response = f'renamed {count} users'
            if invalid_uids:
                response += '\n failed to find the following users: ' + ' '.join(invalid_uids)
            if failed_renames:
                response += '\n failed to rename the following users: ' + ' '.join(failed_renames)
            return await msg.reply(response)
        return False
