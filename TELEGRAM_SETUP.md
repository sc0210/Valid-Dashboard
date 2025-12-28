# 🤖 Telegram Bot Setup Guide

This guide will help you integrate Telegram notifications with your Test Dashboard system.

## 📋 Overview

The Telegram bot sends real-time notifications to users about their test execution:
- 🚀 Test started
- ✅ Test completed successfully  
- ❌ Test failed
- ⏹️ Test stopped

## 🔧 Setup Steps

### Step 1: Get Your Bot Token

You mentioned you already have a Telegram bot registered. You should have received a **bot token** from BotFather that looks like this:
```
123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ
```

If you don't have the token yet:
1. Open Telegram and search for `@BotFather`
2. Send `/newbot` command
3. Follow the instructions to create your bot
4. Copy the bot token provided

### Step 2: Configure Environment Variables

Create a `.env` file in your project directory:

```bash
cp .env.example .env
```

Then edit the `.env` file and add your bot token:

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Optional: Server configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=3000
DEBUG_MODE=True
```

**Important**: Never commit `.env` to git! It's already in `.gitignore`.

### Step 3: Install Dependencies

Install the required libraries:

```bash
cd /Users/samchen/Documents/Dev/ValidDashboard
pip install -r requirements.txt
```

This will install:
- `python-telegram-bot` - Telegram bot library
- `python-dotenv` - Environment variable loader
- Other dependencies

### Step 4: Start the Dashboard Server

Start your dashboard server as usual:

```bash
python app.py
```

You should see:
```
🤖 Initializing Telegram bot...
✅ Telegram bot initialized successfully!
🤖 Telegram bot started in background
Starting Test Dashboard Controller...
Access dashboard at: http://localhost:3000
```

## 👥 User Registration

Each user who wants to receive notifications must register with the bot:

### Step 1: Find Your Bot

1. Open Telegram
2. Search for your bot by the username you gave it (e.g., `@YourTestDashboardBot`)
3. Click on the bot to open a chat

### Step 2: Register for Notifications

Send these commands to your bot:

1. **Start the bot:**
   ```
   /start
   ```
   
   The bot will greet you with available commands.

2. **Register your username:**
   ```
   /register Alice
   ```
   
   Replace `Alice` with the **exact username** you use in the dashboard (the "owner" field).
   
   ⚠️ **Important:** The username must match exactly with what you enter in the dashboard's owner field!

3. **Verify registration:**
   ```
   /status
   ```
   
   This will confirm your registration and show your Chat ID.

## 📱 Bot Commands

| Command | Description |
|---------|-------------|
| `/start` | Show welcome message and help |
| `/register <username>` | Register to receive notifications for a specific username |
| `/unregister` | Stop receiving notifications |
| `/status` | Check your registration status |
| `/help` | Show help message |

## 📬 Notification Examples

### Test Started
```
🚀 Test Started

Slot: 5
Test Case: SSD Performance Test
SSD Serial: S12345678

Time: 2025-12-27 14:30:25
```

### Test Completed
```
✅ Test Completed Successfully

Slot: 5
Test Case: SSD Performance Test
Progress: 100%
Duration: 2h 15m 30s

Time: 2025-12-27 16:45:55
```

### Test Failed
```
❌ Test Failed

Slot: 5
Test Case: SSD Performance Test
Progress: 45%
Error: Connection timeout after 30s

Time: 2025-12-27 15:15:30
```

## 🔄 Multi-User Setup

Multiple users can register with the same bot:

1. **Alice** registers:
   ```
   /register Alice
   ```
   → Will receive notifications for tests where owner = "Alice"

2. **Bob** registers:
   ```
   /register Bob
   ```
   → Will receive notifications for tests where owner = "Bob"

3. **Charlie** registers:
   ```
   /register Charlie
   ```
   → Will receive notifications for tests where owner = "Charlie"

Each user only receives notifications for their own tests!

## 📝 Configuration File Details

The system uses two configuration methods:

### 1. `.env` file (for secrets and settings)

```bash
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ

# Optional: Pre-register users (format: username:chat_id,username2:chat_id2)
TELEGRAM_CHAT_IDS=Alice:987654321,Bob:876543210

# Server Configuration
SERVER_HOST=0.0.0.0
SERVER_PORT=3000
DEBUG_MODE=True

# Data Storage
DATA_FILE=test_slots.json
LOG_DIRECTORY=logs
NUM_SLOTS=16
```

### 2. `telegram_config.json` (auto-managed for dynamic registrations)

This file is automatically created and updated when users register via `/register` command:

```json
{
  "chat_ids": {
    "Alice": 987654321,
    "Bob": 876543210,
    "Charlie": 765432109
  }
}
```

**You don't need to manually edit this file!** It's managed automatically by the bot.

⚠️ **Security Best Practices:**
- Store bot token in `.env` file only
- Never commit `.env` to version control
- Keep `.env.example` updated as a template (without secrets)

## 🐛 Troubleshooting

### Bot doesn't start

**Problem:** You see `⚠️ Telegram bot token not configured`

**Solution:** Make sure you've created `.env` file with your bot token:
```bash
cp .env.example .env
# Then edit .env and add your TELEGRAM_BOT_TOKEN
```

---

### Not receiving notifications

**Problem:** Tests run but no Telegram messages arrive

**Solutions:**
1. Verify you've registered with the bot: `/status`
2. Make sure the username in `/register` matches the owner field in the dashboard exactly
3. Check that the owner field is filled in when launching a test
4. Restart the dashboard server after registering

---

### Import error

**Problem:** `ImportError: No module named 'telegram'`

**Solution:** Install the required library:
```bash
pip install python-telegram-bot==21.0
```

---

### Bot token invalid

**Problem:** `Error initializing Telegram bot: Unauthorized`

**Solution:** Your bot token is incorrect. Get a new token from @BotFather:
1. Send `/token` to @BotFather
2. Select your bot
3. Copy the new token to `.env` file:
   ```bash
   TELEGRAM_BOT_TOKEN=your_new_token_here
   ```
4. Restart the server

## 🔒 Security Notes

- **Keep your bot token secret!** Store it in `.env` file only
- Never commit `.env` to public repositories
- `.env` is already in `.gitignore` for your protection
- Share `.env.example` (template) but never `.env` (actual secrets)
- Only authorized users who know your bot's username can register
- Each user can only register their own username

## 💡 Tips

1. **Test the integration:** Register yourself and run a quick test to verify notifications work
2. **Bot naming:** Choose a descriptive bot name like "MyCompanyTestNotifier" for easy identification
3. **Multiple bots:** You can run different bots for different environments (dev/staging/prod)
4. **Notification timing:** Notifications are sent immediately when test status changes

## 📞 Support

If you encounter issues:
1. Check the server console for error messages
2. Verify your bot token with @BotFather
3. Ensure the `python-telegram-bot` library is installed
4. Check that usernames match exactly between dashboard and Telegram registration

## 🎉 You're All Set!

Once configured, your team can:
1. Register with the bot once using `/register <username>`
2. Receive automatic notifications for all their tests
3. Monitor test progress without constantly checking the dashboard

Happy testing! 🚀
