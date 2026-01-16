"""
Agent T3: Database Integration Tests
Priority: 🔥 High - Tests database layer functionality
"""

import sys
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime


class DatabaseTester:
    def __init__(self):
        self.tests_passed = 0
        self.tests_failed = 0
        self.report_lines = []

    def log(self, message, level="INFO"):
        """Log message to console and report"""
        print(f"[{level}] {message}")
        self.report_lines.append(f"[{level}] {message}")

    def test_migrations(self):
        """Test database migrations with alembic"""
        self.log("=" * 60)
        self.log("1️⃣ Testing Database Migrations")
        self.log("=" * 60)

        try:
            result = subprocess.run(
                ["alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                timeout=60
            )

            self.report_lines.append(result.stdout)

            if result.returncode == 0:
                self.log("✓ Database migrations applied successfully", "PASS")
                self.tests_passed += 1
                return True
            else:
                self.log(f"✗ Database migration failed", "FAIL")
                self.log(f"  Error: {result.stderr}", "ERROR")
                self.tests_failed += 1
                return False

        except Exception as e:
            self.log(f"✗ Migration error: {e}", "FAIL")
            self.tests_failed += 1
            return False

    async def test_connectivity(self):
        """Test database connectivity"""
        self.log("")
        self.log("=" * 60)
        self.log("2️⃣ Testing Database Connectivity")
        self.log("=" * 60)

        try:
            from src.utils.database import DatabaseManager

            db = DatabaseManager()
            await db.initialize()
            self.log("✓ Database connection successful", "PASS")
            await db.close()
            self.tests_passed += 1
            return True

        except Exception as e:
            self.log(f"✗ Database connection failed: {e}", "FAIL")
            self.tests_failed += 1
            return False

    async def test_crud_operations(self):
        """Test CRUD operations"""
        self.log("")
        self.log("=" * 60)
        self.log("3️⃣ Testing CRUD Operations")
        self.log("=" * 60)

        try:
            from src.utils.database import DatabaseManager
            from src.types import ExecutionResult, ArbitrageOpportunity

            db = DatabaseManager()
            await db.initialize()

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
            self.log("  Testing save_trade()...")
            trade = await db.save_trade(result, opp)
            self.log(f"  ✓ Trade saved with ID: {trade.id}", "INFO")

            # Test create_position
            self.log("  Testing create_position()...")
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
            self.log(f"  ✓ Position created with ID: {position.id}", "INFO")

            # Test get_open_positions
            self.log("  Testing get_open_positions()...")
            positions = await db.get_open_positions()
            self.log(f"  ✓ Retrieved {len(positions)} open positions", "INFO")

            # Test get_daily_loss
            self.log("  Testing get_daily_loss()...")
            daily_loss = await db.get_daily_loss()
            self.log(f"  ✓ Daily loss: ${daily_loss:.2f}", "INFO")

            # Test calculate_performance_metrics
            self.log("  Testing calculate_performance_metrics()...")
            metrics = await db.calculate_performance_metrics(days=30)
            self.log(f"  ✓ Performance metrics calculated: {metrics['total_trades']} trades", "INFO")

            await db.close()

            self.log("✓ All CRUD operations passed", "PASS")
            self.tests_passed += 1
            return True

        except Exception as e:
            self.log(f"✗ CRUD operations failed: {e}", "FAIL")
            import traceback
            self.log(traceback.format_exc(), "ERROR")
            self.tests_failed += 1
            return False

    async def test_performance_metrics(self):
        """Test performance metrics calculation"""
        self.log("")
        self.log("=" * 60)
        self.log("4️⃣ Testing Performance Metrics Calculation")
        self.log("=" * 60)

        try:
            from src.utils.database import DatabaseManager

            db = DatabaseManager()
            await db.initialize()

            metrics = await db.calculate_performance_metrics(days=1)

            required_keys = [
                'total_trades', 'winning_trades', 'losing_trades',
                'win_rate', 'net_profit', 'avg_profit_per_trade',
                'sharpe_ratio', 'max_drawdown'
            ]

            for key in required_keys:
                if key not in metrics:
                    self.log(f"  ✗ Missing metric: {key}", "FAIL")
                    await db.close()
                    self.tests_failed += 1
                    return False

            self.log("  ✓ All required metrics present", "INFO")
            self.log(f"    Total Trades: {metrics['total_trades']}", "INFO")
            self.log(f"    Win Rate: {metrics['win_rate']:.1f}%", "INFO")
            self.log(f"    Net Profit: ${metrics['net_profit']:.2f}", "INFO")

            await db.close()

            self.log("✓ Performance metrics test passed", "PASS")
            self.tests_passed += 1
            return True

        except Exception as e:
            self.log(f"✗ Performance metrics test failed: {e}", "FAIL")
            self.tests_failed += 1
            return False

    def generate_report(self):
        """Generate and save test report"""
        self.log("")
        self.log("=" * 60)
        self.log("Database Integration Summary")
        self.log("=" * 60)
        self.log(f"Tests Passed: {self.tests_passed}")
        self.log(f"Tests Failed: {self.tests_failed}")

        # Save report
        report_dir = Path("test_reports")
        report_dir.mkdir(exist_ok=True)

        report_file = report_dir / "t3_database_report.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write("=== Database Integration Test Report ===\n")
            f.write(f"Date: {datetime.now()}\n\n")
            f.write("\n".join(self.report_lines))
            f.write(f"\n\n--- Summary ---\n")
            f.write(f"Tests Passed: {self.tests_passed}\n")
            f.write(f"Tests Failed: {self.tests_failed}\n")

        self.log(f"\nReport saved to: {report_file}")

        return self.tests_failed == 0

    def run(self):
        """Run all database tests"""
        print("\n" + "=" * 60)
        print("Agent T3: Database Integration Tests")
        print("=" * 60)

        # Run migrations
        if not self.test_migrations():
            self.generate_report()
            print("\n✗ Database migration failed, stopping tests")
            return 1

        # Run async tests
        async def run_async_tests():
            if not await self.test_connectivity():
                return False
            if not await self.test_crud_operations():
                return False
            if not await self.test_performance_metrics():
                return False
            return True

        success = asyncio.run(run_async_tests())

        if not success:
            self.generate_report()
            print(f"\n✗ {self.tests_failed} database test(s) failed")
            return 1

        success = self.generate_report()

        if success:
            print("\n✓ All database tests passed!")
            return 0
        else:
            print(f"\n✗ {self.tests_failed} database test(s) failed")
            return 1


if __name__ == "__main__":
    tester = DatabaseTester()
    exit_code = tester.run()
    sys.exit(exit_code)