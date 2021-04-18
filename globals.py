from __future__ import annotations
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from discord_connection import DiscordConnection
    from config import Config

bot: DiscordConnection = None
conf: Config = None
