from commands.command import Command, Category
import discord
import config
import globals
from listeners import ReactionListener


class SolverCommand(Command, ReactionListener):
    name = 'solver'
    category = Category.NOTPRON
    arg_range = (1, 3)
    description = 'announce notpron solver'
    arg_desc = '[user id | name] <solver number>'
    unconfirmed = {}

    async def check(self, args, msg, test=True):
        return await super().check(args, msg, test) and await config.is_mod(msg.author)

    @staticmethod
    def ordinal(n):
        return "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])

    async def execute(self, args, msg):
        solver_nr = int(args[-1])
        if len(args) == 1:
            description = f'Notpron has just been completed for the {self.ordinal(solver_nr)} time! Congratulations'
            solver = None
        else:
            try:
                guild = await config.get_main_guild()
                solver = await guild.fetch_member(int(args[0]))
                description = f'Congratulations {solver.mention},' \
                              f'the {self.ordinal(solver_nr)} person to complete Notpron.'
            except (discord.HTTPException, ValueError) as e:
                name = discord.utils.escape_markdown(' '.join(args[:-1]))
                description = f'Congratulations **{name}**, the {self.ordinal(solver_nr)} person to complete Notpron.'
                solver = None
        embed = discord.Embed(title=f'New Solver', description=description,
                              color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
        if solver:
            embed.set_thumbnail(url=solver.avatar_url_as(size=128))
        announcement_chid = globals.conf.get(globals.conf.keys.ANNOUNCEMENT_CHANNEL)
        if announcement_chid is None:
            raise RuntimeError('Announcement channel not configured.')
        announce_ch = globals.bot.get_channel(announcement_chid)
        prompt = await msg.channel.send(f'send this to {announce_ch.mention}, {msg.author.mention}?', embed=embed)
        await prompt.add_reaction('✅')
        await prompt.add_reaction('❌')
        self.unconfirmed[prompt.id] = {'text': None, 'channel': announce_ch, 'embed': embed, 'author': msg.author}

    async def on_reaction_add(self, reaction, user):
        confirming = self.unconfirmed.get(reaction.message.id)
        if confirming and user.id == confirming.get('author').id:
            if reaction.emoji == '❌':
                del self.unconfirmed[reaction.message.id]
                await reaction.message.delete()
            elif reaction.emoji == '✅':
                ch = confirming['channel']
                msg = await ch.send(confirming.get('text'), embed=confirming.get('embed'))
                if ch.is_news():
                    await msg.publish()
                del self.unconfirmed[reaction.message.id]
                await reaction.message.delete()
            else:
                await reaction.message.channel.send(f'that\'s a stupid emoji???')
            return
        elif confirming:
            await reaction.message.channel.send(f'{user.mention}, you are {user.id} and not {confirming.get("author").id}!')

    async def on_reaction_remove(self, reaction, user):
        pass
