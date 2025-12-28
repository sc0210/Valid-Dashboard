# Webhook Receiver - Local Notification System

A standalone Flask server that receives and displays test execution notifications from ValidDashboard without requiring internet access.

## 🎯 Purpose

Perfect for air-gapped or offline environments where Telegram cannot reach the internet. Provides a local web dashboard to monitor test notifications in real-time.

## 🚀 Quick Start

### 1. Start the Webhook Receiver

```bash
python webhook_receiver.py
```

The server will start on `http://0.0.0.0:8080`

### 2. Configure ValidDashboard

Update your `.env` file:

```bash
# Use webhook instead of Telegram
NOTIFICATION_METHOD=webhook
WEBHOOK_URL=http://192.168.1.50:8080/notifications

# Or use both
NOTIFICATION_METHOD=both
WEBHOOK_URL=http://192.168.1.50:8080/notifications
```

### 3. Access the Dashboard

Open in browser: `http://localhost:8080` or `http://<server-ip>:8080`

## 📡 API Endpoints

### Receive Notifications (from ValidDashboard)
```http
POST /notifications
Content-Type: application/json

{
  "type": "test_failed",
  "slot_id": 5,
  "owner": "Alice",
  "test_case": "Performance_Test",
  "error": "Exit code 1",
  "timestamp": "2025-12-27T14:30:00",
  "details_url": "http://192.168.1.100:3000/slot/5"
}
```

### Get All Notifications
```http
GET /api/notifications
```

### Clear All Notifications
```http
DELETE /api/notifications
```

### Health Check
```http
GET /health
```

## 🌐 Network Setup

### Same Machine
```bash
# .env
WEBHOOK_URL=http://localhost:8080/notifications
```

### Local Network
```bash
# Find server IP
ifconfig  # or ipconfig on Windows

# .env
WEBHOOK_URL=http://192.168.1.50:8080/notifications
```

### Multiple Receivers
You can run multiple receivers on different ports for different teams:

```bash
# Team 1
python webhook_receiver.py  # Port 8080

# Team 2 (modify port in script)
# Change: app.run(host="0.0.0.0", port=8081, ...)
python webhook_receiver.py  # Port 8081
```

## 🎨 Features

- ✅ **Real-time Dashboard**: Auto-refreshes every 3 seconds
- ✅ **Notification History**: Stores last 100 notifications
- ✅ **Statistics**: Total and recent notification counts
- ✅ **Clickable Links**: Direct links to slot detail pages
- ✅ **Color-coded Alerts**: Different colors for each event type
- ✅ **No Internet Required**: Works completely offline
- ✅ **RESTful API**: Easy integration with other tools

## 📊 Notification Types

| Type | Icon | Color | Description |
|------|------|-------|-------------|
| `test_started` | 🚀 | Blue | Test execution started |
| `test_completed` | ✅ | Green | Test passed successfully |
| `test_failed` | ❌ | Red | Test encountered errors |
| `test_stopped` | ⏹️ | Orange | Test manually stopped |

## 🔧 Customization

### Change Port
Edit `webhook_receiver.py`:
```python
app.run(host="0.0.0.0", port=9000, ...)  # Use port 9000
```

### Change Storage Limit
```python
notifications = deque(maxlen=500)  # Store 500 notifications
```

### Add Authentication
Add simple token-based auth:
```python
SECRET_TOKEN = "your_secret_token"

@app.route("/notifications", methods=["POST"])
def receive_notification():
    auth_token = request.headers.get("Authorization")
    if auth_token != f"Bearer {SECRET_TOKEN}":
        return jsonify({"error": "Unauthorized"}), 401
    # ... rest of code
```

Then in ValidDashboard's `src/notification_manager.py`:
```python
headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer your_secret_token"
}
```

## 🐳 Docker Deployment

```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY webhook_receiver.py requirements.txt ./
RUN pip install Flask flask-cors
EXPOSE 8080
CMD ["python", "webhook_receiver.py"]
```

## 📝 Integration Examples

### Send Test Alert
```bash
curl -X POST http://localhost:8080/notifications \
  -H "Content-Type: application/json" \
  -d '{
    "type": "test_failed",
    "slot_id": 3,
    "owner": "Bob",
    "test_case": "Stress_Test",
    "error": "Timeout exceeded",
    "timestamp": "2025-12-27T15:00:00",
    "details_url": "http://192.168.1.100:3000/slot/3"
  }'
```

### Get Recent Notifications
```bash
curl http://localhost:8080/api/notifications
```

## 🛡️ Security Notes

- **Local Network Only**: Bind to specific interface if needed
- **Firewall**: Configure firewall rules for port 8080
- **No HTTPS**: For production, add SSL/TLS with nginx reverse proxy
- **Authentication**: Add token-based auth for production use

## 🔍 Troubleshooting

### Port Already in Use
```bash
# Find process using port 8080
lsof -i :8080
# Kill process
kill -9 <PID>
```

### Cannot Connect from Other Machine
- Check firewall settings
- Verify server IP address
- Ensure using `0.0.0.0` not `127.0.0.1`

### Notifications Not Appearing
- Check ValidDashboard `.env` has correct `WEBHOOK_URL`
- Verify `NOTIFICATION_METHOD=webhook` or `both`
- Check webhook receiver logs for errors
- Test endpoint: `curl http://localhost:8080/health`

## 📦 Requirements

- Python 3.7+
- Flask
- flask-cors

Install:
```bash
pip install Flask flask-cors
```

## 🤝 Integration with Other Tools

The webhook receiver can forward notifications to:
- Email (local SMTP)
- Slack/Mattermost
- Database logging
- Custom monitoring systems
- Desktop notifications

Simply modify the `receive_notification()` function to add your integration.

---

**Note**: This receiver is designed for local network use. For internet-exposed deployments, add proper authentication and HTTPS.
