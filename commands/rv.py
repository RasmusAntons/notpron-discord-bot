import io

import discord
import random
from commands.command import Command, Category
import os
import shutil
import math
import datetime
from PIL import Image, ImageOps, ImageDraw, ImageFont
from utils import get_user
import globals


def gen_thumbs(images, cols, s=(250, 250)):
    bw = 2
    pad = 5
    title = 28
    rows = math.ceil(len(images) / cols)
    res = Image.new('RGB', (cols * s[0] + 2 * pad, rows * s[1]), (54, 57, 63))
    for i, image in enumerate(images):
        im = Image.open(image)
        im.thumbnail((s[0] - 2 * bw - 2 * pad, s[1] - 2 * bw - 2 * pad - title))
        th = ImageOps.expand(im, border=bw, fill='lightgray')
        x_off = (s[0] - th.width) // 2
        x = (i % cols) * s[0] + pad + x_off
        y = (i // cols) * (s[1]) + pad
        res.paste(th, (x, y + title))
        draw = ImageDraw.Draw(res)
        font = ImageFont.truetype(r'res/DejaVuSans.ttf', 24)
        text = f'{i + 1}'
        w, h = draw.textsize(text, font=font)
        draw.text((x + (th.width - w) // 2, y), text, font=font, fill='lightgray')
    return res


class RvCommand(Command):
    name = 'rv'
    category = Category.NOTPRON
    arg_range = (1, 2)
    description = 'remote view some images'
    arg_desc = 'init | done | show <id> | cancel | solve <id> | stats | log'
    n_choices = 4

    def __init__(self):
        super().__init__()
        for coll_name in ('rv', 'rv_stats'):
            globals.bot.db[coll_name].create_index('uid', unique=True)

    async def execute(self, args, msg):
        rv_path = globals.conf.get(globals.conf.keys.RV_PATH)
        coll = globals.bot.db['rv']
        coll_logs = globals.bot.db['rv_logs']
        coll_stats = globals.bot.db['rv_stats']
        prefix = globals.conf.get(globals.conf.keys.PREFIX)
        session = coll.find_one({'uid': msg.author.id})
        await msg.channel.trigger_typing()
        if args[0] == 'stats':
            embed = discord.Embed(title=f'RV Stats', color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
            if len(msg.mentions) == 1:
                usr = msg.mentions[0]
                usr_stats = coll_stats.find_one({'uid': usr.id}) or {}
                usr_total = usr_stats.get('total', 0)
                usr_correct = usr_stats.get('correct', 0)
                usr_cancelled = usr_stats.get('cancelled', 0)
                usr_text = f'{usr_total} total attempts\n{usr_correct} successful attempts\n{usr_cancelled}' \
                           f' cancelled attempts\n{100 * usr_correct / usr_total:5.2f}% success rate'
                embed.add_field(name=usr.display_name, value=usr_text, inline=False)
            else:
                total_stats = coll_stats.aggregate([{'$group': {
                    '_id': None, 'total': {'$sum': '$total'},
                    'correct': {'$sum': '$correct'}, 'cancelled': {'$sum': '$cancelled'}
                }}]).next()
                total, correct, cancelled = total_stats['total'], total_stats['correct'], total_stats['cancelled']
                global_stats = f'{total} total attempts\n{correct} successful attempts' \
                               f'\n{cancelled} cancelled attempts\n{100 * correct / total:5.2f}% success rate'
                embed.add_field(name=f'Global', value=global_stats, inline=False)
                best_users = coll_stats.aggregate([{'$match': {'total': {'$gte': 10}}}, {'$project': {
                    'ratio': {'$divide': ['$correct', '$total']},
                    'uid': '$uid', 'total': '$total', 'correct': '$correct', 'cancelled': '$cancelled'
                }}, {'$sort': {'ratio': -1}}, {'$limit': 15}])
                lines = []
                for i, user_stats in enumerate(best_users):
                    total, correct, ratio = user_stats['total'], user_stats['correct'], user_stats['ratio']
                    user = await get_user(user_stats['uid'])
                    lines.append(f'{i + 1}. {100 * ratio:05.2f}% ({correct:2d}/{total:2d}) {user.name}')
                embed.add_field(name=f'Most successful', value='\n'.join(lines) or '-', inline=False)
                embed.set_footer(text=f'Only users with at least 10 total attempts are shown.')
            await msg.channel.send(embed=embed)
        elif args[0] == 'init':
            if session:
                code = session['code']
                await msg.reply(f'You already have the target **{code}**.'
                                f' Use `{prefix}{self.name} done` when you are ready to solve.')
            else:
                code = '-'.join([f'{random.randrange(0, 1000):03d}' for _ in range(4)])
                choices = os.listdir(rv_path)
                target = os.path.join(rv_path, random.choice(choices))
                shutil.copyfile(target, f'rv/{code}.jpg')
                coll.insert_one({'uid': msg.author.id, 'code': code, 'target': target, 't_start': datetime.datetime.utcnow()})
                await msg.reply(f'Your target is **{code}**.'
                                f' This number is randomly generated and I have copied a randomly'
                                f' chosen image into a file with the name {code}.jpg.'
                                f' Use `{prefix}{self.name} done` when you are ready to solve.')
        elif args[0] == 'done':
            if session and session.get('target'):
                selection = session.get('selection')
                code = session.get('code')
                if selection is None:
                    choices = os.listdir(rv_path)
                    selection = [session['target']]
                    while len(selection) < self.n_choices:
                        new_image = os.path.join(rv_path, random.choice(choices))
                        if new_image not in selection:
                            selection.append(new_image)
                    random.shuffle(selection)
                    coll.update_one(session, {'$set': {'selection': selection}})
                im = gen_thumbs(selection, min(5, self.n_choices), (320, 320))
                out_file = io.BytesIO()
                im.save(out_file, 'PNG')
                out_file.seek(0)
                text = f'Please identify your target image and enter its number with' \
                       f' `{prefix}{self.name} solve <id>` where <id> is the number shown above' \
                       f' the image. Use `{prefix}{self.name} show <id>` to see an image in its' \
                       f' full resolution. If there are multiple matching images, you can use' \
                       f' `{prefix}{self.name} cancel` to cancel and try another target.'
                await msg.reply(text, file=discord.File(out_file, filename=f'rv/{code}.png'))
            else:
                await msg.reply(f'You don\'t have a target yet. Use `{prefix}{self.name} init` to request one.')
        elif args[0] == 'show':
            if session and session.get('target'):
                selection = session.get('selection')
                if selection is None:
                    await msg.reply(f'You don\'t have a target selection yet.'
                                    f' Use `{prefix}{self.name} done` to get images to select'
                                    f' your target from.')
                    return
                if len(args) < 2:
                    await msg.channel.send(f' Use `{prefix}{self.name} show <id>`'
                                           f' to view one specific image.')
                    return
                img_id = int(args[1])
                if not 1 <= img_id <= self.n_choices:
                    raise ValueError('image id must be between 1 and 20')
                text = f'{msg.author.mention}, this is your option {img_id}'
                await msg.channel.send(text, file=discord.File(selection[img_id - 1]))
            else:
                await msg.reply(f'You don\'t have a target yet. Use `{prefix}{self.name} init` to request one.')
        elif args[0] == 'solve':
            if session and session.get('target'):
                code = session['code']
                selection = session.get('selection')
                if selection is None:
                    await msg.channel.send(f'{msg.author.mention} you don\'t have a target selection yet.'
                                           f' Use `{prefix}{self.name} done` to get images to select'
                                           f' your target from.')
                    return
                if len(args) < 2:
                    await msg.channel.send(f' Use `{prefix}{self.name} solve <id>` to enter your choice.')
                    return
                img_id = int(args[1])
                if not 1 <= img_id <= self.n_choices:
                    raise ValueError('image id must be between 1 and 20')
                choice = selection[img_id - 1]
                usr_stats = coll_stats.find_one({'uid': msg.author.id})
                if usr_stats is None:
                    usr_stats = {'uid': msg.author.id, 'total': 0, 'correct': 0, 'cancelled': 0}
                correct = choice == session['target']
                log_entry = {'uid': msg.author.id, 'correct': correct, 'target': session['target'],
                             'selection': selection, 't_start': session['t_start'], 't_end': datetime.datetime.utcnow()}
                if correct:
                    usr_stats['total'] = usr_stats['total'] + 1
                    usr_stats['correct'] = usr_stats['correct'] + 1
                    await msg.reply(f'Correct! This was your target. You have'
                                    f' viewed {usr_stats["correct"]}/{usr_stats["total"]} images correctly',
                                    file=discord.File(f'rv/{code}.jpg'))
                else:
                    usr_stats['total'] = usr_stats['total'] + 1
                    await msg.reply(f'Wrong. This was your target. You have'
                                    f' viewed {usr_stats["correct"]}/{usr_stats["total"]} images correctly',
                                    file=discord.File(f'rv/{code}.jpg'))
                coll_stats.replace_one({'uid': msg.author.id}, usr_stats)
                coll_logs.insert_one(log_entry)
                coll.delete_one({'uid': msg.author.id})
                os.remove(f'rv/{code}.jpg')
            else:
                await msg.reply(f'You don\'t have a target yet. Use `{prefix}{self.name} init` to request one.')
        elif args[0] == 'cancel':
            if session and session.get('target'):
                code = session['code']
                selection = session.get('selection')
                if selection is None:
                    await msg.reply(f'You don\'t have a target selection yet.'
                                    f' Use `{prefix}{self.name} done` to get images to select your target from.')
                    return
                usr_stats = coll_stats.find_one({'uid': msg.author.id})
                if usr_stats is None:
                    usr_stats = {'uid': msg.author.id, 'total': 0, 'correct': 0, 'cancelled': 0}
                log_entry = {'uid': msg.author.id, 'target': session['target'], 'selection': selection,
                             't_start': session['t_start'], 't_end': datetime.datetime.now()}
                usr_stats['cancelled'] = usr_stats.get('cancelled', 0) + 1
                await msg.channel.send(f'{msg.author.mention} Cancelled. This was your target. Use'
                                       f' `{prefix}{self.name} init` to get another target.',
                                       file=discord.File(f'rv/{code}.jpg'))
                coll_stats.replace_one({'uid': msg.author.id}, usr_stats)
                coll_logs.insert_one(log_entry)
                coll.delete_one({'uid': msg.author.id})
                os.remove(f'rv/{code}.jpg')
            else:
                await msg.reply(f'You don\'t have a target yet. Use `{prefix}{self.name} init` to request one.')
        elif args[0] == 'log':
            log = coll_logs.find({}).sort('t_end', 1)
            out_file = io.StringIO()
            out_file.write('Time(UTC),UserID,Success,Duration(s)\n')
            for log_entry in log:
                t_end = log_entry.get('t_end').replace(microsecond=0)
                uid = f'"{log_entry.get("uid")}"'
                suc = str(log_entry.get('correct', 'cancelled')).upper()
                dur = int((log_entry.get('t_end') - log_entry.get('t_start')).total_seconds())
                out_file.write(f'{t_end.isoformat()},{uid},{suc},{dur}\n')
            out_file.seek(0)
            fn = f'rv/rv_log_{datetime.datetime.utcnow().isoformat()}.csv'
            await msg.channel.send(file=discord.File(out_file, filename=fn))
        else:
            raise RuntimeError('valid operators are: ' + self.arg_desc)
