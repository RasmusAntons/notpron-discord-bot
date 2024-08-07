import enum
from .key_models import *


class Key(enum.Enum):
    INSTANCE = ConfigKey('instance', ConfigDatatype.STRING, required=True, help_text='Identifier for this bot instance.')
    DB_URL = ConfigKey('db_url', ConfigDatatype.STRING, required=True, default='/tmp/mongodb-27017.sock', help_text='Url to the mongodb instance.')
    DISCORD_TOKEN = ConfigKey('discord_token', ConfigDatatype.STRING, required=True, protected=True, help_text='Discord bot token.')
    API_PORT = ConfigKey('api_port', ConfigDatatype.INT, help_text='Listening port for the API.')
    ENIGMATICS_URL = ConfigKey('enigmatics_url', ConfigDatatype.STRING, help_text='Private URL of enigmatics.org')
    BADGE_EMOJI = ConfigDictKey('badge_emoji', ConfigDatatype.STRING, ConfigDatatype.STRING, help_text='emoji of badges')

    PREFIX = ConfigKey('prefix', ConfigDatatype.STRING, required=True, help_text='Command prefix.')
    LISTENING = ConfigKey('listening', ConfigDatatype.STRING, help_text='Displayed in the bot\'s status.')
    BLACKLIST_CATEGORIES = ConfigListKey('blacklist_categories', ConfigDatatype.STRING, help_text='Disable commands of these categories.')
    EMBED_COLOUR = ConfigKey('embed_colour', ConfigDatatype.INT, help_text='Numerical colour (RGB) value used for embeds.')
    GUILD = ConfigKey('guild', ConfigDatatype.INT, help_text='Id of the main guild this bot belongs to.')
    ANNOUNCEMENT_CHANNEL = ConfigKey('announcement_channel', ConfigDatatype.INT, help_text='Id of channel to send announcements to.')
    CONTROL_CHANNEL = ConfigKey('control_channel', ConfigDatatype.INT, help_text='Id of channel for log messages etc.')
    MOD_CHANNEL = ConfigKey('mod_channel', ConfigDatatype.INT, help_text='Id of channel for mod messages.')
    CHANNELS = ConfigListKey('channels', ConfigDatatype.INT, help_text='Ids of channels the bot is active in.')
    RATELIMITS = ConfigDictKey('ratelimits', ConfigDatatype.INT, ConfigDatatype.INT, help_text='Ratelimits in seconds per channel id.')
    MARKOV_CHANNELS = ConfigListKey('markov_channels', ConfigDatatype.INT, help_text='Ids of channels used for markov chain generation.')
    MARKOV_CHANCE = ConfigKey('markov_chance', ConfigDatatype.INT, help_text='Chance of random response in percent', default=0)
    ARCHIVE_CHANNELS = ConfigListKey('archive_channels', ConfigDatatype.INT, help_text='Ids of channels archived continuously.')
    EVAL_TIMEOUT = ConfigKey('eval_timeout', ConfigDatatype.INT, help_text='Timeout for eval command in milliseconds.')
    FONT = ConfigKey('font', ConfigDatatype.STRING, help_text='Font to use in the font command.')
    RV_PATH = ConfigKey('rv_path', ConfigDatatype.STRING, help_text='Directory with RV images.')
    IMAGINE_SUFFIX = ConfigKey('imagine_suffix', ConfigDatatype.STRING, help_text='Appended to each imagine query.')
    DEFAULT_ROLE = ConfigKey('default_role', ConfigDatatype.INT, help_text='Role assigned to new members on join.')
    DM_RELAY_CHANNEL = ConfigKey('dm_relay_channel', ConfigDatatype.INT, help_text='Channel to send bot dms to.')
    ANAGRAM_MIN_LENGTH = ConfigKey('anagram_min_length', ConfigDatatype.INT, help_text='Minimum length of anagrams should be reacted to.', default=8)

    MOD_ROLES = ConfigListKey('mod_roles', ConfigDatatype.INT, help_text='Ids of moderator roles.')
    ADMIN_USERS = ConfigListKey('admin_users', ConfigDatatype.INT, help_text='Ids of admin users.')
    TRUSTED_USER_ROLES = ConfigListKey('trusted_user_roles', ConfigDatatype.INT, help_text='Ids of moderator roles.')
    ROLE_CHANNEL = ConfigKey('role_channel', ConfigDatatype.INT, help_text='Id of channel with role assignment reactions.')
    ASSIGN_ROLES = ConfigDictKey('assign_roles', ConfigDatatype.STRING, ConfigDatatype.INT, help_text='Emoji (id as string or string representation) and their respective roles.')
    EXCLUSIVE_ROLES = ConfigListKey('exclusive_roles', ConfigDatatype.INT, help_text='Ids of mutually exclusive roles.')
    ADULT_ROLES = ConfigListKey('adult_roles', ConfigDatatype.INT, help_text='Ids of adult-only roles.')
    WEEKLIES_CHANNELS = ConfigDictKey('weeklies_channels', ConfigDatatype.STRING, ConfigDatatype.INT, help_text='Ids of weekly discussion channels')
    WEEKLY_SOLVER_ROLE = ConfigKey('weekly_solver_role', ConfigDatatype.INT, help_text='Role id of weekly-solver role.')
    WEEKLIES_CHANNEL_ADMIN_ROLE = ConfigKey('weeklies_channel_admin_role', ConfigDatatype.INT, help_text='Role id of weeklies-channel-admin role.')
    QUARANTINE_ROLE = ConfigKey('quarantine_role', ConfigDatatype.INT, help_text='Role id of quarantine role.')
    SILENCED_ROLE = ConfigKey('silenced_role', ConfigDatatype.INT, help_text='Role id of silenced role.')
    COUNTING_CHANNEL = ConfigKey('counting_channel', ConfigDatatype.INT, help_text='Id of counting channel.')

    OPENAI_RATELIMIT_MINUTES = ConfigKey('openai_ratelimit_minutes', ConfigDatatype.INT, help_text='Time window for openai ratelimit.', default=360)
    OPENAI_RATELIMIT_BURST_CHAT = ConfigKey('openai_ratelimit_burst_chat', ConfigDatatype.INT, help_text='Number of openai chat requests during time window.', default=20)
    OPENAI_RATELIMIT_BURST_IMAGES = ConfigKey('openai_ratelimit_burst_images', ConfigDatatype.INT, help_text='Number of openai image requests during time window.', default=5)
    OPENAI_DAILY_BANNER_HOUR = ConfigKey('openai_daily_banner_hour', ConfigDatatype.INT, help_text='Hour in UTC to change daily banner (None = disabled)')

    IMAGE_API_KEY = ConfigKey('image_api_key', ConfigDatatype.STRING, protected=True, help_text='Api key for google image search.')
    IMAGE_SEARCH_CX = ConfigKey('image_search_cx', ConfigDatatype.STRING, protected=True, help_text='Google custom search engine.')
    GMAPS_API_KEY = ConfigKey('gmaps_api_key', ConfigDatatype.STRING, protected=True, help_text='Api key for google maps geocoding.')
    OWM_API_KEY = ConfigKey('owm_api_key', ConfigDatatype.STRING, protected=True, help_text='API key for openweathermap.org.')
    WORDNIK_API_KEY = ConfigKey('wordnik_api_key', ConfigDatatype.STRING, protected=True, help_text='API key for wordnik.com')
    OPENAI_ORGANIZATION = ConfigKey('openai_organization', ConfigDatatype.STRING, help_text='Organization ID for openai.com')
    OPENAI_API_KEY = ConfigKey('openai_api_key', ConfigDatatype.STRING, protected=True, help_text='API key for openai.com')
