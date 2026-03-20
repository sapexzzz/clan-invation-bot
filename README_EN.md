# Telegram Bot Invite Clan

Python Telegram bot for handling Standoff 2 clan applications with moderator review in a Telegram group.

## Features

- Step-by-step application flow using FSM
- Minimum requirement checks:
  - KD >= 1.0
  - Hours >= 50
- Automatic rejection for invalid applications
- Anti-spam protection: one application per 10 minutes
- Blocks new submissions while the user already has a pending application
- Sends each new application to the admin group with inline action buttons
- Verifies admin rights before accepting or rejecting
- Generates a one-time invite link valid for 24 hours after approval
- Stores data in SQLite using aiosqlite

## Stack

- Python 3.11+
- aiogram 3.x
- aiosqlite
- python-dotenv

## Project Structure

```text
main.py
bot/
  config.py
  database.py
  states.py
  keyboards.py
  handlers/
    start.py
    application.py
    admin.py
requirements.txt
.env.example
```

## Installation

```bash
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Configuration

Create a `.env` file in the project root:

```env
BOT_TOKEN=your_bot_token
GROUP_ID=-1001234567890
TOPIC_ID=968
```

### Environment Variables

- `BOT_TOKEN` — bot token from BotFather
- `GROUP_ID` — target group or forum group ID for applications
- `TOPIC_ID` — forum topic ID, optional

## Bot Permissions

The bot must be an admin in the target group and have permission to:

- send messages
- create invite links

## Run

```bash
.venv/bin/python main.py
```

## How It Works

1. The user presses the apply button.
2. The bot collects application data step by step: game ID, nickname, ranks, hours, and KD.
3. If hours are below 50 or KD is outside the allowed range, the application is auto-rejected.
4. If the data is valid, the bot shows a confirmation summary and allows editing any field.
5. After submission, the application is saved in SQLite and posted to the admin group.
6. An admin accepts or rejects the application using inline buttons.
7. If accepted, the user receives a personal invite link valid for 24 hours.

## Database

The bot uses two tables:

- `users` — stores `telegram_id` and last application timestamp
- `applications` — stores the full application data and status

## Application Statuses

- `pending`
- `accepted`
- `rejected`
- `rejected_auto`

## Notes

- For forum groups, `TOPIC_ID` is used as `message_thread_id`.
- If `TOPIC_ID` is not set, messages are sent to the main chat.
- FSM state storage currently uses `MemoryStorage`.
