# Database Layer Documentation

## Overview

The database layer provides persistent storage for the Polymarket arbitrage trading system. It implements:

- **Trade Execution History**: Complete record of all arbitrage trades
- **Position Tracking**: Open and closed positions across markets
- **Performance Metrics**: Win rate, Sharpe ratio, drawdowns, etc.
- **Risk Monitoring**: Daily loss tracking, capital at risk calculations

## Architecture

### Components

1. **Models** ([src/utils/models.py](../src/utils/models.py))
   - `Trade`: Represents a completed trade execution
   - `Position`: Represents market positions (open/closed)

2. **Database Manager** ([src/utils/database.py](../src/utils/database.py))
   - Async interface for all database operations
   - CRUD operations for trades and positions
   - Performance metrics calculation
   - Risk limit monitoring

3. **Migrations** (alembic/)
   - Schema version control with Alembic
   - Initial migration: `001_initial.py`

## Usage

### Basic Setup

```python
from src.utils import DatabaseManager

# Initialize database
db = DatabaseManager("sqlite+aiosqlite:///./arbitrage.db")
await db.initialize()

# Or use as async context manager
async with DatabaseManager() as db:
    # Database operations here
    pass
```

### Saving Trades

```python
from src.types.orders import ExecutionResult
from src.types.opportunities import ArbitrageOpportunity

# After executing a trade
execution_result = ExecutionResult(
    opportunity_id="opp-123",
    success=True,
    yes_filled_size=100.0,
    yes_avg_price=0.55,
    yes_status="FILLED",
    no_filled_size=100.0,
    no_avg_price=0.45,
    no_status="FILLED",
    total_capital_used=1000.0,
    actual_profit_usd=18.5,
    actual_profit_pct=1.85,
    execution_time_ms=234.5,
)

# Save to database
trade = await db.save_trade(execution_result, opportunity)
print(f"Trade saved with ID: {trade.id}")
```

### Managing Positions

```python
# Create a new position
position = await db.create_position(
    trade_id=trade.id,
    token_id="token-yes-123",
    event_id="event-123",
    event_title="Will BTC reach $100k?",
    side="YES",
    size=100.0,
    entry_price=0.55,
    cost_basis=550.0,
)

# Update position value based on market price
await db.update_position_value(position.id, current_price=0.60)

# Close position and realize P&L
await db.close_position(position.id, exit_price=0.65)

# Get all open positions
open_positions = await db.get_open_positions()
for pos in open_positions:
    print(f"Position: {pos.token_id}, Size: {pos.size}, P&L: {pos.unrealized_pnl}")
```

### Risk Monitoring

```python
# Check daily loss
daily_loss = await db.get_daily_loss()
print(f"Today's loss: ${daily_loss:.2f}")

# Get capital at risk
capital_at_risk = await db.get_total_capital_at_risk()
print(f"Capital at risk: ${capital_at_risk:.2f}")

# Count today's trades
trade_count = await db.get_trade_count_today()
print(f"Trades today: {trade_count}")
```

### Performance Metrics

```python
# Calculate performance metrics (last 30 days)
metrics = await db.calculate_performance_metrics(days=30)

print(f"Total trades: {metrics['total_trades']}")
print(f"Win rate: {metrics['win_rate']:.2f}%")
print(f"Net profit: ${metrics['net_profit']:.2f}")
print(f"Sharpe ratio: {metrics['sharpe_ratio']:.3f}")
print(f"Max drawdown: {metrics['max_drawdown']:.2f}%")
print(f"Avg profit/trade: ${metrics['avg_profit_per_trade']:.2f}")
```

### Querying Trades

```python
# Get recent trades
recent_trades = await db.get_recent_trades(limit=10)
for trade in recent_trades:
    print(f"{trade.executed_at}: ${trade.actual_profit_usd:.2f}")

# Find trade by opportunity ID
trade = await db.get_trade_by_opportunity_id("opp-123")
if trade:
    print(f"Found trade: Success={trade.success}, Profit=${trade.actual_profit_usd}")
```

## Database Schema

### Trades Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key (auto-increment) |
| opportunity_id | String(50) | Links to ArbitrageOpportunity |
| event_id | String(100) | Polymarket event ID |
| event_title | String(500) | Event title for logging |
| success | Boolean | Overall trade success |
| yes_token_id | String(100) | YES token ID |
| yes_filled_size | Float | YES shares filled |
| yes_avg_price | Float | YES average price |
| yes_status | String(20) | "FILLED", "PARTIAL", "FAILED" |
| no_token_id | String(100) | NO token ID |
| no_filled_size | Float | NO shares filled |
| no_avg_price | Float | NO average price |
| no_status | String(20) | "FILLED", "PARTIAL", "FAILED" |
| total_capital_used | Float | Total USDC used |
| actual_profit_usd | Float | Actual profit/loss in USD |
| actual_profit_pct | Float | Profit percentage |
| execution_time_ms | Float | Execution time in milliseconds |
| error_message | String(1000) | Error description (if failed) |
| partial_fill_risk | Boolean | Single-leg fill risk flag |
| executed_at | DateTime | Trade execution timestamp |
| created_at | DateTime | Record creation timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `idx_executed_at` on `executed_at`
- `idx_success` on `success`
- `idx_opportunity_id` on `opportunity_id`

### Positions Table

| Column | Type | Description |
|--------|------|-------------|
| id | Integer | Primary key (auto-increment) |
| trade_id | Integer | Foreign key to trades.id |
| token_id | String(100) | Token/market ID |
| event_id | String(100) | Event ID |
| event_title | String(500) | Event title |
| side | String(10) | "YES" or "NO" |
| size | Float | Number of shares |
| entry_price | Float | Entry price (0-1) |
| current_price | Float | Current market price |
| cost_basis | Float | Total USDC invested |
| current_value | Float | Current market value |
| unrealized_pnl | Float | Unrealized profit/loss |
| realized_pnl | Float | Realized profit/loss (on close) |
| status | String(20) | "OPEN", "CLOSED", "EXPIRED" |
| opened_at | DateTime | Position open timestamp |
| closed_at | DateTime | Position close timestamp |
| updated_at | DateTime | Last update timestamp |

**Indexes:**
- `idx_status` on `status`
- `idx_token_id` on `token_id`
- `idx_event_id` on `event_id`
- `idx_opened_at` on `opened_at`
- `ix_positions_trade_id` on `trade_id`

## Database Migrations

### Running Migrations

```bash
# Run all pending migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Show current version
alembic current

# Show migration history
alembic history
```

### Creating New Migrations

```bash
# Auto-generate migration from model changes
alembic revision --autogenerate -m "Add new column"

# Create empty migration
alembic revision -m "Custom migration"
```

## Testing

Run the test suite:

```bash
# Run all database tests
pytest tests/test_database.py -v

# Run with coverage
pytest tests/test_database.py --cov=src/utils --cov-report=html

# Run specific test
pytest tests/test_database.py::test_save_trade_success -v
```

### Test Coverage

The test suite covers:
- ✅ Trade saving (success and failure cases)
- ✅ Trade status updates
- ✅ Trade retrieval by opportunity ID
- ✅ Position creation and management
- ✅ Position value updates
- ✅ Position closing and P&L calculation
- ✅ Risk monitoring (daily loss, capital at risk)
- ✅ Performance metrics calculation
- ✅ Recent trades queries
- ✅ Context manager usage
- ✅ Model serialization (to_dict)

**Target Coverage**: >80% for all modules, >95% for core logic

## Integration with Other Modules

### With Executor (Agent B)

```python
from src.strategy.arbitrage_executor import ArbitrageExecutor
from src.utils import DatabaseManager

executor = ArbitrageExecutor(trader, config)
db = DatabaseManager()
await db.initialize()

# Execute opportunity
result = await executor.execute_opportunity(opportunity, position_size)

# Save result to database
trade = await db.save_trade(result, opportunity)

# Create positions if successful
if result.success and result.both_legs_filled:
    await db.create_position(
        trade_id=trade.id,
        token_id=opportunity.yes_token_id,
        event_id=opportunity.event_id,
        event_title=opportunity.event_title,
        side="YES",
        size=result.yes_filled_size,
        entry_price=result.yes_avg_price,
        cost_basis=result.yes_filled_size * result.yes_avg_price,
    )
```

### With Position Manager (Agent D)

```python
from src.strategy.position_manager import PositionManager

position_manager = PositionManager(config, db)

# Check risk limits before trading
risk_check = await position_manager.check_risk_limits()
if not risk_check["can_trade"]:
    logger.warning("Risk limits exceeded, skipping trade")
    return

# Get available capital
available = await position_manager.get_available_capital()
```

## Configuration

### Database URL Format

The database URL follows SQLAlchemy's async driver format:

```python
# SQLite (async)
db_url = "sqlite+aiosqlite:///./arbitrage.db"

# PostgreSQL (async)
db_url = "postgresql+asyncpg://user:pass@localhost/arbitrage"

# MySQL (async)
db_url = "mysql+aiomysql://user:pass@localhost/arbitrage"
```

### Environment Variables

Add to your `.env` file:

```bash
DATABASE_URL=sqlite+aiosqlite:///./arbitrage.db
```

Access via config:

```python
from config import settings

db = DatabaseManager(settings.database.url)
```

## Performance Considerations

### Query Optimization

- All frequently queried columns are indexed
- Use `get_open_positions()` instead of filtering all positions
- Performance metrics are calculated in-memory after fetching data
- Connection pooling is handled automatically by SQLAlchemy

### Best Practices

1. **Use Context Managers**: Always use `async with` for automatic cleanup
2. **Batch Operations**: When possible, batch multiple operations
3. **Transaction Handling**: Database operations use transactions automatically
4. **Error Handling**: All methods log errors and raise SQLAlchemyError
5. **Connection Management**: Engine disposal is handled by `close()` or context manager

## Troubleshooting

### Common Issues

**Issue**: `ModuleNotFoundError: No module named 'aiosqlite'`
```bash
pip install aiosqlite
```

**Issue**: `alembic.util.exc.CommandError: Can't locate revision identified by '001_initial'`
```bash
# Initialize alembic version table
alembic stamp head
```

**Issue**: Database locked errors
```python
# Use SQLite with WAL mode for better concurrency
from sqlalchemy import event
from sqlalchemy.engine import Engine

@event.listens_for(Engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.close()
```

## API Reference

See full API documentation in:
- [src/utils/database.py](../src/utils/database.py) - DatabaseManager class
- [src/utils/models.py](../src/utils/models.py) - Trade and Position models

## Changelog

### Version 1.0.0 (2026-01-15)
- Initial implementation
- Trade and Position models
- DatabaseManager with full CRUD operations
- Performance metrics calculation
- Risk monitoring queries
- Alembic migration setup
- Comprehensive test suite (>80% coverage)

---

**Maintained by**: Agent C
**Last Updated**: 2026-01-15
