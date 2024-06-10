import time
import discord
import config
from discord import app_commands
from discord.ext import commands

import globals


class SoftbanCog(commands.Cog, name='Softban', description='quarantine users'):
    def __init__(self):
        self.coll = globals.bot.db['softban']
        self.coll.create_index('uid')

    @app_commands.command(name='softban', description='quarantine user')
    async def softban(self, interaction: discord.Interaction, member: discord.Member):
        if not await config.is_trusted_user(interaction.user):
            await interaction.response.send_message('permission denied', ephemeral=True)
            return
        if self.coll.find_one({'uid': member.id}) is not None:
            await interaction.response.send_message('user is already softbanned, use softunban first', ephemeral=True)
            return
        await interaction.response.send_message(f'softbanning {member.mention}...', ephemeral=True)
        previous_roles = [role for role in member.roles if role.is_assignable()]
        previous_role_ids = [role.id for role in previous_roles]
        self.coll.insert_one({'uid': member.id, 'by': interaction.user.id, 'ts': time.time(), 'roles': previous_role_ids})
        quarantine_role = discord.utils.get(member.guild.roles, id=globals.bot.conf.get(globals.bot.conf.keys.QUARANTINE_ROLE))
        if previous_roles:
            await member.remove_roles(*previous_roles, reason=f'softban by {interaction.user.name}')
        if quarantine_role:
            await member.add_roles(quarantine_role, reason=f'softban by {interaction.user.name}')
        await interaction.edit_original_response(content='ok')
        mod_channel = discord.utils.get(interaction.guild.channels, id=globals.bot.conf.get(globals.bot.conf.keys.MOD_CHANNEL))
        if mod_channel:
            await mod_channel.send(f'{member.mention} has been softbanned by {interaction.user.mention}')

    @app_commands.command(name='softunban', description='un-quarantine user')
    async def softunban(self, interaction: discord.Interaction, member: discord.Member):
        if not await config.is_trusted_user(interaction.user):
            await interaction.response.send_message('permission denied', ephemeral=True)
            return
        await interaction.response.send_message(f'softunbanning {member.mention}...', ephemeral=True)
        if (ban := self.coll.find_one({'uid': member.id})) is not None:
            self.coll.delete_one({'uid': member.id})
            previous_role_ids = ban.get('roles')
            if previous_role_ids:
                previous_roles = [member.guild.get_role(role_id) for role_id in previous_role_ids]
                await member.add_roles(*previous_roles, reason=f'softunban by {interaction.user.name}')
        quarantine_role = discord.utils.get(member.guild.roles, id=globals.bot.conf.get(globals.bot.conf.keys.QUARANTINE_ROLE))
        if quarantine_role:
            await member.remove_roles(quarantine_role, reason=f'softunban by {interaction.user.name}')
        await interaction.edit_original_response(content='ok')
        mod_channel = discord.utils.get(interaction.guild.channels, id=globals.bot.conf.get(globals.bot.conf.keys.MOD_CHANNEL))
        if mod_channel:
            await mod_channel.send(f'{member.mention} has been softunbanned by {interaction.user.mention}')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self._find_ban(member.id):
            quarantine_role = discord.utils.get(member.guild.roles, id=globals.bot.conf.get(globals.bot.conf.keys.QUARANTINE_ROLE))
            await member.add_roles(quarantine_role, reason=f'softban by {interaction.user.name}')
