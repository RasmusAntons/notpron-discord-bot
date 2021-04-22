from listeners import MemberJoinListener
import discord
import globals


class DefaultRoleListener(MemberJoinListener):
    async def on_member_join(self, member):
        default_role_id = globals.conf.get(globals.conf.keys.DEFAULT_ROLE)
        if default_role_id:
            role = discord.utils.get(member.guild.roles, id=default_role_id)
            if role is None:
                return
            await member.add_roles(role)
