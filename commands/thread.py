from commands.command import Command


class ThreadCommand(Command):
    name = 'thread'
    arg_range = (1, 2)
    description = 'request a DM with a link to the forum thread to a level'
    arg_desc = '<level name>'

    async def execute(self, args, msg):
        n = ''.join(args).replace('-', 'minus ')
        thread = self.bot.config.get_thread(n)
        if thread is None:
            res = "No thread with that name found"
        else:
            res = f'Level {n}: {thread}'
        dm_channel = await self.bot.get_dm_channel(msg.author)
        await dm_channel.send(res)
