# Test Execution Dashboard

A professional real-time web dashboard for monitoring test execution progress on server machines. This system provides high-level visibility into test case execution across multiple slots, with comprehensive slot details, SSD information tracking, and separate log management for each test case.

## ✨ Features

### 🎨 Professional Dashboard UI
- **Left Sidebar Navigation**: Quick access to views, actions, and resources
- **Grid View**: Overview of all test slots with status at a glance
- **Detailed Slot View**: Click any slot to see comprehensive information
- **Real-time Updates**: Auto-refresh every 3 seconds
- **Live Statistics**: Running, success, and failed test counts
- **Responsive Design**: Works on desktop and tablet screens

### 📊 Comprehensive Slot Information
Each slot displays:
- **Test Info**: Owner, test case name, timestamps
- **SSD Details**: Serial Number (SN) and EUI Number
- **Script Details**: Path, command, and log file location
- **Progress Tracking**: Visual progress bars and status indicators
- **Manual Editing**: Update slot information through the UI

### 📝 Advanced Log Management
- **Separate log files** for each test case
- **Organized by owner** (optional subdirectories)
- **Automatic timestamping** of log files
- **Dual output** (console + log file simultaneously)
- **Export functionality** with filtering options
- **Old log cleanup** to manage disk space

### 🤖 Telegram Notifications (NEW!)
- **Real-time notifications** sent to Telegram
- **Test status updates**: started, completed, failed, stopped
- **Multi-user support**: Each user registers their own username
- **Smart notifications**: Only receive alerts for your own tests
- **Easy setup**: Simple bot commands for registration

📘 **[Complete Telegram Setup Guide →](docs/TELEGRAM_SETUP.md)**

## 🚀 Quick Start

### 1. Installation

**Option A: Using the start script (Recommended)**
```bash
cd /Users/samchen/Documents/Dev/ValidDashboard
./start_dashboard.sh
```

**Option B: Manual installation**
```bash
# Install dependencies
pip install -r requirements.txt

# Start server
python app.py
```

### 2. Access the Dashboard

Open your browser and go to: **http://localhost:3000**

For network access from other machines: **http://YOUR_SERVER_IP:3000**

### 3. Run an Example Test

```bash
# In a new terminal
python example_test.py
```

Then watch the dashboard update in real-time!

## 📖 Usage in Your Test Scripts

### Complete Example with All Features

```python
from test_client import TestSlotClient
from log_manager import LogManager
import sys
import os

# Initialize
slot_id = 1  # Use different slot for each test machine/process
client = TestSlotClient(slot_id=slot_id, server_url='http://localhost:3000')
log_mgr = LogManager('logs')

# Create separate log file for this test case
log_file = log_mgr.create_log_file('MyTestCase', owner='JohnDoe')
log_mgr.start_logging(log_file)

# Capture script information automatically
script_path = os.path.abspath(__file__)
script_command = ' '.join(sys.argv)

# Start test with full details including SSD info
client.start_test(
    owner='John Doe',
    test_case='MyTestCase_001',
    log_file=log_file,
    script_path=script_path,
    script_command=script_command,
    ssd_serial='S5XNNG0N123456',  # Your SSD serial number
    ssd_eui='0x002538c00000001f'   # Your SSD EUI number
)

# Your test code here
# Update progress as needed
client.update_progress(25)
# ... more test code ...
client.update_progress(50)
# ... more test code ...
client.update_progress(75)

# Complete the test
client.complete_test(success=True)  # or success=False if failed

# Stop logging
log_mgr.stop_logging()
```

### Detecting SSD Information

Here's how to automatically detect SSD information in Linux:

```python
import subprocess
import json

def get_ssd_info(device='/dev/nvme0'):
    """Get SSD serial number and EUI from nvme device"""
    try:
        result = subprocess.run(
            ['nvme', 'id-ctrl', device, '-o', 'json'],
            capture_output=True,
            text=True
        )
        data = json.loads(result.stdout)
        
        ssd_serial = data.get('sn', '').strip()
        eui = data.get('eui64', '')
        ssd_eui = f"0x{eui}" if eui else ''
        
        return ssd_serial, ssd_eui
    except Exception as e:
        print(f"Could not detect SSD info: {e}")
        return '', ''

# Use in your test
ssd_sn, ssd_eui = get_ssd_info()
client.start_test(
    owner='TestUser',
    test_case='My_Test',
    log_file='test.log',
    ssd_serial=ssd_sn,
    ssd_eui=ssd_eui,
    script_path=__file__,
    script_command=' '.join(sys.argv)
)
```

## Usage Examples

### Example 1: Basic Test Integration

```python
from test_client import TestSlotClient
import time

# Connect to dashboard (slot 1)
client = TestSlotClient(slot_id=1)

# Start your test
client.start_test(owner="Alice", test_case="Smoke_Test")

# Run test with progress updates
for i in range(0, 101, 20):
    client.update_progress(i)
    time.sleep(1)  # Your actual test work here

# Mark as completed
client.complete_test(success=True)
```

### Example 2: Log Management

```python
from log_manager import LogManager

log_mgr = LogManager('logs')

# Create log file with owner subdirectory
log_file = log_mgr.create_log_file('Integration_Test', owner='Alice')

# Start logging (redirects print statements to log file + console)
log_mgr.start_logging(log_file)

print("Test started...")
# Your test code here
print("Test completed!")

# Stop logging
log_mgr.stop_logging()

# List all logs from a specific owner
alice_logs = log_mgr.list_logs(owner='Alice')
print(f"Alice's logs: {alice_logs}")

# Export logs
log_mgr.export_logs('exported_logs', filter_owner='Alice')

# Cleanup old logs (older than 30 days)
log_mgr.cleanup_old_logs(days=30)
```

### Example 3: Complete Test Script

See [example_test.py](example_test.py) for a full working example.

## Project Structure

```
ValidDashboard/
├── app.py                 # Flask web server (backend)
├── test_client.py         # Client library for test scripts
├── log_manager.py         # Log separation and management
├── templates/
│   └── dashboard.html     # Web dashboard (frontend)
├── logs/                  # Log files directory (auto-created)
│   ├── Alice/            # Per-owner subdirectories
│   └── Bob/
├── test_slots.json        # Current slot states (auto-created)
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## API Reference

### Dashboard Server API

**GET /api/slots**
- Get all test slot information

**PUT /api/slots/{slot_id}**
- Update a specific slot
- Body: JSON with fields (owner, status, progress, test_case, log_file, start_time)

**POST /api/slots/{slot_id}/reset**
- Reset a specific slot to idle state

**POST /api/slots/reset-all**
- Reset all slots to idle

### Test Client API

**TestSlotClient(slot_id, server_url)**
- Initialize client for a specific slot

**start_test(owner, test_case, log_file)**
- Mark test as started

**update_progress(progress, status)**
- Update progress (0-100)

**complete_test(success)**
- Mark test as completed (success/failed)

**reset()**
- Reset slot to idle

### Log Manager API

**LogManager(base_log_dir)**
- Initialize log manager

**create_log_file(test_case_name, owner, add_timestamp)**
- Create new log file with header

**start_logging(log_file_path)**
- Redirect stdout/stderr to log file

**stop_logging()**
- Stop logging and restore outputs

**export_logs(output_dir, filter_owner, filter_date)**
- Export logs with filtering

**list_logs(owner)**
- List all log files

**cleanup_old_logs(days)**
- Remove old log files

## Configuration

### Change Number of Slots

Edit [app.py](app.py) line 17:

```python
DEFAULT_SLOTS = {
    'slots': [
        {...} for i in range(8)  # Change 8 to desired number
    ]
}
```

### Change Auto-Refresh Interval

Edit [templates/dashboard.html](templates/dashboard.html) line 328:

```javascript
let refreshInterval = 3000; // Change 3000 (3 seconds) to desired milliseconds
```

### Change Server Port

Edit [app.py](app.py) last line:

```python
app.run(host='0.0.0.0', port=3000, debug=True)  # Change port here
```

## Troubleshooting

### Dashboard not accessible from other machines

1. Check firewall settings on the server machine
2. Ensure the server is bound to `0.0.0.0` (not `127.0.0.1`)
3. Use the correct IP address of the server

### Test script can't connect to dashboard

1. Verify the dashboard server is running
2. Check the server URL in your test script
3. Ensure network connectivity between machines

### Logs not appearing

1. Check that `logs/` directory has write permissions
2. Verify `start_logging()` is called before printing
3. Call `stop_logging()` to flush the log file

## Advanced Features

### Run Multiple Tests in Parallel

Use different slot IDs for each test:

```python
# Machine 1
client1 = TestSlotClient(slot_id=1)

# Machine 2
client2 = TestSlotClient(slot_id=2)

# And so on...
```

### Network Access

The dashboard server binds to `0.0.0.0` by default, making it accessible from other machines on your local network. Access it using:

```
http://<server-ip-address>:3000
```

In your test scripts running on other machines:

```python
client = TestSlotClient(
    slot_id=1,
    server_url='http://<server-ip-address>:3000'
)
```

## License

MIT License - Feel free to modify and use for your needs.

## Contributing

This is an internal tool. Feel free to customize it for your specific testing needs!

## Support

For issues or questions, contact your team lead or check the project repository.
