#!/bin/bash
################################################################################
# Advanced Parallel Test Demo Script
# 
# This script demonstrates the Test Controller Dashboard with complex scenarios:
# - Staggered test starts (different start times)
# - Multiple test types (Basic, Performance, SSD, Quick)
# - Various test durations
# - Mixed success/failure scenarios
# - Different engineers managing multiple slots
#
# Usage: ./demo_parallel_tests.sh [--staggered|--waves|--all-at-once]
################################################################################

# Configuration
API_URL="http://localhost:3000/api"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAUNCH_MODE="${1:---staggered}"  # Default to staggered mode

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Banner
print_banner() {
    echo -e "${CYAN}"
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║      Test Controller Dashboard - Advanced Parallel Demo        ║"
    echo "║       Complex Scenarios with Staggered Test Execution          ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo -e "${NC}"
    echo -e "${YELLOW}Launch Mode: ${LAUNCH_MODE}${NC}"
    echo ""
}

# Print section header
print_section() {
    echo -e "\n${BLUE}▶ $1${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
}

# Check if server is running
check_server() {
    echo -e "${YELLOW}Checking if dashboard server is running...${NC}"
    if curl -s -o /dev/null -w "%{http_code}" "$API_URL/slots" | grep -q "200"; then
        echo -e "${GREEN}✓ Server is running${NC}"
        return 0
    else
        echo -e "${RED}✗ Server is not running!${NC}"
        echo -e "${YELLOW}Please start the server first:${NC}"
        echo "  cd $SCRIPT_DIR"
        echo "  python app.py"
        exit 1
    fi
}

# Reset all slots before starting
reset_all_slots() {
    print_section "Resetting All Slots"
    echo "Clearing all existing test data..."
    
    curl -s -X POST "$API_URL/slots/reset-all" > /dev/null
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✓ All slots reset successfully${NC}"
        sleep 1
    else
        echo -e "${RED}✗ Failed to reset slots${NC}"
        exit 1
    fi
}

# Launch test on a specific slot
launch_test() {
    local slot_id=$1
    local owner=$2
    local test_case=$3
    local script_name=$4
    local ssd_serial=$5
    local ssd_eui=$6
    local log_port=$7
    
    local script_path="$SCRIPT_DIR/example_scripts/$script_name"
    
    # Build JSON payload
    local json_payload=$(cat <<EOF
{
  "owner": "$owner",
  "test_case": "$test_case",
  "script_path": "$script_path",
  "ssd_serial": "$ssd_serial",
  "ssd_eui": "$ssd_eui",
  "log_ip": "192.168.1.100",
  "log_port": "$log_port"
}
EOF
)
    
    # Launch the test
    response=$(curl -s -X POST "$API_URL/slots/$slot_id/launch" \
        -H "Content-Type: application/json" \
        -d "$json_payload")
    
    # Check if launch was successful using jq
    if echo "$response" | jq -e '.status' > /dev/null 2>&1; then
        echo -e "${GREEN}✓ Slot $slot_id${NC}: $test_case (${CYAN}$owner${NC})"
        return 0
    else
        echo -e "${RED}✗ Slot $slot_id${NC}: Failed to launch"
        echo "  Error: $response" >&2
        return 1
    fi
}

# Launch all tests in parallel
launch_parallel_tests() {
    print_section "Launching Tests with ${LAUNCH_MODE} Strategy"
    
    case "$LAUNCH_MODE" in
        --staggered)
            echo "Starting tests with staggered delays (realistic scenario)"
            launch_staggered_tests
            ;;
        --waves)
            echo "Starting tests in waves (4 slots at a time)"
            launch_wave_tests
            ;;
        --all-at-once)
            echo "Starting all tests simultaneously"
            launch_all_at_once
            ;;
        *)
            echo "Unknown launch mode: $LAUNCH_MODE"
            echo "Using default staggered mode..."
            launch_staggered_tests
            ;;
    esac
}

# Launch tests with staggered delays (more realistic)
launch_staggered_tests() {
    echo ""
    echo -e "${CYAN}Phase 1: Quick Tests (immediate start)${NC}"
    launch_test 6 "Eve-SSSTC" "L1_Quick_001" "quick_test.sh" "S5XNNG0N123007" "0x002538c001000007" "3007" &
    launch_test 11 "Eve-SSSTC" "L1_Quick_003" "quick_test.sh" "S5XNNG0N123012" "0x002538c00100000c" "3012" &
    launch_test 15 "Grace-SSSTC" "L1_Quick_004" "quick_test.sh" "S5XNNG0N123016" "0x002538c001000010" "3016" &
    sleep 2
    
    echo -e "${CYAN}Phase 2: Basic Tests (2s delay)${NC}"
    launch_test 0 "Alice-SSSTC" "L1_Basic_001" "basic_test.sh" "S5XNNG0N123001" "0x002538c001000001" "3001" &
    launch_test 1 "Bob-SSSTC" "L1_Basic_002" "basic_test.sh" "S5XNNG0N123002" "0x002538c001000002" "3002" &
    launch_test 12 "Alice-SSSTC" "L1_Basic_004" "basic_test.sh" "S5XNNG0N123013" "0x002538c00100000d" "3013" &
    sleep 3
    
    echo -e "${CYAN}Phase 3: Performance Tests (5s delay)${NC}"
    launch_test 2 "SamChen-SSSTC" "L2_Performance_001" "performance_test.sh" "S5XNNG0N123003" "0x002538c001000003" "3003" &
    launch_test 3 "Charlie-SSSTC" "L2_Performance_002" "performance_test.sh" "S5XNNG0N123004" "0x002538c001000004" "3004" &
    sleep 2
    
    launch_test 9 "Charlie-SSSTC" "L2_Performance_003" "performance_test.sh" "S5XNNG0N123010" "0x002538c00100000a" "3010" &
    launch_test 13 "Charlie-SSSTC" "L2_Performance_004" "performance_test.sh" "S5XNNG0N123014" "0x002538c00100000e" "3014" &
    sleep 4
    
    echo -e "${CYAN}Phase 4: SSD Tests (11s delay)${NC}"
    launch_test 4 "SamChen-SSSTC" "L3_SSD_001" "ssd_test.sh" "S5XNNG0N123005" "0x002538c001000005" "3005" &
    launch_test 5 "Diana-SSSTC" "L3_SSD_002" "ssd_test.sh" "S5XNNG0N123006" "0x002538c001000006" "3006" &
    sleep 2
    
    launch_test 10 "Diana-SSSTC" "L3_SSD_003" "ssd_test.sh" "S5XNNG0N123011" "0x002538c00100000b" "3011" &
    launch_test 14 "Grace-SSSTC" "L3_SSD_004" "ssd_test.sh" "S5XNNG0N123015" "0x002538c00100000f" "3015" &
    sleep 3
    
    echo -e "${CYAN}Phase 5: Additional Tests (16s delay)${NC}"
    launch_test 7 "SamChen-SSSTC" "L1_Quick_002" "quick_test.sh" "S5XNNG0N123008" "0x002538c001000008" "3008" &
    launch_test 8 "Bob-SSSTC" "L1_Basic_003" "basic_test.sh" "S5XNNG0N123009" "0x002538c001000009" "3009" &
    
    wait
    echo ""
    echo -e "${GREEN}✓ All slots launched with staggered timing!${NC}"
}

# Launch tests in waves
launch_wave_tests() {
    echo ""
    echo -e "${CYAN}Wave 1: Slots 0-3${NC}"
    launch_test 0 "Alice-SSSTC" "L1_Basic_001" "basic_test.sh" "S5XNNG0N123001" "0x002538c001000001" "3001" &
    launch_test 1 "Bob-SSSTC" "L1_Basic_002" "basic_test.sh" "S5XNNG0N123002" "0x002538c001000002" "3002" &
    launch_test 2 "SamChen-SSSTC" "L2_Performance_001" "performance_test.sh" "S5XNNG0N123003" "0x002538c001000003" "3003" &
    launch_test 3 "Charlie-SSSTC" "L2_Performance_002" "performance_test.sh" "S5XNNG0N123004" "0x002538c001000004" "3004" &
    sleep 5
    
    echo -e "${CYAN}Wave 2: Slots 4-7${NC}"
    launch_test 4 "SamChen-SSSTC" "L3_SSD_001" "ssd_test.sh" "S5XNNG0N123005" "0x002538c001000005" "3005" &
    launch_test 5 "Diana-SSSTC" "L3_SSD_002" "ssd_test.sh" "S5XNNG0N123006" "0x002538c001000006" "3006" &
    launch_test 6 "Eve-SSSTC" "L1_Quick_001" "quick_test.sh" "S5XNNG0N123007" "0x002538c001000007" "3007" &
    launch_test 7 "SamChen-SSSTC" "L1_Quick_002" "quick_test.sh" "S5XNNG0N123008" "0x002538c001000008" "3008" &
    sleep 5
    
    echo -e "${CYAN}Wave 3: Slots 8-11${NC}"
    launch_test 8 "Bob-SSSTC" "L1_Basic_003" "basic_test.sh" "S5XNNG0N123009" "0x002538c001000009" "3009" &
    launch_test 9 "Charlie-SSSTC" "L2_Performance_003" "performance_test.sh" "S5XNNG0N123010" "0x002538c00100000a" "3010" &
    launch_test 10 "Diana-SSSTC" "L3_SSD_003" "ssd_test.sh" "S5XNNG0N123011" "0x002538c00100000b" "3011" &
    launch_test 11 "Eve-SSSTC" "L1_Quick_003" "quick_test.sh" "S5XNNG0N123012" "0x002538c00100000c" "3012" &
    sleep 5
    
    echo -e "${CYAN}Wave 4: Slots 12-15${NC}"
    launch_test 12 "Alice-SSSTC" "L1_Basic_004" "basic_test.sh" "S5XNNG0N123013" "0x002538c00100000d" "3013" &
    launch_test 13 "Charlie-SSSTC" "L2_Performance_004" "performance_test.sh" "S5XNNG0N123014" "0x002538c00100000e" "3014" &
    launch_test 14 "Grace-SSSTC" "L3_SSD_004" "ssd_test.sh" "S5XNNG0N123015" "0x002538c00100000f" "3015" &
    launch_test 15 "Grace-SSSTC" "L1_Quick_004" "quick_test.sh" "S5XNNG0N123016" "0x002538c001000010" "3016" &
    
    wait
    echo ""
    echo -e "${GREEN}✓ All waves completed!${NC}"
}

# Launch all tests at once (original behavior)
launch_all_at_once() {
    echo ""
    echo "Launching all 16 slots simultaneously..."
    echo ""
    
    # Define test configurations for each slot
    # Format: slot_id owner test_case script_name ssd_serial ssd_eui log_port
    # Note: Some engineers manage multiple slots with different SSDs
    
    # Alice - Testing 3 SSDs (Slots 0, 4, 12)
    launch_test 0 "Alice-SSSTC" "L1_Basic_001" "basic_test.sh" "S5XNNG0N123001" "0x002538c001000001" "3001" &
    
    # Bob - Testing 2 SSDs (Slots 1, 8)
    launch_test 1 "Bob-SSSTC" "L1_Basic_002" "basic_test.sh" "S5XNNG0N123002" "0x002538c001000002" "3002" &
    
    # Charlie - Performance tests on 4 SSDs (Slots 2, 3, 9, 13)
    launch_test 2 "SamChen-SSSTC" "L2_Performance_001" "performance_test.sh" "S5XNNG0N123003" "0x002538c001000003" "3003" &
    launch_test 3 "Charlie-SSSTC" "L2_Performance_002" "performance_test.sh" "S5XNNG0N123004" "0x002538c001000004" "3004" &
    
    # Alice - 2nd slot
    launch_test 4 "SamChen-SSSTC" "L3_SSD_001" "ssd_test.sh" "S5XNNG0N123005" "0x002538c001000005" "3005" &
    
    # Diana - Testing 2 SSDs (Slots 5, 10)
    launch_test 5 "Diana-SSSTC" "L3_SSD_002" "ssd_test.sh" "S5XNNG0N123006" "0x002538c001000006" "3006" &
    
    # Eve - Quick tests on 2 SSDs (Slots 6, 11)
    launch_test 6 "Eve-SSSTC" "L1_Quick_001" "quick_test.sh" "S5XNNG0N123007" "0x002538c001000007" "3007" &
    
    # Frank - Single slot
    launch_test 7 "SamChen-SSSTC" "L1_Quick_002" "quick_test.sh" "S5XNNG0N123008" "0x002538c001000008" "3008" &
    
    # Bob - 2nd slot
    launch_test 8 "Bob-SSSTC" "L1_Basic_003" "basic_test.sh" "S5XNNG0N123009" "0x002538c001000009" "3009" &
    
    # Charlie - 2nd slot
    launch_test 9 "Charlie-SSSTC" "L2_Performance_003" "performance_test.sh" "S5XNNG0N123010" "0x002538c00100000a" "3010" &
    
    # Diana - 2nd slot
    launch_test 10 "Diana-SSSTC" "L3_SSD_003" "ssd_test.sh" "S5XNNG0N123011" "0x002538c00100000b" "3011" &
    
    # Eve - 2nd slot
    launch_test 11 "Eve-SSSTC" "L1_Quick_003" "quick_test.sh" "S5XNNG0N123012" "0x002538c00100000c" "3012" &
    
    # Alice - 3rd slot
    launch_test 12 "Alice-SSSTC" "L1_Basic_004" "basic_test.sh" "S5XNNG0N123013" "0x002538c00100000d" "3013" &
    
    # Charlie - 3rd slot
    launch_test 13 "Charlie-SSSTC" "L2_Performance_004" "performance_test.sh" "S5XNNG0N123014" "0x002538c00100000e" "3014" &
    
    # Grace - Testing 2 SSDs (Slots 14, 15)
    launch_test 14 "Grace-SSSTC" "L3_SSD_004" "ssd_test.sh" "S5XNNG0N123015" "0x002538c00100000f" "3015" &
    launch_test 15 "Grace-SSSTC" "L1_Quick_004" "quick_test.sh" "S5XNNG0N123016" "0x002538c001000010" "3016" &
    
    # Wait for all launch commands to complete
    wait
    
    echo ""
    echo -e "${GREEN}✓ All 16 slots launched successfully!${NC}"
}

# Monitor test progress
monitor_progress() {
    print_section "Monitoring Test Progress"
    echo "Press Ctrl+C to stop monitoring (tests will continue running)"
    echo ""
    
    local iteration=0
    
    while true; do
        iteration=$((iteration + 1))
        
        # Fetch current slot status and parse with jq
        response=$(curl -s "$API_URL/slots")
        
        # Count slots by status using jq
        idle=$(echo "$response" | jq '[.slots[] | select(.status == "idle")] | length')
        running=$(echo "$response" | jq '[.slots[] | select(.status == "running")] | length')
        success=$(echo "$response" | jq '[.slots[] | select(.status == "success")] | length')
        failed=$(echo "$response" | jq '[.slots[] | select(.status == "failed")] | length')
        
        # Clear line and print status
        echo -ne "\r${CYAN}[Update $iteration]${NC} "
        echo -ne "Idle: ${YELLOW}$idle${NC} | "
        echo -ne "Running: ${BLUE}$running${NC} | "
        echo -ne "Success: ${GREEN}$success${NC} | "
        echo -ne "Failed: ${RED}$failed${NC}   "
        
        # If no tests are running, break
        if [ "$running" -eq 0 ] && [ $iteration -gt 5 ]; then
            echo ""
            echo ""
            echo -e "${GREEN}✓ All tests completed!${NC}"
            break
        fi
        
        sleep 2
    done
}

# Display final summary
show_summary() {
    print_section "Test Execution Summary"
    
    # Fetch final status
    response=$(curl -s "$API_URL/slots")
    
    # Optional: Save response for debugging
    # echo "$response" > /tmp/demo_final_status.json
    # echo "Debug: Raw response saved to /tmp/demo_final_status.json"
    
    echo ""
    echo "Slot | Owner    | Test Case            | Status  | Progress"
    echo "─────┼──────────┼──────────────────────┼─────────┼─────────"
    
    for slot_id in {0..15}; do
        # Use jq to extract slot data properly
        owner=$(echo "$response" | jq -r ".slots[$slot_id].owner")
        test_case=$(echo "$response" | jq -r ".slots[$slot_id].test_case")
        status=$(echo "$response" | jq -r ".slots[$slot_id].status")
        progress=$(echo "$response" | jq -r ".slots[$slot_id].progress")
        
        # Handle empty/null values
        [ -z "$owner" ] || [ "$owner" = "null" ] && owner="-"
        [ -z "$test_case" ] || [ "$test_case" = "null" ] && test_case="-"
        [ -z "$status" ] || [ "$status" = "null" ] && status="idle"
        [ -z "$progress" ] || [ "$progress" = "null" ] && progress="0"
        
        # Format status with color
        case "$status" in
            "success") status_colored="${GREEN}Success${NC}" ;;
            "failed")  status_colored="${RED}Failed${NC}" ;;
            "running") status_colored="${BLUE}Running${NC}" ;;
            "idle")    status_colored="${YELLOW}Idle${NC}" ;;
            *)         status_colored="$status" ;;
        esac
        
        # Truncate long test case names
        if [ ${#test_case} -gt 20 ]; then
            test_case="${test_case:0:17}..."
        fi
        
        printf "%4d | %-8s | %-20s | " "$slot_id" "$owner" "$test_case"
        echo -e "$status_colored | $progress%"
    done
    
    echo ""
    
    # Calculate success rate using jq
    success_count=$(echo "$response" | jq '[.slots[] | select(.status == "success")] | length')
    failed_count=$(echo "$response" | jq '[.slots[] | select(.status == "failed")] | length')
    total=$((success_count + failed_count))
    
    if [ $total -gt 0 ]; then
        success_rate=$((success_count * 100 / total))
        echo -e "Success Rate: ${GREEN}$success_rate%${NC} ($success_count/$total)"
    fi
}

# Display dashboard URL
show_dashboard_link() {
    print_section "Dashboard Access"
    echo ""
    echo -e "View live dashboard: ${CYAN}http://localhost:3000${NC}"
    echo -e "Test Cases library:  ${CYAN}http://localhost:3000/testcase${NC}"
    echo ""
    echo -e "${YELLOW}Tip:${NC} Click on any slot to see detailed logs and terminal output"
}

# Main execution
main() {
    print_banner
    
    # Check if server is running
    check_server
    
    # Reset all slots
    reset_all_slots
    
    # Launch all tests in parallel
    launch_parallel_tests
    
    # Show dashboard link
    show_dashboard_link
    
    # Monitor progress
    monitor_progress
    
    # Show final summary
    show_summary
    
    echo ""
    echo -e "${GREEN}╔════════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${GREEN}║              Demo Completed Successfully! 🎉                   ║${NC}"
    echo -e "${GREEN}╚════════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# Run main function
main
