"""
Agent T1: Environment Verification
Priority: 🔥 Critical - Must pass before any other tests
"""

import sys
import importlib.util
from pathlib import Path
from datetime import datetime


class EnvironmentTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.report_lines = []

    def log(self, message, level="INFO"):
        """Log message to console and report"""
        print(f"[{level}] {message}")
        self.report_lines.append(f"[{level}] {message}")

    def check_python_version(self):
        """Check Python version >= 3.7"""
        self.log("=" * 60)
        self.log("1️⃣ Python Environment Check")
        self.log("=" * 60)

        version = sys.version_info
        version_str = f"{version.major}.{version.minor}.{version.micro}"
        self.log(f"Python version: {version_str}")

        if version >= (3, 7):
            self.log("✓ Python 3.7+ detected", "PASS")
            self.tests_passed += 1
            return True
        else:
            self.log(f"✗ Python 3.7+ required (found {version_str})", "FAIL")
            self.tests_failed += 1
            return False

    def check_dependencies(self):
        """Check all required Python packages"""
        self.log("")
        self.log("=" * 60)
        self.log("2️⃣ Python Dependencies Check")
        self.log("=" * 60)

        required_packages = {
            "httpx": "httpx",
            "sqlalchemy": "sqlalchemy",
            "aiosqlite": "aiosqlite",
            "loguru": "loguru",
            "apscheduler": "apscheduler",
            "fastapi": "fastapi",
            "uvicorn": "uvicorn",
            "pytest": "pytest",
            "pytest_asyncio": "pytest-asyncio",
            "alembic": "alembic",
            "py_clob_client": "py_clob_client",
            "eth_account": "eth-account",
        }

        for module_name, package_name in required_packages.items():
            if importlib.util.find_spec(module_name):
                self.log(f"✓ {package_name} installed", "PASS")
                self.tests_passed += 1
            else:
                self.log(f"✗ {package_name} not found", "FAIL")
                self.tests_failed += 1

    def check_environment_variables(self):
        """Check .env file and required variables"""
        self.log("")
        self.log("=" * 60)
        self.log("3️⃣ Environment Variables Check")
        self.log("=" * 60)

        env_file = Path(".env")
        if env_file.exists():
            self.log("✓ .env file exists", "PASS")
            self.tests_passed += 1

            # Check required variables
            content = env_file.read_text()
            required_vars = ["POLYMARKET_PRIVATE_KEY", "DATABASE_URL"]

            for var in required_vars:
                if var in content:
                    self.log(f"✓ {var} found in .env", "PASS")
                    self.tests_passed += 1
                else:
                    self.log(f"✗ {var} missing in .env", "FAIL")
                    self.tests_failed += 1
        else:
            self.log("✗ .env file not found", "FAIL")
            self.tests_failed += 1

    def check_project_structure(self):
        """Check all required files exist"""
        self.log("")
        self.log("=" * 60)
        self.log("4️⃣ Project Structure Check")
        self.log("=" * 60)

        required_files = [
            "config/settings.py",
            "src/api/polymarket_client.py",
            "src/api/trader.py",
            "src/analyzer/arbitrage_detector.py",
            "src/strategy/arbitrage_executor.py",
            "src/strategy/position_manager.py",
            "src/utils/database.py",
            "src/utils/kelly.py",
            "src/utils/logger.py",
            "src/utils/models.py",
            "main.py",
        ]

        for file_path in required_files:
            path = Path(file_path)
            if path.exists():
                self.log(f"✓ {file_path}", "PASS")
                self.tests_passed += 1
            else:
                self.log(f"✗ {file_path} not found", "FAIL")
                self.tests_failed += 1

    def check_database_connection(self):
        """Test database connectivity"""
        self.log("")
        self.log("=" * 60)
        self.log("5️⃣ Database Connectivity Check")
        self.log("=" * 60)

        try:
            import asyncio
            from src.utils.database import DatabaseManager

            async def test_db():
                db = DatabaseManager()
                await db.initialize()
                await db.close()

            asyncio.run(test_db())
            self.log("✓ Database connection successful", "PASS")
            self.tests_passed += 1
        except Exception as e:
            self.log(f"⚠ Database connection failed: {e}", "WARN")
            self.log("  (This may be expected if database not initialized)", "INFO")

    def generate_report(self):
        """Generate and save test report"""
        self.log("")
        self.log("=" * 60)
        self.log("Summary")
        self.log("=" * 60)
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Tests Failed: {self.tests_failed}")

        # Save report
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / "t1_environment_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("=== Environment Verification Report ===\n")
            f.write(f"Date: {datetime.now()}\n\n")
            f.write("\n".join(self.report_lines))
            f.write(f"\n\n--- Summary ---\n")
            f.write(f"Tests Passed: {self.tests_passed}\n")
            f.write(f"Tests Failed: {self.tests_failed}\n")

        self.log(f"\nReport saved to: {report_file}")

        return self.tests_failed == 0

    def run(self):
        """Run all environment checks"""
        print("\n" + "=" * 60)
        print("Agent T1: Environment Verification")
        print("=" * 60 + "\n")

        self.check_python_version()
        self.check_dependencies()
        self.check_environment_variables()
        self.check_project_structure()
        self.check_database_connection()

        success = self.generate_report()

        if success:
            print("\n✓ All environment checks passed!")
            return 0
        else:
            print(f"\n✗ {self.tests_failed} checks failed. Please fix before proceeding.")
            return 1


if __name__ == "__main__":
    tester = EnvironmentTester()
    exit_code = tester.run()
    sys.exit(exit_code)