"""
Log Manager - Separate and export logs for different test cases
Handles log file redirection and organization
"""

import os
import sys
from datetime import datetime
from pathlib import Path


class LogManager:
    """Manages separate log files for different test cases"""

    def __init__(self, base_log_dir="logs"):
        """
        Initialize log manager

        Args:
            base_log_dir: Base directory for storing logs
        """
        self.base_log_dir = Path(base_log_dir)
        self.base_log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
        self.original_stdout = sys.stdout
        self.original_stderr = sys.stderr

    def create_log_file(self, test_case_name, owner="", add_timestamp=True):
        """
        Create a new log file for a test case

        Args:
            test_case_name: Name of the test case
            owner: Owner of the test (optional)
            add_timestamp: Whether to add timestamp to filename

        Returns:
            Path to the created log file
        """
        # Create owner subdirectory if specified
        if owner:
            log_dir = self.base_log_dir / owner
            log_dir.mkdir(exist_ok=True)
        else:
            log_dir = self.base_log_dir

        # Generate filename
        if add_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"{test_case_name}_{timestamp}.log"
        else:
            filename = f"{test_case_name}.log"

        log_path = log_dir / filename

        # Create log file with header
        with open(log_path, "w") as f:
            f.write("=" * 80 + "\n")
            f.write(f"Test Case: {test_case_name}\n")
            if owner:
                f.write(f"Owner: {owner}\n")
            f.write(f"Start Time: {datetime.now().isoformat()}\n")
            f.write("=" * 80 + "\n\n")

        return str(log_path)

    def start_logging(self, log_file_path):
        """
        Redirect stdout and stderr to log file

        Args:
            log_file_path: Path to log file
        """
        self.current_log_file = open(log_file_path, "a")

        # Create tee that writes to both console and file
        class TeeOutput:
            def __init__(self, *files):
                self.files = files

            def write(self, data):
                for f in self.files:
                    f.write(data)
                    f.flush()

            def flush(self):
                for f in self.files:
                    f.flush()

        sys.stdout = TeeOutput(self.original_stdout, self.current_log_file)
        sys.stderr = TeeOutput(self.original_stderr, self.current_log_file)

    def stop_logging(self):
        """Stop logging and restore original stdout/stderr"""
        if self.current_log_file:
            # Write footer
            self.current_log_file.write("\n" + "=" * 80 + "\n")
            self.current_log_file.write(f"End Time: {datetime.now().isoformat()}\n")
            self.current_log_file.write("=" * 80 + "\n")

            # Restore original streams
            sys.stdout = self.original_stdout
            sys.stderr = self.original_stderr

            self.current_log_file.close()
            self.current_log_file = None

    def export_logs(self, output_dir, filter_owner=None, filter_date=None):
        """
        Export logs to a specified directory with optional filtering

        Args:
            output_dir: Directory to export logs to
            filter_owner: Only export logs from this owner (optional)
            filter_date: Only export logs from this date (YYYYMMDD format, optional)
        """
        output_path = Path(output_dir)
        output_path.mkdir(exist_ok=True)

        exported_count = 0

        # Walk through log directory
        for log_file in self.base_log_dir.rglob("*.log"):
            # Apply filters
            if filter_owner and filter_owner not in str(log_file):
                continue

            if filter_date and filter_date not in log_file.name:
                continue

            # Copy log file
            import shutil

            dest = output_path / log_file.name
            shutil.copy2(log_file, dest)
            exported_count += 1

        print(f"Exported {exported_count} log file(s) to {output_dir}")
        return exported_count

    def list_logs(self, owner=None):
        """
        List all log files, optionally filtered by owner

        Args:
            owner: Filter by owner (optional)

        Returns:
            List of log file paths
        """
        logs = []
        for log_file in self.base_log_dir.rglob("*.log"):
            if owner and owner not in str(log_file.parent):
                continue
            logs.append(str(log_file))
        return sorted(logs)

    def cleanup_old_logs(self, days=30):
        """
        Remove log files older than specified days

        Args:
            days: Number of days to keep logs
        """
        import time

        cutoff_time = time.time() - (days * 86400)
        removed_count = 0

        for log_file in self.base_log_dir.rglob("*.log"):
            if log_file.stat().st_mtime < cutoff_time:
                log_file.unlink()
                removed_count += 1

        print(f"Removed {removed_count} old log file(s)")
        return removed_count


# Example usage:
if __name__ == "__main__":
    # Create log manager
    log_mgr = LogManager("logs")

    # Example 1: Create a log file for a test case
    log_file = log_mgr.create_log_file("TestCase_001", owner="JohnDoe")
    print(f"Created log file: {log_file}")

    # Example 2: Start logging (redirect output to file)
    log_mgr.start_logging(log_file)
    print("This will appear in both console and log file")
    print("Running test case...")

    # Your test code here
    for i in range(5):
        print(f"Step {i+1} completed")

    # Stop logging
    log_mgr.stop_logging()
    print("Logging stopped - this only appears in console")

    # Example 3: List all logs
    print("\nAll log files:")
    for log in log_mgr.list_logs():
        print(f"  - {log}")

    # Example 4: Export logs
    log_mgr.export_logs("exported_logs", filter_owner="JohnDoe")
