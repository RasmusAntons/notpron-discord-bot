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

    def _is_banned(self, uid):
        return self.coll.find_one({'uid': uid}) is not None

    @app_commands.command(name='softban', description='quarantine user')
    async def softban(self, interaction: discord.Interaction, member: discord.Member):
        if not await config.is_trusted_user(interaction.user):
            await interaction.response.send_message('permission denied', ephemeral=True)
            return
        if not self._is_banned(member.id):
            self.coll.insert_one({'uid': member.id, 'by': interaction.user.id, 'ts': time.time()})
        quarantine_role = discord.utils.get(member.guild.roles, id=globals.bot.conf.get(globals.bot.conf.keys.QUARANTINE_ROLE))
        if quarantine_role:
            await member.add_roles(quarantine_role, reason=f'softban by {interaction.user.name}')
        await interaction.response.send_message('ok', ephemeral=True)
        mod_channel = discord.utils.get(interaction.guild.channels, id=globals.bot.conf.get(globals.bot.conf.keys.MOD_CHANNEL))
        if mod_channel:
            await mod_channel.send(f'{member.mention} has been softbanned by {interaction.user.mention}')

    @app_commands.command(name='softunban', description='un-quarantine user')
    async def softunban(self, interaction: discord.Interaction, member: discord.Member):
        if not await config.is_trusted_user(interaction.user):
            await interaction.response.send_message('permission denied', ephemeral=True)
            return
        if self._is_banned(member.id):
            self.coll.delete_one({'uid': member.id})
        quarantine_role = discord.utils.get(member.guild.roles, id=globals.bot.conf.get(globals.bot.conf.keys.QUARANTINE_ROLE))
        if quarantine_role:
            await member.remove_roles(quarantine_role, reason=f'softunban by {interaction.user.name}')
        await interaction.response.send_message('ok', ephemeral=True)
        mod_channel = discord.utils.get(interaction.guild.channels, id=globals.bot.conf.get(globals.bot.conf.keys.MOD_CHANNEL))
        if mod_channel:
            await mod_channel.send(f'{member.mention} has been softunbanned by {interaction.user.mention}')

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if self._is_banned(member.id):
            quarantine_role = discord.utils.get(member.guild.roles, id=globals.bot.conf.get(globals.bot.conf.keys.QUARANTINE_ROLE))
            await member.add_roles(quarantine_role, reason=f'softban by {interaction.user.name}')
