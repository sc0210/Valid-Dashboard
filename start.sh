#!/bin/bash

# ValidDashboard Quick Start Script
# Automates the setup and startup process

set -e  # Exit on error

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

echo "════════════════════════════════════════════════════════════"
echo "  ValidDashboard Quick Start"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check Python version
echo "🔍 Checking Python version..."
if command -v python3 &> /dev/null; then
    PYTHON_CMD=python3
elif command -v python &> /dev/null; then
    PYTHON_CMD=python
else
    echo "❌ Python not found. Please install Python 3.7+"
    exit 1
fi

PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "✅ Found Python $PYTHON_VERSION"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "📦 Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    echo "✅ Virtual environment created"
    echo ""
fi

# Activate virtual environment
echo "🔌 Activating virtual environment..."
source venv/bin/activate
echo ""

# Install/upgrade dependencies
echo "📥 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo "✅ Dependencies installed"
echo ""

# Setup environment file
if [ ! -f ".env" ]; then
    echo "⚙️  Creating .env file from template..."
    cp .env.example .env
    echo "✅ .env file created"
    echo ""
    echo "⚠️  IMPORTANT: Please edit .env file and configure:"
    echo "   - TELEGRAM_BOT_TOKEN (if using Telegram)"
    echo "   - NOTIFICATION_METHOD (telegram, webhook, or both)"
    echo "   - WEBHOOK_URL (if using webhook notifications)"
    echo ""
    read -p "Press Enter to continue after configuring .env..."
fi

# Display notification options
echo "════════════════════════════════════════════════════════════"
echo "  Notification Setup"
echo "════════════════════════════════════════════════════════════"
echo ""
echo "Choose your notification method:"
echo ""
echo "1️⃣  Telegram Only (requires internet)"
echo "   - Real-time notifications to mobile devices"
echo "   - Requires bot token from @BotFather"
echo ""
echo "2️⃣  Webhook Only (offline/local network)"
echo "   - No internet required"
echo "   - View notifications on local web dashboard"
echo "   - Run: python webhook_receiver.py (separate terminal)"
echo ""
echo "3️⃣  Both (hybrid mode)"
echo "   - Best of both worlds"
echo "   - Telegram + Local webhook"
echo ""
read -p "Select mode (1/2/3) or press Enter to use current config: " MODE_CHOICE

case $MODE_CHOICE in
    1)
        sed -i.bak 's/NOTIFICATION_METHOD=.*/NOTIFICATION_METHOD=telegram/' .env
        echo "✅ Set to Telegram mode"
        ;;
    2)
        sed -i.bak 's/NOTIFICATION_METHOD=.*/NOTIFICATION_METHOD=webhook/' .env
        echo "✅ Set to Webhook mode"
        echo ""
        echo "💡 Remember to start webhook receiver:"
        echo "   python webhook_receiver.py"
        ;;
    3)
        sed -i.bak 's/NOTIFICATION_METHOD=.*/NOTIFICATION_METHOD=both/' .env
        echo "✅ Set to Both (hybrid) mode"
        ;;
    *)
        echo "ℹ️  Using existing configuration"
        ;;
esac
echo ""

# Check if webhook receiver should be started
source .env 2>/dev/null || true
if [[ "$NOTIFICATION_METHOD" == "webhook" ]] || [[ "$NOTIFICATION_METHOD" == "both" ]]; then
    echo "════════════════════════════════════════════════════════════"
    echo "  Webhook Receiver"
    echo "════════════════════════════════════════════════════════════"
    echo ""
    read -p "Start webhook receiver now? (y/n): " START_WEBHOOK
    if [[ "$START_WEBHOOK" == "y" ]] || [[ "$START_WEBHOOK" == "Y" ]]; then
        echo "🚀 Starting webhook receiver in background..."
        $PYTHON_CMD webhook_receiver.py > webhook_receiver.log 2>&1 &
        WEBHOOK_PID=$!
        echo "✅ Webhook receiver started (PID: $WEBHOOK_PID)"
        echo "   View dashboard: http://localhost:8080"
        echo "   Logs: tail -f webhook_receiver.log"
        echo ""
    fi
fi

# Start main application
echo "════════════════════════════════════════════════════════════"
echo "  Starting ValidDashboard"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if port is already in use
if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo "⚠️  Port 3000 is already in use!"
    read -p "Kill existing process and continue? (y/n): " KILL_CHOICE
    if [[ "$KILL_CHOICE" == "y" ]] || [[ "$KILL_CHOICE" == "Y" ]]; then
        lsof -ti:3000 | xargs kill -9
        echo "✅ Existing process terminated"
    else
        echo "❌ Exiting..."
        exit 1
    fi
fi

echo "🚀 Starting ValidDashboard server..."
echo ""

$PYTHON_CMD app.py

# Cleanup on exit
trap "echo ''; echo '🛑 Shutting down...'; [ ! -z '$WEBHOOK_PID' ] && kill $WEBHOOK_PID 2>/dev/null; exit 0" INT TERM
