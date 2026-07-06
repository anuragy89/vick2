import asyncio
from telegram.error import Forbidden, BadRequest
import db


async def run_broadcast(bot, text: str, sender_chat_id: int):
    """Owner promotion tool: sends `text` to every DM user AND every group/channel
    the bot has been added to. Rate-limited to stay under Telegram's flood limits
    (~20 msgs/sec is a safe ceiling). Auto-cleans dead users/chats (bot blocked or
    removed) so growth stats stay accurate."""
    user_ids = await db.get_all_user_ids()
    chat_ids = await db.get_all_chat_ids()
    total = len(user_ids) + len(chat_ids)
    sent = 0
    failed = 0
    counter = 0

    await bot.send_message(
        sender_chat_id,
        f"📣 Starting broadcast...\n👤 Users: {len(user_ids)}\n👥 Groups/Channels: {len(chat_ids)}",
    )

    async def _send(target_id: int, is_chat: bool):
        nonlocal sent, failed
        try:
            await bot.send_message(target_id, text)
            sent += 1
        except Forbidden:
            # bot was blocked (user) or removed (chat) - clean it up
            failed += 1
            if is_chat:
                await db.remove_chat(target_id)
            else:
                await db.remove_user(target_id)
        except BadRequest:
            failed += 1
        except Exception:
            failed += 1

    for uid in user_ids:
        counter += 1
        await _send(uid, is_chat=False)
        if counter % 20 == 0:
            await asyncio.sleep(1)

    for cid in chat_ids:
        counter += 1
        await _send(cid, is_chat=True)
        if counter % 20 == 0:
            await asyncio.sleep(1)

    await bot.send_message(
        sender_chat_id,
        f"✅ Broadcast done.\nSent: {sent}\nFailed: {failed}\nTotal: {total}",
    )
