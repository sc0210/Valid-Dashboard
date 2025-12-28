#!/bin/bash
################################################################################
# Basic Test Script with Log Export
# Demonstrates progress reporting and UART log export to dashboard
################################################################################

# Configuration
LOG_IP="${1:-}"
LOG_PORT="${2:-}"
LOG_DIR="${3:-./logs}"
TEST_CASE="${4:-BasicTest}"
OWNER="${5:-DefaultUser}"

# Create unique timestamp for this test run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
UNIQUE_ID="${TEST_CASE}_${TIMESTAMP}"

# Create log directory structure
mkdir -p "$LOG_DIR"
TEST_LOG_DIR="$LOG_DIR/${OWNER}"
mkdir -p "$TEST_LOG_DIR"

# Log files
MASTER_LOG="$TEST_LOG_DIR/${UNIQUE_ID}_master.log"
UART_LOG="$TEST_LOG_DIR/${UNIQUE_ID}_uart.log"

echo "============================================"
echo "Test Started: $(date)"
echo "============================================"
echo "Test Case: $TEST_CASE"
echo "Owner: $OWNER"
echo "Log Directory: $TEST_LOG_DIR"
echo ""

# Initial progress
echo "Progress: 0%"
sleep 2

# Phase 1: Initialization
echo "[Phase 1] Initializing test environment..." | tee -a "$MASTER_LOG"
echo "[UART] Device: Connected" | tee -a "$UART_LOG"
echo "[UART] Firmware: v2.1.0" | tee -a "$UART_LOG"
sleep 3
echo "Progress: 20%"

# Phase 2: Setup
echo "[Phase 2] Setting up test configuration..." | tee -a "$MASTER_LOG"
echo "[UART] Config: Loaded" | tee -a "$UART_LOG"
sleep 3
echo "Progress: 40%"

# Phase 3: Execution
echo "[Phase 3] Executing test cases..." | tee -a "$MASTER_LOG"
for i in {1..5}; do
    echo "  Running test case $i/5..." | tee -a "$MASTER_LOG"
    echo "[UART] Test $i: PASS" | tee -a "$UART_LOG"
    sleep 2
done
echo "Progress: 70%"

# Phase 4: Validation
echo "[Phase 4] Validating results..." | tee -a "$MASTER_LOG"
echo "[UART] Validation: OK" | tee -a "$UART_LOG"
sleep 3
echo "Progress: 90%"

# Phase 5: Cleanup
echo "[Phase 5] Cleaning up..." | tee -a "$MASTER_LOG"
echo "[UART] Cleanup: Complete" | tee -a "$UART_LOG"
sleep 2
echo "Progress: 100%"

echo ""
echo "============================================"
echo "Test Completed Successfully: $(date)"
echo "============================================"
echo "Logs saved to: $TEST_LOG_DIR"

# Export log file path for dashboard
echo "LOG_FILE=$UART_LOG"

# Exit with success
exit 0
