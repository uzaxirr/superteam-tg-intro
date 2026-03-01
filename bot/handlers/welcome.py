import logging
from telegram import ChatMember, ChatMemberUpdated, Update
from telegram.ext import ChatMemberHandler, ContextTypes

from bot.config import EXAMPLE_INTRO, MAIN_GROUP_ID, WELCOME_MESSAGE
from bot.database import STATUS_INTRODUCED, add_user, get_user

logger = logging.getLogger(__name__)


def _is_new_member(update: ChatMemberUpdated) -> bool:
    """Check if the update represents a user newly joining the chat."""
    old = update.old_chat_member
    new = update.new_chat_member

    if old is None:
        return new.status in (ChatMember.MEMBER, ChatMember.RESTRICTED)

    was_not_member = old.status in (
        ChatMember.LEFT,
        ChatMember.BANNED,
    )
    is_now_member = new.status in (
        ChatMember.MEMBER,
        ChatMember.RESTRICTED,
    )
    return was_not_member and is_now_member


def _escape_md(text: str) -> str:
    special = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{ch}" if ch in special else ch for ch in text)


async def handle_chat_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle new members joining the main group."""
    if not update.chat_member:
        return

    chat_member = update.chat_member
    if chat_member.chat.id != MAIN_GROUP_ID:
        return

    if not _is_new_member(chat_member):
        return

    user = chat_member.new_chat_member.user
    if user.is_bot:
        return

    logger.info("New member detected: %s (id=%d)", user.full_name, user.id)

    # Check if user already introduced (rejoining case)
    existing = await get_user(user.id)
    if existing and existing["status"] == STATUS_INTRODUCED:
        logger.info("User %d already introduced, skipping welcome.", user.id)
        return

    # Store user in DB as pending
    await add_user(user.id, user.username, user.full_name)

    # Send welcome message in the group
    mention = f"[{_escape_md(user.full_name)}](tg://user?id={user.id})"
    full_message = f"{mention}\n{WELCOME_MESSAGE}\n{EXAMPLE_INTRO}"

    try:
        await context.bot.send_message(
            chat_id=MAIN_GROUP_ID,
            text=full_message,
            parse_mode="MarkdownV2",
        )
    except Exception:
        logger.exception("Failed to send welcome message for user %d", user.id)

    # Also try to DM the user
    try:
        await context.bot.send_message(
            chat_id=user.id,
            text=full_message,
            parse_mode="MarkdownV2",
        )
    except Exception:
        logger.debug("Could not DM user %d (they may not have started the bot).", user.id)


def get_handler() -> ChatMemberHandler:
    return ChatMemberHandler(handle_chat_member, ChatMemberHandler.CHAT_MEMBER)
