from commands.command import Command
from pytimeparse.timeparse import timeparse
from discord.utils import escape_markdown, escape_mentions
import datetime


class PurgeCommand(Command):
    name = 'purge'
    arg_range = (1, 99)
    description = 'purge messages'
    arg_desc = '[mention...] [number | duration]'
    unconfirmed = {}

    def __init__(self, bot):
        super().__init__(bot)
        bot.reaction_listeners.add(self)

    async def check(self, args, msg):
        if msg.author.permissions_in(msg.channel).manage_messages:
            return True
        return False

    async def execute(self, args, msg):
        td = None
        n = None
        t = datetime.datetime.utcnow()
        try:
            n = int(args[-1])
            if n > 100:
                raise ValueError(f'{msg.author.mention}, I\'m not allowed to delete more than 100 messages')
            quantifier = f'the last {n} messages'
        except ValueError:
            tds = timeparse(args[-1])
            if tds:
                td = datetime.timedelta(seconds=tds)
                if tds > 1800:
                    raise ValueError(f'{msg.author.mention}, I\'m not allowed to delete more than 30 minutes')
                quantifier = f'messages of the last {td}'
            else:
                quantifier = 'all messages (up to 100)'
        if msg.mentions:
            user_str = ' by ' + ', '.join([user.display_name for user in msg.mentions])
        else:
            if not n and not td:
                await msg.channel.send(f'{msg.author.mention}, please mention users, the number or time interval of '
                                       f'messages to purge')
                return
            user_str = ''
        text = f'{msg.author.mention}, do you want to purge {quantifier}{user_str}?'
        prompt = await msg.channel.send(text)
        await prompt.add_reaction('✅')
        await prompt.add_reaction('❌')
        self.unconfirmed[prompt.id] = {'author': msg.author, 'users': msg.mentions, 'td': td, 'n': n, 't': t}

    async def on_reaction_add(self, reaction, user):
        try:
            confirming = self.unconfirmed.get(reaction.message.id)
            if confirming and user.id == confirming.get('author').id:
                if reaction.emoji == '❌':
                    del self.unconfirmed[reaction.message.id]
                    await reaction.message.delete()
                elif reaction.emoji == '✅':
                    if confirming.get('n') and confirming.get('n') < 0:
                        for _ in range(-confirming.get('n')):
                            await self.bot.markov.talk(reaction.message.channel, cont_chance=0)
                    else:
                        users = confirming.get('users')
                        after = confirming.get('t') - confirming.get('td') if confirming.get('td') else None
                        limit = confirming.get('n') if confirming.get('n') is not None else 100
                        await reaction.message.channel.purge(limit=limit,
                                                             check=lambda m: not users or m.author in users,
                                                             after=after, before=confirming.get('t'))
                    del self.unconfirmed[reaction.message.id]
                    await reaction.message.delete()
                else:
                    await reaction.message.channel.send(f'that\'s a stupid emoji???')
        except Exception as e:
            await reaction.message.channel.send(escape_markdown(escape_mentions(str(e))))
            raise e
