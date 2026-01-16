#!/usr/bin/env python
"""
Installation and configuration verification script

Checks that all dependencies are installed and configuration is valid.
Run this before starting the orchestrator for the first time.
"""
import sys
import os
from pathlib import Path


def print_status(check_name: str, passed: bool, message: str = ""):
    """Print colored status message"""
    status = "✓" if passed else "✗"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    msg = f" - {message}" if message else ""
    print(f"{color}{status}{reset} {check_name}{msg}")
    return passed


def check_python_version():
    """Check Python version is 3.8+"""
    version = sys.version_info
    passed = version.major == 3 and version.minor >= 8
    msg = f"Python {version.major}.{version.minor}.{version.micro}"
    return print_status("Python Version", passed, msg)


def check_dependencies():
    """Check all required packages are installed"""
    required = [
        "httpx",
        "aiohttp",
        "websockets",
        "web3",
        "eth_account",
        "pandas",
        "numpy",
        "sqlalchemy",
        "aiosqlite",
        "apscheduler",
        "loguru",
        "pydantic",
        "pytest",
    ]

    all_installed = True
    for package in required:
        try:
            __import__(package)
            print_status(f"  {package}", True)
        except ImportError:
            print_status(f"  {package}", False, "NOT INSTALLED")
            all_installed = False

    return all_installed


def check_directories():
    """Check required directories exist"""
    dirs = ["logs", "data", "src", "config", "tests"]
    all_exist = True

    for dirname in dirs:
        path = Path(dirname)
        exists = path.exists()
        if not exists:
            all_exist = False
        print_status(f"  {dirname}/", exists)

    return all_exist


def check_config_files():
    """Check configuration files exist"""
    files = [
        "config/settings.py",
        "config/__init__.py",
        ".env.example",
    ]

    all_exist = True
    for filepath in files:
        path = Path(filepath)
        exists = path.is_file()
        if not exists:
            all_exist = False
        print_status(f"  {filepath}", exists)

    return all_exist


def check_env_file():
    """Check if .env file exists and has required variables"""
    env_path = Path(".env")
    if not env_path.exists():
        print_status(".env File", False, "File not found (copy from .env.example)")
        return False

    print_status(".env File", True, "Found")

    # Check for required variables
    with open(env_path) as f:
        content = f.read()

    required_vars = ["POLYMARKET_PRIVATE_KEY"]
    all_set = True

    for var in required_vars:
        if var in content and not content.count(f"{var}=\n"):
            print_status(f"  {var}", True, "Configured")
        else:
            print_status(f"  {var}", False, "Not configured")
            all_set = False

    return all_set


def check_main_files():
    """Check main implementation files exist"""
    files = [
        "main.py",
        "src/api/polymarket_client.py",
        "src/api/trader.py",
        "src/analyzer/arbitrage_detector.py",
        "src/strategy/arbitrage_executor.py",
        "src/utils/database.py",
        "src/utils/kelly.py",
        "src/utils/logger.py",
        "src/types/opportunities.py",
        "src/types/orders.py",
        "src/types/common.py",
    ]

    all_exist = True
    for filepath in files:
        path = Path(filepath)
        exists = path.is_file()
        if not exists:
            all_exist = False
        print_status(f"  {filepath}", exists)

    return all_exist


def check_imports():
    """Check that main modules can be imported"""
    sys.path.insert(0, os.getcwd())

    modules = [
        ("config", "settings"),
        ("src.types", "ArbitrageOpportunity"),
        ("src.types", "ExecutionResult"),
        ("src.utils", "logger"),
        ("main", "ArbitrageOrchestrator"),
    ]

    all_importable = True
    for module, item in modules:
        try:
            exec(f"from {module} import {item}")
            print_status(f"  {module}.{item}", True)
        except Exception as e:
            print_status(f"  {module}.{item}", False, str(e)[:50])
            all_importable = False

    return all_importable


def main():
    """Run all verification checks"""
    print("=" * 70)
    print("Polymarket Arbitrage System - Installation Verification")
    print("=" * 70)
    print()

    all_passed = True

    print("1. Checking Python Version...")
    all_passed &= check_python_version()
    print()

    print("2. Checking Dependencies...")
    all_passed &= check_dependencies()
    print()

    print("3. Checking Directories...")
    all_passed &= check_directories()
    print()

    print("4. Checking Configuration Files...")
    all_passed &= check_config_files()
    print()

    print("5. Checking Environment Variables...")
    all_passed &= check_env_file()
    print()

    print("6. Checking Implementation Files...")
    all_passed &= check_main_files()
    print()

    print("7. Checking Module Imports...")
    all_passed &= check_imports()
    print()

    print("=" * 70)
    if all_passed:
        print("\033[92m✓ All checks passed! System is ready to run.\033[0m")
        print()
        print("Next steps:")
        print("  1. Configure .env with your POLYMARKET_PRIVATE_KEY")
        print("  2. Run dry-run mode: python main.py --dry-run")
        print("  3. Run single cycle: python main.py --once")
        print("  4. Start system: python main.py")
    else:
        print("\033[91m✗ Some checks failed. Please fix the issues above.\033[0m")
        print()
        print("Common fixes:")
        print("  - Install dependencies: pip install -r requirements.txt")
        print("  - Copy environment file: cp .env.example .env")
        print("  - Create directories: mkdir -p logs data")

    print("=" * 70)

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
