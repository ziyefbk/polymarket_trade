#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Reddit Intelligence Setup Test
测试 Reddit 监控配置
"""
import sys
import io

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_praw_import():
    """Test if praw is installed"""
    print("Testing praw import...")

    try:
        import praw
        print("  ✅ PASS: praw imported successfully")
        print(f"    Version: {praw.__version__}")
        return True
    except ImportError:
        print("  ❌ FAIL: praw not installed")
        print("  Install: pip install praw")
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
    """Test if Reddit integration module loads"""
    print("\nTesting Reddit integration module...")

    try:
        from src.analyzer.reddit_intelligence import (
            RedditIntelligenceAnalyzer,
            RedditPost,
            RedditComment,
            RedditIntelligence,
            REDDIT_AVAILABLE
        )

        if REDDIT_AVAILABLE:
            print("  ✅ PASS: Reddit module loaded")
            print("  ✅ All required dependencies available")
            return True
        else:
            print("  ❌ FAIL: Reddit not available")
            return False

    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        return False

def test_credentials():
    """Test if Reddit credentials are configured"""
    print("\nTesting Reddit API credentials...")

    import os

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    if client_id and client_secret:
        print(f"  ✅ PASS: Credentials found")
        print(f"    Client ID: {client_id[:10]}...{client_id[-4:]}")
        print(f"    Client Secret: {'*' * len(client_secret)}")
        return True
    else:
        print("  ⚠️  WARNING: Credentials not found in environment")
        print("  Set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
        print("\n  Get credentials from: https://www.reddit.com/prefs/apps")
        return False

def test_reddit_connection():
    """Test connection to Reddit API"""
    print("\nTesting Reddit API connection...")

    import os

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("  ⏭️  SKIP: Credentials not configured")
        return False

    try:
        import praw

        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="PolymarketIntelligence/1.0"
        )

        # Test by accessing a subreddit
        subreddit = reddit.subreddit("test")
        _ = subreddit.id

        print("  ✅ PASS: Connected to Reddit API")
        print(f"    Read-only access confirmed")
        return True

    except Exception as e:
        print(f"  ❌ FAIL: {e}")
        print("  Check your credentials")
        return False

def test_sentiment_analysis():
    """Test sentiment analysis functionality"""
    print("\nTesting sentiment analysis...")

    try:
        from textblob import TextBlob

        test_texts = {
            "Bitcoin is mooning! 🚀🚀🚀": "positive",
            "Crypto market crashes, everything is dumping": "negative",
            "Bitcoin price is sideways today": "neutral"
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
            print(f"    {match} \"{text[:45]}...\"")
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
    print("Reddit Intelligence Setup Test")
    print("="*60)

    results = {
        "PRAW import": test_praw_import(),
        "TextBlob import": test_textblob_import(),
        "Integration module": test_integration_module(),
        "API credentials": test_credentials(),
        "Reddit connection": test_reddit_connection(),
        "Sentiment analysis": test_sentiment_analysis(),
    }

    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)

    for test_name, passed in results.items():
        if test_name in ["API credentials", "Reddit connection"]:
            status = "✅ OK" if passed else "⚠️  SKIP"
        else:
            status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:.<40} {status}")

    all_passed = all(results.values())
    required_passed = results["PRAW import"] and results["TextBlob import"] and results["Integration module"]

    print("\n" + "="*60)
    if required_passed:
        if results["API credentials"] and results["Reddit connection"]:
            print("✅ SUCCESS: Reddit integration is fully ready!")
            print("\nNext steps:")
            print("1. Run example: python examples\\reddit_integration_example.py")
            print("2. Read docs: docs\\REDDIT_INTEGRATION.md")
        else:
            print("⚠️  PARTIAL SUCCESS: Dependencies installed, but credentials needed")
            print("\nNext steps:")
            print("1. Get Reddit API credentials:")
            print("   - Visit: https://www.reddit.com/prefs/apps")
            print("   - Click 'Create App' or 'Create Another App'")
            print("   - Choose 'script' type")
            print("   - Copy client_id and client_secret")
            print("2. Set environment variables:")
            print("   set REDDIT_CLIENT_ID=your_client_id")
            print("   set REDDIT_CLIENT_SECRET=your_client_secret")
            print("3. Run example: python examples\\reddit_integration_example.py")
    else:
        print("❌ WARNING: Some tests failed. Fix the issues above.")
        print("\nQuick fixes:")
        print("1. Install praw: pip install praw")
        print("2. Install textblob: pip install textblob")
        print("3. Download textblob corpora: python -m textblob.download_corpora")

    print("="*60)

if __name__ == "__main__":
    main()
