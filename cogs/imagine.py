import datetime
import random

from discord.ext import commands
from google_images_search import GoogleImagesSearch
import pymongo

import globals


class ImagineCog(commands.Cog, name='Imagine', description='get an image for your query'):
    def __init__(self):
        self.coll = globals.bot.db['imagine']
        self.coll.create_index([('query', pymongo.ASCENDING), ('safe', pymongo.ASCENDING)], unique=True)

    @commands.hybrid_command(name='imagine', description='get an image for your query')
    async def imagine(self, ctx: commands.Context, query: str) -> None:
        suffix = globals.conf.get(globals.conf.keys.IMAGINE_SUFFIX)
        if suffix:
            query = f'{query} {suffix}'
        search_params = {
            'q': query,
            'safe': 'off' if ctx.channel.is_nsfw() else 'medium',
            'num': 10
        }

        async def _imagine():
            results = self.coll.find_one({'query': search_params['q'], 'safe': search_params['safe']})
            if results is None or results['date'] + datetime.timedelta(days=7) < datetime.datetime.utcnow():
                image_api_key = globals.conf.get(globals.conf.keys.IMAGE_API_KEY, bypass_protected=True)
                image_search_cx = globals.conf.get(globals.conf.keys.IMAGE_SEARCH_CX, bypass_protected=True)
                if image_api_key is None or image_search_cx is None:
                    raise RuntimeError(f'Google search API key or custom search engine not configured.')
                gis = GoogleImagesSearch(image_api_key, image_search_cx)
                gis.search(search_params=search_params)
                good_ext = {'jpg', 'jpeg', 'JPG', 'JPEG', 'png', 'PNG', 'gif', 'webm', 'mp4', 'wav', 'mp3', 'ogg'}
                urls = list(filter(
                    lambda u: u.split('?')[0].split('.')[-1] in good_ext,
                    map(lambda r: r.url, gis.results()))
                )
                results = {'query': search_params['q'], 'safe': search_params['safe'], 'urls': urls, 'state': 0,
                           'date': datetime.datetime.utcnow()}
                self.coll.replace_one({'query': search_params['q'], 'safe': search_params['safe']}, results,
                                      upsert=True)
            if len(results['urls']) == 0:
                excuses = ['I cannot imagine that', 'I don\'t even know what that is']
                return await ctx.reply(random.choice(excuses))
            next_state = (results['state'] + 1) % len(results['urls'])
            self.coll.update_one(results, {'$set': {'state': next_state}})
            await ctx.reply(results['urls'][results['state']])
        if ctx.interaction:
            await ctx.interaction.response.defer()
            await _imagine()
        else:
            async with ctx.channel.typing():
                await _imagine()
