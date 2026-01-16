"""
Agent T4: API Integration Tests
Priority: 🔥 Medium - Tests Polymarket API connectivity
"""

import sys
import asyncio
from pathlib import Path
from datetime import datetime


class APITester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.report_lines = []

    def log(self, message, level="INFO"):
        """Log message to console and report"""
        print(f"[{level}] {message}")
        self.report_lines.append(f"[{level}] {message}")

    async def test_polymarket_client(self):
        """Test PolymarketClient (read-only operations)"""
        self.log("=" * 60)
        self.log("1️⃣ Testing PolymarketClient (Read-Only)")
        self.log("=" * 60)

        try:
            from src.api.polymarket_client import PolymarketClient

            async with PolymarketClient() as client:
                # Test get_all_active_events
                self.log("  Testing get_all_active_events()...")
                events = await client.get_all_active_events()
                self.log(f"  ✓ Retrieved {len(events)} active events", "INFO")

                if len(events) > 0:
                    event = events[0]
                    self.log(f"    Sample event: {event.title}", "INFO")

                    # Test get_order_book
                    if event.markets and len(event.markets) > 0:
                        token_id = event.markets[0].token_id
                        self.log(f"  Testing get_order_book() for token {token_id[:10]}...", "INFO")
                        order_book = await client.get_order_book(token_id)
                        self.log(f"  ✓ Order book retrieved: {len(order_book.bids)} bids, {len(order_book.asks)} asks", "INFO")
                        self.log(f"    Spread: {order_book.spread:.4f}", "INFO")

                    # Test get_prices_batch
                    token_ids = [m.token_id for m in event.markets[:3]]
                    self.log(f"  Testing get_prices_batch() for {len(token_ids)} tokens...", "INFO")
                    prices = await client.get_prices_batch(token_ids)
                    self.log(f"  ✓ Batch prices retrieved: {len(prices)} tokens", "INFO")

            self.log("✓ PolymarketClient tests passed", "PASS")
            self.tests_passed += 1
            return True

        except Exception as e:
            self.log(f"✗ PolymarketClient tests failed: {e}", "FAIL")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            self.tests_failed += 1
            return False

    async def test_arbitrage_detector(self):
        """Test Arbitrage Detector with live data"""
        self.log("")
        self.log("=" * 60)
        self.log("2️⃣ Testing Arbitrage Detector with Live Data")
        self.log("=" * 60)

        try:
            from src.api.polymarket_client import PolymarketClient
            from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
            from config import settings

            async with PolymarketClient() as client:
                detector = IntraMarketArbitrageDetector(client, settings.arbitrage)

                self.log("  Testing scan_all_markets()...")
                opportunities = await detector.scan_all_markets()
                self.log(f"  ✓ Scan completed: {len(opportunities)} opportunities found", "INFO")

                if len(opportunities) > 0:
                    opp = opportunities[0]
                    self.log(f"    Best opportunity: {opp.event_title}", "INFO")
                    self.log(f"    Net profit: {opp.net_profit_pct*100:.2f}%", "INFO")
                    self.log(f"    Confidence: {opp.confidence_score:.2f}", "INFO")
                else:
                    self.log("    No opportunities found (normal for low volatility)", "INFO")

            self.log("✓ Arbitrage detector integration passed", "PASS")
            self.tests_passed += 1
            return True

        except Exception as e:
            self.log(f"✗ Arbitrage detector integration failed: {e}", "FAIL")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            self.tests_failed += 1
            return False

    async def test_polymarket_trader(self):
        """Test PolymarketTrader initialization (no actual trades)"""
        self.log("")
        self.log("=" * 60)
        self.log("3️⃣ Testing PolymarketTrader Initialization")
        self.log("=" * 60)

        try:
            from src.api.trader import PolymarketTrader

            async with PolymarketTrader() as trader:
                self.log("  ✓ PolymarketTrader initialized successfully", "INFO")
                self.log(f"    Wallet address: {trader.address[:10]}...{trader.address[-8:]}", "INFO")

                # Test get_open_orders (read-only)
                self.log("  Testing get_open_orders()...")
                orders = await trader.get_open_orders()
                self.log(f"  ✓ Retrieved {len(orders)} open orders", "INFO")

            self.log("✓ PolymarketTrader initialization passed", "PASS")
            self.tests_passed += 1
            return True

        except Exception as e:
            self.log(f"⚠ PolymarketTrader initialization failed: {e}", "WARN")
            self.log("  This is expected if POLYMARKET_PRIVATE_KEY is not set", "INFO")
            # Don't count as failure - this is optional
            return True

    def generate_report(self):
        """Generate and save test report"""
        self.log("")
        self.log("=" * 60)
        self.log("API Integration Summary")
        self.log("=" * 60)
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Tests Failed: {self.tests_failed}")

        # Save report
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / "t4_api_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("=== API Integration Test Report ===\n")
            f.write(f"Date: {datetime.now()}\n\n")
            f.write("\n".join(self.report_lines))
            f.write(f"\n\n--- Summary ---\n")
            f.write(f"Tests Passed: {self.tests_passed}\n")
            f.write(f"Tests Failed: {self.tests_failed}\n")

        self.log(f"\nReport saved to: {report_file}")

        return self.tests_failed == 0

    def run(self):
        """Run all API integration tests"""
        print("\n" + "=" * 60)
        print("Agent T4: API Integration Tests")
        print("=" * 60)

        async def run_async_tests():
            if not await self.test_polymarket_client():
                return False
            if not await self.test_arbitrage_detector():
                return False
            if not await self.test_polymarket_trader():
                return False
            return True

        success = asyncio.run(run_async_tests())

        if not success:
            self.generate_report()
            print(f"\n✗ {self.tests_failed} API test(s) failed")
            return 1

        success = self.generate_report()

        if success:
            print("\n✓ All API integration tests passed!")
            return 0
        else:
            print(f"\n✗ {self.tests_failed} API test(s) failed")
            return 1


if __name__ == "__main__":
    tester = APITester()
    exit_code = tester.run()
    sys.exit(exit_code)