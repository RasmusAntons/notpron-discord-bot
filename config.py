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

    def get_control_channel(self):
        return self.conf['control']

    def get_markov_channels(self):
        return self.conf['markov']

    def get_api_port(self):
        return self.conf['api_port']

    def get_hint(self, level):
        return self.conf['hints'].get(f'{level}')

    def get_antihint(self, level):
        return self.conf['antihints'].get(f'{level}')

    def get_thread(self, thread):
        return self.conf['threads'].get(thread)

    def get_names(self):
        return self.conf['names']

    def get_owm_key(self):
        return self.conf['owm_key']
