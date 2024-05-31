import discord
from discord import app_commands
from discord.ext import commands

class SayCog(commands.Cog, name='Say', description='say something'):
    @app_commands.command(name='say', description='say something')
    async def say(self, interaction: discord.Interaction, text: str, attachment: discord.Attachment = None):
        if attachment is not None:
            await interaction.response.defer(ephemeral=True)
            file = await attachment.to_file()
            await interaction.channel.send(text, file=file)
            await interaction.followup.send('ok', ephemeral=True)
        else:
            await interaction.channel.send(text)
            await interaction.response.send_message('ok', ephemeral=True)
