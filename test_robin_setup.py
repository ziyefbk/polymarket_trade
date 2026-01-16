#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Quick setup test for Robin integration
测试 Robin 集成是否正确配置
"""
import sys
import io
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_robin_import():
    """Test if Robin can be imported"""
    print("Testing Robin imports...")

    robin_path = Path(__file__).parent / "robin_signals"
    if not robin_path.exists():
        print("FAIL: robin_signals directory not found!")
        return False

    sys.path.insert(0, str(robin_path))

    try:
        from search import get_search_results
        from llm import get_llm
        print("PASS: Robin core modules imported successfully")
        return True
    except ImportError as e:
        print(f"FAIL: Failed to import Robin modules: {e}")
        print("Run: cd robin_signals && pip install -r requirements.txt")
        return False

def test_tor_connection():
    """Test if Tor is running"""
    print("\nTesting Tor connection...")

    try:
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex(('127.0.0.1', 9050))
        sock.close()

        if result == 0:
            print("PASS: Tor is running on port 9050")
            return True
        else:
            print("FAIL: Tor is not running")
            print("Download and install: https://www.torproject.org/download/")
            print("Start Tor Browser or run: tor.exe")
            return False
    except Exception as e:
        print(f"FAIL: Error checking Tor: {e}")
        return False

def test_env_config():
    """Test if .env is configured"""
    print("\nTesting environment configuration...")

    env_file = Path(__file__).parent / "robin_signals" / ".env"

    if not env_file.exists():
        print("WARN: .env file not found in robin_signals/")
        print("Run: copy robin_signals\\.env.example robin_signals\\.env")
        print("Then edit .env and add your API keys")
        return False

    # Check for at least one API key
    try:
        with open(env_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except:
        with open(env_file, 'r') as f:
            content = f.read()

    has_openai = "OPENAI_API_KEY=" in content and "your_" not in content.split("OPENAI_API_KEY=")[1].split("\n")[0]
    has_anthropic = "ANTHROPIC_API_KEY=" in content and "your_" not in content.split("ANTHROPIC_API_KEY=")[1].split("\n")[0]
    has_google = "GOOGLE_API_KEY=" in content and "your_" not in content.split("GOOGLE_API_KEY=")[1].split("\n")[0]

    if has_openai:
        print("PASS: OpenAI API key configured")
        return True
    elif has_anthropic:
        print("PASS: Anthropic API key configured")
        return True
    elif has_google:
        print("PASS: Google API key configured")
        return True
    else:
        print("WARN: No LLM API keys found in .env")
        print("Add at least one: OPENAI_API_KEY, ANTHROPIC_API_KEY, or GOOGLE_API_KEY")
        return False

def test_polymarket_integration():
    """Test if Robin integration module works"""
    print("\nTesting Robin integration module...")

    try:
        from src.analyzer.robin_intelligence import ROBIN_AVAILABLE, RobinIntelligenceAnalyzer

        if not ROBIN_AVAILABLE:
            print("WARN: Robin not available (dependencies missing)")
            return False

        print("PASS: Robin integration module imported successfully")
        return True
    except Exception as e:
        print(f"FAIL: Failed to import integration: {e}")
        return False

def main():
    print("="*60)
    print("Robin Integration Setup Test")
    print("="*60)

    results = {
        "Robin imports": test_robin_import(),
        "Tor connection": test_tor_connection(),
        "Environment config": test_env_config(),
        "Integration module": test_polymarket_integration(),
    }

    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)

    for test_name, passed in results.items():
        status = "PASS" if passed else "FAIL"
        print(f"{test_name:.<40} {status}")

    all_passed = all(results.values())

    print("\n" + "="*60)
    if all_passed:
        print("SUCCESS: All tests passed! Robin integration is ready.")
        print("\nNext steps:")
        print("1. Run example: python examples\\robin_integration_example.py")
        print("2. Read docs: docs\\ROBIN_INTEGRATION.md")
    else:
        print("WARNING: Some tests failed. Fix the issues above.")
        print("\nQuick fixes:")
        print("1. Install deps: run setup_robin.bat")
        print("2. Install Tor: https://www.torproject.org/download/")
        print("3. Configure API: copy robin_signals\\.env.example robin_signals\\.env")
        print("   Then edit robin_signals\\.env with your API keys")
    print("="*60)

if __name__ == "__main__":
    main()
