"""
Notification Manager
Handles all notification methods (Telegram, Webhook, etc.)
"""

import os
import json
import requests
from datetime import datetime
from typing import Optional, Dict, Any
from .config import Config


class NotificationManager:
    """Manages notifications across multiple channels"""

    def __init__(self):
        self.telegram_notifier = None
        self.config = Config

        # Initialize Telegram if enabled
        if self.config.is_telegram_enabled():
            try:
                from .telegram_bot import notifier as telegram_notifier

                self.telegram_notifier = telegram_notifier
                print("✅ Telegram notifications enabled")
            except ImportError:
                print("⚠️  Telegram bot module not available")

        # Check webhook configuration
        if self.config.is_webhook_enabled():
            print(f"✅ Webhook notifications enabled: {self.config.WEBHOOK_URL}")

    def notify_test_started(self, username: str, slot_id: int, test_case: str) -> bool:
        """Send test started notification"""
        success = True

        # Build notification data
        slot_url = f"{self.config.DASHBOARD_URL}/slot/{slot_id}"
        data = {
            "type": "test_started",
            "slot_id": slot_id,
            "owner": username,
            "test_case": test_case,
            "timestamp": datetime.now().isoformat(),
            "details_url": slot_url,
        }

        # Telegram notification
        if self.telegram_notifier and username in self.telegram_notifier.chat_ids:
            try:
                self.telegram_notifier.notify_test_started(username, slot_id, test_case)
            except Exception as e:
                print(f"Telegram notification failed: {e}")
                success = False

        # Webhook notification
        if self.config.is_webhook_enabled():
            try:
                self._send_webhook(data)
            except Exception as e:
                print(f"Webhook notification failed: {e}")
                success = False

        return success

    def notify_test_completed(
        self, username: str, slot_id: int, test_case: str, duration: str
    ) -> bool:
        """Send test completed notification"""
        success = True

        slot_url = f"{self.config.DASHBOARD_URL}/slot/{slot_id}"
        data = {
            "type": "test_completed",
            "slot_id": slot_id,
            "owner": username,
            "test_case": test_case,
            "duration": duration,
            "timestamp": datetime.now().isoformat(),
            "details_url": slot_url,
        }

        # Telegram notification
        if self.telegram_notifier and username in self.telegram_notifier.chat_ids:
            try:
                self.telegram_notifier.notify_test_completed(
                    username, slot_id, test_case, duration
                )
            except Exception as e:
                print(f"Telegram notification failed: {e}")
                success = False

        # Webhook notification
        if self.config.is_webhook_enabled():
            try:
                self._send_webhook(data)
            except Exception as e:
                print(f"Webhook notification failed: {e}")
                success = False

        return success

    def notify_test_failed(
        self, username: str, slot_id: int, test_case: str, error_msg: str
    ) -> bool:
        """Send test failed notification"""
        success = True

        slot_url = f"{self.config.DASHBOARD_URL}/slot/{slot_id}"
        data = {
            "type": "test_failed",
            "slot_id": slot_id,
            "owner": username,
            "test_case": test_case,
            "error": error_msg,
            "timestamp": datetime.now().isoformat(),
            "details_url": slot_url,
        }

        # Telegram notification
        if self.telegram_notifier and username in self.telegram_notifier.chat_ids:
            try:
                self.telegram_notifier.notify_test_failed(
                    username, slot_id, test_case, error_msg
                )
            except Exception as e:
                print(f"Telegram notification failed: {e}")
                success = False

        # Webhook notification
        if self.config.is_webhook_enabled():
            try:
                self._send_webhook(data)
            except Exception as e:
                print(f"Webhook notification failed: {e}")
                success = False

        return success

    def notify_test_stopped(self, username: str, slot_id: int, test_case: str) -> bool:
        """Send test stopped notification"""
        success = True

        slot_url = f"{self.config.DASHBOARD_URL}/slot/{slot_id}"
        data = {
            "type": "test_stopped",
            "slot_id": slot_id,
            "owner": username,
            "test_case": test_case,
            "timestamp": datetime.now().isoformat(),
            "details_url": slot_url,
        }

        # Telegram notification
        if self.telegram_notifier and username in self.telegram_notifier.chat_ids:
            try:
                self.telegram_notifier.notify_test_stopped(username, slot_id, test_case)
            except Exception as e:
                print(f"Telegram notification failed: {e}")
                success = False

        # Webhook notification
        if self.config.is_webhook_enabled():
            try:
                self._send_webhook(data)
            except Exception as e:
                print(f"Webhook notification failed: {e}")
                success = False

        return success

    def _send_webhook(self, data: Dict[str, Any]) -> bool:
        """Send notification via webhook"""
        try:
            response = requests.post(
                self.config.WEBHOOK_URL,
                json=data,
                timeout=self.config.WEBHOOK_TIMEOUT,
                headers={"Content-Type": "application/json"},
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Webhook request failed: {e}")
            return False


# Singleton instance
notification_manager = NotificationManager()
