import logging
import random
from datetime import datetime, timedelta, timezone

from telegram import Update, ChatPermissions
from telegram.constants import ChatAction, ParseMode
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

import config
import db
import ai_engine
import matcher
import moderation
from moods import mood_emoji, maybe_sticker
from keyboards import start_keyboard, back_keyboard
from broadcast import run_broadcast

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger("vick2")

WELCOME_TEXT = (
    "heyy 👋 main Vick hu~\n\n"
    "bas normal insaan jaisi baat karti hu, mujhe kuch bhi bolo main reply karungi 😊\n"
    "group me add karna ho ya kuch help chahiye, neeche buttons se dekh lo 👇"
)

HELP_TEXT = (
    "🆘 *Help*\n\n"
    "• Bas mujhe message karo, main reply karungi jaise ek normal ladki karti hai.\n"
    "• Group me add karke bhi mujhse baat kar sakte ho — bas mujhe *mention* ya *reply* karo.\n"
    "• Abusive language ya spam allowed nahi hai, warnings ke baad mute ho sakte ho.\n"
    "• Koi issue ho to Support group join karo.\n"
)


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        await db.upsert_user(user.id, user.first_name, user.username)
        await update.message.reply_text(WELCOME_TEXT, reply_markup=start_keyboard())
    else:
        await db.upsert_chat(chat.id, chat.type, chat.title)
        await update.message.reply_text("heyy! main Vick 😊 mujhe mention/reply karke baat karo yahan.")


async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=back_keyboard())


async def stats_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.OWNER_ID:
        return
    s = await db.get_stats()
    text = (
        "📊 *Bot Growth Stats*\n\n"
        f"👤 *Users (DM):* {s['total_users']}\n"
        f"   ➕ {s['new_users_today']} today  |  ➕ {s['new_users_week']} this week\n\n"
        f"👥 *Groups/Channels:* {s['total_chats']}\n"
        f"   ➕ {s['new_chats_today']} today  |  ➕ {s['new_chats_week']} this week\n\n"
        f"📈 *Total broadcast reach:* {s['total_users'] + s['total_chats']}"
    )
    await update.message.reply_text(text, parse_mode=ParseMode.MARKDOWN)


async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.OWNER_ID:
        return
    if not context.args:
        await update.message.reply_text("Usage: /broadcast your message here")
        return
    text = update.message.text.split(" ", 1)[1]
    await run_broadcast(context.bot, text, update.effective_chat.id)


async def getstickerid_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != config.OWNER_ID:
        return
    if update.message.reply_to_message and update.message.reply_to_message.sticker:
        fid = update.message.reply_to_message.sticker.file_id
        await update.message.reply_text(f"`{fid}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("Reply to a sticker with /getstickerid.")


# ---------------------------------------------------------------------------
# Track when the bot is added to / removed from a group or channel
# ---------------------------------------------------------------------------
async def track_chat_membership(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.my_chat_member
    chat = result.chat
    new_status = result.new_chat_member.status

    if new_status in ("member", "administrator"):
        await db.upsert_chat(chat.id, chat.type, chat.title)
        logger.info(f"Bot added to chat {chat.id} ({chat.title})")
    elif new_status in ("left", "kicked"):
        await db.remove_chat(chat.id)
        logger.info(f"Bot removed from chat {chat.id}")


# ---------------------------------------------------------------------------
# Callback buttons
# ---------------------------------------------------------------------------
async def button_cb(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    if q.data == "help":
        await q.edit_message_text(HELP_TEXT, parse_mode=ParseMode.MARKDOWN, reply_markup=back_keyboard())
    elif q.data == "back":
        await q.edit_message_text(WELCOME_TEXT, reply_markup=start_keyboard())


# ---------------------------------------------------------------------------
# Sticker handler (also doubles as owner's file_id grabber)
# ---------------------------------------------------------------------------
async def sticker_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if user.id == config.OWNER_ID:
        fid = update.message.sticker.file_id
        await update.message.reply_text(f"file_id:\n`{fid}`", parse_mode=ParseMode.MARKDOWN)
    else:
        await update.message.reply_text("haha nice sticker 😄")


# ---------------------------------------------------------------------------
# Group mention/reply gate
# ---------------------------------------------------------------------------
def _should_respond_in_group(update: Update, bot_username: str) -> bool:
    msg = update.message
    if msg.reply_to_message and msg.reply_to_message.from_user and \
       msg.reply_to_message.from_user.username == bot_username:
        return True
    if msg.text and f"@{bot_username}".lower() in msg.text.lower():
        return True
    return False


# ---------------------------------------------------------------------------
# Core chat logic - fully stateless (no history, no per-user memory)
# ---------------------------------------------------------------------------
async def chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    user = update.effective_user
    text = update.message.text

    if chat.type == "private":
        await db.upsert_user(user.id, user.first_name, user.username)
    else:
        # keep the chat's "last_active"/existence fresh even if my_chat_member
        # was somehow missed (e.g. bot added before this deployment existed)
        await db.upsert_chat(chat.id, chat.type, chat.title)
        bot_username = context.bot.username
        if not _should_respond_in_group(update, bot_username):
            return
        text = text.replace(f"@{bot_username}", "").strip()

    if not text:
        return

    # ---------------- Moderation: spam flood ----------------
    if moderation.is_flooding(user.id):
        await update.message.reply_text("thoda slow bolo na, itni jaldi jaldi mat karo 😅")
        return

    # ---------------- Moderation: abusive language ----------------
    if await moderation.is_abusive(text):
        warns = moderation.add_warning(user.id)
        if warns >= config.WARN_LIMIT:
            if chat.type != "private":
                try:
                    mute_permissions = ChatPermissions(
                        can_send_messages=False,
                        can_send_audios=False,
                        can_send_documents=False,
                        can_send_photos=False,
                        can_send_videos=False,
                        can_send_video_notes=False,
                        can_send_voice_notes=False,
                        can_send_polls=False,
                        can_send_other_messages=False,
                        can_add_web_page_previews=False,
                    )
                    until = datetime.now(timezone.utc) + timedelta(minutes=config.MUTE_MINUTES)
                    await context.bot.restrict_chat_member(
                        chat.id, user.id, permissions=mute_permissions, until_date=until
                    )
                    await update.message.reply_text(
                        f"{user.first_name} ko {config.MUTE_MINUTES} min ke liye mute kar diya 🚫"
                    )
                except Exception:
                    logger.warning("Could not mute user (bot may lack admin rights)")
                    await update.message.reply_text("please stop using abusive language 🚫")
            else:
                await update.message.reply_text("please stop using abusive language 🚫")
            moderation.reset_warnings(user.id)
        else:
            await update.message.reply_text(
                f"aise mat bolo please 😐 ({warns}/{config.WARN_LIMIT} warning)"
            )
        return

    # instant "typing..." feedback -> feels fast/human
    await context.bot.send_chat_action(chat_id=chat.id, action=ChatAction.TYPING)

    # stateless mood guess from THIS message only
    mood = matcher.detect_mood(text)

    # ---------------- Primary reply source: MongoDB intents ----------------
    canned_reply, intent_mood = await matcher.find_reply(text)
    if intent_mood:
        mood = intent_mood

    reply = None

    if canned_reply:
        if random.random() < config.AI_FLAVOR_CHANCE:
            try:
                reply = await ai_engine.generate_reply(text, mood)
            except Exception:
                logger.warning("AI flavor call failed, using canned reply instead")
        if not reply:
            reply = canned_reply
    else:
        if random.random() < config.AI_FALLBACK_CHANCE:
            try:
                reply = await ai_engine.generate_reply(text, mood)
            except Exception:
                logger.warning("AI fallback call failed, using canned fallback instead")
        if not reply:
            fallback_options = await db.get_fallbacks(mood)
            reply = random.choice(fallback_options)

    if not any(e in reply for e in ["😊", "😄", "😍", "😉", "😔", "😤", "🥰"]):
        if random.random() < 0.3:
            reply = f"{reply} {mood_emoji(mood)}"

    await update.message.reply_text(reply)

    sticker_id = maybe_sticker(mood)
    if sticker_id:
        await context.bot.send_sticker(chat.id, sticker_id)


# ---------------------------------------------------------------------------
# App bootstrap
# ---------------------------------------------------------------------------
def build_app() -> Application:
    app = ApplicationBuilder().token(config.BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    app.add_handler(CommandHandler("stats", stats_cmd))
    app.add_handler(CommandHandler("broadcast", broadcast_cmd))
    app.add_handler(CommandHandler("getstickerid", getstickerid_cmd))
    app.add_handler(CallbackQueryHandler(button_cb))
    app.add_handler(ChatMemberHandler(track_chat_membership, ChatMemberHandler.MY_CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.Sticker.ALL, sticker_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, chat_handler))

    return app


if __name__ == "__main__":
    application = build_app()
    logger.info("Vick 2.0 starting (polling mode, mongo-first + light AI)...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)
