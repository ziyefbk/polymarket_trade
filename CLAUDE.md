# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Polymarket arbitrage trading system** built in Python. The system monitors Polymarket prediction markets, detects arbitrage opportunities through sentiment analysis and price discrepancies, and executes automated trades.

**Current Status:** Complete arbitrage trading system with detector, executor, database, and orchestrator. Robin signal system integrated for enhanced trade signals.

## Development Commands

### Python Environment
**IMPORTANT:** Always activate the conda environment before running any Python commands:
```bash
conda activate math
```

### Setup
```bash
# Activate conda environment
conda activate math

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your credentials:
# - POLYMARKET_PRIVATE_KEY (Polygon wallet)
# - NEWSAPI_KEY (from newsapi.org)
# - TWITTER_BEARER_TOKEN (from developer.twitter.com)
```

### Testing
```bash
# Activate conda environment first
conda activate math

# Run all tests
pytest tests/

# Run specific test file
pytest tests/test_polymarket_client.py

# Run with coverage
pytest --cov=src tests/
```

### Running the System
```bash
# Activate conda environment first
conda activate math

# Run in dry-run mode (detect opportunities but don't trade)
python main.py --dry-run

# Run single scan cycle
python main.py --once

# Run continuous monitoring
python main.py
```

## Architecture

### Component Structure

```
├── config/              # Configuration management (Pydantic-based)
│   └── settings.py      # Central config with PolymarketConfig, TradingConfig, ArbitrageConfig
├── src/
│   ├── api/            # Polymarket API integration (IMPLEMENTED)
│   │   ├── polymarket_client.py  # Read-only client: markets, events, order books
│   │   └── trader.py             # Trading client: order execution, wallet auth
│   ├── analyzer/       # Market analysis (IMPLEMENTED)
│   │   ├── arbitrage_detector.py # Intra-market arbitrage detection
│   │   └── robin_intelligence.py # Dark web OSINT intelligence gathering
│   ├── strategy/       # Trading strategy logic (IMPLEMENTED)
│   │   ├── arbitrage_executor.py # Trade execution with risk management
│   │   └── position_manager.py   # Position sizing and management
│   └── utils/          # Helper functions (IMPLEMENTED)
│       ├── database.py  # SQLAlchemy database manager
│       ├── kelly.py     # Kelly criterion position sizing
│       └── logger.py    # Logging configuration
├── robin_signals/      # Robin dark web OSINT tool (integrated)
└── tests/              # Test suite (IMPLEMENTED)
```

### Data Flow

1. **Data Collection:** `polymarket_client.py` fetches market data, events, order books
2. **Intelligence Gathering:** `robin_intelligence.py` searches dark web for event-related intelligence
3. **Analysis:** `arbitrage_detector.py` detects intra-market arbitrage opportunities
4. **Strategy:** `arbitrage_executor.py` evaluates opportunities and calculates position sizes
5. **Execution:** `trader.py` signs and submits orders to Polymarket CLOB
6. **Storage:** SQLite database tracks trades, positions, and performance

### Key Data Models

**Market Data** ([src/api/polymarket_client.py](src/api/polymarket_client.py)):
- `Market`: Represents a single outcome (token_id, price, volume, liquidity)
- `Event`: Contains multiple markets (event_id, title, markets)
- `OrderBook`: Snapshot of bids/asks with spread calculation

**Trading** ([src/api/trader.py](src/api/trader.py)):
- `Order`: Represents an order (order_id, side, price, size, status)
- `TradeResult`: Execution result (success, filled_size, avg_price, error)

### Configuration System

All configuration is centralized in [config/settings.py](config/settings.py) using Pydantic:

- **PolymarketConfig**: API endpoints (CLOB + Gamma), chain_id, private_key
- **NewsConfig**: NewsAPI and Twitter credentials
- **TradingConfig**: Risk limits (max_position_size: 1000 USDC, max_daily_loss: 100 USDC, min_profit_threshold: 2%, slippage_tolerance: 1%)
- **ArbitrageConfig**: Detection parameters (min_discrepancy: 3%, correlation_threshold: 0.8, scan_interval: 30s)

Access settings via: `from config import settings`

### API Clients

**PolymarketClient** (read-only):
```python
async with PolymarketClient() as client:
    events = await client.get_all_active_events()
    order_book = await client.get_order_book(token_id)
    prices = await client.get_prices_batch(token_ids)
```

**PolymarketTrader** (requires wallet):
```python
async with PolymarketTrader() as trader:
    result = await trader.buy(token_id, price=0.55, size=100)
    orders = await trader.get_open_orders()
    await trader.cancel_order(order_id)
```

## Important Implementation Notes

### Async Pattern
All components use async/await. Always use async context managers (`async with`) for API clients.

### Authentication
Trading requires Ethereum wallet authentication via private key signing. The trader client:
1. Signs messages with private key (ECDSA via eth-account)
2. Creates auth headers (POLY_ADDRESS, POLY_SIGNATURE, POLY_TIMESTAMP)
3. Includes headers in order requests

### Rate Limiting
Batch operations include built-in rate limiting (0.1s delay between batches). Respect API limits when implementing new features.

### Price Validation
Polymarket prices are probabilities (0-1 range). Always validate:
- Prices must be between 0 and 1
- Sizes must be positive
- Check slippage tolerance before execution

### Risk Management
Enforce limits defined in TradingConfig:
- Max position size per trade
- Max daily loss threshold
- Minimum profit threshold before entering positions

### Error Handling
All API methods return structured results or catch exceptions. Check `TradeResult.success` before proceeding with trade logic.

## Blockchain Context

- **Network:** Polygon mainnet (chain_id: 137)
- **Currency:** USDC for trading
- **Wallet Requirements:** Private key must have USDC balance and approved spending on Polymarket contracts
- **Transaction Signing:** All orders are signed locally with private key before submission

## Missing Components

### Robin Dark Web Intelligence (NEW - Integrated)

Robin 是一个暗网 OSINT 工具，现已集成到系统中用于情报收集。详细使用说明见 [docs/ROBIN_INTEGRATION.md](docs/ROBIN_INTEGRATION.md)。

**功能：**
- 暗网搜索和信息抓取
- LLM 驱动的查询优化和结果过滤
- 为 Polymarket 事件生成情报报告
- 支持多种 LLM 模型（GPT-4o, Claude, Gemini, Ollama）

**使用场景：**
- 提前发现重大事件信号（政治、安全、经济）
- 识别市场移动信息
- 关联暗网活动与预测市场结果

**要求：**
- Tor 服务必须运行
- 至少一个 LLM API 密钥（OpenAI/Anthropic/Google）

## Future Enhancements

以下组件可以进一步开发：

1. **高级情报分析**：自动化情报评分、实时监控特定暗网论坛
2. **多源情报融合**：结合 Robin（暗网）、NewsAPI（新闻）、Twitter（社交媒体）
3. **回测系统**：使用历史数据验证策略表现
4. **Dashboard**：Web 界面展示机会、交易、性能指标
5. **告警系统**：高置信度机会的实时通知