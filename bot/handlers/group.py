from __future__ import annotations

import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.config import (
    INTRO_ACCEPTED,
    INTRO_NUDGE,
    INTRO_REMINDER,
    MAIN_GROUP_ID,
)
from bot.database import STATUS_INTRODUCED, STATUS_PENDING, add_user, get_user, mark_introduced
from bot.utils.validation import validate_intro

logger = logging.getLogger(__name__)


def _escape_md(text: str) -> str:
    special = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{ch}" if ch in special else ch for ch in text)


async def handle_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle every text message in the main group.

    - If user is already introduced → do nothing, let message through.
    - If user is pending → check if the message is a valid intro.
      - Valid intro → mark introduced, send congrats.
      - Too short intro → delete message, send nudge.
      - Not an intro at all → delete message, send reminder.
    """
    message = update.effective_message
    if not message or not message.from_user:
        return

    if message.chat.id != MAIN_GROUP_ID:
        return

    user = message.from_user
    if user.is_bot:
        return

    # Look up user in DB
    db_user = await get_user(user.id)

    # If user is already introduced, let them chat
    if db_user and db_user["status"] == STATUS_INTRODUCED:
        return

    # User is pending (or not tracked yet) — they need to introduce themselves
    if not db_user:
        await add_user(user.id, user.username, user.full_name)

    text = message.text or message.caption or ""
    mention = f"[{_escape_md(user.full_name)}](tg://user?id={user.id})"

    # Check if this message looks like an intro attempt
    is_valid, missing = validate_intro(text)

    if is_valid:
        # Valid intro — mark user as introduced
        await mark_introduced(user.id, message.message_id)
        logger.info("User %d (%s) completed introduction.", user.id, user.full_name)

        try:
            await message.reply_text(
                INTRO_ACCEPTED.format(mention=mention),
                parse_mode="MarkdownV2",
            )
        except Exception:
            logger.exception("Failed to send acceptance message for user %d", user.id)
    else:
        # Delete the non-intro message
        try:
            await message.delete()
        except Exception:
            logger.exception("Failed to delete message from user %d", user.id)

        # Decide whether to nudge (looks like an attempt) or remind (not an intro)
        looks_like_attempt = len(text) > 30
        reply_text = INTRO_NUDGE if looks_like_attempt else INTRO_REMINDER.format(mention=mention)

        try:
            reminder = await context.bot.send_message(
                chat_id=MAIN_GROUP_ID,
                text=reply_text,
                parse_mode="MarkdownV2",
            )
            # Auto-delete the reminder after 30 seconds
            context.job_queue.run_once(
                _delete_message,
                30,
                data={"chat_id": MAIN_GROUP_ID, "message_id": reminder.message_id},
            )
        except Exception:
            logger.exception("Failed to send reminder to user %d", user.id)


async def _delete_message(context: ContextTypes.DEFAULT_TYPE) -> None:
    data = context.job.data
    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
        )
    except Exception:
        pass


def get_handler() -> MessageHandler:
    return MessageHandler(
        filters.Chat(MAIN_GROUP_ID) & (filters.TEXT | filters.CAPTION) & ~filters.COMMAND,
        handle_group_message,
    )
