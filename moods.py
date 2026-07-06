import random

# ---------------------------------------------------------------------------
# STICKERS: paste real file_ids here. To get one, send a sticker to the bot
# in DM as the OWNER - it replies with the file_id automatically.
# ---------------------------------------------------------------------------
STICKERS = {
    "happy": [],
    "flirty": [],
    "angry": [],
    "jealous": [],
    "sad": [],
    "normal": [],
}

EMOJIS = {
    "happy": ["😄", "🥰", "😆", "✨"],
    "flirty": ["😏", "😘", "🙈", "💗"],
    "angry": ["😤", "🙄", "😒"],
    "jealous": ["😑", "🙃", "👀"],
    "sad": ["🥺", "😔", "💔"],
    "normal": ["😊", "🙂", "👍"],
}


def mood_emoji(mood: str) -> str:
    return random.choice(EMOJIS.get(mood, EMOJIS["normal"]))


def maybe_sticker(mood: str):
    pool = STICKERS.get(mood, [])
    if pool and random.random() < 0.3:
        return random.choice(pool)
    return None
