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
