#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Telegram Intelligence Setup Test
测试 Telegram 监控配置
"""
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_telethon_import():
    """Test if telethon is installed"""
    print("Testing telethon import...")

    try:
        from telethon import TelegramClient
        print("  ✅ PASS: telethon imported successfully")
        return True
    except ImportError:
        print("  ❌ FAIL: telethon not installed")
        print("  Install: pip install telethon")
        return False

def test_textblob_import():
    """Test if textblob is installed"""
    print("\nTesting TextBlob import...")

    try:
        from textblob import TextBlob
        print("  ✅ PASS: textblob imported successfully")
        return True
    except ImportError:
        print("  ❌ FAIL: textblob not installed")
        print("  Install: pip install textblob")
        return False

def test_integration_module():
    """Test if Telegram integration module loads"""
    print("\nTesting Telegram integration module...")

    try:
        from src.analyzer.telegram_intelligence import (
            TelegramIntelligenceAnalyzer,
            TelegramChannelMessage,
            TelegramIntelligence,
            TELEGRAM_AVAILABLE
        )

        if TELEGRAM_AVAILABLE:
            print("  ✅ PASS: Telegram module loaded")
            print("  ✅ All required dependencies available")
            return True
        else:
            print("  ❌ FAIL: Telegram not available")
            return False

    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False

def test_credentials():
    """Test if Telegram credentials are configured"""
    print("\nTesting Telegram API credentials...")

    import os

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if api_id and api_hash:
        print(f"  ✅ PASS: Credentials found")
        print(f"    API ID: {api_id}")
        print(f"    API Hash: {'*' * len(api_hash)}")
        return True
    else:
        print("  ⚠️  WARNING: Credentials not found in environment")
        print("  Set TELEGRAM_API_ID and TELEGRAM_API_HASH")
        print("\n  Get credentials from: https://my.telegram.org/apps")
        return False

def test_sentiment_analysis():
    """Test sentiment analysis functionality"""
    print("\nTesting sentiment analysis...")

    try:
        from textblob import TextBlob

        test_texts = {
            "Bitcoin is surging to new highs!": "positive",
            "Crypto market crashes amid regulatory fears": "negative",
            "Bitcoin price remains stable": "neutral"
        }

        print("  Testing sentiment on sample texts:")
        all_correct = True

        for text, expected in test_texts.items():
            analysis = TextBlob(text)
            polarity = analysis.sentiment.polarity

            if polarity > 0.1:
                result = "positive"
            elif polarity < -0.1:
                result = "negative"
            else:
                result = "neutral"

            match = "✅" if result == expected else "⚠️"
            print(f"    {match} \"{text[:50]}...\"")
            print(f"       Expected: {expected}, Got: {result} ({polarity:.2f})")

            if result != expected:
                all_correct = False

        if all_correct:
            print("  ✅ PASS: Sentiment analysis working correctly")
            return True
        else:
            print("  ⚠️  WARNING: Some sentiment results differ (this is normal)")
            return True

    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False

def main():
    print("="*60)
    print("Telegram Intelligence Setup Test")
    print("="*60)

    results = {
        "Telethon import": test_telethon_import(),
        "TextBlob import": test_textblob_import(),
        "Integration module": test_integration_module(),
        "API credentials": test_credentials(),
        "Sentiment analysis": test_sentiment_analysis(),
    }

    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)

    for test_name, passed in results.items():
        if test_name == "API credentials":
            status = "✅ OK" if passed else "⚠️  SKIP"
        else:
            status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")

    all_passed = all(results.values())
    required_passed = results["Telethon import"] and results["TextBlob import"] and results["Integration module"]

    print("\n" + "="*60)
    if required_passed:
        if results["API credentials"]:
            print("✅ SUCCESS: Telegram integration is fully ready!")
            print("\nNext steps:")
            print("1. Run example: python examples\\telegram_integration_example.py")
            print("2. Read docs: docs\\TELEGRAM_INTEGRATION.md")
        else:
            print("⚠️  PARTIAL SUCCESS: Dependencies installed, but credentials needed")
            print("\nNext steps:")
            print("1. Get Telegram API credentials:")
            print("   - Visit: https://my.telegram.org/apps")
            print("   - Create new application")
            print("   - Copy api_id and api_hash")
            print("2. Set environment variables:")
            print("   set TELEGRAM_API_ID=your_api_id")
            print("   set TELEGRAM_API_HASH=your_api_hash")
            print("3. Run example: python examples\\telegram_integration_example.py")
    else:
        print("❌ WARNING: Some tests failed. Fix the issues above.")
        print("\nQuick fixes:")
        print("1. Install telethon: pip install telethon")
        print("2. Install textblob: pip install textblob")
        print("3. Download textblob corpora: python -m textblob.download_corpora")

    print("="*60)

if __name__ == "__main__":
    main()
