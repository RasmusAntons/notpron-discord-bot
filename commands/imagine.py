from commands.command import Command, Category
from google_images_search import GoogleImagesSearch
import random
import globals
import pymongo
import datetime


class ImagineCommand(Command):
    name = 'imagine'
    category = Category.UTILITY
    arg_range = (1, 99)
    description = 'get an image for your query'
    arg_desc = '<query...>'
    state = {}

    def __init__(self):
        super().__init__()
        coll = globals.bot.db['imagine']
        coll.create_index([('query', pymongo.ASCENDING), ('safe', pymongo.ASCENDING)], unique=True)

    async def execute(self, args, msg):
        query = ' '.join(args)
        suffix = globals.conf.get(globals.conf.keys.IMAGINE_SUFFIX)
        if suffix:
            query = f'{query} {suffix}'
        search_params = {
            'q': query,
            'safe': 'off' if msg.channel.is_nsfw() else 'medium',
            'num': 10
        }
        await msg.channel.trigger_typing()
        coll = globals.bot.db['imagine']
        results = coll.find_one({'query': search_params['q'], 'safe': search_params['safe']})
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
            coll.replace_one({'query': search_params['q'], 'safe': search_params['safe']}, results, upsert=True)
        if len(results['urls']) == 0:
            excuses = ['I cannot imagine that', 'I don\'t even know what that is']
            return await msg.channel.send(f'{msg.author.mention} {random.choice(excuses)}')
        await msg.channel.send(results['urls'][results['state']])
        next_state = (results['state'] + 1) % len(results['urls'])
        coll.update_one(results, {'$set': {'state': next_state}})
