# Superteam MY — Telegram Onboarding Bot

A Telegram bot that onboards new members in the Superteam Malaysia group by requiring them to introduce themselves before they can participate. Everything happens in a single group — no separate channels needed.

## Features

- **New member detection** — Detects when users join via `ChatMemberUpdated`
- **Welcome message** — Sends a formatted welcome with the intro template and an example
- **Soft enforcement** — Messages from non-introduced users are auto-deleted with a reminder
- **Intro validation** — Heuristic check that the introduction roughly follows the expected format
- **Instant access** — Once a valid intro is posted in the group, the user can chat freely
- **Admin commands** — `/reset`, `/approve`, `/status`, `/stats`
- **Persistent storage** — SQLite database survives restarts
- **Edge case handling** — Leave & rejoin, bot restart, partial intros get a nudge

## Demo

### Quick Overview

![Demo](screenshots/demo.gif)

### Live Test Group

Want to try it yourself? Join the test group and experience the full onboarding flow:

1. **Join the group:** [Superteam MY Test](https://t.me/+vRitdSyP82w3MmQ1)
2. Try sending a message — it will be deleted with a reminder to introduce yourself
3. Post your intro in the group following the format — the bot will validate and approve you
4. Now you can chat freely

> A [demo video](screenshots/demo.mp4) is also available in the repo.

### Screenshots

<details>
<summary>Click to expand screenshots</summary>

#### Enforcement — Non-introduced users can't chat

When a user who hasn't introduced themselves tries to send a message, the bot deletes it and sends a reminder with the intro format.

![Enforcement](screenshots/enforcement.png)

#### Intro Validation & Acceptance

Once the user posts a valid introduction in the group, the bot validates it and confirms acceptance.

![Intro Accepted](screenshots/intro_accepted.png)

#### Post-Intro — Full Access Granted

After completing their introduction, the user can freely participate with no restrictions.

![Post Intro](screenshots/post_intro.png)

#### Admin Stats

Admins can use `/stats` to get a quick overview of onboarding progress.

![Admin Stats](screenshots/admin_stats.png)

</details>

---

## Setup

### Prerequisites

- Python 3.9+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- The bot must be an **admin** in the group with permissions to:
  - Delete messages
  - Send messages

### BotFather Configuration

1. Go to [@BotFather](https://t.me/BotFather)
2. `/mybots` → Select your bot → Bot Settings → Group Privacy → **Turn OFF**
   - This allows the bot to see all messages in the group (required for enforcement and intro detection)
3. Also enable "Allow Groups?" if not already enabled

### Getting the Chat ID

1. Add the bot to your group
2. Send a message in the group
3. Visit `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find the `chat.id` value for your group (it'll be a negative number like `-1001234567890`)

### Environment Variables

Copy the example env file and fill in your values:

```bash
cp .env.example .env
```

| Variable | Description | Required |
|---|---|---|
| `BOT_TOKEN` | Telegram bot token from BotFather | Yes |
| `MAIN_GROUP_ID` | Chat ID of the group | Yes |
| `ADMIN_IDS` | Comma-separated Telegram user IDs for admins | Yes |
| `MIN_INTRO_LENGTH` | Minimum character length for intros (default: 50) | No |
| `DB_PATH` | SQLite database path (default: `data/bot.db`) | No |

### Run Locally

```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Run the bot
python -m bot.main
```

### Run with Docker

```bash
# Build and start
docker compose up -d

# View logs
docker compose logs -f bot

# Stop
docker compose down
```

## Admin Commands

All commands are restricted to user IDs listed in `ADMIN_IDS`.

| Command | Description | Usage |
|---|---|---|
| `/reset` | Reset a user's intro status (messages will be deleted again) | Reply to a message or `/reset <user_id>` |
| `/approve` | Manually approve a user (skip intro requirement) | Reply to a message or `/approve <user_id>` |
| `/status` | Check a user's onboarding status | Reply to a message or `/status <user_id>` |
| `/stats` | Show overall onboarding statistics | `/stats` |

## How It Works

```
User joins group
        │
        ▼
Bot sends welcome message with intro format
        │
        ▼
User sends a message
        │
        ▼
Bot checks: is this a valid intro?
        │
   ┌────┴────┐
   ▼         ▼
 Valid     Not an intro
   │         │
   ▼         ▼
Mark as    Delete message,
introduced send reminder
   │
   ▼
User can now
chat freely
```

## Project Structure

```
├── bot/
│   ├── main.py              # Entry point
│   ├── config.py             # Configuration & message templates
│   ├── database.py           # SQLite operations
│   ├── handlers/
│   │   ├── welcome.py        # New member detection + welcome message
│   │   ├── group.py          # Message handler: intro validation + enforcement
│   │   └── admin.py          # Admin commands
│   └── utils/
│       └── validation.py     # Intro format heuristic checker
├── screenshots/              # Demo screenshots
├── .env.example
├── Dockerfile
├── docker-compose.yml
├── requirements.txt
└── README.md
```

## Validation Logic

The bot uses a heuristic scoring system to check intros:

- **Length** — At least 50 characters
- **Identity** — Mentions who they are / what they do
- **Location** — Mentions where they're based
- **Fun fact** — Shares something personal
- **Contribution** — Mentions how they want to contribute

A score of 3/5 or higher is accepted. Below that, the bot gently nudges the user to add more detail.
