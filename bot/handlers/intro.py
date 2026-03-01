import logging
from telegram import ChatPermissions, Update
from telegram.ext import ContextTypes, MessageHandler, filters

from bot.config import (
    INTRO_ACCEPTED,
    INTRO_CHANNEL_ID,
    INTRO_NUDGE,
    MAIN_GROUP_ID,
)
from bot.database import STATUS_PENDING, get_user, mark_introduced
from bot.utils.validation import validate_intro

logger = logging.getLogger(__name__)


async def handle_intro_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Monitor messages in the intro channel and validate introductions."""
    message = update.effective_message
    if not message or not message.from_user:
        return

    if message.chat.id != INTRO_CHANNEL_ID:
        return

    user = message.from_user
    if user.is_bot:
        return

    # Check if user is pending
    db_user = await get_user(user.id)
    if not db_user or db_user["status"] != STATUS_PENDING:
        return

    text = message.text or message.caption or ""
    is_valid, missing = validate_intro(text)

    if is_valid:
        # Mark as introduced
        await mark_introduced(user.id, message.message_id)
        logger.info("User %d completed introduction.", user.id)

        # Unrestrict in main group
        try:
            await context.bot.restrict_chat_member(
                chat_id=MAIN_GROUP_ID,
                user_id=user.id,
                permissions=ChatPermissions(
                    can_send_messages=True,
                    can_send_media_messages=True,
                    can_send_polls=True,
                    can_send_other_messages=True,
                    can_add_web_page_previews=True,
                    can_invite_users=True,
                ),
            )
            logger.info("Unrestricted user %d in main group.", user.id)
        except Exception:
            logger.exception("Failed to unrestrict user %d", user.id)

        # Send acceptance message in intro channel
        mention = f"[{_escape_md(user.full_name)}](tg://user?id={user.id})"
        intro_link = _build_channel_link(context)
        try:
            await message.reply_text(
                INTRO_ACCEPTED.format(mention=mention, intro_link=intro_link),
                parse_mode="MarkdownV2",
            )
        except Exception:
            logger.exception("Failed to send acceptance message for user %d", user.id)

        # Also notify in main group
        try:
            await context.bot.send_message(
                chat_id=MAIN_GROUP_ID,
                text=INTRO_ACCEPTED.format(mention=mention, intro_link=intro_link),
                parse_mode="MarkdownV2",
            )
        except Exception:
            logger.exception("Failed to send main group notification for user %d", user.id)
    else:
        # Nudge the user to improve
        try:
            await message.reply_text(
                INTRO_NUDGE,
                parse_mode="MarkdownV2",
            )
        except Exception:
            logger.exception("Failed to send nudge to user %d", user.id)


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
        filters.Chat(INTRO_CHANNEL_ID) & filters.TEXT & ~filters.COMMAND,
        handle_intro_message,
    )
