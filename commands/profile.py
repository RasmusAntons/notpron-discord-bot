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
        embed = discord.Embed(title=f'{profile["name"]}', url=profile['url'])
        if profile['badges']:
            badges = '\n'.join([badge['name'] for badge in profile['badges']])
            embed.add_field(name='badges', value=badges, inline=False)
        if profile['active_puzzles']:
            active_puzzles = '\n'.join(f'{puzzle}: {note}' if note else puzzle
                                       for puzzle, note in profile['active_puzzles'].items())
            embed.add_field(name='active puzzles', value=active_puzzles, inline=False)
        if profile['completed_puzzles']:
            completed_puzzles = '\n'.join(f'{puzzle}: {note}' if note else puzzle
                                          for puzzle, note in profile['completed_puzzles'].items())
            embed.add_field(name='completed puzzles', value=completed_puzzles, inline=False)
        if profile['weeklies']:
            weeklies = '\n'.join([f'{name}: {points}' for name, points in profile['weeklies'].items()])
            embed.add_field(name='weeklies', value=weeklies, inline=False)
        await msg.reply(embed=embed)
