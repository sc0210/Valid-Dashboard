"""
Test Client Library
Use this in your test scripts to update the dashboard
"""

import requests
from datetime import datetime
import os


class TestSlotClient:
    """Client for updating test slot status on the dashboard"""

    def __init__(self, slot_id, server_url="http://localhost:3000"):
        """
        Initialize test slot client

        Args:
            slot_id: The slot number to use (1-based)
            server_url: Dashboard server URL
        """
        self.slot_id = slot_id
        self.server_url = server_url
        self.api_url = f"{server_url}/api/slots/{slot_id}"

    def start_test(
        self,
        owner,
        test_case,
        log_file="",
        script_path="",
        script_command="",
        ssd_serial="",
        ssd_eui="",
    ):
        """
        Mark test as started

        Args:
            owner: Test owner name
            test_case: Test case name
            log_file: Path to log file (optional)
            script_path: Path to test script (optional)
            script_command: Command to run script (optional)
            ssd_serial: SSD serial number (optional)
            ssd_eui: SSD EUI number (optional)
        """
        data = {
            "owner": owner,
            "test_case": test_case,
            "status": "running",
            "progress": 0,
            "log_file": log_file,
            "script_path": script_path,
            "script_command": script_command,
            "ssd_serial": ssd_serial,
            "ssd_eui": ssd_eui,
            "start_time": datetime.now().isoformat(),
        }
        try:
            response = requests.put(self.api_url, json=data, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Warning: Could not update dashboard: {e}")
            return False

    def update_progress(self, progress, status="running"):
        """Update test progress (0-100)"""
        data = {"progress": progress, "status": status}
        try:
            response = requests.put(self.api_url, json=data, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Warning: Could not update dashboard: {e}")
            return False

    def complete_test(self, success=True):
        """Mark test as completed"""
        data = {"status": "success" if success else "failed", "progress": 100}
        try:
            response = requests.put(self.api_url, json=data, timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Warning: Could not update dashboard: {e}")
            return False

    def fail_test(self, error_msg=""):
        """Mark test as failed"""
        return self.complete_test(success=False)

    def reset(self):
        """Reset the slot to idle"""
        try:
            response = requests.post(f"{self.api_url}/reset", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"Warning: Could not reset slot: {e}")
            return False


# Example usage in your test script:
if __name__ == "__main__":
    import time

    # Initialize client for slot 1
    client = TestSlotClient(slot_id=1)

    # Start test
    print("Starting test...")
    client.start_test(
        owner="John Doe", test_case="TestCase_001", log_file="logs/test_001.log"
    )

    # Simulate test progress
    for progress in range(0, 101, 20):
        print(f"Progress: {progress}%")
        client.update_progress(progress)
        time.sleep(2)

    # Complete test
    print("Test completed!")
    client.complete_test(success=True)
