from sqlitedict import SqliteDict
import discord
import random
from commands.command import Command
import os
import shutil
import math
import time
import queue
from PIL import Image, ImageOps, ImageDraw, ImageFont


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
    arg_range = (1, 2)
    description = 'remote view some images'
    arg_desc = 'init | done | show <id> | solve <id> | stats'

    async def execute(self, args, msg):
        rv_path = self.bot.config.get_rv_path()
        with SqliteDict('rv/db.sqlite') as rvdb:
            session = rvdb.get(msg.author.id)
            await msg.channel.trigger_typing()
            if args[0] == 'stats':
                best = queue.PriorityQueue()
                stats = rvdb.get('stats', {})
                total = 0
                correct = 0
                for uid, usr_stats in stats.items():
                    total += usr_stats['total']
                    correct += usr_stats['correct']
                    if usr_stats['total'] >= 10:
                        best.put((-usr_stats['correct'] / usr_stats['total'], [uid, usr_stats['correct'], usr_stats['total']]))
                embed = discord.Embed(title=f'RV Stats', color=self.bot.config.get_embed_colour())
                global_stats = f'{total} total attempts\n{correct} successful attempts' \
                               f'\n{100 * correct / total:5.2f}% success rate'
                embed.add_field(name=f'Global', value=global_stats, inline=False)
                best_users = []
                i = 0
                while i < 5 and not best.empty():
                    ratio, user_stats = best.get()
                    uid, correct, total = user_stats
                    user = self.bot.get_user(uid) or await self.bot.fetch_user(uid)
                    ratio = correct / total
                    best_users.append(f'{i + 1}. {100 * ratio:05.2f}% ({correct:2d}/{total:2d}) {user.name}')
                    i += 1
                embed.add_field(name=f'Most successful', value='\n'.join(best_users) or '', inline=False)
                embed.set_footer(text=f'Only users with at least 10 total attempts are shown.')
                await msg.channel.send(embed=embed)
            elif args[0] == 'init':
                if session:
                    code = session['code']
                    await msg.channel.send(f'{msg.author.mention} you already have the target **{code}**.'
                                           f' Use `{self.bot.prefix}{self.name} done` when you are ready to solve.')
                else:
                    code = '-'.join([f'{random.randrange(0, 1000):03d}' for _ in range(4)])
                    choices = os.listdir(rv_path)
                    target = os.path.join(rv_path, random.choice(choices))
                    shutil.copyfile(target, f'rv/{code}.jpg')
                    rvdb[msg.author.id] = {'code': code, 'target': target, 't_start': time.time()}
                    rvdb.commit()
                    await msg.channel.send(f'{msg.author.mention} your target is **{code}**.'
                                           f' This number is randomly generated and I have copied a randomly'
                                           f' chosen image into a file with the name {code}.jpg.'
                                           f' Use `{self.bot.prefix}{self.name} done` when you are ready to solve.')
            elif args[0] == 'done':
                if session and session.get('target'):
                    selection = session.get('selection')
                    code = session.get('code')
                    if selection is None:
                        choices = os.listdir(rv_path)
                        selection = [session['target']]
                        while len(selection) < 20:
                            new_image = os.path.join(rv_path, random.choice(choices))
                            if new_image not in selection:
                                selection.append(new_image)
                        random.shuffle(selection)
                        session['selection'] = selection
                        rvdb[msg.author.id] = session
                        rvdb.commit()
                    im = gen_thumbs(selection, 5)
                    im.save(f'rv/{code}.png')
                    text = f'{msg.author.mention} please identify your target image and enter its number with' \
                           f' `{self.bot.prefix}{self.name} solve <id>` where <id> is the number shown above' \
                           f' the image. Use `{self.bot.prefix}{self.name} show <id>` to see an image in its' \
                           f' full resolution.'
                    await msg.channel.send(text, file=discord.File(f'rv/{code}.png'))
                else:
                    await msg.channel.send(f'{msg.author.mention} you don\'t have a target yet.'
                                           f' Use `{self.bot.prefix}{self.name} init` to request one.')
            elif args[0] == 'show':
                if session and session.get('target'):
                    if len(args) < 2:
                        await msg.channel.send(f' Use `{self.bot.prefix}{self.name} show <id>`'
                                               f' to view one specific image.')
                        return
                    img_id = int(args[1])
                    if not 1 <= img_id <= 20:
                        raise ValueError('image id must be between 1 and 20')
                    selection = session.get('selection')
                    if selection is None:
                        await msg.channel.send(f'{msg.author.mention} you don\'t have a target selection yet.'
                                               f' Use `{self.bot.prefix}{self.name} done` to get images to select'
                                               f' your target from.')
                        return
                    text = f'{msg.author.mention}, this is your option {img_id}'
                    await msg.channel.send(text, file=discord.File(selection[img_id - 1]))
                else:
                    await msg.channel.send(f'{msg.author.mention} you don\'t have a target yet.'
                                           f' Use `{self.bot.prefix}{self.name} init` to request one.')
            elif args[0] == 'solve':
                if session and session.get('target'):
                    if len(args) < 2:
                        await msg.channel.send(f' Use `{self.bot.prefix}{self.name} solve <id>` to enter your choice.')
                        return
                    img_id = int(args[1])
                    if not 1 <= img_id <= 20:
                        raise ValueError('image id must be between 1 and 20')
                    code = session['code']
                    selection = session.get('selection')
                    if selection is None:
                        await msg.channel.send(f'{msg.author.mention} you don\'t have a target selection yet.'
                                               f' Use `{self.bot.prefix}{self.name} done` to get images to select'
                                               f' your target from.')
                        return
                    choice = selection[img_id - 1]
                    stats = rvdb.get('stats', {})
                    usr_stats = stats.get(msg.author.id, {'total': 0, 'correct': 0})
                    correct = choice == session['target']
                    log_entry = {'uid': msg.author.id, 'correct': correct, 'target': session['target'],
                                 'selection': selection, 't_start': session['t_start'], 't_end': time.time()}
                    if correct:
                        usr_stats['total'] = usr_stats['total'] + 1
                        usr_stats['correct'] = usr_stats['correct'] + 1
                        await msg.channel.send(f'{msg.author.mention} Correct! This was your target. You have'
                                               f' viewed {usr_stats["correct"]}/{usr_stats["total"]} images correctly',
                                               file=discord.File(f'rv/{code}.jpg'))
                    else:
                        usr_stats['total'] = usr_stats['total'] + 1
                        await msg.channel.send(f'{msg.author.mention} Wrong. This was your target. You have'
                                               f' viewed {usr_stats["correct"]}/{usr_stats["total"]} images correctly',
                                               file=discord.File(f'rv/{code}.jpg'))
                    stats[msg.author.id] = usr_stats
                    rvdb['stats'] = stats
                    log = rvdb.get('log', [])
                    log.append(log_entry)
                    rvdb['log'] = log
                    del rvdb[msg.author.id]
                    rvdb.commit()
                    os.remove(f'rv/{code}.jpg')
                else:
                    await msg.channel.send(f'{msg.author.mention} you don\'t have a target yet.'
                                           f' Use `{self.bot.prefix}{self.name} init` to request one.')
            else:
                raise RuntimeError('valid operators are: ' + self.arg_desc)
