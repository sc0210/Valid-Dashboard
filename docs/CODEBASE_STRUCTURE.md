# ValidDashboard - Codebase Organization

## 📁 Directory Structure

```
ValidDashboard/
├── app.py                      # Main Flask application (entry point)
├── webhook_receiver.py         # Standalone notification receiver
├── requirements.txt            # Python dependencies
├── .env / .env.example        # Environment configuration
├── test_slots.json            # Slot data storage
├── telegram_config.json       # Telegram user registrations
│
├── src/                       # Source code modules
│   ├── __init__.py           # Package initialization
│   ├── config.py             # Configuration management
│   ├── notification_manager.py  # Unified notification system
│   ├── telegram_bot.py       # Telegram bot integration
│   └── log_manager.py        # Log file management
│
├── templates/                 # HTML templates (Flask)
│   ├── dashboard.html        # Main dashboard page
│   ├── slot_detail.html      # Individual slot view
│   ├── serial_monitor.html   # Serial communication interface
│   ├── bot_monitor.html      # Telegram bot monitoring
│   ├── resource_monitor.html # System resource monitoring
│   └── settings.html         # User settings page
│
├── example_scripts/           # Test script examples
│   ├── basic_test.sh         # Simple test script
│   ├── performance_test.sh   # Multi-phase test orchestrator
│   ├── test_phase1_init.py   # Phase 1: Initialization
│   ├── test_phase2_performance.py  # Phase 2: Performance
│   ├── test_phase3_stress.py      # Phase 3: Stress testing
│   └── test_phase4_validation.py  # Phase 4: Validation
│
├── logs/                      # Test execution logs
│   ├── Alice/                # Per-user log directories
│   └── Bob/
│
├── exported_logs/             # Archived/exported logs
│
└── docs/                      # Documentation
    ├── README.md
    ├── QUICKSTART.md
    ├── TELEGRAM_SETUP.md
    ├── WEBHOOK_SETUP.md
    └── CHANGES.md
```

## 🎯 Module Responsibilities

### Core Application (`app.py`)
- Flask web server and routing
- REST API endpoints
- Slot management and test execution
- Integration with notification system

### Source Modules (`src/`)

#### `config.py`
- Centralized configuration loading
- Environment variable management
- Configuration validation
- Helper methods for settings

#### `notification_manager.py`
- **Unified notification interface**
- Supports multiple channels (Telegram, Webhook)
- Handles all test event notifications
- Configurable notification methods

#### `telegram_bot.py`
- Telegram Bot API integration
- User registration and commands
- Message sending and receiving
- Activity logging

#### `log_manager.py`
- Log file creation and management
- Output redirection
- Log separation by test case
- Timestamped log generation

### Notification System (`webhook_receiver.py`)
- **Standalone Flask server**
- Receives webhook notifications
- Web-based notification viewer
- No internet required (local network)
- RESTful API for integrations

## 🔄 Notification Flow

```
Test Event → app.py → notification_manager.py
                              ↓
                    ┌─────────┴─────────┐
                    ↓                   ↓
            telegram_bot.py      HTTP POST
                    ↓                   ↓
              Telegram API       webhook_receiver.py
                    ↓                   ↓
              User's Phone      Local Dashboard
```

## 🚀 Getting Started

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your settings
```

### 3. Choose Notification Method

#### Option A: Telegram (requires internet)
```bash
# .env
NOTIFICATION_METHOD=telegram
TELEGRAM_BOT_TOKEN=your_token_here
```

#### Option B: Webhook (local network only)
```bash
# Terminal 1: Start webhook receiver
python webhook_receiver.py

# Terminal 2: Configure dashboard
# .env
NOTIFICATION_METHOD=webhook
WEBHOOK_URL=http://localhost:8080/notifications
```

#### Option C: Both
```bash
NOTIFICATION_METHOD=both
TELEGRAM_BOT_TOKEN=your_token_here
WEBHOOK_URL=http://192.168.1.50:8080/notifications
```

### 4. Start Dashboard
```bash
python app.py
```

## 📦 Dependencies

### Required
- Flask 3.0.0 - Web framework
- flask-cors 4.0.0 - CORS support
- psutil 5.9.6 - System resource monitoring
- requests 2.31.0 - HTTP requests

### Optional (for Telegram)
- python-telegram-bot 21.0 - Telegram integration
- aiohttp 3.9.1 - Async HTTP for bot

### Optional (for Serial)
- pyserial 3.5 - Serial port communication

## 🔧 Configuration Options

### Notification Methods
- `telegram` - Telegram bot notifications (requires internet)
- `webhook` - HTTP webhooks to local receiver (offline-capable)
- `both` - Send to both Telegram and webhook

### Server Settings
- `SERVER_HOST` - Bind address (0.0.0.0 for all interfaces)
- `SERVER_PORT` - Port number (default: 3000)
- `DEBUG_MODE` - Enable Flask debug mode

### Data Settings
- `DATA_FILE` - Slot data JSON file
- `LOG_DIRECTORY` - Base directory for logs
- `NUM_SLOTS` - Number of test slots (default: 16)

## 🛠️ Development

### Adding New Notification Channels

1. Create handler in `src/notification_manager.py`:
```python
def _send_email(self, data):
    # Your email sending code
    pass
```

2. Add to notification methods:
```python
def notify_test_failed(self, username, slot_id, test_case, error_msg):
    # ... existing code ...
    
    # Add email notification
    if self.config.is_email_enabled():
        self._send_email(data)
```

3. Update `src/config.py`:
```python
EMAIL_ENABLED = os.getenv("EMAIL_ENABLED", "False").lower() == "true"
SMTP_HOST = os.getenv("SMTP_HOST", "localhost")
```

### Code Style
- Use type hints where possible
- Docstrings for all public functions
- Keep functions focused and small
- Use configuration class for all settings

## 📚 Documentation

- **QUICKSTART.md** - Quick setup guide
- **TELEGRAM_SETUP.md** - Telegram bot configuration
- **WEBHOOK_SETUP.md** - Webhook receiver setup
- **CHANGES.md** - Version history and changes

## 🔐 Security Notes

### Local Network Deployment
- Bind to specific IP for security
- Use firewall rules to restrict access
- Consider VPN for remote access

### Internet-Exposed Deployment
- Enable HTTPS/SSL
- Add authentication middleware
- Use environment variables for secrets
- Never commit `.env` file

## 🤝 Contributing

1. Follow existing code structure
2. Add documentation for new features
3. Update relevant README files
4. Test both notification methods

---

**Architecture Design**: Modular, extensible, offline-capable
**Primary Use Case**: Parallel test execution with real-time monitoring
**Target Environment**: Local networks, air-gapped systems, lab environments
