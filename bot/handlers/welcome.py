import logging
from telegram import ChatMember, ChatMemberUpdated, ChatPermissions, Update
from telegram.ext import ChatMemberHandler, ContextTypes

from bot.config import (
    EXAMPLE_INTRO,
    INTRO_CHANNEL_ID,
    MAIN_GROUP_ID,
    WELCOME_MESSAGE,
)
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
        logger.info("User %d already introduced, skipping restriction.", user.id)
        return

    # Store user in DB
    await add_user(user.id, user.username, user.full_name)

    # Restrict user: cannot send messages
    try:
        await context.bot.restrict_chat_member(
            chat_id=MAIN_GROUP_ID,
            user_id=user.id,
            permissions=ChatPermissions(
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
                can_invite_users=False,
            ),
        )
        logger.info("Restricted user %d in main group.", user.id)
    except Exception:
        logger.exception("Failed to restrict user %d", user.id)

    # Build intro channel link
    intro_link = _build_channel_link(context)

    # Send welcome message in main group
    mention = f"[{_escape_md(user.full_name)}](tg://user?id={user.id})"
    welcome = WELCOME_MESSAGE.format(intro_link=intro_link)
    full_message = f"{mention}\n{welcome}\n{EXAMPLE_INTRO}"

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
        # User may not have started the bot — this is expected
        logger.debug("Could not DM user %d (they may not have started the bot).", user.id)


def _build_channel_link(context: ContextTypes.DEFAULT_TYPE) -> str:
    """Build a t.me link for the intro channel."""
    # If we have the channel info cached, use its username
    channel_username = context.bot_data.get("intro_channel_username")
    if channel_username:
        return f"https://t.me/{channel_username}"
    # Fallback: use the numeric ID link format
    channel_id = str(INTRO_CHANNEL_ID)
    if channel_id.startswith("-100"):
        return f"https://t.me/c/{channel_id[4:]}"
    return f"https://t.me/c/{channel_id.lstrip('-')}"


def _escape_md(text: str) -> str:
    """Escape special characters for MarkdownV2."""
    special = r"_*[]()~`>#+-=|{}.!"
    escaped = ""
    for ch in text:
        if ch in special:
            escaped += f"\\{ch}"
        else:
            escaped += ch
    return escaped


def get_handler() -> ChatMemberHandler:
    return ChatMemberHandler(handle_chat_member, ChatMemberHandler.CHAT_MEMBER)
