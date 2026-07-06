import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "vick2bot")

SUPPORT_GROUP_URL = os.getenv("SUPPORT_GROUP_URL", "https://t.me/")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/")
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot")

# ---- AI usage ratios (keep AI as a minority, not the main brain) ----
AI_FALLBACK_CHANCE = 0.5   # when NO mongo intent matches, chance to call AI vs canned fallback
AI_FLAVOR_CHANCE = 0.12    # when an intent DOES match, small chance to use AI instead for variety

# ---- Moderation ----
SPAM_WINDOW_SECONDS = 4      # time window
SPAM_MAX_MESSAGES = 5        # max messages allowed within window before flagged as flood
WARN_LIMIT = 3                # warnings before auto-mute (group only)
MUTE_MINUTES = 10

# how often the intent cache refreshes from Mongo (seconds)
INTENT_CACHE_TTL = 300
