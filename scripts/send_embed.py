import discord
import globals

description = """
✧ announcement! ✧

:point_right: Weekly Puzzles are back. Starting this summer, for 20 weeks, a puzzle will come out each week at the same time and be available for exactly 7 days, after which a solution will be released. Solve the puzzles at a relaxed pace or fight to be the first solver every week - it's up to you and your playstyle! As of right now, we are looking for puzzle submissions! See more information below. 

:point_right: The puzzles will start in late June. Please use the reacts on this message to vote on your preferred time.

✧ what's new ✧

:point_right:  New domain, same website! Visit https://weeklies.enigmatics.org/ and use the Login button on the left. You may notice that the new season demo is up. All solutions will be inputted in such a box under a puzzle.

:point_right:  After logging in, you will have access to your own user profile which will display any previous and future weekly badges as well as other site events. More profile functionality is coming soon!

✧ puzzle creation ✧

:point_right:  Puzzle guidelines: Feel free to use your creativity however you'd like to make fun and unique submission, but remember that participants will only have a week to solve. The tools required should only be the ones found in other typical internet riddles (gimp, audacity, cipher converters). Remember some people don't have knowledge that is too technical, so while your puzzles can be hard, please keep them accessible. 

:point_right:  Once you're ready to submit your weekly, ask a weekly mod if they are available to review it BEFORE sending it. 
this year's vetters are RedRabbit, Catz, owlbot, Ronald_D_D and weaver. The deadline for submitting is June 10th.

:one: FRIDAY 18:00 (UTC) ✧ :two: SATURDAY 18:00 (UTC) ✧ :three: SATURDAY 22:00 (UTC) ✧ :four: SUNDAY 22:00 (UTC)
"""

description_notpron = """
✧ announcement! ✧

:point_right: Weekly Puzzles are back. Starting this summer, for 20 weeks, a puzzle will come out each week at the same time and be available for exactly 7 days, after which a solution will be released. Solve the puzzles at a relaxed pace or fight to be the first solver every week - it's up to you and your playstyle! As of right now, we are looking for puzzle submissions! See more information below. 

:point_right: The puzzles will start in late June. Please use the reacts on this message to vote on your preferred time.

✧ what's new ✧

:point_right:  New domain, same website! Visit https://weeklies.enigmatics.org/ and use the Login button on the left. You may notice that the new season demo is up. All solutions will be inputted in such a box under a puzzle.

:point_right:  After logging in, you will have access to your own user profile which will display any previous and future weekly badges as well as other site events. More profile functionality is coming soon!

:bangbang:  To encourage the participation of all puzzling enthusiasts (inside and outside the Notpron Community), we're migrating Weeklies to a new dedicated server. Solvers will be announced there and pings will no longer appear in this community. Join us here: https://discord.gg/GQqHc9acYN :bangbang: 
:point_right:  You can find out more about puzzle submissions in our new server.

:one: FRIDAY 18:00 (UTC) ✧ :two: SATURDAY 18:00 (UTC) ✧ :three: SATURDAY 22:00 (UTC) ✧ :four: SUNDAY 22:00 (UTC)
"""

async def send_embed():
    ch = globals.bot.get_channel(791704264111161375)
    embed = discord.Embed(title='', description=description, color=0x0)
    msg = await ch.send('@everyone', embed=embed)
    for num_react in ['1️⃣', '2️⃣', '3️⃣', '4️⃣']:
        await msg.add_reaction(num_react)
