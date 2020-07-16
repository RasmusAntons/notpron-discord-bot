import argparse
from config import Config
import discord
from queue import Queue


class ExecDiscordConnection(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.playing = False
        self.tts_n = 0
        self.post_tts_delay = None
        self.tts_queue = Queue()

    async def on_ready(self):
        print('I\'m in.')

        """
        ch = self.get_channel(729417691206778910)
        # msg = await ch.fetch_message(722981667488399420)
        # roles = [722970084359798816, 722970087518371880, 722970089804136518, 722970091955814476, 722970093960691733, 722970096204644365, 722970102370140271]
        # description = '\n'.join([discord.utils.get(ch.guild.roles, id=role).mention for role in roles])
        user = self.get_user(586321204047249423)
        description = f'`too many hints` by {user.mention}'
        embed = discord.Embed(title='ɴᴇᴡ ᴡᴇᴇᴋʟʏ ᴘᴜᴢᴢʟᴇ', description=description, color=0xa6ce86)
        embed.set_thumbnail(url='https://cdn.discordapp.com/avatars/586321204047249423/bf58bbd2ee7c9e2df2e00501879aa9f2.png?size=128')
        #embed.add_field(name="Week 3", value=f"`Sol` by {user.mention}", inline=False)
        #embed.add_field(name="portuguese", value=":flag_br:", inline=False)
        #embed.add_field(name="(18+) nsfw (sexual content)", value=":underage:", inline=False)
        #embed.add_field(name="(18+) wasteland (scarcely moderated content, cursed images)", value=":nauseated_face:", inline=False)
        embed.set_footer(text='To learn how to turn these notifications off, look at the message above.')
        msg = await ch.send('@everyone', embed=embed)
        # await msg.edit(embed=embed)
        #await msg.add_reaction('<:mc:721206165605974019>')
        #await msg.add_reaction('🇧🇷')
        #await msg.add_reaction('🔞')
        #await msg.add_reaction('🤢')
        oldmsg = await ch.fetch_message(729486803324764180)
        await oldmsg.delete()
        """

        ch = self.get_channel(722966982454149171)
        #user = await self.fetch_user(200329561437765652)
        #txt = base64.b64encode(user.name.encode('utf-8'))
        #await self.user.edit(username="")
        await ch.send('uwu')

        #ch = self.get_channel(610041285633376276)
        #text = '```\nOwO what\'s this?\n```\n:grey_question: <https://weeklies.3po.ch/> :grey_question:\n\nAttention, @everyone! The **summer weekly riddles** by the Notpron Discord community have officially begun. Visit the website, read the "ABOUT" page, log in with your Discord account and solve the first riddle!'
        #await ch.send(text)


def run_bot(config):
    disc = ExecDiscordConnection(config)
    disc.loop.run_until_complete(disc.login(config.get_discord_token()))
    disc.loop.run_until_complete(disc.connect())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='config.json', help='config json')
    args = parser.parse_args()
    run_bot(Config(args.config))
