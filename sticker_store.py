"""
Auto-learns stickers from real conversations so the bot builds its own
sticker-reply pool over time, instead of needing the owner to manually
configure every file_id.

IMPORTANT HONEST LIMITATION: Telegram's Bot API does not expose the actual
image content of a sticker - only its file_id, its pack's name/title, and the
single emoji the pack creator associated with it. This filter can only block
packs whose NAME/TITLE contains an obvious explicit-content keyword. It
CANNOT verify what a sticker actually depicts. An innocently-named pack could
still contain inappropriate content and this filter would not catch it. Treat
this as a basic safety net, not a guarantee - review /getstickerid style
audits periodically if this matters a lot for your community.
"""
import time
import random

import db

_cache = {"stickers": [], "loaded_at": 0}

# Keyword filter applied to sticker pack name + title (best-effort only -
# see the limitation notice above). Expand this list as needed.
BLOCKED_KEYWORDS = [
    "porn", "sex", "xxx", "nsfw", "adult", "hentai", "erotic", "nude",
    "naked", "18+", "fuck", "hot18", "boobs", "onlyfans",
]

EMOJI_MOOD_MAP = {
    "😂": "happy", "😄": "happy", "😁": "happy", "🎉": "happy", "😆": "happy",
    "😢": "sad", "😭": "sad", "🥺": "sad", "😔": "sad",
    "😡": "angry", "😠": "angry", "🙄": "angry", "😤": "angry",
    "😍": "flirty", "😘": "flirty", "🥰": "flirty", "😏": "flirty",
    "😑": "jealous", "🙃": "jealous", "👀": "jealous",
}


def _is_blocked(set_name: str, title: str = "") -> bool:
    combined = f"{set_name or ''} {title or ''}".lower()
    return any(kw in combined for kw in BLOCKED_KEYWORDS)


def _guess_mood(emoji: str) -> str:
    return EMOJI_MOOD_MAP.get(emoji, "normal")


async def _get_cache() -> dict:
    import config
    now = time.time()
    if now - _cache["loaded_at"] > config.INTENT_CACHE_TTL or not _cache["stickers"]:
        _cache["stickers"] = await db.get_all_stickers()
        _cache["loaded_at"] = now
    return _cache


async def learn_sticker(bot, file_id: str, set_name: str, emoji: str) -> bool:
    """Attempts to save a sticker for future reuse. Returns False (and skips
    saving) if the pack name/title matches the blocked-keyword filter."""
    title = ""
    if set_name:
        try:
            sticker_set = await bot.get_sticker_set(set_name)
            title = sticker_set.title or ""
        except Exception:
            pass  # couldn't fetch title - fall back to name-only check

    if _is_blocked(set_name, title):
        return False

    mood = _guess_mood(emoji)
    await db.save_sticker(file_id, set_name, emoji, mood)

    cache = await _get_cache()
    if not any(s.get("_id") == file_id for s in cache["stickers"]):
        cache["stickers"].append(
            {"_id": file_id, "set_name": set_name, "emoji": emoji, "mood": mood}
        )
    return True


async def get_sticker(mood: str = None) -> str | None:
    """Returns a file_id to reply with, preferring the given mood's pool."""
    cache = await _get_cache()
    pool = cache["stickers"]
    if not pool:
        return None
    if mood:
        matching = [s["_id"] for s in pool if s.get("mood") == mood]
        if matching:
            return random.choice(matching)
    return random.choice([s["_id"] for s in pool])
