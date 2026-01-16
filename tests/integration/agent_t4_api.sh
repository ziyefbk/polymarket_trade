#!/bin/bash
# Agent T4: API Integration Tests
# Priority: 🔥 Medium - Tests Polymarket API connectivity

set -e  # Exit immediately if any command fails

OUTPUT_DIR="test_reports"
REPORT_FILE="$OUTPUT_DIR/t4_api_report.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Agent T4: API Integration Tests"
echo "=============================================="
echo ""

mkdir -p "$OUTPUT_DIR"

# Start report
echo "=== API Integration Test Report ===" > "$REPORT_FILE"
echo "Date: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

TESTS_PASSED=0
TESTS_FAILED=0

# 1. PolymarketClient Tests
echo "1️⃣ Testing PolymarketClient (Read-Only)"
echo "--- PolymarketClient Tests ---" >> "$REPORT_FILE"

python << EOF 2>&1 | tee -a "$REPORT_FILE"
import asyncio
from src.api.polymarket_client import PolymarketClient

async def test_client():
    async with PolymarketClient() as client:
        try:
            # Test get_all_active_events
            print("Testing get_all_active_events()...")
            events = await client.get_all_active_events()
            print(f"✓ Retrieved {len(events)} active events")

            if len(events) > 0:
                event = events[0]
                print(f"  Sample event: {event.title}")

                # Test get_order_book
                if event.markets and len(event.markets) > 0:
                    token_id = event.markets[0].token_id
                    print(f"Testing get_order_book() for token {token_id}...")
                    order_book = await client.get_order_book(token_id)
                    print(f"✓ Order book retrieved: {len(order_book.bids)} bids, {len(order_book.asks)} asks")
                    print(f"  Spread: {order_book.spread:.4f}")

                # Test get_prices_batch
                token_ids = [m.token_id for m in event.markets[:3]]
                print(f"Testing get_prices_batch() for {len(token_ids)} tokens...")
                prices = await client.get_prices_batch(token_ids)
                print(f"✓ Batch prices retrieved: {len(prices)} tokens")

            return True

        except Exception as e:
            print(f"✗ PolymarketClient test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if asyncio.run(test_client()):
    exit(0)
else:
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PolymarketClient tests passed${NC}"
    echo "[PASS] PolymarketClient" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ PolymarketClient tests failed${NC}"
    echo "[FAIL] PolymarketClient" >> "$REPORT_FILE"
    ((TESTS_FAILED++))
fi

echo "" >> "$REPORT_FILE"

# 2. Arbitrage Detector Integration
echo ""
echo "2️⃣ Testing Arbitrage Detector with Live Data"
echo "--- Arbitrage Detector Integration ---" >> "$REPORT_FILE"

python << EOF 2>&1 | tee -a "$REPORT_FILE"
import asyncio
from src.api.polymarket_client import PolymarketClient
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from config import settings

async def test_detector():
    async with PolymarketClient() as client:
        try:
            detector = IntraMarketArbitrageDetector(client, settings.arbitrage)

            print("Testing scan_all_markets()...")
            opportunities = await detector.scan_all_markets()
            print(f"✓ Scan completed: {len(opportunities)} opportunities found")

            if len(opportunities) > 0:
                opp = opportunities[0]
                print(f"  Best opportunity: {opp.event_title}")
                print(f"  Net profit: {opp.net_profit_pct*100:.2f}%")
                print(f"  Confidence: {opp.confidence_score:.2f}")

            return True

        except Exception as e:
            print(f"✗ Arbitrage detector test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

if asyncio.run(test_detector()):
    exit(0)
else:
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Arbitrage detector integration passed${NC}"
    echo "[PASS] Arbitrage Detector Integration" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Arbitrage detector integration failed${NC}"
    echo "[FAIL] Arbitrage Detector Integration" >> "$REPORT_FILE"
    ((TESTS_FAILED++))
fi

echo "" >> "$REPORT_FILE"

# 3. PolymarketTrader Initialization (No actual trades)
echo ""
echo "3️⃣ Testing PolymarketTrader Initialization"
echo "--- PolymarketTrader Initialization ---" >> "$REPORT_FILE"

python << EOF 2>&1 | tee -a "$REPORT_FILE"
import asyncio
from src.api.trader import PolymarketTrader

async def test_trader():
    try:
        async with PolymarketTrader() as trader:
            print("✓ PolymarketTrader initialized successfully")
            print(f"  Wallet address: {trader.address[:10]}...{trader.address[-8:]}")

            # Test get_open_orders (read-only)
            print("Testing get_open_orders()...")
            orders = await trader.get_open_orders()
            print(f"✓ Retrieved {len(orders)} open orders")

            return True

    except Exception as e:
        print(f"✗ PolymarketTrader initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if asyncio.run(test_trader()):
    exit(0)
else:
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ PolymarketTrader initialization passed${NC}"
    echo "[PASS] PolymarketTrader Initialization" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
else
    echo -e "${YELLOW}⚠ PolymarketTrader initialization failed (may be expected if no private key)${NC}"
    echo "[WARN] PolymarketTrader Initialization" >> "$REPORT_FILE"
fi

echo "" >> "$REPORT_FILE"

# Summary
echo ""
echo "=============================================="
echo "API Integration Summary"
echo "=============================================="
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

echo "--- Summary ---" >> "$REPORT_FILE"
echo "Tests Passed: $TESTS_PASSED" >> "$REPORT_FILE"
echo "Tests Failed: $TESTS_FAILED" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All API integration tests passed!${NC}"
    echo "[RESULT] SUCCESS - API connectivity is functional" >> "$REPORT_FILE"
    exit 0
else
    echo -e "${RED}✗ $TESTS_FAILED API test(s) failed${NC}"
    echo "[RESULT] FAILURE - API has $TESTS_FAILED issue(s)" >> "$REPORT_FILE"
    exit 1
fi