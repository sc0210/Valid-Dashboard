#!/usr/bin/env python3
"""
Phase 1: Initialization Test
Part of multi-phase performance test suite
"""
import sys
import time
import random


def main(log_dir, test_case):
    """Run initialization phase"""
    print(f"[Phase 1] Starting initialization for {test_case}")
    print(f"Log directory: {log_dir}")

    # Simulate initialization steps
    steps = [
        "Connecting to device",
        "Reading device info",
        "Checking firmware version",
        "Validating configuration",
        "Setting up test environment",
    ]

    total_steps = len(steps)
    for i, step in enumerate(steps, 1):
        print(f"[Phase 1] {step}...")
        time.sleep(random.uniform(0.5, 1.5))
        progress = int((i / total_steps) * 20)  # Phase 1 = 0-20%
        print(f"Progress: {progress}%")

        # Simulate UART output
        print(f"[UART] Device response: OK for {step}")

    print("[Phase 1] Initialization completed successfully")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: test_phase1_init.py <log_dir> <test_case>")
        sys.exit(1)

    log_dir = sys.argv[1]
    test_case = sys.argv[2]
    sys.exit(main(log_dir, test_case))
