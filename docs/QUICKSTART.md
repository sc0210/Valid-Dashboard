# 🚀 Quick Setup Guide

## 1. Create `.env` file

```bash
cp .env.example .env
```

## 2. Add your Telegram bot token

Edit `.env`:
```bash
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

## 3. Install dependencies

```bash
pip install -r requirements.txt
```

## 4. Start the server

```bash
python app.py
```

## 5. Register users with the bot

Each user in Telegram:
1. Find your bot (search for its username)
2. Send: `/start`
3. Send: `/register YourUsername`

Done! 🎉

## Environment Variables

All configuration in `.env`:

```bash
# Required for Telegram
TELEGRAM_BOT_TOKEN=your_bot_token_here

# Optional settings
SERVER_HOST=0.0.0.0        # Server bind address
SERVER_PORT=3000            # Server port
DEBUG_MODE=True             # Debug mode
NUM_SLOTS=16                # Number of test slots
DATA_FILE=test_slots.json   # Data file location
LOG_DIRECTORY=logs          # Log directory path
```

## Notes

- Never commit `.env` to git (it's in `.gitignore`)
- Share `.env.example` as a template for others
- Full setup guide: [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)
