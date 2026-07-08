import re
import time
import random

import db

_cache = {"intents": [], "learned": [], "loaded_at": 0}


async def _refresh_cache():
    _cache["intents"] = await db.get_all_intents()
    _cache["learned"] = await db.get_all_learned()
    _cache["loaded_at"] = time.time()


async def _get_cache() -> dict:
    import config
    now = time.time()
    if now - _cache["loaded_at"] > config.INTENT_CACHE_TTL or (
        not _cache["intents"] and not _cache["learned"]
    ):
        await _refresh_cache()
    return _cache


def _matches(pattern: str, text: str) -> bool:
    try:
        return re.search(pattern, text, re.IGNORECASE) is not None
    except re.error:
        return pattern.lower() in text.lower()


def _normalize(text: str) -> str:
    return text.strip().lower()


async def find_reply(text: str):
    """Looks up a reply in two layers, both from Mongo, no AI involved:
    1. Seeded intents (regex keyword patterns, curated via seed_data.py)
    2. Learned replies (AI answers saved from real past conversations)
    Returns (reply, mood) or (None, None) if nothing matches either layer.
    """
    cache = await _get_cache()

    for intent in cache["intents"]:
        for pattern in intent.get("patterns", []):
            if _matches(pattern, text):
                responses = intent.get("responses", [])
                if responses:
                    return random.choice(responses), intent.get("mood", "normal")

    normalized = _normalize(text)
    for doc in cache["learned"]:
        if doc.get("_id") == normalized:
            responses = doc.get("responses", [])
            if responses:
                return random.choice(responses), doc.get("mood", "normal")

    return None, None


async def learn(text: str, response: str, mood: str):
    """Saves an AI-generated reply to Mongo keyed by the exact message that
    triggered it. Next time the same message comes in, find_reply() answers
    it from Mongo directly - no AI call needed. This is how AI dependency
    goes down over time as real conversations get recorded."""
    normalized = _normalize(text)
    if not normalized:
        return

    await db.save_learned(normalized, response, mood)

    # keep the in-memory cache in sync immediately, don't wait for TTL refresh
    for doc in _cache["learned"]:
        if doc.get("_id") == normalized:
            responses = doc.setdefault("responses", [])
            if response not in responses:
                responses.append(response)
            doc["mood"] = mood
            return
    _cache["learned"].append({"_id": normalized, "responses": [response], "mood": mood})


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
