import asyncio
from html.parser import HTMLParser
import aiohttp
import re

from mongodb_markov import MongodbMarkov


seasons = [(1, 6), (2, 22), (3, 23), (4, 14), (5, 26), (6, 24), (7, 24), (8, 24), (9, 23)]
url_template = 'https://www.officequotes.net/no{season:d}-{episode:02d}.php'
character_map = {
    'Bob': 'Bob Vance'
}


class OfficeQuotesParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.quotes = []
        self.in_quote = False
        self.in_character = False
        self.current_character = None
        self.current_quote = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        classes = attrs.get('class', '').split()
        if tag == 'div' and 'quote' in classes:
            self.in_quote = True
        if tag == 'b' and self.in_quote:
            if self.current_character is not None and not self.current_character.startswith('Deleted'):
                self.quotes.append((character_map.get(self.current_character, self.current_character), ' '.join(self.current_quote)))
                self.current_quote = []
            self.in_character = True

    def handle_data(self, data):
        if self.in_character:
            self.current_character = data.strip(' :')
            self.in_character = False
        elif self.in_quote:
            self.current_quote.append(data.strip())

    def handle_endtag(self, tag):
        if tag == 'div' and self.in_quote:
            if self.current_character is not None and not self.current_character.startswith('Deleted'):
                self.quotes.append((character_map.get(self.current_character, self.current_character), ' '.join(self.current_quote)))
            self.in_quote = False
            self.current_character = None
            self.current_quote = []


async def parse_all():
    markov = MongodbMarkov(db_name='office_markov')
    markov.words.delete_many({})
    markov.triples.delete_many({})
    characters = set()
    for season, episodes in seasons:
        for episode in range(1, episodes + 1):
            url = url_template.format(season=season, episode=episode)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    data = await resp.read()
                    text = data.decode('utf-8', errors='replace')
                    parser = OfficeQuotesParser()
                    parser.feed(text)
                    for character, quote in parser.quotes:
                        characters.add(character)
                        markov.insert_text(quote, tag=re.sub(r'[^a-zA-Z]', '', character.lower()))
                print(f'{url=}')
    print(f'{characters=}')


if __name__ == '__main__':
    asyncio.run(parse_all())
