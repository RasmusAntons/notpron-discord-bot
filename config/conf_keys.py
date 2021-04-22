import enum
from .key_models import *


class Key(enum.Enum):
    INSTANCE = ConfigKey('instance', ConfigDatatype.STRING, required=True, help_text='Identifier for this bot instance.')
    DB_URL = ConfigKey('db_url', ConfigDatatype.STRING, required=True, default='/tmp/mongodb-27017.sock', help_text='Url to the mongodb instance.')
    DISCORD_TOKEN = ConfigKey('discord_token', ConfigDatatype.STRING, required=True, protected=True, help_text='Discord bot token.')
    API_PORT = ConfigKey('api_port', ConfigDatatype.INT, help_text='Listening port for the API.')

    PREFIX = ConfigKey('prefix', ConfigDatatype.STRING, required=True, help_text='Command prefix.')
    LISTENING = ConfigKey('listening', ConfigDatatype.STRING, help_text='Displayed in the bot\'s status.')
    BLACKLIST_CATEGORIES = ConfigListKey('blacklist_categories', ConfigDatatype.STRING, help_text='Disable commands of these categories.')
    EMBED_COLOUR = ConfigKey('embed_colour', ConfigDatatype.INT, help_text='Numerical colour (RGB) value used for embeds.')
    GUILD = ConfigKey('guild', ConfigDatatype.INT, help_text='Id of the main guild this bot belongs to.')
    ANNOUNCEMENT_CHANNEL = ConfigKey('announcement_channel', ConfigDatatype.INT, help_text='Id of channel to send announcements to.')
    CONTROL_CHANNEL = ConfigKey('control_channel', ConfigDatatype.INT, help_text='Id of channel for log messages etc.')
    CHANNELS = ConfigListKey('channels', ConfigDatatype.INT, help_text='Ids of channels the bot is active in.')
    RATELIMITS = ConfigDictKey('ratelimits', ConfigDatatype.INT, ConfigDatatype.INT, help_text='Ratelimits in seconds per channel id.')
    MARKOV_CHANNELS = ConfigListKey('markov_channels', ConfigDatatype.INT, help_text='Ids of channels used for markov chain generation.')
    EVAL_TIMEOUT = ConfigKey('eval_timeout', ConfigDatatype.INT, help_text='Timeout for eval command in milliseconds.')
    FONT = ConfigKey('font', ConfigDatatype.STRING, help_text='Font to use in the font command.')
    RV_PATH = ConfigKey('rv_path', ConfigDatatype.STRING, help_text='Directory with RV images.')
    IMAGINE_SUFFIX = ConfigKey('imagine_suffix', ConfigDatatype.STRING, help_text='Appended to each imagine query.')
    DEFAULT_ROLE = ConfigKey('default_role', ConfigDatatype.INT, help_text='Role assigned to new members on join.')
    DM_RELAY_CHANNEL = ConfigKey('dm_relay_channel', ConfigDatatype.INT, help_text='Channel to send bot dms to.')

    MOD_ROLES = ConfigListKey('mod_roles', ConfigDatatype.INT, help_text='Ids of moderator roles.')
    ADMIN_USERS = ConfigListKey('admin_users', ConfigDatatype.INT, help_text='Ids of admin users.')
    ROLE_CHANNEL = ConfigKey('role_channel', ConfigDatatype.INT, help_text='Id of channel with role assignment reactions.')
    ASSIGN_ROLES = ConfigDictKey('assign_roles', ConfigDatatype.STRING, ConfigDatatype.INT, help_text='Emoji (id as string or string representation) and their respective roles.')
    EXCLUSIVE_ROLES = ConfigListKey('exclusive_roles', ConfigDatatype.INT, help_text='Ids of mutually exclusive roles.')
    ADULT_ROLES = ConfigListKey('adult_roles', ConfigDatatype.INT, help_text='Ids of adult-only roles.')

    IMAGE_API_KEY = ConfigKey('image_api_key', ConfigDatatype.STRING, protected=True, help_text='Api key for google image search.')
    IMAGE_SEARCH_CX = ConfigKey('image_search_cx', ConfigDatatype.STRING, protected=True, help_text='Google custom search engine.')
    GMAPS_API_KEY = ConfigKey('gmaps_api_key', ConfigDatatype.STRING, protected=True, help_text='Api key for google maps geocoding.')
    OWM_API_KEY = ConfigKey('owm_api_key', ConfigDatatype.STRING, protected=True, help_text='API key for openweathermap.org.')
