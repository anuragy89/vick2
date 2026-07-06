from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import config


def start_keyboard() -> InlineKeyboardMarkup:
    add_url = f"https://t.me/{config.BOT_USERNAME}?startgroup=true"
    rows = [
        [InlineKeyboardButton("➕ Add me to your Group", url=add_url)],
        [
            InlineKeyboardButton("🆘 Help", callback_data="help"),
            InlineKeyboardButton("💬 Support", url=config.SUPPORT_GROUP_URL),
        ],
        [InlineKeyboardButton("📢 Channel", url=config.CHANNEL_URL)],
    ]
    return InlineKeyboardMarkup(rows)


def back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Back", callback_data="back")]])
