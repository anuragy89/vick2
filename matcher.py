import re
import time
import random

import db

_cache = {"intents": [], "loaded_at": 0}


async def _get_intents_cached() -> list[dict]:
    import config
    now = time.time()
    if now - _cache["loaded_at"] > config.INTENT_CACHE_TTL or not _cache["intents"]:
        _cache["intents"] = await db.get_all_intents()
        _cache["loaded_at"] = now
    return _cache["intents"]


def _matches(pattern: str, text: str) -> bool:
    try:
        return re.search(pattern, text, re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in text.lower()


async def find_reply(text: str):
    """Look up a canned reply from Mongo intents. Returns (reply, mood) or (None, None)."""
    intents = await _get_intents_cached()
    for intent in intents:
        for pattern in intent.get("patterns", []):
            if _matches(pattern, text):
                responses = intent.get("responses", [])
                if responses:
                    return random.choice(responses), intent.get("mood", "normal")
    return None, None


def detect_mood(text: str) -> str:
    """Stateless, single-message mood guess purely from current text - no memory used."""
    low = text.lower()
    checks = {
        "flirty": [r"\bcute\b", r"\bbeautiful\b", r"\blove you\b", r"\bpyaar\b", r"❤️", r"😍"],
        "angry": [r"\bshut up\b", r"\bstupid\b", r"\bidiot\b", r"\bhate\b", r"\bbakwas\b"],
        "jealous": [r"\bother girl\b", r"\bmy girlfriend\b", r"\bmy ex\b"],
        "sad": [r"\balone\b", r"\bsad\b", r"\bmiss you\b"],
        "happy": [r"\bhappy\b", r"\byay\b", r"😂", r"🎉"],
    }
    for mood, patterns in checks.items():
        for p in patterns:
            if re.search(p, low):
                return mood
    return "normal"
