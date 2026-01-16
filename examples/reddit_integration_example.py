"""
Reddit Intelligence Integration Examples

Demonstrates how to use Reddit monitoring for Polymarket trading signals.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzer.reddit_intelligence import (
    RedditIntelligenceAnalyzer,
    REDDIT_AVAILABLE
)


def example_1_subreddit_search():
    """Example 1: Search specific subreddits"""
    print("\n" + "="*80)
    print("Example 1: Search Subreddits for Crypto Discussion")
    print("="*80)

    if not REDDIT_AVAILABLE:
        print("❌ PRAW not available. Install: pip install praw")
        return

    # Get credentials from environment
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("\n⚠️  Reddit API credentials not found in environment")
        print("Please set REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET")
        print("\nGet credentials from: https://www.reddit.com/prefs/apps")
        return

    try:
        analyzer = RedditIntelligenceAnalyzer(
            client_id=client_id,
            client_secret=client_secret
        )

        # Search crypto subreddits
        subreddits = ["cryptocurrency", "bitcoin", "ethtrader"]
        query = "bitcoin OR btc"

        print(f"\nSearching r/{', r/'.join(subreddits)}")
        print(f"Query: {query}")
        print("Time filter: Last week\n")

        posts = analyzer.search_posts(
            query=query,
            subreddits=subreddits,
            time_filter="week",
            limit=50
        )

        if posts:
            print(f"✓ Found {len(posts)} posts")

            # Show top posts
            print("\nTop 5 Posts by Score:")
            print("-" * 80)

            for i, post in enumerate(sorted(posts, key=lambda p: p.score, reverse=True)[:5], 1):
                print(f"\n{i}. r/{post.subreddit} - {post.title[:70]}")
                print(f"   Score: {post.score:,} | Comments: {post.num_comments:,}")
                print(f"   Sentiment: {post.sentiment_label} ({post.sentiment_score:.2f})")
                print(f"   {post.url}")

            # Sentiment summary
            avg_sentiment = sum(p.sentiment_score for p in posts) / len(posts)
            print(f"\n📊 Average Sentiment: {avg_sentiment:.3f}", end=" ")

            if avg_sentiment > 0.1:
                print("(POSITIVE 📈)")
            elif avg_sentiment < -0.1:
                print("(NEGATIVE 📉)")
            else:
                print("(NEUTRAL ➖)")

        else:
            print("No posts found")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_2_event_monitoring():
    """Example 2: Monitor Reddit for specific event"""
    print("\n" + "="*80)
    print("Example 2: Monitor Reddit for Specific Event")
    print("="*80)

    if not REDDIT_AVAILABLE:
        print("❌ PRAW not available.")
        return

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("⚠️  Reddit API credentials not found")
        return

    try:
        analyzer = RedditIntelligenceAnalyzer(
            client_id=client_id,
            client_secret=client_secret
        )

        event_title = "2024 Presidential Election"
        keywords = ["election", "trump", "biden", "president", "2024"]

        print(f"\nEvent: {event_title}")
        print(f"Keywords: {keywords}\n")

        # Monitor event (auto-selects political subreddits)
        report = analyzer.monitor_event(
            event_title=event_title,
            keywords=keywords,
            time_filter="week"
        )

        if report:
            analyzer.print_report(report)

            # Trading signal
            print("\n" + "="*80)
            print("TRADING SIGNAL")
            print("="*80)

            print(f"\nCommunity Consensus: {report.community_consensus}")
            print(f"Consensus Strength: {report.consensus_strength:.2f}")

            if report.community_consensus == "BULLISH" and report.consensus_strength > 0.6:
                print("\n✅ STRONG BULLISH SIGNAL")
                print("   → High confidence in YES outcome")
            elif report.community_consensus == "BEARISH" and report.consensus_strength > 0.6:
                print("\n⚠️  STRONG BEARISH SIGNAL")
                print("   → High confidence in NO outcome")
            else:
                print("\n🤔 MIXED SIGNALS")
                print("   → Community divided or uncertain")

        else:
            print("No intelligence gathered")

    except Exception as e:
        print(f"❌ Error: {e}")


async def example_3_combined_analysis():
    """Example 3: Combine Reddit with arbitrage detection"""
    print("\n" + "="*80)
    print("Example 3: Combined Reddit + Arbitrage Analysis")
    print("="*80)

    if not REDDIT_AVAILABLE:
        print("❌ PRAW not available.")
        return

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("⚠️  Reddit API credentials not found")
        return

    try:
        from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
        from src.api.polymarket_client import PolymarketClient

        # Get Reddit intelligence
        print("\n[1/2] Getting Reddit intelligence...")

        reddit = RedditIntelligenceAnalyzer(
            client_id=client_id,
            client_secret=client_secret
        )

        reddit_report = reddit.monitor_event(
            event_title="Bitcoin Price Prediction",
            keywords=["bitcoin", "btc", "100k", "price"],
            subreddits=["cryptocurrency", "bitcoin"],
            time_filter="week"
        )

        if reddit_report:
            print(f"✓ Analyzed {reddit_report.total_posts} posts")
            print(f"  Consensus: {reddit_report.community_consensus}")
            print(f"  Sentiment: {reddit_report.avg_sentiment:.2f}")

        # Get arbitrage opportunities
        print("\n[2/2] Scanning for arbitrage opportunities...")

        async with PolymarketClient() as client:
            detector = IntraMarketArbitrageDetector(client)
            opportunities = await detector.scan_all_markets()

        if not opportunities:
            print("No arbitrage opportunities found")
            return

        print(f"✓ Found {len(opportunities)} opportunities")

        # Enhance with Reddit data
        print("\n" + "="*80)
        print("ENHANCED ANALYSIS")
        print("="*80)

        for i, opp in enumerate(opportunities[:3], 1):
            print(f"\n--- Opportunity #{i}: {opp.event_title} ---")
            print(f"Spread: {opp.spread:.2%}")
            print(f"Net Profit: {opp.net_profit_pct:.2%}")
            print(f"Base Confidence: {opp.confidence_score:.2f}")

            # Reddit enhancement
            if reddit_report:
                print(f"\n📊 Reddit Intelligence:")
                print(f"  Posts: {reddit_report.total_posts}")
                print(f"  Comments: {reddit_report.total_comments}")
                print(f"  Consensus: {reddit_report.community_consensus}")
                print(f"  Sentiment: {reddit_report.avg_sentiment:.2f}")

                # Calculate boost
                reddit_boost = 0

                if reddit_report.community_consensus == "BULLISH":
                    reddit_boost = 0.1 * reddit_report.consensus_strength
                elif reddit_report.community_consensus == "BEARISH":
                    reddit_boost = -0.1 * reddit_report.consensus_strength

                # Sentiment boost
                if abs(reddit_report.avg_sentiment) > 0.2:
                    reddit_boost += reddit_report.avg_sentiment * 0.05

                enhanced_confidence = min(
                    opp.confidence_score + reddit_boost,
                    1.0
                )

                print(f"\n🎯 ENHANCED CONFIDENCE: {enhanced_confidence:.2f}")
                print(f"   Original: {opp.confidence_score:.2f}")
                print(f"   Reddit Boost: {reddit_boost:+.2f}")

                if enhanced_confidence > 0.75:
                    print("\n✅ STRONG SIGNAL: Execute trade")
                elif enhanced_confidence > 0.6:
                    print("\n⚠️  MODERATE SIGNAL: Proceed with caution")
                else:
                    print("\n❌ WEAK SIGNAL: Skip")

    except Exception as e:
        print(f"❌ Error: {e}")


def example_4_expert_opinions():
    """Example 4: Extract expert opinions from comments"""
    print("\n" + "="*80)
    print("Example 4: Expert Opinions from High-Karma Users")
    print("="*80)

    if not REDDIT_AVAILABLE:
        print("❌ PRAW not available.")
        return

    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    if not client_id or not client_secret:
        print("⚠️  Reddit API credentials not found")
        return

    try:
        analyzer = RedditIntelligenceAnalyzer(
            client_id=client_id,
            client_secret=client_secret
        )

        # Get top posts
        posts = analyzer.search_posts(
            query="bitcoin prediction",
            subreddits=["cryptocurrency"],
            time_filter="week",
            limit=10
        )

        if not posts:
            print("No posts found")
            return

        print(f"Found {len(posts)} posts. Getting expert comments...\n")

        # Get comments from top posts
        all_expert_comments = []

        for post in posts[:3]:  # Top 3 posts
            print(f"Analyzing: {post.title[:60]}...")

            comments = analyzer.get_post_comments(post, limit=50)

            # Filter for "expert" comments (high score or top-level)
            expert_comments = [
                c for c in comments
                if c.score >= 100 or c.is_top_level
            ]

            all_expert_comments.extend(expert_comments)

        if all_expert_comments:
            print(f"\n✓ Found {len(all_expert_comments)} expert comments")

            print("\n" + "-"*80)
            print("TOP EXPERT OPINIONS")
            print("-"*80)

            # Sort by score
            top_experts = sorted(
                all_expert_comments,
                key=lambda c: c.score,
                reverse=True
            )[:5]

            for i, comment in enumerate(top_experts, 1):
                print(f"\n{i}. u/{comment.author} (Score: {comment.score:,})")
                print(f"   {comment.text[:150]}...")
                print(f"   Sentiment: {comment.sentiment_label} ({comment.sentiment_score:.2f})")

            # Sentiment of expert opinions
            expert_sentiment = sum(c.sentiment_score for c in all_expert_comments) / len(all_expert_comments)

            print(f"\n📊 Expert Consensus Sentiment: {expert_sentiment:.3f}")

            if expert_sentiment > 0.15:
                print("   📈 Experts are BULLISH")
            elif expert_sentiment < -0.15:
                print("   📉 Experts are BEARISH")
            else:
                print("   ➖ Experts are NEUTRAL")

        else:
            print("No expert comments found")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run examples"""
    print("\n" + "="*80)
    print("Reddit Intelligence Integration Examples")
    print("="*80)

    if not REDDIT_AVAILABLE:
        print("\n❌ PRAW not available!")
        print("Install required package:")
        print("  pip install praw textblob")
        return

    print("\n⚠️  REQUIREMENTS:")
    print("1. Reddit API credentials (client_id and client_secret)")
    print("   Get from: https://www.reddit.com/prefs/apps")
    print("2. Set environment variables:")
    print("   - REDDIT_CLIENT_ID")
    print("   - REDDIT_CLIENT_SECRET")
    print()

    print("Available examples:")
    print("1. Subreddit search (crypto discussion)")
    print("2. Event-specific monitoring")
    print("3. Combined Reddit + arbitrage analysis")
    print("4. Expert opinions extraction")

    choice = input("\nWhich example to run? (1-4): ").strip()

    if choice == "1":
        example_1_subreddit_search()
    elif choice == "2":
        example_2_event_monitoring()
    elif choice == "3":
        asyncio.run(example_3_combined_analysis())
    elif choice == "4":
        example_4_expert_opinions()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
