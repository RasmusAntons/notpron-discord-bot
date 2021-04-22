import random
import globals
from listeners import MessageListener


def sus_resp(username):
    n_impostors = random.randint(1, 2)
    was_impostor = random.randint(0, 1)
    n = max(1, (len(username) - 8) // 2)
    article = "An" if n_impostors > was_impostor else "The"
    reveal = f'{username} was not {article} Impostor.{"　 。　."[:-n]}'
    plural_s = 's' if n_impostors - was_impostor != 1 else ''
    conjugation_s = 's' if n_impostors - was_impostor == 1 else ''
    remaining = f'{n_impostors - was_impostor} Impostor{plural_s} remain{conjugation_s}'
    text = f'. 　　　。　　　　•　 　ﾟ　　。 　　.\n\n' \
           f'　　　.　　　 　　.　　　　　。　　 。　. 　\n\n' \
           f'.　　 。　　　　　 ඞ 。 . 　　 • 　　　　•\n\n' \
           f'{"    　　ﾟ　　  "[:-n]}{reveal}\n\n' \
           f'　　\'　　　 {remaining} 　 　　。\n\n' \
           f'　　ﾟ　　　.　　　. ,　　　　.　 .\n\n'
    return text


class AmongUsListener(MessageListener):
    async def on_message(self, msg):
        if not globals.conf.list_contains(globals.conf.keys.CHANNELS, msg.channel.id):
            return
        prefix = globals.conf.get(globals.conf.keys.PREFIX)
        if not msg.content.startswith(prefix) and 'sus' in msg.content.split(' ') and len(msg.mentions) == 1:
            if '@everyone' not in msg.content and '@here' not in msg.content:
                await msg.channel.send(sus_resp(msg.mentions[0].name))
