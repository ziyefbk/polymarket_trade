"""
Serial Integration Test Runner
Runs all integration tests in sequence, stopping on first failure
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime
import time


class SerialTestRunner:
    def __init__(self):
        self.start_time = time.time()
        self.test_results = []

    def print_header(self):
        """Print test suite header"""
        print("\n" + "=" * 70)
        print(" " * 15 + "POLYMARKET ARBITRAGE SYSTEM")
        print(" " * 15 + "Serial Integration Test Suite")
        print("=" * 70)
        print(f"Start Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 70 + "\n")

    def run_test(self, test_script, test_name, priority):
        """Run a single test script"""
        print(f"\n{'='*70}")
        print(f"Running: {test_name} ({priority})")
        print(f"{'='*70}\n")

        test_path = Path(test_script)
        if not test_path.exists():
            print(f"❌ ERROR: Test script not found: {test_script}")
            return False, "Script not found"

        try:
            result = subprocess.run(
                [sys.executable, str(test_path)],
                capture_output=False,  # Show output in real-time
                timeout=600  # 10 minutes timeout per test
            )

            if result.returncode == 0:
                print(f"\n✅ {test_name} PASSED")
                self.test_results.append((test_name, "PASS", None))
                return True, None
            else:
                print(f"\n❌ {test_name} FAILED (exit code: {result.returncode})")
                self.test_results.append((test_name, "FAIL", f"Exit code {result.returncode}"))
                return False, f"Exit code {result.returncode}"

        except subprocess.TimeoutExpired:
            print(f"\n❌ {test_name} TIMEOUT (10 minutes)")
            self.test_results.append((test_name, "TIMEOUT", "Exceeded 10 minute limit"))
            return False, "Timeout"
        except Exception as e:
            print(f"\n❌ {test_name} ERROR: {e}")
            self.test_results.append((test_name, "ERROR", str(e)))
            return False, str(e)

    def print_summary(self):
        """Print final test summary"""
        elapsed_time = time.time() - self.start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)

        print("\n" + "=" * 70)
        print(" " * 25 + "FINAL SUMMARY")
        print("=" * 70)

        passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
        failed = sum(1 for _, status, _ in self.test_results if status in ["FAIL", "TIMEOUT", "ERROR"])

        print(f"\nTotal Tests Run: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"⏱️  Total Time: {minutes}m {seconds}s")

        print("\n" + "-" * 70)
        print("Individual Test Results:")
        print("-" * 70)

        for test_name, status, error in self.test_results:
            status_icon = "✅" if status == "PASS" else "❌"
            print(f"{status_icon} {test_name}: {status}")
            if error:
                print(f"     Error: {error}")

        print("=" * 70 + "\n")

        # Save summary report
        self.save_summary_report(elapsed_time)

        return failed == 0

    def save_summary_report(self, elapsed_time):
        """Save summary report to file"""
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / "integration_test_summary.txt"

        with open(report_file, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("POLYMARKET ARBITRAGE SYSTEM\n")
            f.write("Serial Integration Test Summary\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Total Time: {int(elapsed_time // 60)}m {int(elapsed_time % 60)}s\n\n")

            passed = sum(1 for _, status, _ in self.test_results if status == "PASS")
            failed = sum(1 for _, status, _ in self.test_results if status in ["FAIL", "TIMEOUT", "ERROR"])

            f.write(f"Total Tests: {len(self.test_results)}\n")
            f.write(f"Passed: {passed}\n")
            f.write(f"Failed: {failed}\n\n")

            f.write("-" * 70 + "\n")
            f.write("Individual Test Results:\n")
            f.write("-" * 70 + "\n\n")

            for test_name, status, error in self.test_results:
                f.write(f"{test_name}: {status}\n")
                if error:
                    f.write(f"  Error: {error}\n")
                f.write("\n")

        print(f"Summary report saved to: {report_file}")

    def run(self):
        """Run all tests in serial order"""
        self.print_header()

        # Define test sequence (order matters!)
        tests = [
            ("tests/integration/agent_t1_environment.py", "Agent T1: Environment Verification", "Critical"),
            ("tests/integration/agent_t2_unit_tests.py", "Agent T2: Unit Tests", "High"),
            ("tests/integration/agent_t3_database.py", "Agent T3: Database Integration", "High"),
            ("tests/integration/agent_t4_api.py", "Agent T4: API Integration", "Medium"),
            ("tests/integration/agent_t5_e2e.py", "Agent T5: End-to-End Integration", "Highest"),
        ]

        print(f"Total tests to run: {len(tests)}")
        print("Mode: SERIAL (stop on first failure)\n")

        # Run tests sequentially
        for test_script, test_name, priority in tests:
            success, error = self.run_test(test_script, test_name, priority)

            if not success:
                print(f"\n{'='*70}")
                print(f"❌ STOPPING: {test_name} failed")
                print(f"{'='*70}")
                print(f"\nReason: {error}")
                print("Fix the issue and re-run the test suite.")
                break

        # Print final summary
        success = self.print_summary()

        if success:
            print("\n🎉 ALL INTEGRATION TESTS PASSED! System is ready for deployment.\n")
            return 0
        else:
            print("\n❌ INTEGRATION TESTS FAILED. Please review the logs and fix issues.\n")
            return 1


if __name__ == "__main__":
    runner = SerialTestRunner()
    exit_code = runner.run()
    sys.exit(exit_code)