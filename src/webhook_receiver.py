"""
Webhook Receiver Server
Simple Flask server to receive and display notifications from ValidDashboard
Can run standalone on any machine in the local network
"""

from flask import Flask, render_template_string, jsonify, request
from flask_cors import CORS
from datetime import datetime
from collections import deque
import threading

app = Flask(__name__)
CORS(app)

# Store recent notifications (max 100)
notifications = deque(maxlen=100)
notifications_lock = threading.Lock()

# HTML Template for notification viewer
NOTIFICATION_VIEWER_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Notification Receiver - ValidDashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
        }
        .header {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 {
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }
        .header p {
            color: #7f8c8d;
            font-size: 1.1em;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.1);
            text-align: center;
        }
        .stat-value {
            font-size: 3em;
            font-weight: 700;
            color: #667eea;
            margin-bottom: 10px;
        }
        .stat-label {
            color: #7f8c8d;
            font-size: 1em;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        .notifications-container {
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        .notifications-header {
            font-size: 1.5em;
            font-weight: 600;
            color: #2c3e50;
            margin-bottom: 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .notification {
            background: #f8f9fa;
            border-left: 4px solid #667eea;
            padding: 20px;
            margin-bottom: 15px;
            border-radius: 8px;
            transition: transform 0.2s;
            animation: slideIn 0.3s ease-out;
        }
        @keyframes slideIn {
            from { transform: translateX(-20px); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .notification:hover {
            transform: translateX(5px);
            box-shadow: 0 3px 15px rgba(0,0,0,0.1);
        }
        .notification.test_started { border-left-color: #3498db; }
        .notification.test_completed { border-left-color: #27ae60; }
        .notification.test_failed { border-left-color: #e74c3c; }
        .notification.test_stopped { border-left-color: #f39c12; }
        .notification-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 12px;
        }
        .notification-type {
            font-size: 1.2em;
            font-weight: 600;
            color: #2c3e50;
        }
        .notification-time {
            color: #95a5a6;
            font-size: 0.9em;
        }
        .notification-details {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 10px;
            margin-bottom: 12px;
        }
        .detail-item {
            color: #7f8c8d;
            font-size: 0.95em;
        }
        .detail-item strong {
            color: #2c3e50;
        }
        .notification-link {
            display: inline-block;
            margin-top: 10px;
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 0.9em;
            transition: background 0.2s;
        }
        .notification-link:hover {
            background: #5568d3;
        }
        .empty-state {
            text-align: center;
            padding: 60px 20px;
            color: #95a5a6;
        }
        .empty-icon {
            font-size: 4em;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📡 ValidDashboard Notifications</h1>
            <p>Real-time test execution alerts</p>
        </div>

        <div class="stats">
            <div class="stat-card">
                <div class="stat-value" id="total-count">0</div>
                <div class="stat-label">Total Notifications</div>
            </div>
            <div class="stat-card">
                <div class="stat-value" id="recent-count">0</div>
                <div class="stat-label">Last Hour</div>
            </div>
        </div>

        <div class="notifications-container">
            <div class="notifications-header">
                <span>📬 Recent Notifications</span>
                <button onclick="clearNotifications()" style="padding: 8px 16px; background: #e74c3c; color: white; border: none; border-radius: 6px; cursor: pointer;">Clear All</button>
            </div>
            <div id="notifications-list">
                <div class="empty-state">
                    <div class="empty-icon">📭</div>
                    <div>No notifications yet</div>
                </div>
            </div>
        </div>
    </div>

    <script>
        function formatType(type) {
            const icons = {
                'test_started': '🚀',
                'test_completed': '✅',
                'test_failed': '❌',
                'test_stopped': '⏹️'
            };
            const labels = {
                'test_started': 'Test Started',
                'test_completed': 'Test Completed',
                'test_failed': 'Test Failed',
                'test_stopped': 'Test Stopped'
            };
            return `${icons[type] || '📢'} ${labels[type] || type}`;
        }

        function formatTime(isoString) {
            const date = new Date(isoString);
            return date.toLocaleString();
        }

        function renderNotifications(notifications) {
            const container = document.getElementById('notifications-list');
            
            if (notifications.length === 0) {
                container.innerHTML = `
                    <div class="empty-state">
                        <div class="empty-icon">📭</div>
                        <div>No notifications yet</div>
                    </div>
                `;
                return;
            }

            container.innerHTML = notifications.map(notif => `
                <div class="notification ${notif.type}">
                    <div class="notification-header">
                        <div class="notification-type">${formatType(notif.type)}</div>
                        <div class="notification-time">${formatTime(notif.timestamp)}</div>
                    </div>
                    <div class="notification-details">
                        <div class="detail-item"><strong>Slot:</strong> ${notif.slot_id}</div>
                        <div class="detail-item"><strong>Owner:</strong> ${notif.owner}</div>
                        <div class="detail-item"><strong>Test:</strong> ${notif.test_case}</div>
                        ${notif.duration ? `<div class="detail-item"><strong>Duration:</strong> ${notif.duration}</div>` : ''}
                    </div>
                    ${notif.error ? `<div style="color: #e74c3c; margin-top: 10px;"><strong>Error:</strong> ${notif.error}</div>` : ''}
                    <a href="${notif.details_url}" target="_blank" class="notification-link">View Details →</a>
                </div>
            `).join('');
        }

        function updateStats(notifications) {
            document.getElementById('total-count').textContent = notifications.length;
            
            const oneHourAgo = new Date(Date.now() - 3600000).toISOString();
            const recentCount = notifications.filter(n => n.timestamp > oneHourAgo).length;
            document.getElementById('recent-count').textContent = recentCount;
        }

        async function loadNotifications() {
            try {
                const response = await fetch('/api/notifications');
                const data = await response.json();
                renderNotifications(data.notifications);
                updateStats(data.notifications);
            } catch (error) {
                console.error('Failed to load notifications:', error);
            }
        }

        async function clearNotifications() {
            if (!confirm('Clear all notifications?')) return;
            try {
                await fetch('/api/notifications', { method: 'DELETE' });
                loadNotifications();
            } catch (error) {
                console.error('Failed to clear notifications:', error);
            }
        }

        // Auto-refresh every 3 seconds
        setInterval(loadNotifications, 3000);
        
        // Initial load
        loadNotifications();
    </script>
</body>
</html>
"""


@app.route("/")
def index():
    """Display notification viewer dashboard"""
    return render_template_string(NOTIFICATION_VIEWER_HTML)


@app.route("/notifications", methods=["POST"])
def receive_notification():
    """Receive notification webhook from ValidDashboard"""
    try:
        data = request.json
        if not data:
            return jsonify({"error": "No data provided"}), 400

        # Add received timestamp
        data["received_at"] = datetime.now().isoformat()

        # Store notification
        with notifications_lock:
            notifications.append(data)

        print(
            f"📬 Received: {data.get('type')} - Slot {data.get('slot_id')} - {data.get('owner')}"
        )

        return jsonify({"success": True, "message": "Notification received"}), 200

    except Exception as e:
        print(f"Error receiving notification: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/api/notifications", methods=["GET"])
def get_notifications():
    """Get all notifications"""
    with notifications_lock:
        return jsonify({"notifications": list(reversed(notifications))})


@app.route("/api/notifications", methods=["DELETE"])
def clear_notifications():
    """Clear all notifications"""
    with notifications_lock:
        notifications.clear()
    return jsonify({"success": True, "message": "Notifications cleared"})


@app.route("/health", methods=["GET"])
def health_check():
    """Health check endpoint"""
    return jsonify(
        {
            "status": "ok",
            "service": "ValidDashboard Webhook Receiver",
            "notifications_count": len(notifications),
        }
    )


if __name__ == "__main__":
    print("=" * 60)
    print("🎯 ValidDashboard Webhook Receiver")
    print("=" * 60)
    print("\n📡 Server starting...")
    print(f"🌐 Dashboard: http://localhost:8080")
    print(f"📬 Webhook endpoint: http://localhost:8080/notifications")
    print(f"❤️  Health check: http://localhost:8080/health")
    print("\n💡 Configure ValidDashboard to send webhooks here:")
    print("   NOTIFICATION_METHOD=webhook")
    print("   WEBHOOK_URL=http://<this-server-ip>:8080/notifications")
    print("\n" + "=" * 60 + "\n")

    app.run(host="0.0.0.0", port=8080, debug=False, threaded=True)
