import argparse
from config import Config
import discord
from queue import Queue
import api
import asyncio
from markov import Markov


class ExecDiscordConnection(discord.Client):
    def __init__(self, config):
        super().__init__()
        self.config = config
        self.playing = False
        self.tts_n = 0
        self.post_tts_delay = None
        self.tts_queue = Queue()
        self.markov = Markov(self, config)
        self.api_server = api.ApiServer(self, config)

    async def background_task(self):
        ch = self.get_channel(453284405402927104)
        usr = await ch.guild.fetch_member(441958578962694144)
        while True:
            await ch.send(f'{usr.mention}')
            await self.markov.talk(ch, user=441958578962694144, cont_chance=0)
            await asyncio.sleep(60)

    async def on_ready(self):
        print('I\'m in.')
        # self.loop.create_task(self.background_task())
        #activity = discord.Activity(type=discord.ActivityType.listening, name="!hint | !antihint")
        #await self.change_presence(activity=activity)


        #ch = self.get_channel(363692038002180099)
        #await ch.send('<:monomi:779458067934085150>')
        ch = self.get_channel(721487932606906399)
        msg = await ch.fetch_message(722981667488399420)
        roles = [722970084359798816, 722970087518371880, 722970089804136518, 722970091955814476, 722970093960691733, 722970096204644365, 722970102370140271]
        description = '\n'.join([discord.utils.get(ch.guild.roles, id=role).mention for role in roles])
        # user = self.get_user(586321204047249423)
        # description = f'`too many hints` by {user.mention}'
        embed = discord.Embed(title='Channel Select', description=description, color=0xa6ce86)
        embed.set_thumbnail(url='https://cdn.discordapp.com/attachments/722266017752940685/722965566708514846/pic2.png')
        embed.add_field(name="minecraft", value=f"<:mc:721206165605974019>", inline=False)
        embed.add_field(name="portuguese", value=":flag_br:", inline=False)
        #embed.add_field(name="(18+) nsfw (sexual content)", value=":underage:", inline=False)
        embed.add_field(name="(18+) wasteland (scarcely moderated content, cursed images)", value=":nauseated_face:", inline=False)
        embed.add_field(name="(18+) adult-lounge (sensitive topics, not porn)", value=":coffee:", inline=False)
        embed.add_field(name="tech", value=":robot:", inline=False)
        embed.add_field(name="gamer (no channel - taggable summoning role)", value=":video_game:", inline=False)
        embed.add_field(name="workout (no channel - taggable summoning role)", value=":sweat:", inline=False)
        # embed.set_footer(text='To learn how to turn these notifications off, look at the messagce above.')
        # msg = await ch.send('@everyone', embed=embed)
        await msg.edit(embed=embed)
        #await msg.add_reaction('<:mc:721206165605974019>')
        #await msg.add_reaction('🇧🇷')
        #await msg.add_reaction('🔞')
        #await msg.add_reaction('🤢')
        #await msg.add_reaction('☕')
        #await msg.add_reaction('🤖')
        #await msg.add_reaction('🎮')
        await msg.add_reaction('😓')
        #oldmsg = await ch.fetch_message(729486803324764180)
        #await oldmsg.delete()


        #ch = self.get_channel(363692038002180099)
        #user = await self.fetch_user(720786426660388925)
        #msg = await ch.fetch_message(750017650708709427)
        #await msg.edit(content=f"てめぇは少し基本的だと思います {user.mention}")
        #user = await self.fetch_user(200329561437765652)
        #txt = base64.b64encode(user.name.encode('utf-8'))
        #await self.user.edit(username="")
        #await ch.send(embed=weather.get_weather_msg('Braunschweig', self.config.get_owm_key()))

        #ch = self.get_channel(610041285633376276)
        #text = '```\nOwO what\'s this?\n```\n:grey_question: <https://weeklies.3po.ch/> :grey_question:\n\nAttention, @everyone! The **summer weekly riddles** by the Notpron Discord community have officially begun. Visit the website, read the "ABOUT" page, log in with your Discord account and solve the first riddle!'
        #await ch.send(text)


def run_bot(config):
    disc = ExecDiscordConnection(config)
    disc.loop.run_until_complete(disc.login(config.get_discord_token()))
    disc.loop.create_task(disc.api_server.coro)
    disc.loop.run_until_complete(disc.connect())


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', '-c', type=str, default='config.json', help='config json')
    args = parser.parse_args()
    run_bot(Config(args.config))
