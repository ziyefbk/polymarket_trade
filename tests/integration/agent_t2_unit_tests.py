"""
Agent T2: Unit Tests Execution
Priority: 🔥 High - Must pass before integration tests
"""

import sys
import subprocess
from pathlib import Path
from datetime import datetime


class UnitTestRunner:
    def __init__(self):
        self.total_tests = 0
        self.passed_tests = 0
        self.failed_tests = 0
        self.report_lines = []

    def log(self, message, level="INFO"):
        """Log message to console and report"""
        print(f"[{level}] {message}")
        self.report_lines.append(f"[{level}] {message}")

    def run_test_suite(self, test_file, test_name):
        """Run a single test suite and capture results"""
        self.log("")
        self.log(f"Running: {test_name}")
        self.log("-" * 60)

        test_path = Path(test_file)
        if not test_path.exists():
            self.log(f"✗ Test file not found: {test_file}", "FAIL")
            self.failed_tests += 1
            self.total_tests += 1
            return False

        try:
            # Run pytest
            result = subprocess.run(
                ["pytest", str(test_path), "-v", "--tb=short"],
                capture_output=True,
                text=True,
                timeout=300  # 5 minutes timeout
            )

            # Log output
            output = result.stdout + result.stderr
            self.report_lines.append(output)

            if result.returncode == 0:
                self.log(f"✓ {test_name} PASSED", "PASS")
                self.passed_tests += 1
                self.total_tests += 1
                return True
            else:
                self.log(f"✗ {test_name} FAILED", "FAIL")
                self.log(f"  Exit code: {result.returncode}", "INFO")
                self.failed_tests += 1
                self.total_tests += 1
                return False

        except subprocess.TimeoutExpired:
            self.log(f"✗ {test_name} TIMEOUT (5 minutes)", "FAIL")
            self.failed_tests += 1
            self.total_tests += 1
            return False
        except Exception as e:
            self.log(f"✗ {test_name} ERROR: {e}", "FAIL")
            self.failed_tests += 1
            self.total_tests += 1
            return False

    def generate_report(self):
        """Generate and save test report"""
        self.log("")
        self.log("=" * 60)
        self.log("Unit Tests Summary")
        self.log("=" * 60)
        self.log(f"Total Test Suites: {self.total_tests}")
        self.log(f"Passed: {self.passed_tests}")
        self.log(f"Failed: {self.failed_tests}")

        # Save report
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / "t2_unit_tests_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("=== Unit Tests Execution Report ===\n")
            f.write(f"Date: {datetime.now()}\n\n")
            f.write("\n".join(self.report_lines))
            f.write(f"\n\n--- Summary ---\n")
            f.write(f"Total Test Suites: {self.total_tests}\n")
            f.write(f"Passed: {self.passed_tests}\n")
            f.write(f"Failed: {self.failed_tests}\n")

        self.log(f"\nReport saved to: {report_file}")

        return self.failed_tests == 0

    def run(self):
        """Run all unit test suites"""
        print("\n" + "=" * 60)
        print("Agent T2: Unit Tests Execution")
        print("=" * 60)

        test_suites = [
            ("tests/test_kelly.py", "1️⃣ Kelly Criterion Tests"),
            ("tests/test_position_manager.py", "2️⃣ Position Manager Tests"),
            ("tests/test_arbitrage_detector.py", "3️⃣ Arbitrage Detector Tests"),
            ("tests/test_database.py", "4️⃣ Database Tests"),
            ("tests/test_orchestrator.py", "5️⃣ Orchestrator Tests"),
        ]

        for test_file, test_name in test_suites:
            if not self.run_test_suite(test_file, test_name):
                # If test fails, stop immediately (serial execution)
                self.log(f"\n✗ Stopping due to test failure: {test_name}", "ERROR")
                break

        success = self.generate_report()

        if success:
            print("\n✓ All unit tests passed!")
            return 0
        else:
            print(f"\n✗ {self.failed_tests} test suite(s) failed")
            return 1


if __name__ == "__main__":
    runner = UnitTestRunner()
    exit_code = runner.run()
    sys.exit(exit_code)