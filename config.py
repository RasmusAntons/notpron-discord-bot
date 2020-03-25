import json


class Config:
    def __init__(self, filename):
        self.conf = json.load(open(filename))

    def get_discord_token(self):
        return self.conf['discord']['token']

    def get_channels(self):
        return self.conf['channels']

    def get_music_channels(self):
        return self.conf['music']

    def get_hint(self, level):
        return self.conf['hints'].get(f'{level}')

    def get_antihint(self, level):
        return self.conf['antihints'].get(f'{level}')
