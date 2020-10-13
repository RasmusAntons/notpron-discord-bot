from commands.command import Command
import discord


class SolverCommand(Command):
    name = 'solver'
    arg_range = (1, 3)
    description = 'announce notpron solver'
    arg_desc = '[user id | name] <solver number>'
    unconfirmed = {}

    def __init__(self, bot):
        super().__init__(bot)
        bot.reaction_listeners.add(self)

    async def check(self, args, msg):
        if self.bot.config.get_mod_role() not in [role.id for role in msg.author.roles]:
            return False
        return True

    async def execute(self, args, msg):
        solver_nr = int(args[-1])
        ordinal = lambda n: "%d%s" % (n, "tsnrhtdd"[(n // 10 % 10 != 1) * (n % 10 < 4) * n % 10::4])
        if len(args) == 1:
            description = f'Notpron has just been completed for the {ordinal(solver_nr)} time! Congratulations'
            solver = None
        else:
            try:
                guild = self.bot.get_guild(self.bot.config.get_guild())
                solver = await guild.fetch_member(int(args[0]))
                description = f'Congratulations {solver.mention}, the {ordinal(solver_nr)} person to complete Notpron.'
            except (discord.HTTPException, ValueError) as e:
                name = discord.utils.escape_markdown(' '.join(args[:-1]))
                description = f'Congratulations **{name}**, the {ordinal(solver_nr)} person to complete Notpron.'
                solver = None
        embed = discord.Embed(title=f'New Solver', description=description, color=self.bot.config.get_embed_colour())
        if solver:
            embed.set_thumbnail(url=solver.avatar_url_as(size=128))
        announce_ch = self.bot.get_channel(self.bot.config.get_announcements_channel())
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
