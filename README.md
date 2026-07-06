# Vick 2.0 — Mongo-first Human-like Telegram Bot

Reply engine works like the old Vick bot: **MongoDB keyword→response patterns are the
main brain**. AI (Groq, free) is only a minority supplement — used occasionally to add
human "emotion" flavor, or as a fallback when nothing in Mongo matches. **No chat
history or per-user memory is stored** — every message is handled fresh on its own.

## 🚀 Quick Deploy to Heroku

[![Deploy to Heroku](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy?template=https://github.com/anuragy89/vick2.git)




## How replies are chosen (in order)
1. **Moderation** — flood/spam check, then abusive-language check (warns → auto-mute in
   groups after `WARN_LIMIT` warnings). Both configurable in `config.py`.
2. **Mongo intent match** — `matcher.py` checks the message against patterns stored in
   the `intents` collection. Match found → picks a random canned reply from Mongo. This
   is the primary path, non-AI, instant.
3. **AI flavor (rare)** — even on a match, `AI_FLAVOR_CHANCE` (default 12%) swaps in a
   one-off AI-generated reply instead, just for variety/emotion.
4. **AI fallback (sometimes)** — if nothing matches in Mongo, `AI_FALLBACK_CHANCE`
   (default 50%) decides between calling AI once (stateless, single message, no memory)
   or using a generic canned fallback reply from the `fallbacks` collection.

Because Mongo intents are the default path and AI is only used a fraction of the time,
your Groq usage/cost stays low while still feeling more "alive" than a pure rule bot.

## Broadcast & Stats (owner tools)
- **`/broadcast <message>`** — sends to every DM user **and** every group/channel the bot
  has been added to. Rate-limited (~20 msgs/sec) to avoid Telegram flood bans. If the bot
  gets blocked by a user or removed from a group, that entry is auto-removed from the DB
  so your stats and future broadcasts stay accurate.
- **`/stats`** — shows total users, total groups/channels, and growth (new today / new
  this week) for both — a quick way to see the bot growing.
- Bot's presence in a group is tracked automatically the moment it's added (via
  Telegram's `my_chat_member` update) and removed automatically if it's kicked/leaves.

## Moderation
- **Abuse filter**: word list lives in Mongo `badwords` collection — edit anytime without
  redeploying. Starter list seeded by `seed_data.py`, expand it as you like.
- **Flood control**: more than `SPAM_MAX_MESSAGES` messages within `SPAM_WINDOW_SECONDS`
  seconds triggers a "slow down" reply.
- **Warnings**: abusive language gives a warning; after `WARN_LIMIT` warnings the bot
  tries to mute the user in groups (needs admin rights) or just keeps warning in DM.
- Warning/flood counters are **in-memory only** (reset on restart) — this is operational
  moderation state, not conversational memory, so it fits the "no memory" requirement
  while still catching repeat abuse in a live session.

## No memory, by design
- `users` collection stores only `first_name`, `username`, `is_dm` — enough for
  `/broadcast` to know who to message. No messages, no mood history, no context.
- Mood per reply is guessed fresh from the **current message only** (`matcher.detect_mood`).
- AI calls send just the current message, nothing else — genuinely stateless.

## 1. Get your free keys
1. **Bot token**: [@BotFather](https://t.me/BotFather) → `/newbot`
2. **Groq API key** (free): https://console.groq.com/keys
3. **MongoDB Atlas** (free M0 cluster): https://www.mongodb.com/cloud/atlas/register
   → create cluster → Database Access (user/pass) → Network Access (allow `0.0.0.0/0`
   for Heroku) → copy the connection string

## 2. Configure
Copy `.env.example` → `.env` and fill in every value (bot token, owner id, Groq key,
Mongo URI, support/channel links, bot username without @).

## 3. Seed the bot's brain (one-time)
```bash
pip install -r requirements.txt
python seed_data.py
```
This populates `intents`, `fallbacks`, and `badwords` in MongoDB. Add more intents
anytime directly in Mongo (Atlas UI or a script) — no redeploy needed, the bot refreshes
its intent cache every `INTENT_CACHE_TTL` seconds (default 5 min).

Example intent document shape:
```json
{
  "tag": "greeting",
  "patterns": ["\\bhi\\b", "\\bhello\\b"],
  "responses": ["heyy!", "hii kaise ho"],
  "mood": "happy"
}
```

## 4. Run locally
```bash
python main.py
```

## 5. Deploy to Heroku
```bash
heroku create your-app-name
git init && git add . && git commit -m "Vick 2.0"
heroku git:remote -a your-app-name
git push heroku main

heroku config:set BOT_TOKEN=... OWNER_ID=... GROQ_API_KEY=... MONGO_URI=... \
  SUPPORT_GROUP_URL=... CHANNEL_URL=... BOT_USERNAME=...

heroku ps:scale worker=1
```
This app has no web process — it's a polling worker, matching the Procfile's `worker:`
entry. Standard-2X comfortably handles a large volume of chats since Mongo lookups and
occasional Groq calls are both async/non-blocking.

## 6. Add real stickers per mood
Send any sticker to the bot in DM as the OWNER — it replies with the `file_id`. Paste
into `moods.py` → `STICKERS`. Fires ~30% of the time alongside a text reply.

## Project structure
```
main.py         - bot entrypoint, handlers, moderation + reply orchestration
matcher.py      - Mongo intent matching + stateless mood guess (the "brain")
ai_engine.py    - stateless single-turn Groq call (minority fallback/flavor only)
moderation.py   - abuse word filter + flood detection + warning counters
moods.py        - emoji sets + sticker pool helpers
db.py           - async MongoDB (motor) - users registry, intents, fallbacks, badwords
seed_data.py    - one-time script to populate intents/fallbacks/badwords
keyboards.py    - inline button UI
broadcast.py    - owner broadcast with rate limiting
config.py       - env vars + AI ratio + moderation thresholds
```
