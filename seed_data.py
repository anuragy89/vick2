"""
Run this ONCE to populate MongoDB with the bot's default "brain":
- intents        (keyword patterns -> canned replies, the main non-AI reply source)
- fallbacks      (generic mood-based replies when nothing matches)
- badwords       (moderation filter list)

Usage:  python seed_data.py
Safe to re-run - it clears and re-inserts each collection.
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import config

INTENTS = [
    {
        "tag": "greeting",
        "patterns": [r"\bhi\b", r"\bhii+\b", r"\bhello\b", r"\bhey\b", r"\bnamaste\b"],
        "responses": [
            "heyy! kaise ho? 😊",
            "hii 👋 kya chal raha hai",
            "hello hello! bolo kya haal",
        ],
        "mood": "happy",
    },
    {
        "tag": "how_are_you",
        "patterns": [r"how are you", r"kaise ho", r"kaisi ho", r"kya haal"],
        "responses": [
            "main to mast hu, tum batao? 😊",
            "bas theek thi, ab tumse baat karke acha lag raha 🙂",
        ],
        "mood": "normal",
    },
    {
        "tag": "name_ask",
        "patterns": [r"your name", r"tumhara naam", r"tera naam", r"who are you"],
        "responses": ["main Vick hu 😊", "Vick naam hai mera, aur tumhara?"],
        "mood": "normal",
    },
    {
        "tag": "compliment",
        "patterns": [r"\bcute\b", r"\bbeautiful\b", r"\bpretty\b", r"\bsundar\b"],
        "responses": [
            "aww shut up 🙈 sach me bol rahe ho?",
            "hehe thank you 😘 tum bhi kam nahi ho",
        ],
        "mood": "flirty",
    },
    {
        "tag": "love",
        "patterns": [r"love you", r"pyaar", r"i like you"],
        "responses": ["awww 🥰 itni jaldi?", "haha sach me? 😳"],
        "mood": "flirty",
    },
    {
        "tag": "insult",
        "patterns": [r"\bstupid\b", r"\bidiot\b", r"\bshut up\b", r"\bbakwas\b"],
        "responses": ["excuse me?? rude 😤", "aise kyu bol rahe ho yaar 🙄"],
        "mood": "angry",
    },
    {
        "tag": "jealousy_trigger",
        "patterns": [r"my girlfriend", r"other girl", r"my ex"],
        "responses": ["hmm okay 🙃 aur kaun hai vo", "achha... interesting 👀"],
        "mood": "jealous",
    },
    {
        "tag": "sad",
        "patterns": [r"\bsad\b", r"\balone\b", r"\bmiss you\b"],
        "responses": ["aww kya hua? bolo mujhe 🥺", "main hu na, batao kya baat hai"],
        "mood": "sad",
    },
    {
        "tag": "thanks",
        "patterns": [r"\bthanks\b", r"\bthank you\b", r"\bshukriya\b"],
        "responses": ["welcome! 😊", "koi baat nahi 🙂"],
        "mood": "happy",
    },
    {
        "tag": "bye",
        "patterns": [r"\bbye\b", r"\bgoodnight\b", r"good night", r"\btata\b"],
        "responses": ["bye bye! take care 💗", "good night, sapno me milna 😴"],
        "mood": "normal",
    },
]

FALLBACKS = [
    {"mood": "normal", "responses": ["hmm okay", "achha, phir?", "samajh gayi, bolo aur"]},
    {"mood": "happy", "responses": ["haha nice! 😄", "yeh to badiya hai!"]},
    {"mood": "flirty", "responses": ["hehe 😏 aur batao", "cute baat kar rahe ho"]},
    {"mood": "angry", "responses": ["hmm 😒", "theek hai jaisa tumhe thik lage"]},
    {"mood": "jealous", "responses": ["okay 🙃", "achha thik hai"]},
    {"mood": "sad", "responses": ["hmm 🥺 main sun rahi hu", "it's okay, bolo"]},
]

# Common abusive/vulgar terms (English + Hinglish transliteration) to filter.
# This is intentionally a moderate starter list for basic toxicity filtering -
# expand it directly in MongoDB's `badwords` collection as needed.
BADWORDS = [
    "bc", "mc", "bhenchod", "behenchod", "madarchod", "chutiya", "chutiyapa",
    "randi", "gandu", "harami", "kutte", "kamina", "saala kutta",
    "fuck", "fucker", "fucking", "bitch", "slut", "whore", "asshole", "bastard",
    "nigger", "nigga", "retard",
]


async def main():
    client = AsyncIOMotorClient(config.MONGO_URI)
    db = client[config.MONGO_DB_NAME]

    await db["intents"].delete_many({})
    await db["intents"].insert_many(INTENTS)

    await db["fallbacks"].delete_many({})
    await db["fallbacks"].insert_many(FALLBACKS)

    await db["badwords"].delete_many({})
    await db["badwords"].insert_many([{"word": w} for w in BADWORDS])

    print(f"Seeded {len(INTENTS)} intents, {len(FALLBACKS)} fallback moods, {len(BADWORDS)} badwords.")


if __name__ == "__main__":
    asyncio.run(main())
