#!/bin/bash
################################################################################
# Performance Test Suite - Multi-Phase Test Runner
# Runs multiple Python test scripts with UART log export
################################################################################

# Configuration
LOG_IP="${1:-}"
LOG_PORT="${2:-}"
LOG_DIR="${3:-./logs}"
TEST_CASE="${4:-PerformanceTest}"
OWNER="${5:-DefaultUser}"

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Create unique timestamp for this test run
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
UNIQUE_ID="${TEST_CASE}_${TIMESTAMP}"

# Create log directory structure
mkdir -p "$LOG_DIR"
TEST_LOG_DIR="$LOG_DIR/${OWNER}"
mkdir -p "$TEST_LOG_DIR"

# Log files with unique names
MASTER_LOG="$TEST_LOG_DIR/${UNIQUE_ID}_master.log"
UART_LOG="$TEST_LOG_DIR/${UNIQUE_ID}_uart.log"
ERROR_LOG="$TEST_LOG_DIR/${UNIQUE_ID}_error.log"

echo "============================================"
echo "Performance Test Suite"
echo "============================================"
echo "Test Case: $TEST_CASE"
echo "Owner: $OWNER"
echo "Timestamp: $TIMESTAMP"
echo "Log Directory: $TEST_LOG_DIR"
echo "Master Log: $MASTER_LOG"
echo "UART Log: $UART_LOG"
echo ""

# Function to log to multiple destinations
log_message() {
    local message="$1"
    echo "$message" | tee -a "$MASTER_LOG"
}

# Function to log UART output separately
log_uart() {
    local message="$1"
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $message" | tee -a "$UART_LOG"
    
    # Also send to remote log if configured
    if [ -n "$LOG_IP" ] && [ -n "$LOG_PORT" ]; then
        echo "$message" > /dev/tcp/$LOG_IP/$LOG_PORT 2>/dev/null || true
    fi
}

# Function to run a Python test phase
run_test_phase() {
    local phase_script="$1"
    local phase_name="$2"
    local phase_log="$TEST_LOG_DIR/${UNIQUE_ID}_${phase_name}.log"
    
    log_message "Starting $phase_name..."
    
    if [ ! -f "$phase_script" ]; then
        log_message "ERROR: Phase script not found: $phase_script"
        echo "ERROR: $phase_name - Script not found" >> "$ERROR_LOG"
        return 1
    fi
    
    # Run the Python script and capture all output
    python3 "$phase_script" "$TEST_LOG_DIR" "$TEST_CASE" 2>&1 | while IFS= read -r line; do
        # Parse output and route to appropriate logs
        if [[ "$line" == *"[UART]"* ]]; then
            # UART output goes to UART log
            log_uart "$line"
        elif [[ "$line" == *"Progress:"* ]]; then
            # Progress updates
            echo "$line"
        elif [[ "$line" == *"ERROR"* ]] || [[ "$line" == *"FAIL"* ]]; then
            # Errors go to error log
            log_message "$line"
            echo "[$(date +'%Y-%m-%d %H:%M:%S')] $line" >> "$ERROR_LOG"
        else
            # Everything else goes to master log
            log_message "$line"
        fi
        
        # Also save to phase-specific log
        echo "$line" >> "$phase_log"
    done
    
    local exit_code=${PIPESTATUS[0]}
    
    if [ $exit_code -eq 0 ]; then
        log_message "$phase_name completed successfully"
        return 0
    else
        log_message "ERROR: $phase_name failed with exit code $exit_code"
        echo "ERROR: $phase_name failed (exit code: $exit_code)" >> "$ERROR_LOG"
        return 1
    fi
}

# Initialize
log_message "Initializing test environment..."
echo "Progress: 0%"
sleep 1

# Phase 1: Initialization (0-20%)
if ! run_test_phase "$SCRIPT_DIR/test_phase1_init.py" "Phase1_Init"; then
    log_message "Test suite failed at Phase 1"
    echo "Progress: FAILED"
    exit 1
fi

# Phase 2: Performance Testing (20-60%)
if ! run_test_phase "$SCRIPT_DIR/test_phase2_performance.py" "Phase2_Performance"; then
    log_message "Test suite failed at Phase 2"
    echo "Progress: FAILED"
    exit 1
fi

# Phase 3: Stress Testing (60-90%)
if ! run_test_phase "$SCRIPT_DIR/test_phase3_stress.py" "Phase3_Stress"; then
    log_message "Test suite failed at Phase 3"
    echo "Progress: FAILED"
    exit 1
fi

# Phase 4: Validation and Cleanup (90-100%)
if ! run_test_phase "$SCRIPT_DIR/test_phase4_validation.py" "Phase4_Validation"; then
    log_message "Test suite failed at Phase 4"
    echo "Progress: FAILED"
    exit 1
fi

# Final summary
echo ""
echo "============================================"
echo "Performance Test Suite Completed"
echo "============================================"
log_message "All phases completed successfully"
log_message "Logs saved to: $TEST_LOG_DIR"
log_message "  - Master Log: ${UNIQUE_ID}_master.log"
log_message "  - UART Log: ${UNIQUE_ID}_uart.log"

# Check if there were any errors
if [ -f "$ERROR_LOG" ] && [ -s "$ERROR_LOG" ]; then
    log_message "  - Error Log: ${UNIQUE_ID}_error.log (contains errors)"
else
    log_message "  - No errors detected"
fi

echo ""
echo "Progress: 100%"

# Export log file path for dashboard tracking
echo "LOG_FILE=$UART_LOG"

exit 0

