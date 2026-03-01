import logging
from telegram.ext import ApplicationBuilder

from bot.config import BOT_TOKEN, MAIN_GROUP_ID
from bot.database import init_db
from bot.handlers import admin, group, welcome

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


async def post_init(application) -> None:
    """Run after the application is initialized."""
    await init_db()
    logger.info("Database initialized.")
    logger.info("Bot started. Group: %d", MAIN_GROUP_ID)


def main() -> None:
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is not set. Check your .env file.")
    if not MAIN_GROUP_ID:
        raise ValueError("MAIN_GROUP_ID is not set. Check your .env file.")

    app = (
        ApplicationBuilder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Register handlers
    app.add_handler(welcome.get_handler())
    app.add_handler(group.get_handler())
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
