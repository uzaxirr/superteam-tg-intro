from __future__ import annotations

import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
MAIN_GROUP_ID: int = int(os.getenv("MAIN_GROUP_ID", "0"))
ADMIN_IDS: list[int] = [
    int(uid.strip())
    for uid in os.getenv("ADMIN_IDS", "").split(",")
    if uid.strip()
]
MIN_INTRO_LENGTH: int = int(os.getenv("MIN_INTRO_LENGTH", "50"))

DB_PATH: str = os.getenv("DB_PATH", "data/bot.db")

WELCOME_MESSAGE = (
    "👋 *Welcome to Superteam MY\\!*\n\n"
    "To get started, please introduce yourself in this format 👇\n\n"
    "This helps everyone get context and makes collaboration easier\\.\n\n"
    "*Intro format:*\n"
    "• Who are you \\& what do you do?\n"
    "• Where are you based?\n"
    "• One fun fact about you\n"
    "• How are you looking to contribute to Superteam MY?\n\n"
    "No pressure to be perfect — just be you\\!"
)

EXAMPLE_INTRO = (
    "\n\n✨ *Example intro*\n\n"
    "Hey everyone\\! I'm Marianne 👋\n\n"
    "Together with Han, we are Co\\-Leads of Superteam Malaysia\\!\n\n"
    "📍 Based in Kuala Lumpur and Network School\n"
    "🧑‍🎓 Fun fact: My first Solana project was building an AI Telegram trading "
    "bot, and that's how I found myself in Superteam MY\\!\n"
    "🤝 Looking to contribute by:\n"
    "• Connecting builders with the right mentors, partners, and opportunities\n"
    "• Helping teams refine their story, demos, and go\\-to\\-market\n"
    "• Supporting members who want to go from \"building quietly\" → \"shipping publicly\"\n\n"
    "Excited to build alongside all of you — feel free to reach out anytime 🙌"
)

INTRO_REMINDER = (
    "Hey {mention}\\! Please introduce yourself before chatting here\\.\n\n"
    "*Intro format:*\n"
    "• Who are you \\& what do you do?\n"
    "• Where are you based?\n"
    "• One fun fact about you\n"
    "• How are you looking to contribute to Superteam MY?\n\n"
    "Your message was removed — it'll go through once you've introduced yourself\\! 🙏"
)

INTRO_ACCEPTED = (
    "🎉 Thanks for introducing yourself, {mention}\\! "
    "You now have full access to the group\\. Welcome aboard\\!"
)

INTRO_NUDGE = (
    "Thanks for posting\\! Your intro seems a bit short — "
    "could you add a few more details? Here's the suggested format:\n\n"
    "• Who are you \\& what do you do?\n"
    "• Where are you based?\n"
    "• One fun fact about you\n"
    "• How are you looking to contribute to Superteam MY?\n\n"
    "No worries, just post again with a bit more detail\\! 😊"
)
