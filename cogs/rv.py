import datetime
import io
import math
import os
import random
import shutil

from PIL import Image, ImageOps, ImageDraw, ImageFont
import discord
from discord.ext import commands

import globals
from utils import get_user


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
        w = draw.textlength(text, font=font)
        draw.text((x + (th.width - w) // 2, y), text, font=font, fill='lightgray')
    return res


class RvCog(commands.Cog, name='Rv', description='remote view some images'):
    def __init__(self):
        self.coll = globals.bot.db['rv']
        self.coll.create_index('uid', unique=True)
        self.stats_coll = globals.bot.db['rv_stats']
        self.stats_coll.create_index('uid', unique=True)
        self.logs_coll = globals.bot.db['rv_logs']
        self.logs_coll.create_index('t_end')
        self.n_choices = 4

    @commands.hybrid_group(name='rv', description='remote view some images')
    async def rv_grp(self, ctx):
        return None

    @rv_grp.command(name='stats', description='view rv stats')
    async def stats(self, ctx: commands.Context, user: discord.User = None) -> None:
        embed = discord.Embed(title=f'RV Stats', color=globals.conf.get(globals.conf.keys.EMBED_COLOUR))
        if user:
            usr = user
            usr_stats = self.stats_coll.find_one({'uid': usr.id}) or {}
            usr_total = usr_stats.get('total', 0)
            usr_correct = usr_stats.get('correct', 0)
            usr_cancelled = usr_stats.get('cancelled', 0)
            usr_text = f'{usr_total} total attempts\n{usr_correct} successful attempts\n{usr_cancelled}' \
                       f' cancelled attempts\n{100 * usr_correct / usr_total:5.2f}% success rate'
            embed.add_field(name=usr.display_name, value=usr_text, inline=False)
        else:
            await ctx.defer()
            total_stats = self.stats_coll.aggregate([{'$group': {
                '_id': None, 'total': {'$sum': '$total'},
                'correct': {'$sum': '$correct'}, 'cancelled': {'$sum': '$cancelled'}
            }}]).next()
            total, correct, cancelled = total_stats['total'], total_stats['correct'], total_stats['cancelled']
            global_stats = f'{total} total attempts\n{correct} successful attempts' \
                           f'\n{cancelled} cancelled attempts\n{100 * correct / total:5.2f}% success rate'
            embed.add_field(name=f'Global', value=global_stats, inline=False)
            best_users = self.stats_coll.aggregate([{'$match': {'total': {'$gte': 10}}}, {'$project': {
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
        await ctx.reply(embed=embed)

    @rv_grp.command(name='init', description='initialize rv session')
    async def init(self, ctx: commands.Context) -> None:
        rv_path = globals.conf.get(globals.conf.keys.RV_PATH)
        session = self.coll.find_one({'uid': ctx.author.id})
        if session:
            code = session['code']
            await ctx.reply(f'You already have the target **{code}**.'
                            f' Use `/rv done` when you are ready to solve.')
        else:
            await ctx.defer()
            code = '-'.join([f'{random.randrange(0, 1000):03d}' for _ in range(4)])
            choices = os.listdir(rv_path)
            target = os.path.join(rv_path, random.choice(choices))
            if not os.path.exists('rv'):
                os.makedirs('rv')
            shutil.copyfile(target, f'rv/{code}.jpg')
            self.coll.insert_one(
                {'uid': ctx.author.id, 'code': code, 'target': target, 't_start': datetime.datetime.utcnow()})
            await ctx.reply(f'Your target is **{code}**.'
                            f' This number is randomly generated and I have copied a randomly'
                            f' chosen image into a file with the name {code}.jpg.'
                            f' Use `/rv done` when you are ready to solve.')

    @rv_grp.command(name='done', description='show image options after remote viewing')
    async def done(self, ctx: commands.Context) -> None:
        rv_path = globals.conf.get(globals.conf.keys.RV_PATH)
        session = self.coll.find_one({'uid': ctx.author.id})
        if session and session.get('target'):
            await ctx.defer()
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
                self.coll.update_one(session, {'$set': {'selection': selection}})
            im = gen_thumbs(selection, min(5, self.n_choices), (320, 320))
            out_file = io.BytesIO()
            im.save(out_file, 'PNG')
            out_file.seek(0)
            text = f'Please identify your target image and enter its number with' \
                   f' `/rv solve <id>` where <id> is the number shown above' \
                   f' the image. Use `/rv show <id>` to see an image in its' \
                   f' full resolution. If there are multiple matching images, you can use' \
                   f' `/rv cancel` to cancel and try another target.'
            await ctx.reply(text, file=discord.File(out_file, filename=f'rv/{code}.png'))
        else:
            await ctx.reply(f'You don\'t have a target yet. Use `/rv init` to request one.')

    @rv_grp.command(name='show', description='show one option in full resolution')
    async def show(self, ctx: commands.Context, option: int) -> None:
        session = self.coll.find_one({'uid': ctx.author.id})
        if session and session.get('target'):
            selection = session.get('selection')
            if selection is None:
                await ctx.reply(f'You don\'t have a target selection yet.'
                                f' Use `/rv done` to get images to select'
                                f' your target from.')
                return
            if not 1 <= option <= self.n_choices:
                raise ValueError(f'option must be between 1 and {self.n_choices}')
            text = f'this is your option {option}'
            await ctx.reply(text, file=discord.File(selection[option - 1]))
        else:
            await ctx.reply(f'You don\'t have a target yet. Use `/rv init` to request one.')

    @rv_grp.command(name='solve', description='select the image option you remote viewed')
    async def solve(self, ctx: commands.Context, option: int) -> None:
        session = self.coll.find_one({'uid': ctx.author.id})
        if session and session.get('target'):
            await ctx.defer()
            code = session['code']
            selection = session.get('selection')
            if selection is None:
                await ctx.reply(f'you don\'t have a target selection yet.'
                                f' Use `/rv done` to get images to select'
                                f' your target from.')
                return
            if not 1 <= option <= self.n_choices:
                raise ValueError(f'option must be between 1 and {self.n_choices}')
            choice = selection[option - 1]
            usr_stats = self.stats_coll.find_one({'uid': ctx.author.id})
            if usr_stats is None:
                usr_stats = {'uid': ctx.author.id, 'total': 0, 'correct': 0, 'cancelled': 0}
            correct = choice == session['target']
            log_entry = {'uid': ctx.author.id, 'correct': correct, 'target': session['target'],
                         'selection': selection, 't_start': session['t_start'], 't_end': datetime.datetime.utcnow()}
            if correct:
                usr_stats['total'] = usr_stats['total'] + 1
                usr_stats['correct'] = usr_stats['correct'] + 1
                await ctx.reply(f'Correct! This was your target. You have'
                                f' viewed {usr_stats["correct"]}/{usr_stats["total"]} images correctly',
                                file=discord.File(f'rv/{code}.jpg'))
            else:
                usr_stats['total'] = usr_stats['total'] + 1
                await ctx.reply(f'Wrong. This was your target. You have'
                                f' viewed {usr_stats["correct"]}/{usr_stats["total"]} images correctly',
                                file=discord.File(f'rv/{code}.jpg'))
            self.stats_coll.replace_one({'uid': ctx.author.id}, usr_stats, upsert=True)
            self.logs_coll.insert_one(log_entry)
            self.coll.delete_one({'uid': ctx.author.id})
            os.remove(f'rv/{code}.jpg')
        else:
            await ctx.reply(f'You don\'t have a target yet. Use `/rv init` to request one.')

    @rv_grp.command(name='cancel', description='cancel an rv session')
    async def cancel(self, ctx: commands.Context) -> None:
        session = self.coll.find_one({'uid': ctx.author.id})
        if session and session.get('target'):
            code = session['code']
            selection = session.get('selection')
            if selection is None:
                await ctx.reply(f'You don\'t have a target selection yet.'
                                f' Use `/rv done` to get images to select your target from.')
                return
            usr_stats = self.stats_coll.find_one({'uid': ctx.author.id})
            if usr_stats is None:
                usr_stats = {'uid': ctx.author.id, 'total': 0, 'correct': 0, 'cancelled': 0}
            log_entry = {'uid': ctx.author.id, 'target': session['target'], 'selection': selection,
                         't_start': session['t_start'], 't_end': datetime.datetime.now()}
            usr_stats['cancelled'] = usr_stats.get('cancelled', 0) + 1
            await ctx.reply(f'Cancelled. This was your target. Use'
                            f' `/rv init` to get another target.',
                            file=discord.File(f'rv/{code}.jpg'))
            self.stats_coll.replace_one({'uid': ctx.author.id}, usr_stats)
            self.logs_coll.insert_one(log_entry)
            self.coll.delete_one({'uid': ctx.author.id})
            os.remove(f'rv/{code}.jpg')
        else:
            await ctx.reply(f'You don\'t have a target yet. Use `/rv init` to request one.')

    @rv_grp.command(name='log', description='view rv log')
    async def log(self, ctx: commands.Context) -> None:
        log = self.logs_coll.find({}).sort('t_end', 1)
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
        await ctx.reply(file=discord.File(out_file, filename=fn))
