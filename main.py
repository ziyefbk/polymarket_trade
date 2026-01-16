"""
Main Orchestrator for Polymarket Arbitrage System

This module coordinates all components:
- ArbitrageDetector: Scans markets for opportunities
- ArbitrageExecutor: Executes profitable trades
- DatabaseManager: Stores results and tracks performance
- Scheduler: Runs periodic scans

Usage:
    python main.py [--once] [--dry-run]

Options:
    --once: Run a single scan cycle and exit
    --dry-run: Detect opportunities but don't execute trades
"""
import asyncio
import signal
import sys
from datetime import datetime
from typing import Optional, List
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from config import settings
from src.api.polymarket_client import PolymarketClient
from src.api.trader import PolymarketTrader
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.strategy.arbitrage_executor import ArbitrageExecutor
from src.utils.database import DatabaseManager
from src.utils.kelly import calculate_kelly_fraction, calculate_position_size
from src.types.opportunities import ArbitrageOpportunity
from src.types.orders import ExecutionResult
from src.types.common import RiskLimitExceededError, ArbitrageError


class ArbitrageOrchestrator:
    """
    Main orchestrator that coordinates the arbitrage trading system.

    Responsibilities:
    - Initialize all components (detector, executor, database)
    - Schedule periodic market scans
    - Check risk limits before trading
    - Calculate optimal position sizes
    - Execute profitable opportunities
    - Handle graceful shutdown
    """

    def __init__(self, dry_run: bool = False):
        """
        Initialize the orchestrator

        Args:
            dry_run: If True, detect opportunities but don't execute trades
        """
        self.dry_run = dry_run
        self.cycle_count = 0
        self.running = False

        # Components (initialized in setup())
        self.client: Optional[PolymarketClient] = None
        self.trader: Optional[PolymarketTrader] = None
        self.detector: Optional[IntraMarketArbitrageDetector] = None
        self.executor: Optional[ArbitrageExecutor] = None
        self.db: Optional[DatabaseManager] = None
        self.scheduler: Optional[AsyncIOScheduler] = None

        # Statistics
        self.stats = {
            "total_opportunities": 0,
            "total_trades": 0,
            "successful_trades": 0,
            "failed_trades": 0,
            "total_profit_usd": 0.0,
        }

        logger.info(f"Orchestrator initialized (dry_run={dry_run})")

    async def setup(self) -> None:
        """
        Initialize all components and database connection

        Raises:
            ArbitrageError: If initialization fails
        """
        try:
            logger.info("Setting up arbitrage system...")

            # Create necessary directories
            Path("./logs").mkdir(exist_ok=True)
            Path("./data").mkdir(exist_ok=True)

            # Initialize database
            self.db = DatabaseManager(settings.database_url)
            await self.db.initialize()
            logger.info("Database initialized")

            # Initialize API clients
            self.client = PolymarketClient()
            logger.info("Polymarket client initialized")

            # Initialize trader (only if not dry-run)
            if not self.dry_run:
                if not settings.polymarket.private_key:
                    logger.warning("No private key configured - running in read-only mode")
                    self.dry_run = True
                else:
                    self.trader = PolymarketTrader()
                    logger.info("Polymarket trader initialized")
            else:
                logger.info("Running in dry-run mode (no trades will be executed)")

            # Initialize detector
            self.detector = IntraMarketArbitrageDetector(self.client)
            logger.info("Arbitrage detector initialized")

            # Initialize executor (only if not dry-run)
            if not self.dry_run and self.trader:
                self.executor = ArbitrageExecutor(self.trader, self.client)
                logger.info("Arbitrage executor initialized")

            # Initialize scheduler
            self.scheduler = AsyncIOScheduler()
            self.scheduler.add_job(
                self.scan_cycle,
                trigger=IntervalTrigger(seconds=settings.arbitrage.scan_interval),
                id="scan_cycle",
                name="Market Scan Cycle",
                max_instances=1,  # Prevent overlapping scans
            )

            logger.success("✓ All components initialized successfully")

        except Exception as e:
            logger.exception("Failed to initialize system")
            raise ArbitrageError(f"Setup failed: {e}") from e

    async def check_risk_limits(self) -> dict:
        """
        Check if trading is allowed based on risk limits

        Returns:
            Dictionary with risk check results:
            {
                "daily_loss_ok": bool,
                "position_count_ok": bool,
                "capital_available": bool,
                "can_trade": bool
            }

        Raises:
            ArbitrageError: If database access fails
        """
        try:
            # Get daily loss
            daily_loss = await self.db.get_daily_loss()
            daily_loss_ok = abs(daily_loss) < settings.trading.max_daily_loss

            # Get open positions count
            open_positions = await self.db.get_open_positions()
            position_count_ok = len(open_positions) < settings.trading.max_open_positions

            # Check capital availability (simplified - assumes we have capital)
            capital_available = True

            # Overall check
            can_trade = daily_loss_ok and position_count_ok and capital_available

            result = {
                "daily_loss_ok": daily_loss_ok,
                "position_count_ok": position_count_ok,
                "capital_available": capital_available,
                "can_trade": can_trade,
            }

            # Log warnings if limits exceeded
            if not daily_loss_ok:
                logger.warning(
                    f"Daily loss limit exceeded: ${abs(daily_loss):.2f} / ${settings.trading.max_daily_loss:.2f}"
                )
            if not position_count_ok:
                logger.warning(
                    f"Max open positions reached: {len(open_positions)} / {settings.trading.max_open_positions}"
                )

            return result

        except Exception as e:
            logger.exception("Failed to check risk limits")
            raise ArbitrageError(f"Risk check failed: {e}") from e

    def calculate_position_size(self, opportunity: ArbitrageOpportunity) -> float:
        """
        Calculate optimal position size for an opportunity using Kelly criterion

        Args:
            opportunity: The arbitrage opportunity to size

        Returns:
            Position size in USDC

        Raises:
            ValueError: If opportunity parameters are invalid
        """
        # Use Kelly criterion with conservative factor
        win_probability = opportunity.confidence_score
        profit_ratio = opportunity.net_profit_pct

        # Calculate Kelly fraction
        kelly_fraction = calculate_kelly_fraction(
            win_probability=win_probability,
            profit_ratio=profit_ratio,
            max_fraction=0.25,  # Max 25% of capital per trade
            conservative_factor=0.5,  # Half-Kelly for safety
        )

        # Calculate actual position size
        # For simplicity, assume we have max_position_size as our "capital"
        available_capital = settings.trading.max_position_size
        optimal_size = kelly_fraction * available_capital

        # Apply limits
        position_size = min(
            optimal_size,
            settings.trading.max_position_size,
            opportunity.required_capital,
        )

        # Round to 2 decimal places
        position_size = round(position_size, 2)

        logger.debug(
            f"Position sizing: Kelly={kelly_fraction:.2%}, "
            f"Optimal=${optimal_size:.2f}, "
            f"Final=${position_size:.2f}"
        )

        return position_size

    async def scan_cycle(self) -> None:
        """
        Execute a single scan cycle

        This is the main loop that:
        1. Checks risk limits
        2. Scans markets for opportunities
        3. Calculates position sizes
        4. Executes profitable trades
        5. Records results

        Raises:
            Does not raise - logs all errors internally
        """
        self.cycle_count += 1
        cycle_start = datetime.utcnow()

        logger.info("=" * 80)
        logger.info(f"Starting scan cycle #{self.cycle_count}")

        try:
            # Check risk limits
            risk_status = await self.check_risk_limits()
            if not risk_status["can_trade"]:
                logger.warning("Risk limits exceeded - skipping this cycle")
                return

            # Scan for opportunities
            logger.info("Scanning markets for arbitrage opportunities...")
            opportunities = await self.detector.scan_all_markets()

            self.stats["total_opportunities"] += len(opportunities)

            if not opportunities:
                logger.info("No arbitrage opportunities found")
                return

            logger.info(f"Found {len(opportunities)} opportunities")

            # Filter executable opportunities
            executable = [opp for opp in opportunities if opp.is_executable]
            logger.info(f"{len(executable)} opportunities are executable")

            if not executable:
                return

            # Process each opportunity
            trades_executed = 0
            for opp in executable:
                try:
                    # Log opportunity
                    logger.info(f"\nOpportunity: {opp.event_title}")
                    logger.info(
                        f"  Type: {opp.arbitrage_type}, "
                        f"Spread: {opp.spread:.2%}, "
                        f"Net profit: {opp.net_profit_pct:.2%}, "
                        f"Confidence: {opp.confidence_score:.2f}"
                    )

                    # Calculate position size
                    position_size = self.calculate_position_size(opp)
                    logger.info(f"  Position size: ${position_size:.2f}")

                    # Execute trade (or log if dry-run)
                    if self.dry_run or not self.executor:
                        logger.info("  [DRY RUN] Would execute trade here")
                        continue

                    # Execute the opportunity
                    logger.info(f"  Executing trade...")
                    result = await self.executor.execute_opportunity(opp, position_size)

                    # Record result
                    await self.db.save_trade(result, opp)

                    # Update statistics
                    self.stats["total_trades"] += 1
                    if result.success:
                        self.stats["successful_trades"] += 1
                        self.stats["total_profit_usd"] += result.actual_profit_usd
                        logger.success(
                            f"  ✓ Trade successful! Profit: ${result.actual_profit_usd:.2f} "
                            f"({result.actual_profit_pct:.2%})"
                        )
                    else:
                        self.stats["failed_trades"] += 1
                        logger.error(f"  ✗ Trade failed: {result.error_message}")

                    trades_executed += 1

                    # Respect rate limits between trades
                    await asyncio.sleep(1.0)

                except RiskLimitExceededError as e:
                    logger.warning(f"Risk limit exceeded for opportunity: {e}")
                    break  # Stop processing more opportunities
                except Exception as e:
                    logger.exception(f"Failed to process opportunity {opp.opportunity_id}")
                    continue

            # Log cycle summary
            cycle_duration = (datetime.utcnow() - cycle_start).total_seconds()
            logger.info(f"\nScan cycle #{self.cycle_count} complete:")
            logger.info(f"  Duration: {cycle_duration:.1f}s")
            logger.info(f"  Opportunities found: {len(opportunities)}")
            logger.info(f"  Trades executed: {trades_executed}")
            logger.info(f"  Success rate: {self._get_success_rate():.1%}")
            logger.info(f"  Total profit: ${self.stats['total_profit_usd']:.2f}")
            logger.info("=" * 80)

        except Exception as e:
            logger.exception(f"Scan cycle #{self.cycle_count} failed")

    def _get_success_rate(self) -> float:
        """Calculate success rate of executed trades"""
        total = self.stats["total_trades"]
        if total == 0:
            return 0.0
        return self.stats["successful_trades"] / total

    async def run_once(self) -> None:
        """
        Run a single scan cycle and exit

        Useful for testing or manual operation
        """
        logger.info("Running single scan cycle")
        await self.setup()
        await self.scan_cycle()
        await self.shutdown()

    async def run(self) -> None:
        """
        Start the orchestrator with scheduled scans

        This method runs indefinitely until shutdown() is called
        """
        await self.setup()

        self.running = True
        self.scheduler.start()

        logger.success(
            f"✓ Arbitrage system started! "
            f"Scanning every {settings.arbitrage.scan_interval}s"
        )

        # Keep running until shutdown
        try:
            while self.running:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            logger.info("Received cancellation signal")
        finally:
            await self.shutdown()

    async def shutdown(self) -> None:
        """
        Gracefully shutdown the orchestrator

        Closes all connections and saves final state
        """
        logger.info("Shutting down arbitrage system...")

        self.running = False

        # Stop scheduler
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown(wait=True)
            logger.info("Scheduler stopped")

        # Close API clients
        if self.client:
            await self.client.close()
            logger.info("Client closed")

        if self.trader:
            await self.trader.close()
            logger.info("Trader closed")

        # Close database
        if self.db:
            await self.db.close()
            logger.info("Database closed")

        # Log final statistics
        logger.info("\n" + "=" * 80)
        logger.info("FINAL STATISTICS")
        logger.info("=" * 80)
        logger.info(f"Total scan cycles: {self.cycle_count}")
        logger.info(f"Total opportunities: {self.stats['total_opportunities']}")
        logger.info(f"Total trades: {self.stats['total_trades']}")
        logger.info(f"Successful trades: {self.stats['successful_trades']}")
        logger.info(f"Failed trades: {self.stats['failed_trades']}")
        logger.info(f"Success rate: {self._get_success_rate():.1%}")
        logger.info(f"Total profit: ${self.stats['total_profit_usd']:.2f}")
        logger.info("=" * 80)

        logger.success("✓ Shutdown complete")


# Global orchestrator instance for signal handling
orchestrator: Optional[ArbitrageOrchestrator] = None


def signal_handler(signum, frame):
    """Handle shutdown signals (SIGINT, SIGTERM)"""
    logger.info(f"Received signal {signum}")
    if orchestrator:
        asyncio.create_task(orchestrator.shutdown())
    sys.exit(0)


async def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(description="Polymarket Arbitrage System")
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run a single scan cycle and exit",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Detect opportunities but don't execute trades",
    )
    args = parser.parse_args()

    global orchestrator
    orchestrator = ArbitrageOrchestrator(dry_run=args.dry_run)

    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    try:
        if args.once:
            await orchestrator.run_once()
        else:
            await orchestrator.run()
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        await orchestrator.shutdown()
    except Exception as e:
        logger.exception("Fatal error in main loop")
        await orchestrator.shutdown()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
