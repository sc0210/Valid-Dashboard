"""
Configuration Management
Centralized configuration loading from environment variables
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Config:
    """Application configuration"""

    # Server settings
    SERVER_HOST = os.getenv("SERVER_HOST", "0.0.0.0")
    SERVER_PORT = int(os.getenv("SERVER_PORT", "3000"))
    DEBUG_MODE = os.getenv("DEBUG_MODE", "True").lower() == "true"

    # Data settings
    DATA_FILE = os.getenv("DATA_FILE", "test_slots.json")
    LOG_DIRECTORY = os.getenv("LOG_DIRECTORY", "logs")
    NUM_SLOTS = int(os.getenv("NUM_SLOTS", "16"))

    # Telegram settings
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    DASHBOARD_URL = os.getenv("DASHBOARD_URL", "http://localhost:3000")

    # Notification settings
    NOTIFICATION_METHOD = os.getenv(
        "NOTIFICATION_METHOD", "telegram"
    )  # telegram, webhook, both
    WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
    WEBHOOK_TIMEOUT = int(os.getenv("WEBHOOK_TIMEOUT", "5"))

    @classmethod
    def get_notification_methods(cls):
        """Get list of enabled notification methods"""
        method = cls.NOTIFICATION_METHOD.lower()
        if method == "both":
            return ["telegram", "webhook"]
        return [method]

    @classmethod
    def is_telegram_enabled(cls):
        """Check if Telegram notifications are enabled"""
        return "telegram" in cls.get_notification_methods() and cls.TELEGRAM_BOT_TOKEN

    @classmethod
    def is_webhook_enabled(cls):
        """Check if webhook notifications are enabled"""
        return "webhook" in cls.get_notification_methods() and cls.WEBHOOK_URL
