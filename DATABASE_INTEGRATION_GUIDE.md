# Quick Integration Guide for Database Layer

## For Agent B (Executor)

After executing a trade, save it to the database:

```python
from src.utils import DatabaseManager

class ArbitrageExecutor:
    def __init__(self, trader, config):
        self.trader = trader
        self.config = config
        self.db = DatabaseManager()

    async def initialize(self):
        await self.db.initialize()

    async def execute_opportunity(
        self,
        opp: ArbitrageOpportunity,
        position_size: float
    ) -> ExecutionResult:
        # Execute trade (your existing logic)
        result = ExecutionResult(...)

        # Save to database
        try:
            trade = await self.db.save_trade(result, opp)
            logger.info(f"Trade saved to database: ID={trade.id}")
        except Exception as e:
            logger.error(f"Failed to save trade: {e}")

        return result

    async def close(self):
        await self.db.close()
```

## For Agent D (Position Manager)

Use database for risk checks:

```python
from src.utils import DatabaseManager

class PositionManager:
    def __init__(self, config: TradingConfig, db: DatabaseManager):
        self.config = config
        self.db = db

    async def check_risk_limits(self) -> dict:
        """Check all risk limits using database"""
        # Get today's loss
        daily_loss = await self.db.get_daily_loss()
        daily_loss_ok = daily_loss < self.config.max_daily_loss

        # Get capital at risk
        capital_at_risk = await self.db.get_total_capital_at_risk()
        capital_available = capital_at_risk < self.config.max_position_size * 10

        # Get open position count
        open_positions = await self.db.get_open_positions()
        position_count_ok = len(open_positions) < 20  # Example limit

        return {
            "daily_loss_ok": daily_loss_ok,
            "capital_available": capital_available,
            "position_count_ok": position_count_ok,
            "can_trade": daily_loss_ok and capital_available and position_count_ok,
        }

    async def get_available_capital(self) -> float:
        """Calculate available capital"""
        total_capital = 10000.0  # From config or wallet
        capital_at_risk = await self.db.get_total_capital_at_risk()
        return total_capital - capital_at_risk
```

## For Agent E (Main Scheduler)

Initialize database and run periodic metrics:

```python
from src.utils import DatabaseManager
from apscheduler.schedulers.asyncio import AsyncIOScheduler

class MainOrchestrator:
    def __init__(self):
        self.db = DatabaseManager()
        self.scheduler = AsyncIOScheduler()

    async def start(self):
        """Start the arbitrage system"""
        # Initialize database
        await self.db.initialize()
        logger.info("Database initialized")

        # Schedule periodic metrics calculation
        self.scheduler.add_job(
            self.log_performance_metrics,
            'interval',
            minutes=60,  # Every hour
        )
        self.scheduler.start()

        # Main trading loop
        try:
            while True:
                await self.scan_and_execute()
                await asyncio.sleep(30)
        finally:
            await self.shutdown()

    async def log_performance_metrics(self):
        """Log performance metrics periodically"""
        try:
            metrics = await self.db.calculate_performance_metrics(days=7)
            logger.info(
                f"Performance (7d): "
                f"Trades={metrics['total_trades']}, "
                f"Win Rate={metrics['win_rate']:.1f}%, "
                f"Profit=${metrics['net_profit']:.2f}, "
                f"Sharpe={metrics['sharpe_ratio']:.2f}"
            )
        except Exception as e:
            logger.error(f"Failed to calculate metrics: {e}")

    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("Shutting down...")
        self.scheduler.shutdown()
        await self.db.close()
        logger.info("Database connection closed")
```

## Complete Example: End-to-End Flow

```python
import asyncio
from src.api.polymarket_client import PolymarketClient
from src.api.trader import PolymarketTrader
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.strategy.arbitrage_executor import ArbitrageExecutor
from src.strategy.position_manager import PositionManager
from src.utils import DatabaseManager
from config import settings

async def main():
    # Initialize all components
    client = PolymarketClient()
    trader = PolymarketTrader()
    db = DatabaseManager()

    await db.initialize()

    detector = IntraMarketArbitrageDetector(client, settings.arbitrage)
    executor = ArbitrageExecutor(trader, settings.trading)
    position_manager = PositionManager(settings.trading, db)

    try:
        # Scan for opportunities
        opportunities = await detector.scan_all_markets()
        logger.info(f"Found {len(opportunities)} opportunities")

        for opp in opportunities:
            # Check risk limits BEFORE executing
            risk_check = await position_manager.check_risk_limits()

            if not risk_check["can_trade"]:
                logger.warning(
                    f"Risk limits exceeded: "
                    f"daily_loss_ok={risk_check['daily_loss_ok']}, "
                    f"capital_available={risk_check['capital_available']}"
                )
                break

            # Calculate position size
            position_size = await position_manager.calculate_position_size(opp)

            # Execute trade
            result = await executor.execute_opportunity(opp, position_size)

            # Save to database
            trade = await db.save_trade(result, opp)

            if result.success:
                logger.success(
                    f"✓ Trade executed successfully: "
                    f"Profit=${result.actual_profit_usd:.2f}"
                )

                # Create positions for tracking
                if result.both_legs_filled:
                    await db.create_position(
                        trade_id=trade.id,
                        token_id=opp.yes_token_id,
                        event_id=opp.event_id,
                        event_title=opp.event_title,
                        side="YES",
                        size=result.yes_filled_size,
                        entry_price=result.yes_avg_price,
                        cost_basis=result.yes_filled_size * result.yes_avg_price,
                    )
                    await db.create_position(
                        trade_id=trade.id,
                        token_id=opp.no_token_id,
                        event_id=opp.event_id,
                        event_title=opp.event_title,
                        side="NO",
                        size=result.no_filled_size,
                        entry_price=result.no_avg_price,
                        cost_basis=result.no_filled_size * result.no_avg_price,
                    )
            else:
                logger.error(
                    f"✗ Trade failed: {result.error_message}"
                )

        # Log performance metrics
        metrics = await db.calculate_performance_metrics(days=1)
        logger.info(
            f"Today's Performance: "
            f"{metrics['total_trades']} trades, "
            f"{metrics['win_rate']:.1f}% win rate, "
            f"${metrics['net_profit']:.2f} profit"
        )

    finally:
        await client.close()
        await trader.close()
        await db.close()

if __name__ == "__main__":
    asyncio.run(main())
```

## Common Patterns

### 1. Saving a Successful Trade

```python
result = await executor.execute_opportunity(opp, size)
trade = await db.save_trade(result, opp)
print(f"Saved trade: {trade.id}")
```

### 2. Checking Risk Limits

```python
daily_loss = await db.get_daily_loss()
if daily_loss >= settings.trading.max_daily_loss:
    logger.warning(f"Daily loss limit reached: ${daily_loss:.2f}")
    return  # Stop trading
```

### 3. Tracking Open Positions

```python
open_positions = await db.get_open_positions()
for pos in open_positions:
    # Update with current market price
    current_price = await client.get_price(pos.token_id)
    await db.update_position_value(pos.id, current_price)
    logger.debug(f"Position {pos.id}: P&L=${pos.unrealized_pnl:.2f}")
```

### 4. Closing Positions

```python
# When event resolves or you want to exit
exit_price = 0.95  # Final resolution price
await db.close_position(position.id, exit_price)
logger.info(f"Closed position: realized P&L=${position.realized_pnl:.2f}")
```

### 5. Periodic Performance Reports

```python
# Run every hour
async def report_performance():
    metrics = await db.calculate_performance_metrics(days=30)
    print(f"""
    Performance (Last 30 Days):
    - Total Trades: {metrics['total_trades']}
    - Win Rate: {metrics['win_rate']:.1f}%
    - Net Profit: ${metrics['net_profit']:.2f}
    - Sharpe Ratio: {metrics['sharpe_ratio']:.2f}
    - Max Drawdown: {metrics['max_drawdown']:.1f}%
    - Avg Profit/Trade: ${metrics['avg_profit_per_trade']:.2f}
    """)
```

## Error Handling

Always wrap database operations in try-except:

```python
try:
    trade = await db.save_trade(result, opp)
    logger.info(f"Trade saved: {trade.id}")
except SQLAlchemyError as e:
    logger.error(f"Database error: {e}")
    # Continue execution, don't crash
except Exception as e:
    logger.exception(f"Unexpected error saving trade: {e}")
```

## Testing Your Integration

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_executor_saves_to_db():
    """Test that executor saves trades to database"""
    # Create mock database
    mock_db = AsyncMock()
    mock_db.save_trade.return_value = Trade(id=1, success=True)

    # Create executor with mock
    executor = ArbitrageExecutor(trader, config)
    executor.db = mock_db

    # Execute trade
    result = await executor.execute_opportunity(opp, 1000)

    # Verify database was called
    mock_db.save_trade.assert_called_once()
    assert result.success
```

## Configuration

Add to your `.env` file:

```bash
DATABASE_URL=sqlite+aiosqlite:///./arbitrage.db
```

Access in code:

```python
from config import settings

db = DatabaseManager(settings.database.url)
```

## Troubleshooting

**Q: Import error for DatabaseManager**
```python
# Make sure you import from src.utils
from src.utils import DatabaseManager  # ✓ Correct
from src.utils.database import DatabaseManager  # ✓ Also works
```

**Q: Async errors**
```python
# Always await database calls
trade = await db.save_trade(result)  # ✓ Correct
trade = db.save_trade(result)  # ✗ Wrong (missing await)
```

**Q: Database not initialized**
```python
db = DatabaseManager()
await db.initialize()  # ✓ Must call before using

# Or use context manager
async with DatabaseManager() as db:
    # Automatically initialized
    pass
```

## Need Help?

See full documentation:
- [DATABASE_README.md](DATABASE_README.md) - Complete usage guide
- [DATABASE_ARCHITECTURE.txt](DATABASE_ARCHITECTURE.txt) - Architecture diagram
- [src/utils/database.py](src/utils/database.py) - Source code with docstrings

## Quick Reference

```python
# Initialize
db = DatabaseManager()
await db.initialize()

# Save trade
trade = await db.save_trade(result, opportunity)

# Create position
pos = await db.create_position(trade_id, token_id, event_id,
                                event_title, side, size, price, cost)

# Query
positions = await db.get_open_positions()
daily_loss = await db.get_daily_loss()
capital = await db.get_total_capital_at_risk()
count = await db.get_trade_count_today()
metrics = await db.calculate_performance_metrics(days=30)

# Update
await db.update_position_value(pos_id, price)
await db.close_position(pos_id, exit_price)

# Cleanup
await db.close()
```
