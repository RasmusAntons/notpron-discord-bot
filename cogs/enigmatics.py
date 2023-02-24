import discord
import globals
import aiohttp
from discord.ext import commands


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
