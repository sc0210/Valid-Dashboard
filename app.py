"""
Test Dashboard Backend Server
Provides REST API for managing test execution slots and monitoring progress
"""

from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import json
import os
import subprocess
import threading
import time
import re
import psutil
from datetime import datetime
from threading import Lock

# Import from src package
from src.config import Config
from src.notification_manager import notification_manager

app = Flask(__name__)
CORS(app)

# Use configuration from Config class
DATA_FILE = Config.DATA_FILE
LOG_DIRECTORY = Config.LOG_DIRECTORY
NUM_SLOTS = Config.NUM_SLOTS
SERVER_HOST = Config.SERVER_HOST
SERVER_PORT = Config.SERVER_PORT
DEBUG_MODE = Config.DEBUG_MODE

data_lock = Lock()
running_processes = {}  # Track running test processes

# Get Telegram notifier from notification manager (for backward compatibility)
telegram_notifier = notification_manager.telegram_notifier
TELEGRAM_ENABLED = telegram_notifier is not None

# Initialize default test slots
DEFAULT_SLOTS = {
    "slots": [
        {
            "id": i,
            "owner": "",
            "status": "idle",  # idle, running, success, failed, stopping
            "progress": 0,
            "test_case": "",
            "script_path": "",
            "script_command": "",
            "script_args": "",
            "ssd_serial": "",
            "ssd_eui": "",
            "log_ip": "",
            "log_port": "",
            "log_file": "",
            "start_time": "",
            "last_update": "",
            "error_msg": "",
            "pid": 0,
        }
        for i in range(NUM_SLOTS)
    ]
}


def load_data():
    """Load test slot data from JSON file with error handling"""
    with data_lock:
        return _load_data_unsafe()


def _load_data_unsafe():
    """Internal: Load data without locking (assumes caller holds lock)"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r") as f:
                content = f.read()
                if not content or content.strip() == "":
                    return DEFAULT_SLOTS.copy()
                return json.loads(content)
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading data file: {e}. Using default slots.")
            if os.path.exists(DATA_FILE):
                backup_file = f"{DATA_FILE}.backup.{int(time.time())}"
                os.rename(DATA_FILE, backup_file)
                print(f"Corrupted file backed up to: {backup_file}")
            return DEFAULT_SLOTS.copy()
    return DEFAULT_SLOTS.copy()


def save_data(data):
    """Save test slot data to JSON file with atomic write"""
    with data_lock:
        _save_data_unsafe(data)


def _save_data_unsafe(data):
    """Internal: Save data without locking (assumes caller holds lock)"""
    temp_file = f"{DATA_FILE}.tmp"
    try:
        with open(temp_file, "w") as f:
            json.dump(data, f, indent=2)
        os.replace(temp_file, DATA_FILE)
    except Exception as e:
        print(f"Error saving data: {e}")
        if os.path.exists(temp_file):
            os.remove(temp_file)
        raise


def update_slot_field(slot_id, updates):
    """Atomically update specific fields of a slot

    Args:
        slot_id: The slot ID to update
        updates: Dictionary of field names and values to update
    """
    with data_lock:
        data = _load_data_unsafe()
        if slot_id < 0 or slot_id >= len(data["slots"]):
            return False

        slot = data["slots"][slot_id]
        for key, value in updates.items():
            slot[key] = value

        _save_data_unsafe(data)
        return True


@app.route("/")
def index():
    """Serve the dashboard page"""
    return render_template("dashboard.html")


@app.route("/api/slots", methods=["GET"])
def get_slots():
    """Get all test slots"""
    data = load_data()
    return jsonify(data)


@app.route("/api/slots/<int:slot_id>", methods=["GET", "PUT"])
def update_slot(slot_id):
    """Get or update a specific test slot"""
    data = load_data()

    if slot_id < 0 or slot_id >= len(data["slots"]):
        return jsonify({"error": "Invalid slot ID"}), 400

    slot = data["slots"][slot_id]

    if request.method == "GET":
        return jsonify(slot)

    # PUT method
    update = request.json

    # Update fields
    if "owner" in update:
        slot["owner"] = update["owner"]
    if "status" in update:
        slot["status"] = update["status"]
    if "progress" in update:
        slot["progress"] = update["progress"]
    if "test_case" in update:
        slot["test_case"] = update["test_case"]
    if "script_path" in update:
        slot["script_path"] = update["script_path"]
    if "script_command" in update:
        slot["script_command"] = update["script_command"]
    if "script_args" in update:
        slot["script_args"] = update["script_args"]
    if "ssd_serial" in update:
        slot["ssd_serial"] = update["ssd_serial"]
    if "ssd_eui" in update:
        slot["ssd_eui"] = update["ssd_eui"]
    if "log_ip" in update:
        slot["log_ip"] = update["log_ip"]
    if "log_port" in update:
        slot["log_port"] = update["log_port"]
    if "log_file" in update:
        slot["log_file"] = update["log_file"]
    if "start_time" in update:
        slot["start_time"] = update["start_time"]
    if "error_msg" in update:
        slot["error_msg"] = update["error_msg"]
    if "pid" in update:
        slot["pid"] = update["pid"]

    slot["last_update"] = datetime.now().isoformat()

    save_data(data)
    return jsonify(slot)


@app.route("/api/slots/<int:slot_id>/setup", methods=["POST"])
def setup_slot(slot_id):
    """Manually setup a slot with task information without launching"""
    data = load_data()

    if slot_id < 0 or slot_id >= len(data["slots"]):
        return jsonify({"error": "Invalid slot ID"}), 400

    slot = data["slots"][slot_id]

    # Only allow setup on idle or non-running slots
    if slot["status"] == "running":
        return jsonify({"error": "Cannot setup a running slot. Stop it first."}), 400

    params = request.json

    # Update slot with manual setup
    slot.update(
        {
            "owner": params.get("owner", ""),
            "test_case": params.get("test_case", ""),
            "ssd_serial": params.get("ssd_serial", ""),
            "ssd_eui": params.get("ssd_eui", ""),
            "script_path": params.get("script_path", ""),
            "script_args": params.get("script_args", ""),
            "status": "idle",
            "progress": 0,
            "start_time": "",
            "error_msg": "",
            "last_update": datetime.now().isoformat(),
        }
    )

    save_data(data)
    return jsonify(slot)


@app.route("/api/slots/<int:slot_id>/clear", methods=["POST"])
def clear_slot_data(slot_id):
    """Clear test results and owner, but keep test configuration"""
    data = load_data()

    if slot_id < 0 or slot_id >= len(data["slots"]):
        return jsonify({"error": "Invalid slot ID"}), 400

    slot = data["slots"][slot_id]

    # Can't clear a running test
    if slot["status"] == "running":
        return jsonify({"error": "Cannot clear a running test. Stop it first."}), 400

    # Clear results AND owner, but keep test configuration (test_case, scripts, ssd info, log settings)
    slot["owner"] = ""
    slot["status"] = "idle"
    slot["progress"] = 0
    slot["start_time"] = ""
    slot["error_msg"] = ""
    slot["log_file"] = ""
    slot["pid"] = 0
    slot["last_update"] = datetime.now().isoformat()

    save_data(data)
    return jsonify(slot)


@app.route("/api/slots/<int:slot_id>/reset", methods=["POST"])
def reset_slot(slot_id):
    """Reset a test slot to idle state (clears everything)"""
    data = load_data()

    if slot_id < 0 or slot_id >= len(data["slots"]):
        return jsonify({"error": "Invalid slot ID"}), 400

    # Stop running process if any
    if slot_id in running_processes:
        try:
            running_processes[slot_id].terminate()
            del running_processes[slot_id]
        except:
            pass

    slot = data["slots"][slot_id]
    slot.update(
        {
            "owner": "",
            "status": "idle",
            "progress": 0,
            "test_case": "",
            "script_path": "",
            "script_command": "",
            "script_args": "",
            "ssd_serial": "",
            "ssd_eui": "",
            "log_ip": "",
            "log_port": "",
            "log_file": "",
            "start_time": "",
            "error_msg": "",
            "pid": 0,
            "last_update": datetime.now().isoformat(),
        }
    )

    save_data(data)
    return jsonify(slot)


@app.route("/api/slots/reset-all", methods=["POST"])
def reset_all_slots():
    """Reset all test slots"""
    # Stop all running processes
    for slot_id in list(running_processes.keys()):
        try:
            running_processes[slot_id].terminate()
            del running_processes[slot_id]
        except:
            pass

    data = DEFAULT_SLOTS.copy()
    for slot in data["slots"]:
        slot["last_update"] = datetime.now().isoformat()
    save_data(data)
    return jsonify(data)


@app.route("/api/slots/<int:slot_id>/launch", methods=["POST"])
def launch_test(slot_id):
    """Launch a test script in the specified slot"""
    # Get launch parameters first
    params = request.json
    script_path = params.get("script_path", "")
    script_args = params.get("script_args", "")

    if not script_path:
        return jsonify({"error": "Script path is required"}), 400

    # Atomically check status and update slot information
    with data_lock:
        data = _load_data_unsafe()

        if slot_id < 0 or slot_id >= len(data["slots"]):
            return jsonify({"error": "Invalid slot ID"}), 400

        slot = data["slots"][slot_id]

        # Check if slot is already running
        if slot["status"] == "running":
            return jsonify({"error": "Slot is already running a test"}), 400

        # Update slot information
        slot.update(
            {
                "owner": params.get("owner", ""),
                "test_case": params.get("test_case", ""),
                "script_path": script_path,
                "script_command": f"bash {script_path} {script_args}",
                "script_args": script_args,
                "ssd_serial": params.get("ssd_serial", ""),
                "ssd_eui": params.get("ssd_eui", ""),
                "log_ip": params.get("log_ip", ""),
                "log_port": params.get("log_port", ""),
                "status": "running",
                "progress": 0,
                "start_time": datetime.now().isoformat(),
                "last_update": datetime.now().isoformat(),
                "error_msg": "",
            }
        )

        _save_data_unsafe(data)

    # Launch the test script in a separate thread
    thread = threading.Thread(
        target=run_test_script,
        args=(
            slot_id,
            script_path,
            script_args,
            params.get("log_ip", ""),
            params.get("log_port", ""),
            params.get("test_case", ""),
            params.get("owner", ""),
            params.get("log_folder", LOG_DIRECTORY),
        ),
    )
    thread.daemon = True
    thread.start()

    # Send notifications (Telegram and/or Webhook)
    if slot.get("owner"):
        notification_manager.notify_test_started(
            username=slot["owner"],
            slot_id=slot_id,
            test_case=slot.get("test_case", "Unknown"),
        )

    return jsonify(slot)


@app.route("/api/slots/<int:slot_id>/stop", methods=["POST"])
def stop_test(slot_id):
    """Stop a running test"""
    data = load_data()

    if slot_id < 0 or slot_id >= len(data["slots"]):
        return jsonify({"error": "Invalid slot ID"}), 400

    slot = data["slots"][slot_id]

    # Stop the process
    if slot_id in running_processes:
        try:
            running_processes[slot_id].terminate()
            del running_processes[slot_id]
            slot["status"] = "failed"
            slot["error_msg"] = "Test stopped by user"
            slot["last_update"] = datetime.now().isoformat()
            save_data(data)

            # Send notification
            if slot.get("owner"):
                notification_manager.notify_test_stopped(
                    username=slot["owner"],
                    slot_id=slot_id,
                    test_case=slot.get("test_case", "Unknown"),
                )
        except Exception as e:
            return jsonify({"error": f"Failed to stop test: {str(e)}"}), 500

    return jsonify(slot)


def run_test_script(
    slot_id,
    script_path,
    script_args,
    log_ip="",
    log_port="",
    test_case="",
    owner="",
    log_folder="",
):
    """Run a test script and monitor its progress with proper log handling"""
    try:
        # Build command with log directory and test case parameters
        cmd = ["bash", script_path]

        # Add standard arguments: log_ip, log_port, log_dir, test_case, owner
        if log_ip:
            cmd.append(log_ip)
        else:
            cmd.append("")

        if log_port:
            cmd.append(log_port)
        else:
            cmd.append("")

        # Use provided log folder or default to environment variable
        actual_log_dir = log_folder if log_folder else LOG_DIRECTORY
        cmd.append(actual_log_dir)

        # Add test case name (sanitized for filesystem)
        safe_test_case = (
            test_case.replace(" ", "_").replace("/", "_")
            if test_case
            else "UnknownTest"
        )
        cmd.append(safe_test_case)

        # Add owner
        safe_owner = (
            owner.replace(" ", "_").replace("/", "_") if owner else "DefaultUser"
        )
        cmd.append(safe_owner)

        # Add any additional script args
        if script_args:
            cmd.extend(script_args.split())

        # Start process
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1
        )

        running_processes[slot_id] = process

        # Update PID atomically
        update_slot_field(slot_id, {"pid": process.pid})

        # Monitor output for progress and log file path
        progress_pattern = re.compile(r"progress[:\s]+(\d+)%", re.IGNORECASE)
        log_file_pattern = re.compile(r"LOG_FILE=(.+)")
        detected_log_file = None

        for line in process.stdout:
            # Look for progress indicators
            match = progress_pattern.search(line)
            if match:
                progress = int(match.group(1))
                # Update only progress field atomically
                update_slot_field(
                    slot_id,
                    {
                        "progress": min(progress, 100),
                        "last_update": datetime.now().isoformat(),
                    },
                )

            # Look for log file path
            log_match = log_file_pattern.search(line)
            if log_match:
                detected_log_file = log_match.group(1).strip()
                # Update log file path in slot
                update_slot_field(slot_id, {"log_file": detected_log_file})

        # Wait for process to complete
        return_code = process.wait()

        # Get current slot data for notification
        data = load_data()
        slot = data["slots"][slot_id]
        owner = slot.get("owner", "")
        test_case = slot.get("test_case", "Unknown")
        start_time_str = slot.get("start_time", "")

        # Update final status atomically
        if return_code == 0:
            update_slot_field(
                slot_id,
                {
                    "status": "success",
                    "progress": 100,
                    "last_update": datetime.now().isoformat(),
                },
            )

            # Calculate duration
            duration = ""
            if start_time_str:
                try:
                    start_time = datetime.fromisoformat(start_time_str)
                    duration_sec = (datetime.now() - start_time).total_seconds()
                    hours = int(duration_sec // 3600)
                    minutes = int((duration_sec % 3600) // 60)
                    seconds = int(duration_sec % 60)
                    if hours > 0:
                        duration = f"{hours}h {minutes}m {seconds}s"
                    elif minutes > 0:
                        duration = f"{minutes}m {seconds}s"
                    else:
                        duration = f"{seconds}s"
                except:
                    pass

            # Send success notification
            if owner:
                notification_manager.notify_test_completed(
                    username=owner,
                    slot_id=slot_id,
                    test_case=test_case,
                    duration=duration,
                )
        else:
            stderr_output = process.stderr.read()
            error_msg = (
                stderr_output[:500]
                if stderr_output
                else f"Process exited with code {return_code}"
            )
            update_slot_field(
                slot_id,
                {
                    "status": "failed",
                    "error_msg": error_msg,
                    "last_update": datetime.now().isoformat(),
                },
            )

            # Send failure notification
            if owner:
                notification_manager.notify_test_failed(
                    username=owner,
                    slot_id=slot_id,
                    test_case=test_case,
                    error_msg=error_msg,
                )

        # Clean up
        if slot_id in running_processes:
            del running_processes[slot_id]

    except Exception as e:
        # Get slot data for notification
        try:
            data = load_data()
            slot = data["slots"][slot_id]
            owner = slot.get("owner", "")
            test_case = slot.get("test_case", "Unknown")
        except:
            owner = ""
            test_case = "Unknown"

        # Update slot with error atomically
        error_msg = str(e)
        update_slot_field(
            slot_id,
            {
                "status": "failed",
                "error_msg": error_msg,
                "last_update": datetime.now().isoformat(),
            },
        )

        # Send failure notification
        if owner:
            notification_manager.notify_test_failed(
                username=owner,
                slot_id=slot_id,
                test_case=test_case,
                error_msg=error_msg,
            )

        if slot_id in running_processes:
            del running_processes[slot_id]


@app.route("/api/config", methods=["GET"])
def get_config():
    """Get configuration settings"""
    return jsonify(
        {
            "num_slots": len(load_data()["slots"]),
            "refresh_interval": 3000,  # milliseconds
        }
    )


@app.route("/slot/<int:slot_id>")
def slot_detail(slot_id):
    """Serve the detailed slot view page"""
    return render_template("slot_detail.html")


@app.route("/testcase")
def testcase():
    """Serve the test case library page"""
    return render_template("testcase.html")


@app.route("/uart-log")
def uart_log():
    """Render the UART log monitor page"""
    return render_template("uart_log.html")


@app.route("/serial-monitor")
def serial_monitor():
    """Render the serial monitor page"""
    return render_template("serial_monitor.html")


@app.route("/api/serial/send", methods=["POST"])
def send_serial_data():
    """Send data to serial device

    Accepts JSON payload with:
    - port: Serial port path (e.g., /dev/ttyUSB0)
    - data: Data to send (string or bytes)
    - type: 'command' or 'file'
    - filename: (optional) Original filename if type is 'file'
    """
    try:
        import serial

        payload = request.get_json()
        port = payload.get("port")
        data = payload.get("data")
        data_type = payload.get("type", "command")
        filename = payload.get("filename")

        if not port or data is None:
            return jsonify({"success": False, "error": "Missing port or data"}), 400

        # Get serial port configuration from request or use defaults
        baudrate = payload.get("baudrate", 115200)
        databits = int(payload.get("databits", 8))
        parity = payload.get("parity", "N")
        stopbits = float(payload.get("stopbits", 1))

        # Convert parity character to pyserial constant
        parity_map = {
            "N": serial.PARITY_NONE,
            "E": serial.PARITY_EVEN,
            "O": serial.PARITY_ODD,
            "M": serial.PARITY_MARK,
            "S": serial.PARITY_SPACE,
        }

        try:
            # Open serial port
            ser = serial.Serial(
                port=port,
                baudrate=baudrate,
                bytesize=databits,
                parity=parity_map.get(parity, serial.PARITY_NONE),
                stopbits=stopbits,
                timeout=1,
            )

            # Send data
            if data_type == "command":
                # Text command
                if isinstance(data, str):
                    bytes_written = ser.write(data.encode())
                else:
                    bytes_written = ser.write(data)
            else:
                # File data
                if isinstance(data, str):
                    bytes_written = ser.write(data.encode())
                else:
                    bytes_written = ser.write(data)

            ser.close()

            return jsonify(
                {
                    "success": True,
                    "bytes_written": bytes_written,
                    "type": data_type,
                    "filename": filename,
                }
            )

        except serial.SerialException as e:
            return (
                jsonify({"success": False, "error": f"Serial port error: {str(e)}"}),
                500,
            )

    except ImportError:
        # pyserial not installed - return mock success for demo
        return jsonify(
            {
                "success": True,
                "bytes_written": len(str(payload.get("data", ""))),
                "type": payload.get("type", "command"),
                "note": "pyserial not installed - simulated send",
            }
        )
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route("/bot-monitor")
def bot_monitor():
    """Render the Telegram bot monitor page"""
    return render_template("bot_monitor.html")


@app.route("/settings")
def settings():
    """Render the settings page"""
    return render_template("settings.html")


@app.route("/resource-monitor")
def resource_monitor():
    """Render the resource monitor page"""
    return render_template("resource_monitor.html")


@app.route("/api/system/resources", methods=["GET"])
def get_system_resources():
    """Get system resource usage and running test processes"""
    try:
        # Get RAM usage
        ram = psutil.virtual_memory()
        ram_data = {
            "percent": round(ram.percent, 1),
            "used": round(ram.used / (1024**3), 2),  # Convert to GB
            "total": round(ram.total / (1024**3), 2),
        }

        # Get CPU usage
        cpu_percent = psutil.cpu_percent(interval=0.5)
        cpu_data = {
            "percent": round(cpu_percent, 1),
            "count": psutil.cpu_count(),
        }

        # Get Disk usage
        disk = psutil.disk_usage("/")
        disk_data = {
            "percent": round(disk.percent, 1),
            "used": round(disk.used / (1024**3), 2),
            "total": round(disk.total / (1024**3), 2),
        }

        # Get running test processes
        data = load_data()
        processes = []

        for slot in data["slots"]:
            if slot["status"] == "running" and slot["pid"] > 0:
                try:
                    proc = psutil.Process(slot["pid"])
                    processes.append(
                        {
                            "slot_id": slot["id"],
                            "owner": slot["owner"],
                            "test_case": slot["test_case"],
                            "pid": slot["pid"],
                            "cpu_percent": round(proc.cpu_percent(interval=0.1), 1),
                            "memory_percent": round(proc.memory_percent(), 1),
                            "status": slot["status"],
                        }
                    )
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    # Process no longer exists or access denied
                    continue

        return jsonify(
            {
                "ram": ram_data,
                "cpu": cpu_data,
                "disk": disk_data,
                "processes": processes,
            }
        )
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/telegram/test", methods=["POST"])
def test_telegram_connection():
    """Test Telegram connection for a specific user"""
    if not TELEGRAM_ENABLED or not telegram_notifier:
        return jsonify({"error": "Telegram bot not enabled"}), 503

    data = request.json
    username = data.get("username", "").strip()
    slot_id = data.get("slot_id", 0)

    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Check if user is registered
    if username not in telegram_notifier.chat_ids:
        return (
            jsonify(
                {
                    "error": f"User '{username}' not registered. Use /register in Telegram bot"
                }
            ),
            404,
        )

    # Send test message
    try:
        chat_id = telegram_notifier.chat_ids[username]
        message = f"✅ Connection test successful!\n\n📍 Slot {slot_id}\n👤 User: {username}\n\nYou will receive notifications for your tests."

        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_notifier.bot.send_message(chat_id, message))
        loop.close()

        telegram_notifier.log_activity(
            "command", username, "Connection test", f"Slot {slot_id}"
        )

        return jsonify(
            {
                "success": True,
                "message": f"Test message sent to {username}",
            }
        )
    except Exception as e:
        return jsonify({"error": f"Failed to send message: {str(e)}"}), 500


@app.route("/api/telegram/notify-fail", methods=["POST"])
def notify_telegram_fail():
    """Send fail/error notification to user via Telegram"""
    if not TELEGRAM_ENABLED or not telegram_notifier:
        return jsonify({"error": "Telegram bot not enabled"}), 503

    data = request.json
    username = data.get("username", "").strip()
    slot_id = data.get("slot_id", 0)
    test_case = data.get("test_case", "Unknown")
    error_msg = data.get("error_msg", "Test failed")

    if not username:
        return jsonify({"error": "Username is required"}), 400

    # Check if user is registered
    if username not in telegram_notifier.chat_ids:
        return (
            jsonify(
                {
                    "error": f"User '{username}' not registered. Use /register in Telegram bot"
                }
            ),
            404,
        )

    # Send fail notification
    try:
        chat_id = telegram_notifier.chat_ids[username]
        # Build slot detail URL
        dashboard_url = os.getenv("DASHBOARD_URL", "http://localhost:3000")
        slot_url = f"{dashboard_url}/slot/{slot_id}"

        message = f"🚨 Test Failure Alert\n\n"
        message += f"📍 Slot: {slot_id}\n"
        message += f"📋 Test Case: {test_case}\n"
        message += f"👤 Owner: {username}\n"
        message += f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        message += f"❌ Error: {error_msg}\n\n"
        message += f"🔗 View Details: {slot_url}"

        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(telegram_notifier.bot.send_message(chat_id, message))
        loop.close()

        telegram_notifier.log_activity(
            "notification",
            username,
            "Fail notification sent",
            f"Slot {slot_id}: {test_case}",
        )

        return jsonify(
            {
                "success": True,
                "message": f"Fail notification sent to {username}",
            }
        )
    except Exception as e:
        return jsonify({"error": f"Failed to send notification: {str(e)}"}), 500


@app.route("/api/bot/stats", methods=["GET"])
def get_bot_stats():
    """Get Telegram bot statistics"""
    if TELEGRAM_ENABLED and telegram_notifier:
        stats = telegram_notifier.get_statistics()
        return jsonify(stats)
    return jsonify(
        {
            "total_users": 0,
            "registered_users": [],
            "activity_log": [],
            "bot_status": "disabled",
        }
    )


if __name__ == "__main__":
    # Initialize data file if it doesn't exist
    if not os.path.exists(DATA_FILE):
        save_data(DEFAULT_SLOTS)

    # Initialize and start Telegram bot (only in main process, not reloader)
    is_reloader = os.environ.get("WERKZEUG_RUN_MAIN") == "true"

    if telegram_notifier and (not DEBUG_MODE or is_reloader):
        print("🤖 Initializing Telegram bot...")
        if telegram_notifier.initialize_bot():
            telegram_notifier.start_bot()
        else:
            print("⚠️  Telegram notifications disabled")

    # Print startup information
    print("\n" + "=" * 60)
    print("🚀 ValidDashboard - Test Execution Controller")
    print("=" * 60)
    print(f"\n📊 Configuration:")
    print(f"   Host: {SERVER_HOST}")
    print(f"   Port: {SERVER_PORT}")
    print(f"   Debug: {DEBUG_MODE}")
    print(f"   Slots: {NUM_SLOTS}")
    print(f"\n📬 Notification Settings:")

    if Config.is_telegram_enabled():
        print(f"   ✅ Telegram: Enabled")
    else:
        print(f"   ⚪ Telegram: Disabled (no token or method not selected)")

    if Config.is_webhook_enabled():
        print(f"   ✅ Webhook: {Config.WEBHOOK_URL}")
    else:
        print(f"   ⚪ Webhook: Disabled")

    print(f"\n🌐 Access Points:")
    print(f"   Dashboard: http://localhost:{SERVER_PORT}")
    print(f"   Resource Monitor: http://localhost:{SERVER_PORT}/resource-monitor")
    print(f"   Serial Monitor: http://localhost:{SERVER_PORT}/serial-monitor")
    print("\n" + "=" * 60 + "\n")

    # Run server
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=DEBUG_MODE, threaded=True)
