import discord
import globals


description = """
"""


async def send_embed():
    ch = globals.bot.get_channel(722966982454149171)
    embed = discord.Embed(title='Select your Roles', description=description, color=0x0)
    embed.set_thumbnail(url='https://enigmatics.org/static/aawhite.png')
    embed.add_field(name='<:mc:831732941000409129> Minecraft', value='See the in-game chat', inline=False)
    embed.add_field(name='<:amongus:831735251071533086> Among Us', value='Get pinged sometimes', inline=False)
    embed.add_field(name=':underage: Nsfw', value='18+', inline=False)
    msg = await ch.send('@everyone', embed=embed)


async def edit_embed():
    ch = globals.bot.get_channel(831731239937114152)
    msg = await ch.fetch_message(831739648932970517)
    embed = discord.Embed(title='Select your Roles', description=description, color=0x0)
    embed.set_thumbnail(url='https://enigmatics.org/static/aawhite.png')
    embed.add_field(name='<:mc:831732941000409129> Minecraft', value='See the in-game chat', inline=False)
    embed.add_field(name='<:amongus:831735251071533086> Games', value='Get pinged sometimes', inline=False)
    embed.add_field(name=':film_frames: Movies', value='Get pinged sometimes', inline=False)
    await msg.edit(embed=embed)
