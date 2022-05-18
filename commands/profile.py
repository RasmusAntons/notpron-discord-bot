import discord
from commands.command import Command, Category
import globals
import aiohttp


class ProfileCommand(Command):
    name = 'profile'
    category = Category.UTILITY
    arg_range = (0, 1)
    description = 'Show enigmatics.org profile'
    arg_desc = '[@user]'

    async def execute(self, args, msg):
        target_user = msg.mentions[0] if len(msg.mentions) > 0 else msg.author
        async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(sock_connect=3, sock_read=10)) as client:
            enigmatics_url = globals.conf.get(globals.conf.keys.ENIGMATICS_URL)
            async with client.get(f'{enigmatics_url}/profile_json/{target_user.id}') as res:
                if res.status != 200:
                    await msg.reply('That discord user is not linked to an enigmatics.org account')
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
        await msg.reply(embed=embed)
