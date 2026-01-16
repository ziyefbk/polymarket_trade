"""
Telegram Intelligence Integration Examples

Demonstrates how to use Telegram monitoring for Polymarket trading signals.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzer.telegram_intelligence import (
    TelegramIntelligenceAnalyzer,
    TELEGRAM_AVAILABLE
)


async def example_1_channel_monitoring():
    """Example 1: Monitor specific Telegram channels"""
    print("\n" + "="*80)
    print("Example 1: Monitor Telegram Channels for Crypto News")
    print("="*80)

    if not TELEGRAM_AVAILABLE:
        print("❌ Telethon not available. Install: pip install telethon")
        return

    # Get credentials from environment or user input
    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        print("\n⚠️  Telegram API credentials not found in environment")
        print("Please set TELEGRAM_API_ID and TELEGRAM_API_HASH")
        print("\nGet credentials from: https://my.telegram.org/apps")
        return

    try:
        async with TelegramIntelligenceAnalyzer(
            api_id=int(api_id),
            api_hash=api_hash
        ) as analyzer:
            # Monitor crypto channels
            channels = ["cryptonews", "bitcoin", "ethereum"]
            keywords = ["bitcoin", "btc", "price", "surge", "crash"]

            print(f"\nMonitoring channels: {channels}")
            print(f"Keywords: {keywords}")
            print("Searching last 24 hours...")

            messages = await analyzer.search_messages(
                channels=channels,
                keywords=keywords,
                limit=50,
                hours=24
            )

            if messages:
                print(f"\n✓ Found {len(messages)} matching messages")

                # Generate report
                report = analyzer.generate_intelligence_report(
                    query=" OR ".join(keywords),
                    messages=messages
                )

                if report:
                    analyzer.print_report(report)

                    # Trading signal interpretation
                    print("\n" + "="*80)
                    print("TRADING SIGNAL")
                    print("="*80)

                    if report.channel_consensus == "BULLISH":
                        print("📈 BULLISH consensus detected")
                        print(f"   Strength: {report.consensus_strength:.2f}")
                        print("   → Consider LONG positions on crypto-related markets")
                    elif report.channel_consensus == "BEARISH":
                        print("📉 BEARISH consensus detected")
                        print(f"   Strength: {report.consensus_strength:.2f}")
                        print("   → Consider SHORT positions")
                    else:
                        print("➖ No clear consensus")
            else:
                print("No matching messages found")

    except Exception as e:
        print(f"❌ Error: {e}")


async def example_2_event_monitoring():
    """Example 2: Monitor Telegram for specific Polymarket event"""
    print("\n" + "="*80)
    print("Example 2: Monitor Telegram for Specific Event")
    print("="*80)

    if not TELEGRAM_AVAILABLE:
        print("❌ Telethon not available.")
        return

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        print("⚠️  Telegram API credentials not found")
        return

    try:
        event_title = "Bitcoin to hit $100k by end of 2024?"
        keywords = ["bitcoin", "100k", "btc", "price target", "prediction"]

        print(f"\nEvent: {event_title}")
        print(f"Keywords: {keywords}")

        async with TelegramIntelligenceAnalyzer(
            api_id=int(api_id),
            api_hash=api_hash
        ) as analyzer:
            # Monitor event (auto-selects crypto channels)
            report = await analyzer.monitor_event(
                event_title=event_title,
                keywords=keywords,
                hours=48  # Last 48 hours
            )

            if report:
                analyzer.print_report(report)

                # Consensus analysis
                print("\n" + "="*80)
                print("EVENT ANALYSIS")
                print("="*80)

                print(f"\nCommunity Sentiment: {report.avg_sentiment:.3f}")
                print(f"Consensus: {report.channel_consensus}")
                print(f"Strength: {report.consensus_strength:.2f}")

                if report.channel_consensus == "BULLISH" and report.consensus_strength > 0.7:
                    print("\n✅ STRONG BULLISH SIGNAL")
                    print("   → High confidence in YES outcome")
                elif report.channel_consensus == "BEARISH" and report.consensus_strength > 0.7:
                    print("\n⚠️  STRONG BEARISH SIGNAL")
                    print("   → High confidence in NO outcome")
                else:
                    print("\n🤔 UNCERTAIN SIGNAL")
                    print("   → Community divided or neutral")

            else:
                print("No intelligence gathered")

    except Exception as e:
        print(f"❌ Error: {e}")


async def example_3_combined_analysis():
    """Example 3: Combine Telegram with arbitrage detection"""
    print("\n" + "="*80)
    print("Example 3: Combined Telegram + Arbitrage Analysis")
    print("="*80)

    if not TELEGRAM_AVAILABLE:
        print("❌ Telethon not available.")
        return

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        print("⚠️  Telegram API credentials not found")
        return

    try:
        from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
        from src.api.polymarket_client import PolymarketClient

        async with TelegramIntelligenceAnalyzer(
            api_id=int(api_id),
            api_hash=api_hash
        ) as tg_analyzer:
            print("\n[1/2] Getting Telegram intelligence...")

            # Monitor political channels
            tg_report = await tg_analyzer.monitor_event(
                event_title="2024 Presidential Election",
                keywords=["election", "trump", "biden", "president", "2024"],
                channels=["politicalnews", "breaking247"],
                hours=24
            )

            if tg_report:
                print(f"✓ Analyzed {tg_report.total_messages} Telegram messages")
                print(f"  Consensus: {tg_report.channel_consensus}")
                print(f"  Sentiment: {tg_report.avg_sentiment:.2f}")

            print("\n[2/2] Scanning for arbitrage opportunities...")

            async with PolymarketClient() as client:
                detector = IntraMarketArbitrageDetector(client)
                opportunities = await detector.scan_all_markets()

            if not opportunities:
                print("No arbitrage opportunities found")
                return

            print(f"✓ Found {len(opportunities)} opportunities")

            # Enhance with Telegram data
            print("\n" + "="*80)
            print("ENHANCED ANALYSIS")
            print("="*80)

            for i, opp in enumerate(opportunities[:3], 1):
                print(f"\n--- Opportunity #{i}: {opp.event_title} ---")
                print(f"Spread: {opp.spread:.2%}")
                print(f"Net Profit: {opp.net_profit_pct:.2%}")
                print(f"Base Confidence: {opp.confidence_score:.2f}")

                # Telegram enhancement
                if tg_report:
                    print(f"\n📱 Telegram Intelligence:")
                    print(f"  Messages: {tg_report.total_messages}")
                    print(f"  Consensus: {tg_report.channel_consensus}")
                    print(f"  Sentiment: {tg_report.avg_sentiment:.2f}")

                    # Calculate boost
                    tg_boost = 0

                    if tg_report.channel_consensus == "BULLISH":
                        tg_boost = 0.1 * tg_report.consensus_strength
                    elif tg_report.channel_consensus == "BEARISH":
                        tg_boost = -0.1 * tg_report.consensus_strength

                    # Sentiment boost
                    if abs(tg_report.avg_sentiment) > 0.2:
                        tg_boost += tg_report.avg_sentiment * 0.1

                    enhanced_confidence = min(
                        opp.confidence_score + tg_boost,
                        1.0
                    )

                    print(f"\n🎯 ENHANCED CONFIDENCE: {enhanced_confidence:.2f}")
                    print(f"   Original: {opp.confidence_score:.2f}")
                    print(f"   Telegram Boost: {tg_boost:+.2f}")

                    if enhanced_confidence > 0.75:
                        print("\n✅ STRONG SIGNAL: Execute trade")
                    elif enhanced_confidence > 0.6:
                        print("\n⚠️  MODERATE SIGNAL: Proceed with caution")
                    else:
                        print("\n❌ WEAK SIGNAL: Skip")

    except Exception as e:
        print(f"❌ Error: {e}")


async def example_4_realtime_monitoring():
    """Example 4: Real-time channel monitoring"""
    print("\n" + "="*80)
    print("Example 4: Real-Time Telegram Channel Monitoring")
    print("="*80)

    if not TELEGRAM_AVAILABLE:
        print("❌ Telethon not available.")
        return

    api_id = os.getenv("TELEGRAM_API_ID")
    api_hash = os.getenv("TELEGRAM_API_HASH")

    if not api_id or not api_hash:
        print("⚠️  Telegram API credentials not found")
        return

    print("\nMonitoring crypto channels in real-time...")
    print("Press Ctrl+C to stop...\n")

    try:
        async with TelegramIntelligenceAnalyzer(
            api_id=int(api_id),
            api_hash=api_hash
        ) as analyzer:
            channels = ["cryptonews", "bitcoin"]

            print(f"Channels: {channels}")
            print("Waiting for new messages...\n")

            # Check for new messages every 30 seconds
            while True:
                for channel in channels:
                    messages = await analyzer.get_channel_messages(
                        channel,
                        limit=5  # Latest 5 messages
                    )

                    for msg in messages:
                        # Check if contains trading keywords
                        keywords = ["pump", "dump", "surge", "crash", "moon", "bottom"]
                        if any(kw in msg.text.lower() for kw in keywords):
                            print(f"\n🔔 ALERT from @{msg.channel_username}:")
                            print(f"   {msg.text[:150]}...")
                            print(f"   Sentiment: {msg.sentiment_label} ({msg.sentiment_score:.2f})")
                            print(f"   Views: {msg.views:,}")

                            # Trading signal
                            if msg.sentiment_score > 0.3:
                                print("   📈 BULLISH signal detected")
                            elif msg.sentiment_score < -0.3:
                                print("   📉 BEARISH signal detected")

                # Wait before next check
                await asyncio.sleep(30)

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run examples"""
    print("\n" + "="*80)
    print("Telegram Intelligence Integration Examples")
    print("="*80)

    if not TELEGRAM_AVAILABLE:
        print("\n❌ Telethon not available!")
        print("Install required package:")
        print("  pip install telethon textblob")
        return

    print("\n⚠️  REQUIREMENTS:")
    print("1. Telegram API credentials (api_id and api_hash)")
    print("   Get from: https://my.telegram.org/apps")
    print("2. Set environment variables:")
    print("   - TELEGRAM_API_ID")
    print("   - TELEGRAM_API_HASH")
    print("\n⚠️  First run will require phone verification\n")

    print("Available examples:")
    print("1. Channel monitoring (crypto news)")
    print("2. Event-specific monitoring")
    print("3. Combined Telegram + arbitrage analysis")
    print("4. Real-time channel monitoring")

    choice = input("\nWhich example to run? (1-4): ").strip()

    if choice == "1":
        asyncio.run(example_1_channel_monitoring())
    elif choice == "2":
        asyncio.run(example_2_event_monitoring())
    elif choice == "3":
        asyncio.run(example_3_combined_analysis())
    elif choice == "4":
        asyncio.run(example_4_realtime_monitoring())
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
