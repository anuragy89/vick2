import re
import time
import config
import db

# ---------------------------------------------------------------------------
# These are runtime-only, in-memory structures (reset on restart). They are
# NOT conversation memory / chat history - just operational counters needed
# to catch spam floods and repeat-abuse within a live session.
# ---------------------------------------------------------------------------
_spam_tracker: dict[int, list[float]] = {}
_warn_counts: dict[int, int] = {}

_badwords_cache = {"words": [], "loaded_at": 0}
_BADWORDS_TTL = 300


async def _get_badwords() -> list[str]:
    now = time.time()
    if now - _badwords_cache["loaded_at"] > _BADWORDS_TTL or not _badwords_cache["words"]:
        _badwords_cache["words"] = await db.get_badwords()
        _badwords_cache["loaded_at"] = now
    return _badwords_cache["words"]


async def is_abusive(text: str) -> bool:
    words = await _get_badwords()
    low = f" {text.lower()} "
    for w in words:
        if re.search(rf"\b{re.escape(w.lower())}\b", low):
            return True
    return False


def is_flooding(user_id: int) -> bool:
    """True if user sent too many messages within the configured window."""
    now = time.time()
    timestamps = _spam_tracker.setdefault(user_id, [])
    timestamps.append(now)
    # keep only recent ones
    cutoff = now - config.SPAM_WINDOW_SECONDS
    timestamps[:] = [t for t in timestamps if t > cutoff]
    return len(timestamps) > config.SPAM_MAX_MESSAGES


def add_warning(user_id: int) -> int:
    _warn_counts[user_id] = _warn_counts.get(user_id, 0) + 1
    return _warn_counts[user_id]


def get_warnings(user_id: int) -> int:
    return _warn_counts.get(user_id, 0)


def reset_warnings(user_id: int):
    _warn_counts[user_id] = 0
