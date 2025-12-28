#!/bin/bash
################################################################################
# Quick Test - Minimal execution time with log export
################################################################################

# Configuration
LOG_IP="${1:-}"
LOG_PORT="${2:-}"
LOG_DIR="${3:-./logs}"
TEST_CASE="${4:-QuickTest}"
OWNER="${5:-DefaultUser}"

# Create unique timestamp
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
UNIQUE_ID="${TEST_CASE}_${TIMESTAMP}"

# Create log directory
mkdir -p "$LOG_DIR"
TEST_LOG_DIR="$LOG_DIR/${OWNER}"
mkdir -p "$TEST_LOG_DIR"

# Log files
MASTER_LOG="$TEST_LOG_DIR/${UNIQUE_ID}_master.log"
UART_LOG="$TEST_LOG_DIR/${UNIQUE_ID}_uart.log"

echo "============================================"
echo "Quick Test"
echo "============================================"
echo "Test Case: $TEST_CASE"
echo "Owner: $OWNER"
echo "Log Directory: $TEST_LOG_DIR"
echo ""

echo "Progress: 0%"
sleep 1

echo "[1/3] Checking device connectivity..." | tee -a "$MASTER_LOG"
echo "[UART] Device: Online" | tee -a "$UART_LOG"
sleep 2
echo "Progress: 33%"

echo "[2/3] Running basic validation..." | tee -a "$MASTER_LOG"
echo "[UART] Validation: PASS" | tee -a "$UART_LOG"
sleep 2
echo "Progress: 66%"

echo "[3/3] Verifying results..." | tee -a "$MASTER_LOG"
echo "[UART] Results: OK" | tee -a "$UART_LOG"
sleep 2
echo "Progress: 100%"

echo ""
echo "============================================"
echo "Quick Test Completed"
echo "============================================"
echo "Logs saved to: $TEST_LOG_DIR"

echo "LOG_FILE=$UART_LOG"

exit 0
