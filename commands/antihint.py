from commands.command import Command


class AntiHintCommand(Command):
    name = 'antihint'
    arg_range = (1, 1)
    description = 'request a DM with an antihint for a level'
    arg_desc = '<level name>'
    guilds = [363692038002180097]

    async def execute(self, args, msg):
        hint = None
        try:
            n = int(args[0])
            hint = self.bot.config.get_antihint(n)
        except ValueError:
            pass
        if hint is None:
            res = ['Type !hint <level number from 1-79> for a level specific hint. No hints for 80 and beyond!']
        else:
            res = ['Official antihints for Notpron.', 'These are not REAL hints, just from non-walkthrough.',
                   'In other words, for fun, not for real help.']
            for line in hint:
                res.append(f'{n}: {line}')
        dm_channel = await self.bot.get_dm_channel(msg.author)
        for line in res:
            await dm_channel.send(line)
