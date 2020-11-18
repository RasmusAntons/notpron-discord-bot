from commands.command import Command


class HintCommand(Command):
    name = 'hint'
    arg_range = (1, 1)
    description = 'request a DM with the official hint for a level'
    arg_desc = '<level name>'
    guilds = [363692038002180097]

    async def execute(self, args, msg):
        hint = None
        try:
            n = int(args[0])
            hint = self.bot.config.get_hint(n)
        except ValueError:
            pass
        if hint is None:
            res = ['Type !hint <level number from 1-79> for a level specific hint. No hints for 80 and beyond!']
        else:
            res = ['Official hints for Notpron']
            for line in hint:
                res.append(f'{n}: {line}')
        dm_channel = await self.bot.get_dm_channel(msg.author)
        for line in res:
            await dm_channel.send(line)
