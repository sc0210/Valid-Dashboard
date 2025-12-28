# Example Test Scripts

This folder contains example test scripts that demonstrate how to integrate with the ValidDashboard controller system.

## Scripts Overview

### 1. basic_test.sh
A simple example that demonstrates progress reporting through 5 phases.

**Usage:**
```bash
./basic_test.sh
```

**Features:**
- Basic progress reporting (0%, 20%, 40%, 70%, 90%, 100%)
- Simple phase-based execution
- Takes approximately 15 seconds to complete

**From Dashboard:**
- Owner: Your Name
- Test Case: Basic Test
- Script Path: `/path/to/ValidDashboard/example_scripts/basic_test.sh`
- Script Command: `bash`
- Leave other fields optional

---

### 2. performance_test.sh
Performance test with configurable iterations and remote logging support.

**Usage:**
```bash
./performance_test.sh [LOG_IP] [LOG_PORT] [ITERATIONS]
```

**Parameters:**
- `LOG_IP` - Remote log server IP (default: 192.168.1.100)
- `LOG_PORT` - Remote log server port (default: 3333)
- `ITERATIONS` - Number of test iterations (default: 10)

**Features:**
- Configurable performance testing
- Attempts to connect to remote log via ser2net
- Progress reporting based on iteration count
- Disk I/O operations for realistic testing

**From Dashboard:**
- Owner: Your Name
- Test Case: Performance Test
- Script Path: `/path/to/ValidDashboard/example_scripts/performance_test.sh`
- Script Command: `bash`
- Script Args: Leave empty (will use log IP/port from dashboard fields)
- Log IP: 192.168.1.100 (your ser2net server)
- Log Port: 3333 (your ser2net port)

---

### 3. ssd_test.sh
SSD-specific test that utilizes SSD serial number and EUI information.

**Usage:**
```bash
./ssd_test.sh [SSD_SERIAL] [SSD_EUI]
```

**Parameters:**
- `SSD_SERIAL` - SSD serial number
- `SSD_EUI` - SSD EUI number

**Features:**
- 5-phase SSD testing (Detection, Health, Read, Write, Verification)
- SSD information tracking
- Realistic test flow with SMART checks and I/O tests
- Takes approximately 18 seconds to complete

**From Dashboard:**
- Owner: Your Name
- Test Case: SSD Test
- Script Path: `/path/to/ValidDashboard/example_scripts/ssd_test.sh`
- Script Command: `bash`
- SSD Serial: 1234567890ABC
- SSD EUI: 5CD2E4-123456789ABC
- Script Args: Leave empty (will pass SSD info automatically)

---

## Progress Reporting Format

All scripts must output progress in one of these formats for the dashboard to detect it:

```bash
echo "Progress: 0%"
echo "Progress: 25%"
echo "Progress: 50%"
echo "Progress: 75%"
echo "Progress: 100%"
```

Or variations:
```bash
echo "progress: 50%"      # Case insensitive
echo "Progress:75%"       # Spaces optional
echo "PROGRESS: 100 %"    # Flexible spacing
```

The backend uses this regex pattern:
```
r'progress[:\s]+(\d+)%'
```

## Creating Your Own Test Scripts

### Template Structure

```bash
#!/bin/bash

# Parse arguments
ARG1="${1:-default_value}"
ARG2="${2:-default_value}"

echo "Test Started: $(date)"
echo "Progress: 0%"

# Phase 1
echo "Doing something..."
sleep 2
echo "Progress: 25%"

# Phase 2
echo "Doing more..."
sleep 2
echo "Progress: 50%"

# Phase 3
echo "Almost done..."
sleep 2
echo "Progress: 75%"

# Phase 4
echo "Finishing up..."
sleep 2
echo "Progress: 100%"

echo "Test Completed: $(date)"
exit 0
```

### Best Practices

1. **Always report Progress: 0%** at the start
2. **Always report Progress: 100%** at the end
3. **Use consistent percentage increments** (0%, 25%, 50%, 75%, 100%)
4. **Include timestamps** for debugging
5. **Use meaningful phase descriptions** for clarity
6. **Handle errors gracefully** and exit with proper codes
7. **Accept parameters** for flexibility ($1, $2, etc.)
8. **Echo important information** so it appears in dashboard logs

### Remote Logging (ser2net)

If using remote logging via ser2net from RPi4:

```bash
# At the start of your script
LOG_IP="${1:-192.168.1.100}"
LOG_PORT="${2:-3333}"

# Try to connect (non-blocking)
exec 3<>/dev/tcp/$LOG_IP/$LOG_PORT 2>/dev/null || echo "Warning: Could not connect to remote log"

# Your test code here...

# At the end
exec 3>&- 2>/dev/null
```

## Testing Your Scripts

### Method 1: Command Line
```bash
cd example_scripts
./basic_test.sh
```

### Method 2: From Dashboard
1. Open dashboard: http://localhost:3000
2. Click "Launch Test" on any slot
3. Fill in the form:
   - Owner: Your Name
   - Test Case: Test Name
   - Script Path: Full path to script
   - Script Command: `bash`
4. Click "Start Test"
5. Watch progress update in real-time

## Troubleshooting

### Script Not Running
- **Check permissions**: `chmod +x script.sh`
- **Check path**: Use absolute paths in dashboard
- **Check shebang**: Ensure `#!/bin/bash` is first line

### Progress Not Updating
- **Check output format**: Must be exactly `Progress: XX%`
- **Check stdout**: Script must output to stdout (not stderr)
- **Check buffering**: Use `echo` instead of `printf` for immediate output

### Remote Log Not Working
- **Check network**: Can you ping the remote log server?
- **Check port**: Is ser2net running on the specified port?
- **Check firewall**: Is the port open on the remote server?
- **Test manually**: `telnet LOG_IP LOG_PORT`

## Next Steps

1. **Test the examples**: Run each script from command line first
2. **Test from dashboard**: Launch scripts through the dashboard UI
3. **Create your own**: Use the template to create custom test scripts
4. **Monitor logs**: Check test_slots.json for real-time updates
5. **Configure ser2net**: Set up remote logging on your RPi4

## Additional Resources

- Main README: `../README.md`
- Controller Guide: `../CONTROLLER_GUIDE.md`
- API Reference: `../CONTROLLER_GUIDE.md#api-endpoints`
