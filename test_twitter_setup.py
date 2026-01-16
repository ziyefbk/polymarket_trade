#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Twitter Integration Setup Test
测试 Twitter 集成配置
"""
import sys
import io
import os
from pathlib import Path

# Fix Windows console encoding
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

def test_imports():
    """Test if required packages are installed"""
    print("Testing package imports...")

    packages = {
        'tweepy': 'tweepy',
        'textblob': 'textblob',
    }

    all_ok = True
    for name, import_name in packages.items():
        try:
            __import__(import_name)
            print(f"  PASS: {name}")
        except ImportError:
            print(f"  FAIL: {name} not installed")
            all_ok = False

    if not all_ok:
        print("\nInstall missing packages:")
        print("  pip install tweepy textblob")
        print("  python -m textblob.download_corpora")

    return all_ok

def test_twitter_config():
    """Test if Twitter API credentials are configured"""
    print("\nTesting Twitter API configuration...")

    from dotenv import load_dotenv
    load_dotenv()

    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    api_key = os.getenv('TWITTER_API_KEY')

    if bearer_token and bearer_token != '':
        print("  PASS: TWITTER_BEARER_TOKEN is set")
        return True
    elif api_key and api_key != '':
        print("  PASS: TWITTER_API_KEY is set (v1.1)")
        return True
    else:
        print("  FAIL: No Twitter API credentials found")
        print("\nGet Twitter API access:")
        print("1. Go to: https://developer.twitter.com/en/portal/dashboard")
        print("2. Create an App")
        print("3. Get Bearer Token (API v2) or API Keys (v1.1)")
        print("4. Add to .env file:")
        print("   TWITTER_BEARER_TOKEN=your_token_here")
        return False

def test_twitter_connection():
    """Test if Twitter API connection works"""
    print("\nTesting Twitter API connection...")

    try:
        from src.analyzer.twitter_intelligence import TwitterIntelligenceAnalyzer, TWITTER_AVAILABLE

        if not TWITTER_AVAILABLE:
            print("  FAIL: Twitter integration not available")
            return False

        from dotenv import load_dotenv
        load_dotenv()

        bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
        if not bearer_token:
            print("  SKIP: No bearer token configured")
            return False

        # Try to initialize client
        analyzer = TwitterIntelligenceAnalyzer(bearer_token=bearer_token)

        # Try a simple search (will fail if credentials are invalid)
        try:
            tweets = analyzer.search_tweets("test", max_results=10)
            print(f"  PASS: API connection successful ({len(tweets)} tweets found)")
            return True
        except Exception as e:
            if "401" in str(e):
                print("  FAIL: Invalid credentials (401 Unauthorized)")
            elif "429" in str(e):
                print("  WARN: Rate limit exceeded (429 Too Many Requests)")
                print("        But credentials are valid!")
                return True
            else:
                print(f"  FAIL: {str(e)[:100]}")
            return False

    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_sentiment_analysis():
    """Test sentiment analysis"""
    print("\nTesting sentiment analysis...")

    try:
        from textblob import TextBlob

        # Test positive sentiment
        positive = TextBlob("This is amazing! I love it!").sentiment.polarity
        if positive > 0:
            print(f"  PASS: Positive sentiment detected ({positive:.2f})")
        else:
            print("  FAIL: Positive sentiment not detected")
            return False

        # Test negative sentiment
        negative = TextBlob("This is terrible. I hate it.").sentiment.polarity
        if negative < 0:
            print(f"  PASS: Negative sentiment detected ({negative:.2f})")
        else:
            print("  FAIL: Negative sentiment not detected")
            return False

        return True

    except LookupError:
        print("  FAIL: TextBlob corpora not downloaded")
        print("\nDownload corpora:")
        print("  python -m textblob.download_corpora")
        return False
    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def test_integration_module():
    """Test if Twitter integration module loads"""
    print("\nTesting Twitter integration module...")

    try:
        from src.analyzer.twitter_intelligence import (
            TwitterIntelligenceAnalyzer,
            Tweet,
            TwitterIntelligence,
            TWITTER_AVAILABLE
        )

        if TWITTER_AVAILABLE:
            print("  PASS: Twitter integration module loaded")
            return True
        else:
            print("  FAIL: Twitter integration not available")
            return False

    except Exception as e:
        print(f"  FAIL: {e}")
        return False

def main():
    print("="*60)
    print("Twitter Integration Setup Test")
    print("="*60)

    results = {
        "Package imports": test_imports(),
        "Twitter API config": test_twitter_config(),
        "Integration module": test_integration_module(),
        "Sentiment analysis": test_sentiment_analysis(),
        "Twitter connection": test_twitter_connection(),
    }

    print("\n" + "="*60)
    print("Test Results Summary")
    print("="*60)

    for test_name, passed in results.items():
        if passed:
            status = "PASS"
        elif passed is None:
            status = "SKIP"
        else:
            status = "FAIL"
        print(f"{test_name:.<40} {status}")

    all_passed = all(v for v in results.values() if v is not None)

    print("\n" + "="*60)
    if all_passed:
        print("SUCCESS: Twitter integration is ready!")
        print("\nNext steps:")
        print("1. Run example: python examples\\twitter_integration_example.py")
        print("2. Read docs: docs\\TWITTER_INTEGRATION.md")
    else:
        print("WARNING: Some tests failed. Fix the issues above.")
        print("\nQuick fixes:")
        print("1. Install packages: pip install tweepy textblob")
        print("2. Download corpora: python -m textblob.download_corpora")
        print("3. Get API key: https://developer.twitter.com/en/portal/dashboard")
        print("4. Configure .env: copy .env.example .env")
    print("="*60)

if __name__ == "__main__":
    main()
