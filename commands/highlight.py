from commands.command import Command
import json
import discord
import re
from discord.utils import escape_markdown, escape_mentions


class HighlightCommand(Command):
    name = 'highlight'
    aliases = ['hl']
    arg_range = (1, 99)
    description = 'manage notifications for words or phrases'
    arg_desc = 'add <regular expression...> | list | remove <number>'

    def __init__(self, bot):
        super().__init__(bot)
        bot.message_listeners.add(self)
        with open('highlights.json') as f:
            self.highlights = json.load(f)

    @staticmethod
    def inline_code(text):
        while '``' in text:
            text = text.replace('``', '`​`')
        return f'``{text}``'

    async def execute(self, args, msg):
        user_hl = self.highlights.get(str(msg.author.id), [])
        if args[0] == 'add':
            new_hl = ' '.join(args[1:])
            if not new_hl:
                raise RuntimeError(f'invalid highlight: {new_hl}')
            if new_hl in user_hl:
                await msg.channel.send(f'{msg.author.mention} you already have this highlight configured.')
                return
            else:
                user_hl.append(new_hl)
                self.highlights[str(msg.author.id)] = user_hl
                with open('highlights.json', 'w') as f:
                    json.dump(self.highlights, f)
                await msg.channel.send(f'{msg.author.mention} added highlight {self.inline_code(new_hl)}')
        elif args[0] == 'list':
            embed = discord.Embed(colour=self.bot.config.get_embed_colour())
            text = [f'{msg.author.mention}']
            for i, hl in enumerate(user_hl):
                text.append(f'{i + 1}. {self.inline_code(hl)}')
            if not user_hl:
                text.append(f'None')
            embed.add_field(name='Highlights', value='\n'.join(text), inline=False)
            await msg.channel.send(embed=embed)
        elif args[0] == 'remove':
            n = int(' '.join(args[1:])) - 1
            if n < 0:
                raise RuntimeError(f'invalid index: {" ".join(args[1:])}')
            hl = user_hl.pop(n)
            with open('highlights.json', 'w') as f:
                json.dump(self.highlights, f)
            await msg.channel.send(f'{msg.author.mention} removed highlight {self.inline_code(hl)}')

    async def on_message(self, msg):
        for uid, user_hl in self.highlights.items():
            for hl in user_hl:
                text = msg.content
                if msg.author.id == 417012703035392001 and ':' in text:  # Minecraft
                    text = ':'.join(text.split(':')[1:])
                elif msg.author.bot:
                    return
                try:
                    if re.search(hl, text):
                        member = msg.guild.get_member(uid) or await msg.guild.fetch_member(uid)
                        if not member or not msg.channel.permissions_for(member).read_messages:
                            return
                        ch = await self.bot.get_dm_channel(member)
                        embed = discord.Embed()
                        embed.set_author(name=f'{msg.author.display_name}', icon_url=f'{msg.author.avatar_url_as(size=32)}')
                        link = f'\n[link]({msg.jump_url})'
                        if len(msg.content) > (1024 - len(link)):
                            text = f'{msg.content[:(1021 - len(link))]}...{link}'
                        else:
                            text = f'{msg.content}{link}'
                        embed.add_field(name=f'#{msg.channel.name}', value=text, inline=False)
                        embed.set_footer(text=f'matched this rule: {hl}')
                        await ch.send(embed=embed)
                        break
                except re.error as e:
                    user = self.bot.get_user(uid) or await self.bot.fetch_user(uid)
                    ch = await self.bot.get_dm_channel(user)
                    await ch.send(f'Error in rule {self.inline_code(hl)}: {escape_markdown(escape_mentions(str(e)))}')
