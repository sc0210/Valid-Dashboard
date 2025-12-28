# 🚀 Quick Start - Telegram Bot

## Next Steps

Now that you have registered your Telegram bot, follow these steps:

### 1. Update Configuration (5 minutes)

Edit `telegram_config.json` and add your bot token:

```bash
cd /Users/samchen/Documents/Dev/ValidDashboard
nano telegram_config.json
```

Replace `YOUR_BOT_TOKEN_HERE` with your actual token from BotFather.

### 2. Install Dependencies (2 minutes)

```bash
pip install -r requirements.txt
```

This will install `python-telegram-bot` and all other required packages.

### 3. Start the Server (1 minute)

```bash
python app.py
```

You should see:
```
🤖 Initializing Telegram bot...
✅ Telegram bot initialized successfully!
🤖 Telegram bot started in background
```

### 4. Register Users (2 minutes per user)

Each user who wants notifications should:

1. Open Telegram
2. Search for your bot (by the username you created)
3. Send: `/start`
4. Send: `/register YourUsername`
   - Use the exact username that appears in the dashboard's "owner" field

### 5. Test It! (5 minutes)

Launch a test in your dashboard and watch the magic happen! You'll receive:
- 🚀 Notification when test starts
- ✅ Notification when test completes
- ❌ Notification if test fails

## 📚 Documentation

- **Full Setup Guide**: [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md)
- **Main README**: [README.md](README.md)

## 🆘 Need Help?

Common issues:
- **No notifications?** → Check username matches exactly in both dashboard and `/register` command
- **Bot not starting?** → Verify bot token is correct in `telegram_config.json`
- **Import error?** → Run `pip install python-telegram-bot==21.0`

See [TELEGRAM_SETUP.md](TELEGRAM_SETUP.md) for detailed troubleshooting.

## ✨ Features Overview

The bot sends notifications for:
- ✅ Test started with slot and SSD info
- ✅ Test completed with duration
- ✅ Test failed with error details
- ✅ Test stopped by user

Each user only gets notifications for their own tests!

---

**Estimated total setup time: ~15 minutes**

Have fun! 🎉
