#!/bin/bash
# Agent T3: Database Integration Tests
# Priority: 🔥 High - Tests database layer functionality

set -e  # Exit immediately if any command fails

OUTPUT_DIR="test_reports"
REPORT_FILE="$OUTPUT_DIR/t3_database_report.txt"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=============================================="
echo "Agent T3: Database Integration Tests"
echo "=============================================="
echo ""

mkdir -p "$OUTPUT_DIR"

# Start report
echo "=== Database Integration Test Report ===" > "$REPORT_FILE"
echo "Date: $(date)" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

TESTS_PASSED=0
TESTS_FAILED=0

# 1. Database Migration
echo "1️⃣ Testing Database Migrations"
echo "--- Database Migrations ---" >> "$REPORT_FILE"

if alembic upgrade head 2>&1 | tee -a "$REPORT_FILE"; then
    echo -e "${GREEN}✓ Database migrations applied successfully${NC}"
    echo "[PASS] Database migrations" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Database migration failed${NC}"
    echo "[FAIL] Database migrations" >> "$REPORT_FILE"
    ((TESTS_FAILED++))
fi

echo "" >> "$REPORT_FILE"

# 2. Database Connectivity
echo ""
echo "2️⃣ Testing Database Connectivity"
echo "--- Database Connectivity ---" >> "$REPORT_FILE"

python << EOF 2>&1 | tee -a "$REPORT_FILE"
import asyncio
from src.utils.database import DatabaseManager

async def test_connection():
    db = DatabaseManager()
    try:
        await db.initialize()
        print("✓ Database connection successful")
        await db.close()
        return True
    except Exception as e:
        print(f"✗ Database connection failed: {e}")
        return False

if asyncio.run(test_connection()):
    exit(0)
else:
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Database connectivity test passed${NC}"
    echo "[PASS] Database connectivity" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Database connectivity test failed${NC}"
    echo "[FAIL] Database connectivity" >> "$REPORT_FILE"
    ((TESTS_FAILED++))
fi

echo "" >> "$REPORT_FILE"

# 3. CRUD Operations
echo ""
echo "3️⃣ Testing CRUD Operations"
echo "--- CRUD Operations ---" >> "$REPORT_FILE"

python << EOF 2>&1 | tee -a "$REPORT_FILE"
import asyncio
from datetime import datetime
from src.utils.database import DatabaseManager
from src.types import ExecutionResult, ArbitrageOpportunity

async def test_crud():
    db = DatabaseManager()
    await db.initialize()

    try:
        # Create test opportunity
        opp = ArbitrageOpportunity(
            opportunity_id="test-001",
            event_id="event-001",
            event_title="Test Event",
            yes_token_id="token-yes",
            yes_price=0.52,
            yes_liquidity=10000,
            no_token_id="token-no",
            no_price=0.50,
            no_liquidity=10000,
            price_sum=1.02,
            spread=0.02,
            arbitrage_type="OVERPRICED",
            expected_profit_pct=0.015,
            expected_profit_usd=15.0,
            estimated_fees=5.0,
            estimated_slippage=2.0,
            net_profit_pct=0.008,
            is_executable=True,
            required_capital=1000.0,
            confidence_score=0.85,
            detected_at=datetime.utcnow(),
            valid_until=datetime.utcnow()
        )

        # Create test result
        result = ExecutionResult(
            success=True,
            opportunity_id="test-001",
            yes_order_id="order-yes-001",
            no_order_id="order-no-001",
            yes_filled_size=100.0,
            no_filled_size=100.0,
            yes_avg_price=0.52,
            no_avg_price=0.50,
            total_cost=1020.0,
            actual_profit_usd=8.0,
            execution_time_ms=1500,
            both_legs_filled=True
        )

        # Test save_trade
        print("Testing save_trade()...")
        trade = await db.save_trade(result, opp)
        print(f"✓ Trade saved with ID: {trade.id}")

        # Test create_position
        print("Testing create_position()...")
        position = await db.create_position(
            trade_id=trade.id,
            token_id=opp.yes_token_id,
            event_id=opp.event_id,
            event_title=opp.event_title,
            side="YES",
            size=100.0,
            entry_price=0.52,
            cost_basis=520.0
        )
        print(f"✓ Position created with ID: {position.id}")

        # Test get_open_positions
        print("Testing get_open_positions()...")
        positions = await db.get_open_positions()
        print(f"✓ Retrieved {len(positions)} open positions")

        # Test get_daily_loss
        print("Testing get_daily_loss()...")
        daily_loss = await db.get_daily_loss()
        print(f"✓ Daily loss: \${daily_loss:.2f}")

        # Test calculate_performance_metrics
        print("Testing calculate_performance_metrics()...")
        metrics = await db.calculate_performance_metrics(days=30)
        print(f"✓ Performance metrics calculated: {metrics['total_trades']} trades")

        await db.close()
        print("\n✓ All CRUD operations passed")
        return True

    except Exception as e:
        print(f"\n✗ CRUD test failed: {e}")
        await db.close()
        return False

if asyncio.run(test_crud()):
    exit(0)
else:
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ CRUD operations test passed${NC}"
    echo "[PASS] CRUD operations" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ CRUD operations test failed${NC}"
    echo "[FAIL] CRUD operations" >> "$REPORT_FILE"
    ((TESTS_FAILED++))
fi

echo "" >> "$REPORT_FILE"

# 4. Performance Metrics
echo ""
echo "4️⃣ Testing Performance Metrics Calculation"
echo "--- Performance Metrics ---" >> "$REPORT_FILE"

python << EOF 2>&1 | tee -a "$REPORT_FILE"
import asyncio
from src.utils.database import DatabaseManager

async def test_metrics():
    db = DatabaseManager()
    await db.initialize()

    try:
        metrics = await db.calculate_performance_metrics(days=1)

        required_keys = [
            'total_trades', 'winning_trades', 'losing_trades',
            'win_rate', 'net_profit', 'avg_profit_per_trade',
            'sharpe_ratio', 'max_drawdown'
        ]

        for key in required_keys:
            if key not in metrics:
                print(f"✗ Missing metric: {key}")
                await db.close()
                return False

        print("✓ All required metrics present")
        print(f"  Total Trades: {metrics['total_trades']}")
        print(f"  Win Rate: {metrics['win_rate']:.1f}%")
        print(f"  Net Profit: \${metrics['net_profit']:.2f}")

        await db.close()
        return True

    except Exception as e:
        print(f"✗ Metrics test failed: {e}")
        await db.close()
        return False

if asyncio.run(test_metrics()):
    exit(0)
else:
    exit(1)
EOF

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ Performance metrics test passed${NC}"
    echo "[PASS] Performance metrics" >> "$REPORT_FILE"
    ((TESTS_PASSED++))
else
    echo -e "${RED}✗ Performance metrics test failed${NC}"
    echo "[FAIL] Performance metrics" >> "$REPORT_FILE"
    ((TESTS_FAILED++))
fi

echo "" >> "$REPORT_FILE"

# Summary
echo ""
echo "=============================================="
echo "Database Integration Summary"
echo "=============================================="
echo "Tests Passed: $TESTS_PASSED"
echo "Tests Failed: $TESTS_FAILED"
echo ""

echo "--- Summary ---" >> "$REPORT_FILE"
echo "Tests Passed: $TESTS_PASSED" >> "$REPORT_FILE"
echo "Tests Failed: $TESTS_FAILED" >> "$REPORT_FILE"
echo "" >> "$REPORT_FILE"

if [ $TESTS_FAILED -eq 0 ]; then
    echo -e "${GREEN}✓ All database tests passed!${NC}"
    echo "[RESULT] SUCCESS - Database layer is functional" >> "$REPORT_FILE"
    exit 0
else
    echo -e "${RED}✗ $TESTS_FAILED database test(s) failed${NC}"
    echo "[RESULT] FAILURE - Database has $TESTS_FAILED issue(s)" >> "$REPORT_FILE"
    exit 1
fi