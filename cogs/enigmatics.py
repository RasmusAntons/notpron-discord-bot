import logging

import discord

import config
import globals
import aiohttp
from discord.ext import commands
from discord import app_commands


class EnigmaticsCog(commands.Cog, name='Enigmatics', description='enigmatics commands'):
    guild_ids = [363692038002180097]

    @commands.hybrid_command(name='profile', description='show enigmatics.org profile')
    async def colour(self, ctx: commands.Context, user: discord.Member = None) -> None:
        target_user = user or ctx.author
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(sock_connect=3, sock_read=10)) as client:
            enigmatics_url = globals.conf.get(globals.conf.keys.ENIGMATICS_URL)
            async with client.get(f'{enigmatics_url}/profile_json/{target_user.id}') as res:
                if res.status != 200:
                    await ctx.reply('That discord user is not linked to an enigmatics.org account')
                    return
                profile = await res.json()
        description = []
        if profile['colour']:
            colour = int(profile['colour'][1:], 16)
        else:
            colour = globals.conf.get(globals.conf.keys.EMBED_COLOUR)
        if profile['badges']:
            badges = []
            for badge in profile['badges']:
                badge_name = badge['name']
                emote = globals.conf.dict_get(globals.conf.keys.BADGE_EMOJI, badge_name.replace(' ', '_'))
                badges.append(f'{emote}' if emote else badge_name)
            description.append(' '.join(badges))
            description.append('')
        if profile['active_puzzles']:
            n = len(profile["active_puzzles"])
            description.append(f'{n} active puzzle{"s" if n > 1 else ""}')
        if profile['completed_puzzles']:
            n = len(profile["completed_puzzles"])
            description.append(f'{n} completed puzzle{"s" if n > 1 else ""}')
        url = f'https://enigmatics.org/profile/{profile["name"]}'
        embed = discord.Embed(title=profile["name"], url=url, description='\n'.join(description),
                              colour=colour)
        if profile['weeklies']:
            weeklies = '\n'.join([f'{name}: {points}' for name, points in profile['weeklies'].items()])
            total = sum(points for points in profile['weeklies'].values())
            embed.add_field(name=f'{total} weeklies points', value=weeklies, inline=False)
        await ctx.reply(embed=embed)

    @app_commands.command(name='sync_weekly_channels', description='sync weekly channel access')
    async def sync_weekly_channels(self, interaction: discord.Interaction, member: discord.Member) -> None:
        if not await config.is_trusted_user(interaction.user):
            await interaction.response.send_message('permission denied', ephemeral=True)
            return
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(sock_connect=3, sock_read=10)) as client:
            weeklies_url = globals.conf.get(globals.conf.keys.ENIGMATICS_URL).replace('://', '://weeklies.')
            async with client.get(f'{weeklies_url}/season_progress_json/{member.id}') as res:
                if res.status != 200:
                    await interaction.response.send_message('That discord user is not linked to an enigmatics.org account', ephemeral=True)
                    return
                season_progress = await res.json()
        solved_weeks = list(map(str, season_progress.get("solved_weeks")))
        weeklies_channels = globals.conf.get(globals.conf.keys.WEEKLIES_CHANNELS)
        if weeklies_channels is None:
            await interaction.response.send_message('Weeklies channels not configured', ephemeral=True)
        added_channels = []
        removed_channels = []
        for key, chid in weeklies_channels.items():
            channel = member.guild.get_channel(chid)
            if channel is None:
                continue
            if key in solved_weeks and not channel.permissions_for(member).read_messages:
                await channel.set_permissions(member, read_messages=True)
                added_channels.append(channel.mention)
            elif key not in solved_weeks and channel.permissions_for(member).read_messages:
                await channel.set_permissions(member, read_messages=False)
                removed_channels.append(channel.mention)
        msg = ['Synced weekly channels:']
        if added_channels:
            msg.append(f'Added {member.mention} to {", ".join(added_channels)}.')
        if removed_channels:
            msg.append(f'Removed {member.mention} from {", ".join(removed_channels)}.')
        await interaction.response.send_message('\n'.join(msg))
