# Polymarket Arbitrage System - Orchestrator

## Overview

The main orchestrator (`main.py`) coordinates all components of the Polymarket arbitrage trading system:

- **ArbitrageDetector**: Scans Polymarket markets for price discrepancies
- **ArbitrageExecutor**: Executes profitable trades simultaneously on both legs
- **DatabaseManager**: Records trades and calculates performance metrics
- **APScheduler**: Runs periodic scans based on configured intervals

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your credentials:
```bash
# Required for trading
POLYMARKET_PRIVATE_KEY=your_polygon_private_key_here

# Optional - for future features
NEWSAPI_KEY=your_newsapi_key
TWITTER_BEARER_TOKEN=your_twitter_token
```

### 3. Run the System

**Dry-run mode (no actual trades):**
```bash
python main.py --dry-run
```

**Single scan cycle:**
```bash
python main.py --once
```

**Production mode (continuous scanning):**
```bash
python main.py
```

## Command-Line Options

- `--dry-run`: Detect opportunities but don't execute trades (useful for testing)
- `--once`: Run a single scan cycle and exit (useful for manual operation)

## Configuration

All configuration is in [`config/settings.py`](config/settings.py):

### Trading Parameters

```python
# Minimum profit threshold to execute a trade
min_profit_threshold: 0.02  # 2%

# Maximum position size per trade
max_position_size: 1000.0  # USDC

# Risk limits
max_daily_loss: 100.0  # USDC
max_open_positions: 10

# Slippage tolerance
slippage_tolerance: 0.01  # 1%
```

### Arbitrage Detection

```python
# Minimum price discrepancy to detect
min_discrepancy: 0.03  # 3%

# Scan interval (seconds)
scan_interval: 30  # 30 seconds
```

### Environment Variables

Override settings via environment variables:
```bash
export TRADING_MAX_POSITION_SIZE=500.0
export ARBITRAGE_SCAN_INTERVAL=60
export LOG_LEVEL=DEBUG
```

## How It Works

### Scan Cycle

Each scan cycle performs the following steps:

1. **Risk Check**: Verify daily loss limits and open position counts
2. **Market Scan**: Fetch all active markets and detect arbitrage opportunities
3. **Opportunity Filtering**: Filter for executable opportunities with sufficient confidence
4. **Position Sizing**: Calculate optimal position size using Kelly criterion
5. **Trade Execution**: Execute both legs simultaneously (if not dry-run)
6. **Record Results**: Save execution results to database

### Position Sizing

The orchestrator uses the **Kelly Criterion** for optimal position sizing:

```
f* = (bp - q) / b

Where:
- f* = optimal fraction of capital
- b = profit ratio
- p = win probability (confidence score)
- q = 1 - p
```

The system applies conservative factors:
- **Max fraction**: 25% of capital per trade
- **Half-Kelly**: 50% reduction for safety

### Example Calculation

For an opportunity with:
- Confidence: 0.85 (85%)
- Net profit: 0.03 (3%)

```python
kelly_fraction = calculate_kelly_fraction(
    win_probability=0.85,
    profit_ratio=0.03,
    max_fraction=0.25,
    conservative_factor=0.5
)
# Result: ~0.10 (10% of capital)

position_size = 0.10 * max_position_size
# Result: $100 USDC (if max_position_size = $1000)
```

## Output and Logging

### Console Output

The orchestrator logs real-time progress to the console:

```
2026-01-15 15:30:00.123 | INFO     | main:scan_cycle:256 | ================================================================================
2026-01-15 15:30:00.125 | INFO     | main:scan_cycle:257 | Starting scan cycle #1
2026-01-15 15:30:02.456 | INFO     | main:scan_cycle:268 | Scanning markets for arbitrage opportunities...
2026-01-15 15:30:03.789 | INFO     | main:scan_cycle:274 | Found 3 opportunities
2026-01-15 15:30:03.790 | INFO     | main:scan_cycle:289 |
Opportunity: Will Bitcoin reach $100k by EOY?
2026-01-15 15:30:03.791 | INFO     | main:scan_cycle:290 |   Type: OVERPRICED, Spread: 2.00%, Net profit: 0.80%, Confidence: 0.85
2026-01-15 15:30:03.792 | INFO     | main:scan_cycle:297 |   Position size: $100.00
2026-01-15 15:30:04.123 | SUCCESS  | main:scan_cycle:318 |   ✓ Trade successful! Profit: $8.00 (0.78%)
```

### Log Files

Logs are written to `./logs/arbitrage.log` with:
- **Rotation**: 100 MB per file
- **Retention**: 30 days
- **Compression**: ZIP format

### Database

Trade history and performance metrics are stored in:
- **Location**: `./data/arbitrage.db` (SQLite)
- **Schema**: See [`src/utils/models.py`](src/utils/models.py)

## Performance Metrics

On shutdown, the orchestrator displays statistics:

```
================================================================================
FINAL STATISTICS
================================================================================
Total scan cycles: 48
Total opportunities: 127
Total trades: 23
Successful trades: 21
Failed trades: 2
Success rate: 91.3%
Total profit: $187.50
================================================================================
```

Query additional metrics programmatically:

```python
from src.utils.database import DatabaseManager

db = DatabaseManager()
await db.initialize()

metrics = await db.calculate_performance_metrics()
# Returns:
# {
#     "total_trades": 23,
#     "win_rate": 0.913,
#     "net_profit": 187.50,
#     "sharpe_ratio": 2.34,
#     "max_drawdown": -15.00,
#     "avg_profit_per_trade": 8.15
# }
```

## Risk Management

The orchestrator enforces multiple risk limits:

### Daily Loss Limit

Trading stops if daily losses exceed `max_daily_loss`:

```python
daily_loss = await db.get_daily_loss()
if abs(daily_loss) >= settings.trading.max_daily_loss:
    logger.warning("Daily loss limit exceeded - trading paused")
    return  # Skip this cycle
```

### Position Count Limit

Trading stops if open positions exceed `max_open_positions`:

```python
open_positions = await db.get_open_positions()
if len(open_positions) >= settings.trading.max_open_positions:
    logger.warning("Max open positions reached")
    return  # Skip this cycle
```

### Per-Trade Limits

Each trade is capped at `max_position_size` regardless of Kelly calculation.

## Graceful Shutdown

Press `Ctrl+C` to gracefully shutdown:

1. Scheduler stops accepting new scans
2. Current scan completes
3. All database connections close
4. API clients disconnect
5. Final statistics are displayed

```bash
^C
2026-01-15 15:45:30.123 | INFO     | main:shutdown:456 | Shutting down arbitrage system...
2026-01-15 15:45:30.234 | INFO     | main:shutdown:465 | Scheduler stopped
2026-01-15 15:45:30.345 | INFO     | main:shutdown:470 | Client closed
2026-01-15 15:45:30.456 | SUCCESS  | main:shutdown:497 | ✓ Shutdown complete
```

## Testing

Run the orchestrator tests:

```bash
# All tests
pytest tests/test_orchestrator.py -v

# Specific test
pytest tests/test_orchestrator.py::test_scan_cycle_with_execution -v

# With coverage
pytest tests/test_orchestrator.py --cov=main --cov-report=html
```

### Test Coverage

The test suite includes:

- ✅ Component initialization
- ✅ Risk limit checking
- ✅ Position sizing calculations
- ✅ Scan cycle execution (dry-run and live)
- ✅ Error handling
- ✅ Statistics tracking
- ✅ Graceful shutdown

## Troubleshooting

### No opportunities found

**Cause**: Markets may be efficiently priced, or `min_discrepancy` is too high.

**Solution**: Lower `min_discrepancy` in settings or wait for volatile markets.

### "Private key not configured"

**Cause**: `POLYMARKET_PRIVATE_KEY` not set in `.env`.

**Solution**: Add your Polygon wallet private key to `.env` file.

### "Daily loss limit exceeded"

**Cause**: System has lost more than `max_daily_loss` today.

**Solution**: Wait until next day (UTC), or increase limit in settings.

### Database locked errors

**Cause**: Multiple orchestrator instances accessing same database.

**Solution**: Only run one instance at a time, or use PostgreSQL.

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────┐
│         ArbitrageOrchestrator           │
│                                         │
│  ┌───────────────────────────────────┐ │
│  │      APScheduler (scan_cycle)     │ │
│  └───────────────────────────────────┘ │
│                  │                      │
│                  ▼                      │
│  ┌───────────────────────────────────┐ │
│  │  1. Check Risk Limits (DB)        │ │
│  └───────────────────────────────────┘ │
│                  │                      │
│                  ▼                      │
│  ┌───────────────────────────────────┐ │
│  │  2. Scan Markets (Detector)       │ │
│  └───────────────────────────────────┘ │
│                  │                      │
│                  ▼                      │
│  ┌───────────────────────────────────┐ │
│  │  3. Calculate Size (Kelly)        │ │
│  └───────────────────────────────────┘ │
│                  │                      │
│                  ▼                      │
│  ┌───────────────────────────────────┐ │
│  │  4. Execute Trade (Executor)      │ │
│  └───────────────────────────────────┘ │
│                  │                      │
│                  ▼                      │
│  ┌───────────────────────────────────┐ │
│  │  5. Record Result (DB)            │ │
│  └───────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Data Flow

```
PolymarketClient → IntraMarketArbitrageDetector → ArbitrageOpportunity
                                                          ↓
                                                   Kelly Criterion
                                                          ↓
                                                   ArbitrageExecutor
                                                          ↓
                                                   ExecutionResult
                                                          ↓
                                                   DatabaseManager
```

## Production Deployment

### Using systemd (Linux)

Create `/etc/systemd/system/polymarket-arbitrage.service`:

```ini
[Unit]
Description=Polymarket Arbitrage System
After=network.target

[Service]
Type=simple
User=arbitrage
WorkingDirectory=/opt/polymarket-arbitrage
Environment="PATH=/opt/polymarket-arbitrage/venv/bin"
ExecStart=/opt/polymarket-arbitrage/venv/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable polymarket-arbitrage
sudo systemctl start polymarket-arbitrage
sudo systemctl status polymarket-arbitrage
```

### Using Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["python", "main.py"]
```

Build and run:
```bash
docker build -t polymarket-arbitrage .
docker run -d --name arbitrage \
  --env-file .env \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/data:/app/data \
  polymarket-arbitrage
```

## Support

For issues or questions:
- Check [`INTERFACE_SPEC.md`](INTERFACE_SPEC.md) for component interfaces
- Review [`CLAUDE.md`](CLAUDE.md) for architecture overview
- Examine logs in `./logs/arbitrage.log`
- Run tests: `pytest tests/ -v`

## License

MIT License - See LICENSE file for details.
