import discord
import globals

async def create_weeklies_channels():
    channel_category: discord.CategoryChannel = globals.bot.get_channel(1193260708570349682)
    for channel in channel_category.channels:
        await channel.delete(reason='creating new weekly channels')
    new_channel_ids = {}
    weeklies_channel_admin = channel_category.guild.get_role(859426210638331966)
    overwrites = {
        channel_category.guild.default_role: discord.PermissionOverwrite(read_messages=False),
        weeklies_channel_admin: discord.PermissionOverwrite(read_messages=True),

    }
    for week_number in range(1, 11):
        new_channel = await channel_category.guild.create_text_channel(f'week-{week_number}', category=channel_category, overwrites=overwrites)
        new_channel_ids[f'{week_number}'] = new_channel.id
    print(f'weekly_channels: {new_channel_ids}')
