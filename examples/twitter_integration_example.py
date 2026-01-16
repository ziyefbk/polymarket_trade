"""
Twitter Intelligence Integration Examples

Demonstrates how to use the Twitter monitoring module for Polymarket trading.
"""
import asyncio
import sys
import os
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzer.twitter_intelligence import (
    TwitterIntelligenceAnalyzer,
    TWITTER_AVAILABLE
)
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.api.polymarket_client import PolymarketClient


def example_1_basic_search():
    """Example 1: Basic Twitter search for keywords"""
    print("\n" + "="*80)
    print("Example 1: Basic Twitter Search")
    print("="*80)

    if not TWITTER_AVAILABLE:
        print("❌ Twitter integration not available.")
        print("Install: pip install tweepy textblob")
        return

    # Get Twitter Bearer Token from environment
    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        print("❌ TWITTER_BEARER_TOKEN not found in environment")
        print("Set it in .env file or export TWITTER_BEARER_TOKEN=your_token")
        return

    try:
        # Initialize analyzer
        analyzer = TwitterIntelligenceAnalyzer(bearer_token=bearer_token)

        # Search for tweets about Trump and the 2024 election
        print("\nSearching Twitter for: 'Trump 2024 election'...")
        tweets = analyzer.search_tweets(
            query="Trump 2024 election -is:retweet lang:en",
            max_results=50
        )

        if tweets:
            print(f"✓ Found {len(tweets)} tweets")

            # Generate intelligence report
            report = analyzer.generate_intelligence_report("Trump 2024 election", tweets)

            # Print report
            analyzer.print_report(report)
        else:
            print("No tweets found")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_2_monitor_event():
    """Example 2: Monitor specific Polymarket event"""
    print("\n" + "="*80)
    print("Example 2: Monitor Polymarket Event")
    print("="*80)

    if not TWITTER_AVAILABLE:
        print("❌ Twitter integration not available.")
        return

    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        print("❌ TWITTER_BEARER_TOKEN not set")
        return

    try:
        analyzer = TwitterIntelligenceAnalyzer(bearer_token=bearer_token)

        # Monitor event with keywords and influential accounts
        event_title = "Will Trump win the 2024 presidential election?"
        keywords = ["Trump", "election", "2024", "Biden"]
        influential_accounts = ["realDonaldTrump", "JoeBiden", "nytimes", "FoxNews", "CNN"]

        print(f"\nMonitoring event: {event_title}")
        print(f"Keywords: {keywords}")
        print(f"Influential accounts: {influential_accounts}")

        report = analyzer.monitor_event(
            event_title=event_title,
            keywords=keywords,
            influential_accounts=influential_accounts,
            max_results=100
        )

        if report:
            analyzer.print_report(report)

            # Trading signal interpretation
            print("\n" + "="*80)
            print("TRADING SIGNAL INTERPRETATION")
            print("="*80)

            if report.activity_spike:
                print(f"⚠️  HIGH ACTIVITY: {report.spike_magnitude:.1f}x normal volume")
                print("   → Consider this a strong signal")

            if report.avg_sentiment > 0.2:
                print(f"📈 BULLISH SENTIMENT: {report.avg_sentiment:.2f}")
                print("   → Positive odds for Trump winning")
            elif report.avg_sentiment < -0.2:
                print(f"📉 BEARISH SENTIMENT: {report.avg_sentiment:.2f}")
                print("   → Negative odds for Trump winning")
            else:
                print(f"➖ NEUTRAL SENTIMENT: {report.avg_sentiment:.2f}")
                print("   → No clear signal")

            # Check influential voices
            print("\nInfluential Voices Analysis:")
            for voice in report.influential_voices[:3]:
                sentiment = voice['avg_sentiment']
                if sentiment > 0.2:
                    direction = "BULLISH 📈"
                elif sentiment < -0.2:
                    direction = "BEARISH 📉"
                else:
                    direction = "NEUTRAL ➖"

                print(f"  @{voice['username']} ({voice['followers']:,} followers): {direction}")

        else:
            print("No intelligence gathered")

    except Exception as e:
        print(f"❌ Error: {e}")


async def example_3_combined_analysis():
    """Example 3: Combine Twitter intelligence with arbitrage detection"""
    print("\n" + "="*80)
    print("Example 3: Combined Twitter + Arbitrage Analysis")
    print("="*80)

    if not TWITTER_AVAILABLE:
        print("❌ Twitter integration not available.")
        return

    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        print("❌ TWITTER_BEARER_TOKEN not set")
        return

    try:
        # Initialize components
        twitter = TwitterIntelligenceAnalyzer(bearer_token=bearer_token)

        async with PolymarketClient() as client:
            detector = IntraMarketArbitrageDetector(client)

            print("Scanning Polymarket for arbitrage opportunities...")
            opportunities = await detector.scan_all_markets()

            if not opportunities:
                print("No arbitrage opportunities found")
                return

            print(f"Found {len(opportunities)} arbitrage opportunities")

            # Analyze top 3 opportunities with Twitter intelligence
            for i, opp in enumerate(opportunities[:3], 1):
                print("\n" + "="*80)
                print(f"OPPORTUNITY #{i}: {opp.event_title}")
                print("="*80)
                print(f"Spread: {opp.spread:.2%}")
                print(f"Net Profit: {opp.net_profit_pct:.2%}")
                print(f"Confidence: {opp.confidence_score:.2f}")

                # Extract keywords from event title
                keywords = extract_keywords_from_event(opp.event_title)

                if keywords:
                    print(f"\nGathering Twitter intelligence for keywords: {keywords}")

                    try:
                        report = twitter.monitor_event(
                            event_title=opp.event_title,
                            keywords=keywords,
                            max_results=50
                        )

                        if report:
                            print(f"\n📊 Twitter Intelligence:")
                            print(f"   Tweets: {report.total_tweets}")
                            print(f"   Sentiment: {report.avg_sentiment:.2f} ", end="")

                            if report.avg_sentiment > 0.1:
                                print("(POSITIVE)")
                            elif report.avg_sentiment < -0.1:
                                print("(NEGATIVE)")
                            else:
                                print("(NEUTRAL)")

                            print(f"   Impressions: {report.total_impressions:,}")

                            if report.activity_spike:
                                print(f"   ⚠️  Activity Spike: {report.spike_magnitude:.1f}x")

                            # Enhanced confidence score
                            sentiment_boost = abs(report.avg_sentiment) * 0.2
                            activity_boost = 0.1 if report.activity_spike else 0

                            enhanced_confidence = min(
                                opp.confidence_score + sentiment_boost + activity_boost,
                                1.0
                            )

                            print(f"\n🎯 ENHANCED CONFIDENCE: {enhanced_confidence:.2f}")
                            print(f"   Original: {opp.confidence_score:.2f}")
                            print(f"   Twitter Sentiment Boost: +{sentiment_boost:.2f}")
                            print(f"   Activity Boost: +{activity_boost:.2f}")

                            if enhanced_confidence > 0.7:
                                print("\n✅ STRONG SIGNAL: Consider trading this opportunity")
                            elif enhanced_confidence > 0.5:
                                print("\n⚠️  MODERATE SIGNAL: Proceed with caution")
                            else:
                                print("\n❌ WEAK SIGNAL: Skip this opportunity")

                        else:
                            print("   No Twitter data available")

                    except Exception as e:
                        print(f"   Twitter analysis failed: {e}")
                else:
                    print("   No relevant keywords found")

                # Rate limiting
                if i < min(3, len(opportunities)):
                    print("\nWaiting 10s before next analysis...")
                    await asyncio.sleep(10)

    except Exception as e:
        print(f"❌ Error: {e}")


def extract_keywords_from_event(event_title: str) -> list:
    """Extract relevant keywords from event title"""
    # Remove common question words
    stopwords = {
        'will', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
        'have', 'has', 'had', 'do', 'does', 'did', 'the', 'a', 'an',
        'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'by',
        'from', 'there', 'their', 'they'
    }

    # Extract words
    words = event_title.lower().replace('?', '').split()
    keywords = [w for w in words if w not in stopwords and len(w) > 2]

    # Take first 4-5 meaningful keywords
    return keywords[:5]


def example_4_sentiment_tracking():
    """Example 4: Track sentiment over time"""
    print("\n" + "="*80)
    print("Example 4: Sentiment Tracking Over Time")
    print("="*80)

    if not TWITTER_AVAILABLE:
        print("❌ Twitter integration not available.")
        return

    bearer_token = os.getenv('TWITTER_BEARER_TOKEN')
    if not bearer_token:
        print("❌ TWITTER_BEARER_TOKEN not set")
        return

    try:
        analyzer = TwitterIntelligenceAnalyzer(bearer_token=bearer_token)

        query = "Bitcoin OR BTC"
        print(f"Tracking sentiment for: {query}")

        # Collect multiple samples
        samples = []
        for i in range(3):
            print(f"\nSample #{i+1}...")
            tweets = analyzer.search_tweets(query, max_results=30)

            if tweets:
                avg_sentiment = sum(t.sentiment_score for t in tweets) / len(tweets)
                samples.append({
                    'time': datetime.now(),
                    'tweets': len(tweets),
                    'sentiment': avg_sentiment
                })
                print(f"  Sentiment: {avg_sentiment:.3f}")

            if i < 2:
                print("  Waiting 30s...")
                import time
                time.sleep(30)

        # Analyze trend
        if len(samples) >= 2:
            print("\n" + "="*80)
            print("SENTIMENT TREND ANALYSIS")
            print("="*80)

            sentiments = [s['sentiment'] for s in samples]
            trend = sentiments[-1] - sentiments[0]

            print(f"Start: {sentiments[0]:.3f}")
            print(f"End: {sentiments[-1]:.3f}")
            print(f"Change: {trend:+.3f}")

            if trend > 0.05:
                print("\n📈 BULLISH TREND: Sentiment improving")
            elif trend < -0.05:
                print("\n📉 BEARISH TREND: Sentiment declining")
            else:
                print("\n➖ STABLE: No significant trend")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run examples"""
    print("\n" + "="*80)
    print("Twitter Intelligence Integration Examples")
    print("="*80)

    if not TWITTER_AVAILABLE:
        print("\n❌ Twitter integration not available!")
        print("Install required packages:")
        print("  pip install tweepy textblob")
        print("\nDownload TextBlob corpora:")
        print("  python -m textblob.download_corpora")
        return

    print("\n⚠️  WARNING: These examples will use your Twitter API quota")
    print("⚠️  Make sure TWITTER_BEARER_TOKEN is set in .env\n")

    print("Available examples:")
    print("1. Basic Twitter search")
    print("2. Monitor specific Polymarket event")
    print("3. Combined Twitter + arbitrage analysis")
    print("4. Sentiment tracking over time")

    choice = input("\nWhich example to run? (1-4, or 'all'): ").strip()

    if choice == "1":
        example_1_basic_search()
    elif choice == "2":
        example_2_monitor_event()
    elif choice == "3":
        asyncio.run(example_3_combined_analysis())
    elif choice == "4":
        example_4_sentiment_tracking()
    elif choice.lower() == "all":
        example_1_basic_search()
        example_2_monitor_event()
        asyncio.run(example_3_combined_analysis())
        example_4_sentiment_tracking()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
