import logging
from telegram.ext import ApplicationBuilder

from bot.config import BOT_TOKEN, INTRO_CHANNEL_ID, MAIN_GROUP_ID
from bot.database import init_db
from bot.handlers import admin, enforcement, intro, welcome

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application) -> None:
    """Run after the application is initialized."""
    await init_db()
    logger.info("Database initialized.")

    # Cache intro channel username for building links
    try:
        chat = await application.bot.get_chat(INTRO_CHANNEL_ID)
        if chat.username:
            application.bot_data["intro_channel_username"] = chat.username
            logger.info("Intro channel username: @%s", chat.username)
    except Exception:
        logger.warning("Could not fetch intro channel info. Links will use numeric IDs.")

    logger.info("Bot started. Main group: %d, Intro channel: %d", MAIN_GROUP_ID, INTRO_CHANNEL_ID)


def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set. Check your .env file.")
    if not MAIN_GROUP_ID:
        raise ValueError("MAIN_GROUP_ID is not set. Check your .env file.")
    if not INTRO_CHANNEL_ID:
        raise ValueError("INTRO_CHANNEL_ID is not set. Check your .env file.")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Register handlers
    app.add_handler(welcome.get_handler())
    app.add_handler(intro.get_handler())
    app.add_handler(enforcement.get_handler())
    for handler in admin.get_handlers():
        app.add_handler(handler)

    logger.info("Starting bot polling...")
    app.run_polling(
        allowed_updates=[
            "message",
            "chat_member",
            "my_chat_member",
        ],
        drop_pending_updates=True,
    )


if __name__ == "__main__":
    main()
