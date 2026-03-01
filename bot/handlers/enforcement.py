import logging
from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.config import INTRO_CHANNEL_ID, INTRO_REMINDER, MAIN_GROUP_ID
from bot.database import STATUS_INTRODUCED, get_user

logger = logging.getLogger(__name__)


async def handle_main_group_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete messages from users who haven't introduced themselves yet."""
    message = update.effective_message
    if not message or not message.from_user:
        return

    if message.chat.id != MAIN_GROUP_ID:
        return

    user = message.from_user
    if user.is_bot:
        return

    db_user = await get_user(user.id)

    # If user is not in DB or not introduced, enforce
    if db_user and db_user["status"] == STATUS_INTRODUCED:
        return

    # Delete the message
    try:
        await message.delete()
        logger.info("Deleted message from non-introduced user %d.", user.id)
    except Exception:
        logger.exception("Failed to delete message from user %d", user.id)

    # Send a reminder (and delete it after 30 seconds)
    mention = f"[{_escape_md(user.full_name)}](tg://user?id={user.id})"
    intro_link = _build_channel_link(context)
    try:
        reminder = await context.bot.send_message(
            chat_id=MAIN_GROUP_ID,
            text=INTRO_REMINDER.format(mention=mention, intro_link=intro_link),
            parse_mode="MarkdownV2",
        )
        # Schedule deletion of the reminder after 30 seconds
        context.job_queue.run_once(
            _delete_reminder,
            when=30,
            data={"chat_id": MAIN_GROUP_ID, "message_id": reminder.message_id},
        )
    except Exception:
        logger.exception("Failed to send reminder for user %d", user.id)


async def _delete_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Delete a reminder message after timeout."""
    data = context.job.data
    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
        )
    except Exception:
        pass


def _build_channel_link(context: ContextTypes.DEFAULT_TYPE) -> str:
    channel_username = context.bot_data.get("intro_channel_username")
    if channel_username:
        return f"https://t.me/{channel_username}"
    channel_id = str(INTRO_CHANNEL_ID)
    if channel_id.startswith("-100"):
        return f"https://t.me/c/{channel_id[4:]}"
    return f"https://t.me/c/{channel_id.lstrip('-')}"


def _escape_md(text: str) -> str:
    special = r"_*[]()~`>#+-=|{}.!"
    escaped = ""
    for ch in text:
        if ch in special:
            escaped += f"\\{ch}"
        else:
            escaped += ch
    return escaped


def get_handler() -> MessageHandler:
    return MessageHandler(
        filters.Chat(MAIN_GROUP_ID) & ~filters.COMMAND & ~filters.StatusUpdate.ALL,
        handle_main_group_message,
    )
