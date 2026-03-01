from __future__ import annotations

import logging
from telegram import ChatPermissions, Update
from telegram.ext import CommandHandler, ContextTypes

from bot.config import ADMIN_IDS, MAIN_GROUP_ID
from bot.database import (
    STATUS_INTRODUCED,
    add_user,
    get_stats,
    get_user,
    mark_introduced,
    reset_user,
)

logger = logging.getLogger(__name__)


def _is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


def _extract_target_user(update: Update) -> tuple[int | None, str | None]:
    """Extract target user ID from reply or command argument."""
    message = update.effective_message

    # Check if replying to someone
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user
        return target.id, target.full_name

    # Check command arguments for user ID
    if message.text:
        parts = message.text.split()
        if len(parts) > 1:
            try:
                user_id = int(parts[1])
                return user_id, None
            except ValueError:
                pass

    return None, None


async def cmd_reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Reset a user's intro status. Usage: /reset (reply) or /reset <user_id>"""
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text("You are not authorized to use this command.")
        return

    target_id, target_name = _extract_target_user(update)
    if not target_id:
        await update.effective_message.reply_text(
            "Reply to a user's message or provide a user ID: /reset <user_id>"
        )
        return

    success = await reset_user(target_id)
    if not success:
        await update.effective_message.reply_text(f"User {target_id} not found in database.")
        return

    # Re-restrict the user
    try:
        await context.bot.restrict_chat_member(
            chat_id=MAIN_GROUP_ID,
            user_id=target_id,
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
    except Exception:
        logger.exception("Failed to re-restrict user %d", target_id)

    display = target_name or str(target_id)
    await update.effective_message.reply_text(
        f"Reset intro status for {display}. They must re-introduce themselves."
    )
    logger.info("Admin %d reset user %d", update.effective_user.id, target_id)


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Manually approve a user. Usage: /approve (reply) or /approve <user_id>"""
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text("You are not authorized to use this command.")
        return

    target_id, target_name = _extract_target_user(update)
    if not target_id:
        await update.effective_message.reply_text(
            "Reply to a user's message or provide a user ID: /approve <user_id>"
        )
        return

    # Ensure user exists in DB
    db_user = await get_user(target_id)
    if not db_user:
        await add_user(target_id, None, target_name or "Unknown")

    await mark_introduced(target_id, 0)

    # Unrestrict
    try:
        await context.bot.restrict_chat_member(
            chat_id=MAIN_GROUP_ID,
            user_id=target_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_audios=True,
                can_send_documents=True,
                can_send_photos=True,
                can_send_videos=True,
                can_send_video_notes=True,
                can_send_voice_notes=True,
                can_send_polls=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
                can_invite_users=True,
            ),
        )
    except Exception:
        logger.exception("Failed to unrestrict user %d", target_id)

    display = target_name or str(target_id)
    await update.effective_message.reply_text(f"Manually approved {display}. They can now chat.")
    logger.info("Admin %d approved user %d", update.effective_user.id, target_id)


async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Check a user's onboarding status. Usage: /status (reply) or /status <user_id>"""
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text("You are not authorized to use this command.")
        return

    target_id, target_name = _extract_target_user(update)
    if not target_id:
        await update.effective_message.reply_text(
            "Reply to a user's message or provide a user ID: /status <user_id>"
        )
        return

    db_user = await get_user(target_id)
    if not db_user:
        await update.effective_message.reply_text(f"User {target_id} not found in database.")
        return

    status_emoji = "✅" if db_user["status"] == STATUS_INTRODUCED else "⏳"
    lines = [
        f"User: {db_user['full_name']} (@{db_user['username'] or 'N/A'})",
        f"ID: {db_user['user_id']}",
        f"Status: {status_emoji} {db_user['status']}",
        f"Joined: {db_user['joined_at']}",
    ]
    if db_user["introduced_at"]:
        lines.append(f"Introduced: {db_user['introduced_at']}")

    await update.effective_message.reply_text("\n".join(lines))


async def cmd_stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Show onboarding statistics. Usage: /stats"""
    if not _is_admin(update.effective_user.id):
        await update.effective_message.reply_text("You are not authorized to use this command.")
        return

    stats = await get_stats()
    text = (
        f"📊 Onboarding Stats\n\n"
        f"Total tracked users: {stats['total']}\n"
        f"⏳ Pending: {stats['pending']}\n"
        f"✅ Introduced: {stats['introduced']}"
    )
    await update.effective_message.reply_text(text)


def get_handlers() -> list[CommandHandler]:
    return [
        CommandHandler("reset", cmd_reset),
        CommandHandler("approve", cmd_approve),
        CommandHandler("status", cmd_status),
        CommandHandler("stats", cmd_stats),
    ]
