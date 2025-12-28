"""
Telegram Bot Module for Test Dashboard Notifications
Sends real-time notifications to users about test execution status
"""

import os
import json
import asyncio
import aiohttp
from telegram import Bot, Update
from telegram.ext import Application, CommandHandler, ContextTypes
from datetime import datetime
import threading
from typing import Optional, Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get server URL from environment or use default
SERVER_URL = os.getenv("DASHBOARD_URL", "http://localhost:3000")


class TelegramNotifier:
    """Manages Telegram bot notifications for the test dashboard"""

    def __init__(self, config_file: str = "telegram_config.json"):
        self.config_file = config_file
        self.bot_token = None
        self.chat_ids = {}  # Maps username to chat_id
        self.application = None
        self.bot = None
        self.loop = None
        self.activity_log = []  # Store recent bot activities
        self.max_log_entries = 100  # Keep last 100 entries
        self.load_config()

    def log_activity(
        self, activity_type: str, username: str, message: str, details: str = ""
    ):
        """Log bot activity for monitoring"""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "type": activity_type,  # command, notification, registration, error
            "username": username,
            "message": message,
            "details": details,
        }
        self.activity_log.append(entry)

        # Keep only recent entries
        if len(self.activity_log) > self.max_log_entries:
            self.activity_log = self.activity_log[-self.max_log_entries :]

    def get_statistics(self):
        """Get bot statistics for monitoring"""
        return {
            "total_users": len(self.chat_ids),
            "registered_users": list(self.chat_ids.keys()),
            "activity_log": self.activity_log[-50:],  # Last 50 activities
            "bot_status": "active" if self.bot else "inactive",
        }

    def load_config(self):
        """Load bot token from .env and chat IDs from JSON file"""
        # Load bot token from environment variable (preferred method)
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")

        # Load pre-configured chat IDs from environment (optional)
        env_chat_ids = os.getenv("TELEGRAM_CHAT_IDS", "")
        if env_chat_ids:
            try:
                # Format: username:chat_id,username2:chat_id2
                for pair in env_chat_ids.split(","):
                    if ":" in pair:
                        username, chat_id = pair.strip().split(":", 1)
                        self.chat_ids[username.strip()] = int(chat_id.strip())
            except (ValueError, AttributeError) as e:
                print(f"Warning: Error parsing TELEGRAM_CHAT_IDS: {e}")

        # Load/merge chat IDs from JSON file (for dynamic registrations)
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    config = json.load(f)
                    # Merge with existing chat_ids from env
                    file_chat_ids = config.get("chat_ids", {})
                    self.chat_ids.update(file_chat_ids)
            except (json.JSONDecodeError, IOError) as e:
                print(f"Warning: Error loading {self.config_file}: {e}")

        # If no bot token found, show helpful message
        if not self.bot_token or self.bot_token == "YOUR_BOT_TOKEN_HERE":
            print("💡 Telegram bot not configured.")
            print("   Set TELEGRAM_BOT_TOKEN in .env file to enable notifications.")

    def _create_default_config(self):
        """Create a default configuration file for chat IDs only"""
        config = {"chat_ids": {}}
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
            print(f"Created {self.config_file} for storing user registrations.")
        except IOError as e:
            print(f"Error creating config file: {e}")

    def save_config(self):
        """Save chat IDs to file (bot token is stored in .env)"""
        # Only save dynamically registered chat IDs to JSON
        # Bot token should be configured in .env file
        config = {"chat_ids": self.chat_ids}
        try:
            with open(self.config_file, "w") as f:
                json.dump(config, f, indent=2)
        except IOError as e:
            print(f"Error saving config: {e}")

    def initialize_bot(self):
        """Initialize the Telegram bot"""
        if not self.bot_token or self.bot_token == "YOUR_BOT_TOKEN_HERE":
            print("⚠️  Telegram bot token not configured. Notifications disabled.")
            print("   Please set TELEGRAM_BOT_TOKEN in your .env file.")
            return False

        try:
            self.bot = Bot(token=self.bot_token)
            self.application = Application.builder().token(self.bot_token).build()

            # Add command handlers
            self.application.add_handler(CommandHandler("start", self.cmd_start))
            self.application.add_handler(CommandHandler("register", self.cmd_register))
            self.application.add_handler(
                CommandHandler("unregister", self.cmd_unregister)
            )
            self.application.add_handler(CommandHandler("mystatus", self.cmd_mystatus))
            self.application.add_handler(CommandHandler("mytests", self.cmd_mytests))
            self.application.add_handler(CommandHandler("slot", self.cmd_slot_status))
            self.application.add_handler(CommandHandler("help", self.cmd_help))

            # Add error handler
            self.application.add_error_handler(self.error_handler)

            print("✅ Telegram bot initialized successfully!")
            return True
        except Exception as e:
            print(f"❌ Error initializing Telegram bot: {e}")
            return False

    def start_bot(self):
        """Start the bot in a separate thread"""
        if not self.application:
            if not self.initialize_bot():
                return

        def run_bot():
            """Run bot in event loop"""
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
            # Run polling without signal handlers (since we're in a thread)
            self.loop.run_until_complete(
                self.application.run_polling(
                    stop_signals=None,  # Disable signal handlers for thread safety
                    close_loop=False,
                )
            )

        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        print("🤖 Telegram bot started in background")

    async def error_handler(
        self, update: object, context: ContextTypes.DEFAULT_TYPE
    ) -> None:
        """Handle errors in the bot"""
        try:
            print(f"⚠️  Telegram bot error: {context.error}")
            # Try to notify the user if possible
            if (
                update
                and hasattr(update, "effective_message")
                and update.effective_message
            ):
                try:
                    await update.effective_message.reply_text(
                        "⚠️ Sorry, I encountered an error processing your request. Please try again later."
                    )
                except:
                    pass  # If we can't send the error message, just log it
        except Exception as e:
            print(f"Error in error handler: {e}")

    async def cmd_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        try:
            user = update.effective_user
            username = user.username or user.first_name or str(user.id)
            self.log_activity(
                "command", username, "/start", "User accessed welcome message"
            )

            welcome_msg = (
                "👋 Welcome to Test Dashboard Notification Bot!\n\n"
                "This bot sends you real-time notifications about your test execution:\n"
                "• 🚀 Test started\n"
                "• ✅ Test completed successfully\n"
                "• ❌ Test failed with errors\n"
                "• ⏹️ Test stopped\n\n"
                "Available commands:\n"
                "/register <username> - Register to receive notifications\n"
                "/mytests - Check status of all your tests\n"
                "/slot <id> - Check status of specific slot\n"
                "/mystatus - Check your registration status\n"
                "/unregister - Stop receiving notifications\n"
                "/help - Show this help message\n\n"
                "Example: /register Alice"
            )
            await update.message.reply_text(welcome_msg)
        except Exception as e:
            print(f"Error in cmd_start: {e}")

    async def cmd_register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command"""
        try:
            if not context.args or len(context.args) == 0:
                await update.message.reply_text(
                    "❌ Please provide your username.\n"
                    "Usage: /register <username>\n"
                    "Example: /register Alice"
                )
                return

            username = context.args[0]
            chat_id = update.effective_chat.id

            self.chat_ids[username] = chat_id
            self.save_config()

            self.log_activity(
                "registration",
                username,
                f"Registered with chat_id {chat_id}",
                "New user registered",
            )

            await update.message.reply_text(
                f"✅ Successfully registered!\n"
                f"Username: {username}\n"
                f"Chat ID: {chat_id}\n\n"
                f"You will now receive notifications for tests owned by '{username}'."
            )
            print(f"📝 Registered new user: {username} (chat_id: {chat_id})")
        except Exception as e:
            print(f"Error in cmd_register: {e}")

    async def cmd_unregister(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /unregister command"""
        try:
            chat_id = update.effective_chat.id

            # Find and remove user by chat_id
            username = None
            for user, cid in list(self.chat_ids.items()):
                if cid == chat_id:
                    username = user
                    del self.chat_ids[user]
                    break

            if username:
                self.save_config()
                await update.message.reply_text(
                    f"✅ Successfully unregistered!\n"
                    f"You will no longer receive notifications for '{username}'."
                )
                print(f"📝 Unregistered user: {username}")
            else:
                await update.message.reply_text("ℹ️ You are not currently registered.")
        except Exception as e:
            print(f"Error in cmd_unregister: {e}")

    async def cmd_mystatus(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mystatus command - check registration status"""
        try:
            chat_id = update.effective_chat.id

            username = None
            for user, cid in self.chat_ids.items():
                if cid == chat_id:
                    username = user
                    break

            if username:
                self.log_activity(
                    "command", username, "/mystatus", "Checked registration status"
                )
                await update.message.reply_text(
                    f"✅ Registration Status: Active\n"
                    f"Username: {username}\n"
                    f"Chat ID: {chat_id}\n\n"
                    f"Use /mytests to see your running tests."
                )
            else:
                await update.message.reply_text(
                    "ℹ️ You are not registered.\n"
                    "Use /register <username> to start receiving notifications."
                )
        except Exception as e:
            print(f"Error in cmd_mystatus: {e}")

    async def cmd_mytests(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /mytests command - show all tests owned by user"""
        try:
            chat_id = update.effective_chat.id

            # Find username
            username = None
            for user, cid in self.chat_ids.items():
                if cid == chat_id:
                    username = user
                    break

            if not username:
                await update.message.reply_text(
                    "⚠️ You are not registered.\n" "Use /register <username> first."
                )
                return

            # Fetch data from API
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        f"{SERVER_URL}/api/slots",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        if response.status == 200:
                            data = await response.json()
                            slots = data.get("slots", [])

                            # Filter slots owned by this user
                            my_slots = [
                                s
                                for s in slots
                                if s.get("owner", "").lower() == username.lower()
                            ]

                            if not my_slots:
                                await update.message.reply_text(
                                    f"ℹ️ No tests found for user: {username}\n\n"
                                    f"You can assign tests in the dashboard at:\n"
                                    f"{SERVER_URL}"
                                )
                                return

                            # Build response message
                            msg = f"📊 Your Tests ({len(my_slots)} active):\n\n"

                            for slot in my_slots:
                                status_emoji = {
                                    "idle": "⚪",
                                    "running": "🟢",
                                    "success": "✅",
                                    "failed": "❌",
                                    "stopping": "🟡",
                                }.get(slot.get("status", "idle"), "⚪")

                                msg += f"{status_emoji} Slot {slot['id']}: {slot.get('status', 'idle').upper()}\n"
                                msg += f"   Test: {slot.get('test_case', 'N/A')}\n"
                                msg += f"   Progress: {slot.get('progress', 0)}%\n"

                                if slot.get("start_time"):
                                    msg += f"   Started: {self._format_time(slot['start_time'])}\n"

                                if slot.get("error_msg"):
                                    error = (
                                        slot["error_msg"][:50] + "..."
                                        if len(slot.get("error_msg", "")) > 50
                                        else slot["error_msg"]
                                    )
                                    msg += f"   Error: {error}\n"

                                msg += "\n"

                            msg += f"Use /slot <id> for detailed info"
                            await update.message.reply_text(msg)
                        else:
                            await update.message.reply_text(
                                "⚠️ Failed to fetch test data from server.\n"
                                f"Server returned status: {response.status}"
                            )
                except asyncio.TimeoutError:
                    await update.message.reply_text(
                        "⚠️ Connection timeout. Is the dashboard server running?\n"
                        f"Expected at: {SERVER_URL}"
                    )
                except aiohttp.ClientError as e:
                    await update.message.reply_text(
                        f"⚠️ Cannot connect to dashboard server.\n" f"Error: {str(e)}"
                    )
        except Exception as e:
            print(f"Error in cmd_mytests: {e}")
            await update.message.reply_text(
                "⚠️ An error occurred while fetching your tests."
            )

    async def cmd_slot_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /slot <id> command - show detailed status of specific slot"""
        try:
            if not context.args or len(context.args) == 0:
                await update.message.reply_text(
                    "❌ Please provide a slot ID.\n"
                    "Usage: /slot <id>\n"
                    "Example: /slot 5"
                )
                return

            try:
                slot_id = int(context.args[0])
            except ValueError:
                await update.message.reply_text("❌ Invalid slot ID. Must be a number.")
                return

            # Fetch slot data from API
            async with aiohttp.ClientSession() as session:
                try:
                    async with session.get(
                        f"{SERVER_URL}/api/slots/{slot_id}",
                        timeout=aiohttp.ClientTimeout(total=5),
                    ) as response:
                        if response.status == 200:
                            slot = await response.json()

                            status_emoji = {
                                "idle": "⚪",
                                "running": "🟢",
                                "success": "✅",
                                "failed": "❌",
                                "stopping": "🟡",
                            }.get(slot.get("status", "idle"), "⚪")

                            msg = f"{status_emoji} Slot {slot['id']} - {slot.get('status', 'idle').upper()}\n\n"
                            msg += f"👤 Owner: {slot.get('owner', 'Not assigned')}\n"
                            msg += f"📝 Test Case: {slot.get('test_case', 'None')}\n"
                            msg += f"📊 Progress: {slot.get('progress', 0)}%\n"

                            if slot.get("ssd_serial"):
                                msg += f"💾 SSD Serial: {slot['ssd_serial']}\n"

                            if slot.get("start_time"):
                                msg += f"🕐 Started: {self._format_time(slot['start_time'])}\n"

                            if slot.get("script_path"):
                                msg += f"📜 Script: {slot['script_path']}\n"

                            if slot.get("error_msg"):
                                msg += f"\n❌ Error:\n{slot['error_msg'][:200]}\n"

                            await update.message.reply_text(msg)
                        elif response.status == 404:
                            await update.message.reply_text(
                                f"❌ Slot {slot_id} not found."
                            )
                        else:
                            await update.message.reply_text(
                                f"⚠️ Failed to fetch slot data. Status: {response.status}"
                            )
                except asyncio.TimeoutError:
                    await update.message.reply_text(
                        "⚠️ Connection timeout. Is the dashboard server running?"
                    )
                except aiohttp.ClientError as e:
                    await update.message.reply_text(
                        f"⚠️ Cannot connect to server: {str(e)}"
                    )
        except Exception as e:
            print(f"Error in cmd_slot_status: {e}")
            await update.message.reply_text(
                "⚠️ An error occurred while fetching slot data."
            )

    def _format_time(self, iso_string: str) -> str:
        """Format ISO timestamp to readable string"""
        try:
            dt = datetime.fromisoformat(iso_string)
            return dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            return iso_string

    async def cmd_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        await self.cmd_start(update, context)

    def send_notification(self, username: str, message: str, parse_mode: str = None):
        """Send a notification to a specific user"""
        if not self.bot:
            return  # Bot not initialized

        chat_id = self.chat_ids.get(username)
        if not chat_id:
            print(f"ℹ️  No Telegram registration found for user: {username}")
            return

        if self.loop:
            asyncio.run_coroutine_threadsafe(
                self._send_message(chat_id, message, parse_mode), self.loop
            )

    async def _send_message(self, chat_id: int, message: str, parse_mode: str = None):
        """Internal method to send message asynchronously"""
        try:
            await self.bot.send_message(
                chat_id=chat_id, text=message, parse_mode=parse_mode
            )
        except Exception as e:
            print(f"Error sending Telegram message: {e}")

    # Notification templates

    def notify_test_started(
        self, owner: str, slot_id: int, test_case: str, ssd_serial: str = ""
    ):
        """Notify user that their test has started"""
        message = (
            f"🚀 Test Started\n\n" f"Slot: {slot_id}\n" f"Test Case: {test_case}\n"
        )
        if ssd_serial:
            message += f"SSD Serial: {ssd_serial}\n"
        message += f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        self.log_activity(
            "notification", owner, f"Test started on slot {slot_id}", test_case
        )
        self.send_notification(owner, message)

    def notify_test_completed(
        self,
        owner: str,
        slot_id: int,
        test_case: str,
        duration: str = "",
        progress: int = 100,
    ):
        """Notify user that their test completed successfully"""
        message = (
            f"✅ Test Completed Successfully\n\n"
            f"Slot: {slot_id}\n"
            f"Test Case: {test_case}\n"
            f"Progress: {progress}%\n"
        )
        if duration:
            message += f"Duration: {duration}\n"
        message += f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        self.log_activity(
            "notification",
            owner,
            f"Test completed on slot {slot_id}",
            f"{test_case} - {duration}",
        )
        self.send_notification(owner, message)

    def notify_test_failed(
        self,
        owner: str,
        slot_id: int,
        test_case: str,
        error_msg: str = "",
        progress: int = 0,
    ):
        """Notify user that their test failed"""
        message = (
            f"❌ Test Failed\n\n"
            f"Slot: {slot_id}\n"
            f"Test Case: {test_case}\n"
            f"Progress: {progress}%\n"
        )
        if error_msg:
            # Limit error message length
            error_short = error_msg[:200] + "..." if len(error_msg) > 200 else error_msg
            message += f"Error: {error_short}\n"
        message += f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

        self.log_activity(
            "notification",
            owner,
            f"Test failed on slot {slot_id}",
            f"{test_case} - {error_msg[:100]}",
        )
        self.send_notification(owner, message)

    def notify_test_stopped(self, owner: str, slot_id: int, test_case: str):
        """Notify user that their test was stopped"""
        message = (
            f"⏹️ Test Stopped\n\n"
            f"Slot: {slot_id}\n"
            f"Test Case: {test_case}\n"
            f"\nTime: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )

        self.log_activity(
            "notification", owner, f"Test stopped on slot {slot_id}", test_case
        )
        self.send_notification(owner, message)


# Global notifier instance
notifier = TelegramNotifier()
