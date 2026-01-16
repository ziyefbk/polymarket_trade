"""
On-Chain Intelligence Integration Examples

Demonstrates how to use blockchain monitoring for Polymarket trading signals.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.analyzer.onchain_intelligence import (
    OnChainIntelligenceAnalyzer,
    WEB3_AVAILABLE
)


async def example_1_recent_activity():
    """Example 1: Get recent on-chain activity"""
    print("\n" + "="*80)
    print("Example 1: Recent On-Chain Activity (Last 24 Hours)")
    print("="*80)

    if not WEB3_AVAILABLE:
        print("❌ Web3 not available. Install: pip install web3")
        return

    try:
        # Initialize analyzer
        analyzer = OnChainIntelligenceAnalyzer(
            usdc_threshold=10000  # Track transactions >= $10k
        )

        print("\nAnalyzing Polygon blockchain...")
        print("This may take 1-2 minutes depending on network activity...")

        # Get last 24 hours of activity
        report = await analyzer.get_recent_activity(
            hours=24,
            min_amount=10000  # Only large transactions
        )

        if report:
            # Print detailed report
            analyzer.print_report(report)

            # Trading signal interpretation
            print("\n" + "="*80)
            print("TRADING SIGNAL INTERPRETATION")
            print("="*80)

            # Net flow (deposits - withdrawals)
            deposit_volume = sum(tx.value for tx in report.large_deposits)
            withdrawal_volume = sum(tx.value for tx in report.large_withdrawals)
            net_flow = deposit_volume - withdrawal_volume

            print(f"\nNet Flow Analysis:")
            print(f"  Total Deposits: ${deposit_volume:,.2f}")
            print(f"  Total Withdrawals: ${withdrawal_volume:,.2f}")
            print(f"  Net Flow: ${net_flow:,.2f}")

            if net_flow > 100000:
                print("\n📈 BULLISH: Large net inflow (>${100k:,})")
                print("   → Market participants are adding capital")
            elif net_flow < -100000:
                print("\n📉 BEARISH: Large net outflow (<-${100k:,})")
                print("   → Market participants are withdrawing")
            else:
                print("\n➖ NEUTRAL: Balanced flows")

            # Whale activity
            whale_pct = (report.whale_volume / report.total_volume) * 100
            print(f"\nWhale Activity:")
            print(f"  Whale Volume: {whale_pct:.1f}% of total")

            if whale_pct > 70:
                print("   ⚠️  HIGH: Whales dominating (>70%)")
                print("   → Follow whale movements carefully")
            elif whale_pct > 40:
                print("   📊 MODERATE: Significant whale presence (40-70%)")
            else:
                print("   👥 LOW: Retail-driven market (<40%)")

        else:
            print("No activity data available")

    except Exception as e:
        print(f"❌ Error: {e}")


async def example_2_whale_tracking():
    """Example 2: Track whale wallets"""
    print("\n" + "="*80)
    print("Example 2: Whale Wallet Tracking")
    print("="*80)

    if not WEB3_AVAILABLE:
        print("❌ Web3 not available.")
        return

    try:
        analyzer = OnChainIntelligenceAnalyzer()

        print("\nIdentifying whale wallets from last 48 hours...")

        report = await analyzer.get_recent_activity(hours=48, min_amount=5000)

        if report and report.top_whales:
            print(f"\nFound {len(report.top_whales)} whale wallets")

            print("\n" + "-"*80)
            print("TOP 10 WHALE WALLETS")
            print("-"*80)

            for i, whale in enumerate(report.top_whales[:10], 1):
                print(f"\n{i}. Wallet: {whale.address}")
                print(f"   Total Volume: ${whale.total_volume:,.2f}")
                print(f"   Transactions: {whale.transaction_count}")
                print(f"   Avg Size: ${whale.avg_transaction_size:,.2f}")
                print(f"   Activity Period: {whale.first_seen} to {whale.last_seen}")

                # Check current balance
                balance = await analyzer.get_usdc_balance(whale.address)
                print(f"   Current USDC Balance: ${balance:,.2f}")

            # Find the most active whale
            most_active = max(report.top_whales, key=lambda w: w.transaction_count)
            print(f"\n🐋 Most Active Whale:")
            print(f"   {most_active.address}")
            print(f"   {most_active.transaction_count} transactions in 48 hours")
            print(f"   Average ${most_active.avg_transaction_size:,.0f} per transaction")

        else:
            print("No whale activity detected")

    except Exception as e:
        print(f"❌ Error: {e}")


async def example_3_realtime_monitoring():
    """Example 3: Real-time wallet monitoring"""
    print("\n" + "="*80)
    print("Example 3: Real-Time Wallet Monitoring")
    print("="*80)

    if not WEB3_AVAILABLE:
        print("❌ Web3 not available.")
        return

    # Example whale wallet (replace with actual whale address)
    whale_address = "0x1234567890123456789012345678901234567890"

    print(f"\nMonitoring whale wallet: {whale_address}")
    print("Press Ctrl+C to stop...\n")

    try:
        analyzer = OnChainIntelligenceAnalyzer()

        # Define callback for new transactions
        async def on_transaction(tx):
            print(f"\n🔔 WHALE ALERT!")
            print(f"   Amount: ${tx.value:,.2f} USDC")
            print(f"   Type: {tx.transaction_type}")
            print(f"   From: {tx.from_address[:10]}...{tx.from_address[-8:]}")
            print(f"   To: {tx.to_address[:10]}...{tx.to_address[-8:]}")
            print(f"   Tx Hash: {tx.tx_hash}")
            print(f"   Time: {tx.timestamp}")

            # Trading signal
            if tx.transaction_type == "DEPOSIT" and tx.value > 50000:
                print("   📈 SIGNAL: Large deposit - potential buying pressure")
            elif tx.transaction_type == "WITHDRAW" and tx.value > 50000:
                print("   📉 SIGNAL: Large withdrawal - potential selling pressure")

        # Start monitoring
        await analyzer.track_wallet_in_realtime(
            wallet_address=whale_address,
            callback=on_transaction,
            poll_interval=10  # Check every 10 seconds
        )

    except KeyboardInterrupt:
        print("\n\nMonitoring stopped by user")
    except Exception as e:
        print(f"❌ Error: {e}")


async def example_4_combined_analysis():
    """Example 4: Combine on-chain with arbitrage detection"""
    print("\n" + "="*80)
    print("Example 4: Combined On-Chain + Arbitrage Analysis")
    print("="*80)

    if not WEB3_AVAILABLE:
        print("❌ Web3 not available.")
        return

    try:
        from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
        from src.api.polymarket_client import PolymarketClient

        # Initialize analyzers
        onchain = OnChainIntelligenceAnalyzer()

        print("\n[1/2] Getting on-chain intelligence...")
        onchain_report = await onchain.get_recent_activity(hours=24, min_amount=10000)

        if not onchain_report:
            print("No on-chain data available")
            return

        print(f"✓ Found {onchain_report.total_transactions} transactions")
        print(f"  Total Volume: ${onchain_report.total_volume:,.2f}")
        print(f"  Whale Volume: ${onchain_report.whale_volume:,.2f}")

        print("\n[2/2] Scanning for arbitrage opportunities...")

        async with PolymarketClient() as client:
            detector = IntraMarketArbitrageDetector(client)
            opportunities = await detector.scan_all_markets()

        if not opportunities:
            print("No arbitrage opportunities found")
            return

        print(f"✓ Found {len(opportunities)} opportunities")

        # Enhance opportunities with on-chain data
        print("\n" + "="*80)
        print("ENHANCED ANALYSIS")
        print("="*80)

        for i, opp in enumerate(opportunities[:5], 1):
            print(f"\n--- Opportunity #{i}: {opp.event_title} ---")
            print(f"Spread: {opp.spread:.2%}")
            print(f"Net Profit: {opp.net_profit_pct:.2%}")
            print(f"Base Confidence: {opp.confidence_score:.2f}")

            # On-chain enhancement
            print(f"\n📊 On-Chain Context:")

            # Net flow signal
            deposit_vol = sum(tx.value for tx in onchain_report.large_deposits)
            withdraw_vol = sum(tx.value for tx in onchain_report.large_withdrawals)
            net_flow = deposit_vol - withdraw_vol

            if net_flow > 50000:
                onchain_boost = 0.1
                print(f"  ✓ Positive net flow: ${net_flow:,.0f}")
                print(f"    Confidence boost: +{onchain_boost:.2f}")
            elif net_flow < -50000:
                onchain_boost = -0.05
                print(f"  ⚠️  Negative net flow: ${net_flow:,.0f}")
                print(f"    Confidence penalty: {onchain_boost:.2f}")
            else:
                onchain_boost = 0
                print(f"  → Neutral net flow: ${net_flow:,.0f}")

            # Whale activity signal
            whale_pct = (onchain_report.whale_volume / onchain_report.total_volume) * 100
            if whale_pct > 60:
                whale_boost = 0.05
                print(f"  ✓ High whale activity: {whale_pct:.1f}%")
                print(f"    Confidence boost: +{whale_boost:.2f}")
            else:
                whale_boost = 0

            # Enhanced confidence
            enhanced_confidence = min(
                opp.confidence_score + onchain_boost + whale_boost,
                1.0
            )

            print(f"\n🎯 ENHANCED CONFIDENCE: {enhanced_confidence:.2f}")
            print(f"   Original: {opp.confidence_score:.2f}")
            print(f"   On-Chain Boost: {onchain_boost:+.2f}")
            print(f"   Whale Boost: {whale_boost:+.2f}")

            if enhanced_confidence > 0.75:
                print("\n✅ STRONG SIGNAL: High conviction trade")
            elif enhanced_confidence > 0.6:
                print("\n⚠️  MODERATE SIGNAL: Proceed with caution")
            else:
                print("\n❌ WEAK SIGNAL: Skip this opportunity")

    except Exception as e:
        print(f"❌ Error: {e}")


def main():
    """Run examples"""
    print("\n" + "="*80)
    print("On-Chain Intelligence Integration Examples")
    print("="*80)

    if not WEB3_AVAILABLE:
        print("\n❌ Web3 not available!")
        print("Install required package:")
        print("  pip install web3")
        return

    print("\n⚠️  WARNING: These examples will query Polygon blockchain")
    print("⚠️  May take 1-2 minutes depending on network activity\n")

    print("Available examples:")
    print("1. Recent on-chain activity (24 hours)")
    print("2. Whale wallet tracking")
    print("3. Real-time wallet monitoring")
    print("4. Combined on-chain + arbitrage analysis")

    choice = input("\nWhich example to run? (1-4): ").strip()

    if choice == "1":
        asyncio.run(example_1_recent_activity())
    elif choice == "2":
        asyncio.run(example_2_whale_tracking())
    elif choice == "3":
        asyncio.run(example_3_realtime_monitoring())
    elif choice == "4":
        asyncio.run(example_4_combined_analysis())
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
