import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID", "0"))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# llama-3.3-70b-versatile was deprecated by Groq (June 2026) - using its
# recommended replacement. If Groq deprecates this one too in the future,
# just update this one line (or the GROQ_MODEL env var) - nothing else
# needs to change.
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"

MONGO_URI = os.getenv("MONGO_URI")
MONGO_DB_NAME = os.getenv("MONGO_DB_NAME", "vick2bot")

SUPPORT_GROUP_URL = os.getenv("SUPPORT_GROUP_URL", "https://t.me/")
CHANNEL_URL = os.getenv("CHANNEL_URL", "https://t.me/")
BOT_USERNAME = os.getenv("BOT_USERNAME", "your_bot")

# ---- Group behavior ----
# True: bot replies to EVERY message in a group (needs privacy mode OFF via
#       BotFather -> /setprivacy -> Disable, otherwise Telegram won't even
#       deliver plain messages to the bot in the first place).
# False: bot only replies when mentioned or replied to.
GROUP_REPLY_ALL = os.getenv("GROUP_REPLY_ALL", "true").lower() == "true"

# ---- AI usage ----
# When NO mongo intent matches, AI is now the primary fallback (always tried
# first) - the canned fallback text is only used if the AI call itself fails.
AI_FLAVOR_CHANCE = 0.12    # when an intent DOES match, small chance to use AI instead for variety

# ---- Moderation ----
SPAM_WINDOW_SECONDS = 4
SPAM_MAX_MESSAGES = 8        # a bit higher since group-wide replies mean more traffic
WARN_LIMIT = 3
MUTE_MINUTES = 10

# how often the intent cache refreshes from Mongo (seconds)
INTENT_CACHE_TTL = 300
