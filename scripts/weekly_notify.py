import discord
import discord.errors
import globals
from utils import get_user, get_channel


text = ":point_right: Congratulations on your #1 position on the weekly puzzle leaderboard. :star_struck: " \
       "For your dedication and determination, you may submit your puzzle at any time starting now, " \
       "while other submissions will not start being reviewed for another 10 days.\n\n" \
       ":point_right: Puzzle guidelines: Feel free to use your creativity however you'd like to make a fun " \
       "and unique submission, but remember that participants will only have a week to solve. " \
       "The tools required should only be the ones found in other typical internet riddles " \
       "(gimp, audacity, cipher converters). Some people don't have knowledge that is too technical, " \
       "so while your puzzles can be hard, please keep them accessible.\n\n" \
       ":point_right: Once you're ready to submit your weekly, ask a weekly mod if they are available to review it " \
       "BEFORE sending it.\n" \
       "This year's vetters are RedRabbit, Catz, owlbot, Ronald_D_D and weaver."


async def weekly_notify():
    uids = [258360321431961615, 355560197152047105, 246354921761406978, 429458290477629482, 480374028880838657, 746457711926968470, 515947127432806410, 177438227563675648, 440949067015782401, 277336623996469249, 697331345843814430, 244097774675689473, 349992977621581844, 364055767302799360, 441958578962694144, 430852316363620363, 704372346995081246]
    embed = discord.Embed(title=':shushing_face: Top Secret! :shushing_face:', colour=0xfe1b07)
    embed.description = text
    log_channel = await get_channel(818143082427580456)
    for uid in uids:
        user = await get_user(uid)
        ch = user.dm_channel or await user.create_dm()
        try:
            await ch.send(embed=embed)
        except discord.errors.Forbidden:
            await log_channel.send(f'Failed to dm {user.mention}.')

