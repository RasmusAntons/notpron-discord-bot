from commands.command import Command, Category
from listeners import MessageListener
import config
import globals


class RegenerateCommand(Command, MessageListener):
    name = 'regenerate'
    category = Category.ADMIN
    arg_range = (0, 0)
    description = 'Regenerate markov chains.'

    async def check(self, args, msg, test=False):
        return await super().check(args, msg, test) and config.is_admin(msg.author)

    async def execute(self, args, msg):
        n = await globals.bot.markov.regenerate(msg)
        await msg.channel.send(f"finished regenerating, using {n} messages")

    async def on_message(self, msg):
        if not globals.conf.list_contains(globals.conf.keys.CHANNELS, msg.channel.id):
            return
        if globals.bot.user.mentioned_in(msg):
            if globals.bot.user.mention not in msg.content:
                return
            if '@everyone' not in msg.content and '@here' not in msg.content:
                await globals.bot.markov.talk(msg.channel, query=msg.content)


class ImitateCommand(Command):
    name = 'imitate'
    category = Category.UTILITY
    arg_range = (1, 1)
    description = 'Generate text imitating a user.'
    arg_desc = '<@user>'

    async def execute(self, args, msg):
        if msg.mentions:
            await globals.bot.markov.talk(msg.channel, user=int(msg.mentions[0].id))
        else:
            uname = args[0]
            user = msg.channel.guild.get_member_named(uname)
            if user:
                await globals.bot.markov.talk(msg.channel, user=user.id)
            else:
                try:
                    uid = int(args[0])
                    if 100000000000000 <= uid <= 9999999999999999999:
                        await globals.bot.markov.talk(msg.channel, user=uid)
                except ValueError:
                    pass
