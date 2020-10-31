import random
import string


punct = str.maketrans(dict.fromkeys(string.punctuation))


async def on_message(bot, msg):
    content_lower = msg.content.lower().translate(punct)
    words_lower = content_lower.split()
