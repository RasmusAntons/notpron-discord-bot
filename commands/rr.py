from commands.command import Command
import asyncio
import random
import discord


class RrCommand(Command):
    name = 'rr'
    arg_range = (0, 0)
    description = 'play a round of russian roulette'
    state = 0
    guilds = [363692038002180097]

    async def execute(self, args, msg):
        loadtxt = ' loads one bullet into the revolver and' if self.state == 0 else ''
        await msg.channel.send(f'{msg.author.display_name}{loadtxt} slowly pulls the trigger...')
        await msg.channel.trigger_typing()
        await asyncio.sleep(1)
        if random.randrange(6 - self.state) == 0:
            await msg.channel.send(f'{msg.author.display_name} **died**')
            try:
                await msg.author.edit(nick=f'dead')
            except discord.HTTPException:
                pass
            self.state = 0
        else:
            self.state += 1
            await msg.channel.send(
                f'*click* - empty chamber. {msg.author.display_name} will live another day. Who\'s next? Misses since last death: {self.state}')
