#!/usr/bin/env python3
"""
Phase 2: Performance Testing
Part of multi-phase performance test suite
"""
import sys
import time
import random


def main(log_dir, test_case):
    """Run performance testing phase"""
    print(f"[Phase 2] Starting performance tests for {test_case}")
    print(f"Log directory: {log_dir}")

    # Simulate performance test operations
    operations = [
        {"name": "Sequential Read", "iops": random.randint(80000, 100000)},
        {"name": "Sequential Write", "iops": random.randint(70000, 90000)},
        {"name": "Random Read 4K", "iops": random.randint(50000, 70000)},
        {"name": "Random Write 4K", "iops": random.randint(40000, 60000)},
        {"name": "Mixed Workload", "iops": random.randint(60000, 80000)},
    ]

    total_ops = len(operations)
    for i, op in enumerate(operations, 1):
        print(f"[Phase 2] Testing {op['name']}...")
        time.sleep(random.uniform(1.0, 2.0))

        # Simulate UART output with test results
        print(f"[UART] {op['name']}: {op['iops']} IOPS")
        print(f"[UART] Latency: {random.uniform(0.1, 0.5):.2f} ms")

        # Progress from 20% to 60%
        progress = 20 + int((i / total_ops) * 40)
        print(f"Progress: {progress}%")

    print("[Phase 2] Performance testing completed")
    return 0


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: test_phase2_performance.py <log_dir> <test_case>")
        sys.exit(1)

    log_dir = sys.argv[1]
    test_case = sys.argv[2]
    sys.exit(main(log_dir, test_case))
