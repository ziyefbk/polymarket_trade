"""
Robin Integration Example Script

This script demonstrates how to use Robin dark web intelligence
to enhance Polymarket arbitrage trading decisions.
"""
import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from src.analyzer.robin_intelligence import RobinIntelligenceAnalyzer, ROBIN_AVAILABLE
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.api.polymarket_client import PolymarketClient


async def example_basic_search():
    """Example 1: Basic dark web intelligence search"""
    print("\n" + "="*80)
    print("Example 1: Basic Dark Web Intelligence Search")
    print("="*80)

    if not ROBIN_AVAILABLE:
        print("❌ Robin not available. Please install dependencies.")
        return

    analyzer = RobinIntelligenceAnalyzer(model="gpt-4o", threads=5)

    # Search for intelligence on a topic
    result = analyzer.search_intelligence(
        query="cryptocurrency exchange hacks 2024",
        save_output=True
    )

    if result["success"]:
        print(f"✓ Search completed successfully")
        print(f"  - Refined query: {result['refined_query']}")
        print(f"  - Total results: {result['num_results']}")
        print(f"  - Filtered results: {result['num_filtered']}")
        print(f"  - Scraped pages: {result['num_scraped']}")
        print(f"  - Report saved: {result['summary_file']}")
        print(f"\nSummary preview:")
        print(result['summary'][:500] + "...")
    else:
        print(f"✗ Search failed: {result['error']}")


async def example_event_analysis():
    """Example 2: Analyze intelligence for specific Polymarket event"""
    print("\n" + "="*80)
    print("Example 2: Event-Specific Intelligence Analysis")
    print("="*80)

    if not ROBIN_AVAILABLE:
        print("❌ Robin not available.")
        return

    analyzer = RobinIntelligenceAnalyzer(model="gpt-4o")

    # Example Polymarket event titles
    events = [
        "Will there be a major cyberattack on US infrastructure in 2024?",
        "Will Bitcoin reach $100,000 in 2024?",
        "Will Trump win the 2024 presidential election?"
    ]

    for event_title in events[:1]:  # Just analyze first one for demo
        print(f"\nAnalyzing: {event_title}")

        intel = analyzer.analyze_event_intelligence(event_title)

        if intel and intel["success"]:
            print(f"✓ Intelligence gathered")
            print(f"  - Scraped {intel['num_scraped']} pages")
            print(f"  - Report: {intel['summary_file']}")
        else:
            print(f"✗ Failed to gather intelligence")


async def example_enhanced_arbitrage():
    """Example 3: Combine arbitrage detection with intelligence gathering"""
    print("\n" + "="*80)
    print("Example 3: Enhanced Arbitrage Detection with Intelligence")
    print("="*80)

    if not ROBIN_AVAILABLE:
        print("❌ Robin not available.")
        return

    # Initialize components
    robin = RobinIntelligenceAnalyzer(model="gpt-4o")

    async with PolymarketClient() as client:
        detector = IntraMarketArbitrageDetector(client)

        print("Scanning for arbitrage opportunities...")
        opportunities = await detector.scan_all_markets()

        if not opportunities:
            print("No arbitrage opportunities found")
            return

        print(f"Found {len(opportunities)} opportunities")

        # Analyze top 2 opportunities with intelligence
        for i, opp in enumerate(opportunities[:2], 1):
            print(f"\n--- Opportunity {i}/{min(2, len(opportunities))} ---")
            print(f"Event: {opp.event_title}")
            print(f"Spread: {opp.spread:.2%}")
            print(f"Net profit: {opp.net_profit_pct:.2%}")
            print(f"Confidence: {opp.confidence_score:.2f}")

            print("\nSearching dark web for related intelligence...")
            intel = robin.analyze_event_intelligence(opp.event_title)

            if intel and intel["success"]:
                print(f"✓ Found {intel['num_scraped']} intelligence sources")
                print(f"  Report: {intel['summary_file']}")

                # Here you could add logic to:
                # - Adjust confidence score based on intelligence
                # - Decide whether to trade based on intel findings
                # - Calculate position size adjustment
            else:
                print("✗ No intelligence found")

            # Rate limiting between searches
            if i < min(2, len(opportunities)):
                print("\nWaiting 5s before next search...")
                await asyncio.sleep(5)


async def example_batch_analysis():
    """Example 4: Batch intelligence analysis for multiple events"""
    print("\n" + "="*80)
    print("Example 4: Batch Intelligence Analysis")
    print("="*80)

    if not ROBIN_AVAILABLE:
        print("❌ Robin not available.")
        return

    analyzer = RobinIntelligenceAnalyzer(model="gpt-4o")

    event_titles = [
        "Will Russia use nuclear weapons in 2024?",
        "Will there be a major data breach at a Fortune 500 company?",
        "Will cryptocurrency regulations pass in the US in 2024?"
    ]

    print(f"Analyzing {len(event_titles)} events...")
    reports = analyzer.batch_analyze_events(event_titles, max_concurrent=1)

    print(f"\nBatch analysis complete!")
    for i, report in enumerate(reports, 1):
        if report and report.get("success"):
            print(f"{i}. {report['query']}: ✓ Success ({report['num_scraped']} sources)")
        else:
            print(f"{i}. {report['query']}: ✗ Failed")


async def main():
    """Run all examples"""
    print("\n" + "="*80)
    print("Robin Intelligence Integration Examples")
    print("="*80)

    if not ROBIN_AVAILABLE:
        print("\n❌ Robin is not available!")
        print("Please ensure:")
        print("1. robin_signals directory exists")
        print("2. Robin dependencies are installed: cd robin_signals && pip install -r requirements.txt")
        print("3. Tor is running: sudo service tor start")
        print("4. LLM API key is configured in robin_signals/.env")
        return

    print("\n⚠️  WARNING: These examples will make LLM API calls (costs money)")
    print("⚠️  WARNING: Dark web searches may take several minutes each")
    print("\nAvailable examples:")
    print("1. Basic dark web search")
    print("2. Event-specific intelligence")
    print("3. Enhanced arbitrage with intelligence")
    print("4. Batch event analysis")

    choice = input("\nWhich example to run? (1-4, or 'all'): ").strip()

    if choice == "1":
        await example_basic_search()
    elif choice == "2":
        await example_event_analysis()
    elif choice == "3":
        await example_enhanced_arbitrage()
    elif choice == "4":
        await example_batch_analysis()
    elif choice.lower() == "all":
        await example_basic_search()
        await example_event_analysis()
        await example_enhanced_arbitrage()
        await example_batch_analysis()
    else:
        print("Invalid choice")


if __name__ == "__main__":
    asyncio.run(main())
