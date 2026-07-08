import time
from motor.motor_asyncio import AsyncIOMotorClient
import config

client = AsyncIOMotorClient(config.MONGO_URI)
db = client[config.MONGO_DB_NAME]

# users: DM users only - registry for broadcast + growth stats. No chat history.
users = db["users"]

# chats: groups/channels the bot has been added to - registry for broadcast + stats.
chats = db["chats"]

# intents: the actual "brain" - keyword patterns -> canned replies (non-AI).
intents = db["intents"]

# fallbacks: generic mood-based replies when no intent matches.
fallbacks = db["fallbacks"]

# learned: AI-generated replies get saved here keyed by the exact message that
# triggered them, so the next time someone sends the same message, Mongo
# answers instantly instead of calling AI again. This is how the bot's
# non-AI "brain" grows over time from real conversations.
learned = db["learned"]

# collected_stickers: stickers users send get saved here (after a basic
# content-name filter) so the bot can reply with real stickers over time
# instead of needing the owner to manually configure file_ids.
collected_stickers = db["collected_stickers"]

# badwords: editable moderation filter list.
badwords = db["badwords"]


# ---------------------------------------------------------------------------
# Users (DM only)
# ---------------------------------------------------------------------------
async def upsert_user(user_id: int, first_name: str, username: str | None):
    await users.update_one(
        {"_id": user_id},
        {
            "$set": {
                "first_name": first_name,
                "username": username,
                "last_seen": time.time(),
            },
            "$setOnInsert": {"joined_at": time.time()},
        },
        upsert=True,
    )


async def remove_user(user_id: int):
    await users.delete_one({"_id": user_id})


async def get_all_user_ids() -> list[int]:
    cursor = users.find({}, {"_id": 1})
    return [doc["_id"] async for doc in cursor]


# ---------------------------------------------------------------------------
# Chats (groups/channels bot is added to)
# ---------------------------------------------------------------------------
async def upsert_chat(chat_id: int, chat_type: str, title: str | None):
    await chats.update_one(
        {"_id": chat_id},
        {
            "$set": {
                "type": chat_type,
                "title": title,
                "last_active": time.time(),
            },
            "$setOnInsert": {"added_at": time.time()},
        },
        upsert=True,
    )


async def remove_chat(chat_id: int):
    await chats.delete_one({"_id": chat_id})


async def get_all_chat_ids() -> list[int]:
    cursor = chats.find({}, {"_id": 1})
    return [doc["_id"] async for doc in cursor]


# ---------------------------------------------------------------------------
# Stats / growth
# ---------------------------------------------------------------------------
async def get_stats() -> dict:
    now = time.time()
    today_cutoff = now - 86400
    week_cutoff = now - (7 * 86400)

    total_users = await users.count_documents({})
    new_users_today = await users.count_documents({"joined_at": {"$gte": today_cutoff}})
    new_users_week = await users.count_documents({"joined_at": {"$gte": week_cutoff}})

    total_chats = await chats.count_documents({})
    new_chats_today = await chats.count_documents({"added_at": {"$gte": today_cutoff}})
    new_chats_week = await chats.count_documents({"added_at": {"$gte": week_cutoff}})

    return {
        "total_users": total_users,
        "new_users_today": new_users_today,
        "new_users_week": new_users_week,
        "total_chats": total_chats,
        "new_chats_today": new_chats_today,
        "new_chats_week": new_chats_week,
    }


# ---------------------------------------------------------------------------
# Bot "brain" data
# ---------------------------------------------------------------------------
async def get_all_intents() -> list[dict]:
    cursor = intents.find({})
    return [doc async for doc in cursor]


async def get_fallbacks(mood: str) -> list[str]:
    doc = await fallbacks.find_one({"mood": mood})
    if doc and doc.get("responses"):
        return doc["responses"]
    doc = await fallbacks.find_one({"mood": "normal"})
    return doc["responses"] if doc else ["hmm samajh nahi aaya, thoda aur bolo na 🙂"]


async def get_badwords() -> list[str]:
    cursor = badwords.find({})
    return [doc["word"] async for doc in cursor]


# ---------------------------------------------------------------------------
# Learned replies (AI answers saved for reuse - reduces future AI dependency)
# ---------------------------------------------------------------------------
async def get_all_learned() -> list[dict]:
    cursor = learned.find({})
    return [doc async for doc in cursor]


async def save_learned(pattern: str, response: str, mood: str):
    """Upserts by exact normalized message text. Keeps up to 5 varied AI
    responses per pattern so repeated questions don't feel robotic/identical."""
    await learned.update_one(
        {"_id": pattern},
        {
            "$addToSet": {"responses": response},
            "$set": {"mood": mood, "last_used": time.time()},
            "$setOnInsert": {"created_at": time.time()},
        },
        upsert=True,
    )


# ---------------------------------------------------------------------------
# Collected stickers (auto-learned from users, filtered for safety)
# ---------------------------------------------------------------------------
async def get_all_stickers() -> list[dict]:
    cursor = collected_stickers.find({})
    return [doc async for doc in cursor]


async def save_sticker(file_id: str, set_name: str, emoji: str, mood: str):
    await collected_stickers.update_one(
        {"_id": file_id},
        {
            "$set": {
                "set_name": set_name,
                "emoji": emoji,
                "mood": mood,
                "last_seen": time.time(),
            },
            "$setOnInsert": {"added_at": time.time()},
        },
        upsert=True,
    )
