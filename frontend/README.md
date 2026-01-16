# Web Dashboard for Polymarket Arbitrage Bot

## Agent F - Web UI Frontend

Real-time monitoring dashboard for the Polymarket arbitrage trading bot.

## Features

✓ Real-time status display (running/stopped/error)
✓ 4 key metric cards (daily profit, win rate, trades today, open positions)
✓ Equity curve chart (Chart.js)
✓ Live trade stream with WebSocket updates
✓ Performance metrics details (total profit, Sharpe ratio, max drawdown, avg profit/trade)
✓ Dark theme UI (#0f172a background)
✓ Responsive design (mobile & desktop)

## Technology Stack

- **Backend**: FastAPI + WebSocket + uvicorn
- **Frontend**: Pure HTML/CSS/JavaScript + Chart.js
- **Real-time**: WebSocket communication
- **Styling**: Dark theme with responsive design

## Project Structure

```
polymarket/
├── src/api/
│   └── dashboard_api.py       # FastAPI backend server
├── frontend/
│   ├── index.html             # Main dashboard page
│   ├── css/
│   │   └── style.css          # Dark theme styles
│   └── js/
│       ├── websocket.js       # WebSocket client
│       ├── charts.js          # Chart.js rendering
│       └── main.js            # Dashboard logic
```

## Installation

1. Install required dependencies:
```bash
pip install fastapi uvicorn websockets
```

2. Ensure the database is initialized (handled by Agent C).

## Usage

### Start Dashboard Server

**Option 1: Standalone mode**
```bash
python -m src.api.dashboard_api
```

**Option 2: Integrated with bot (future)**
```bash
python main.py --dashboard
```

### Access Dashboard

Open your browser and navigate to:
```
http://localhost:8000
```

The dashboard will automatically connect via WebSocket and display real-time updates.

## API Endpoints

### REST API

- `GET /` - Serve main dashboard HTML
- `GET /api/status` - Get bot status (uptime, trades, opportunities)
- `GET /api/performance` - Get performance metrics
- `GET /api/trades/recent?limit=20` - Get recent trade history
- `GET /api/positions/open` - Get current open positions
- `GET /api/equity_curve?days=30` - Get equity curve data for chart

### WebSocket

- `WS /ws` - Real-time updates channel

WebSocket message types:
```javascript
// Connection acknowledgment
{ "type": "connected", "message": "..." }

// Periodic status updates
{
  "type": "update",
  "status": { ... },
  "metrics": { ... }
}

// New trade executed
{
  "type": "new_trade",
  "trade": { ... }
}
```

## Dashboard Components

### Status Bar
- Bot running status (green = running, red = disconnected, orange = error)
- Uptime display

### Metric Cards
1. **Daily Profit** - Today's net profit with percentage change
2. **Win Rate** - Success percentage with count (e.g., "12/14 成功")
3. **Today's Trades** - Number of trades executed today with opportunities found
4. **Open Positions** - Current open positions with capital at risk

### Equity Curve
- Interactive Chart.js line chart
- Shows 30-day account equity history
- Hover for specific values

### Trade Stream
- Real-time list of recent trades
- Color-coded by status (green = closed, red = failed, orange = open)
- Shows event title, profit, type, and time

### Performance Details
- Total profit
- Sharpe ratio (risk-adjusted return)
- Maximum drawdown percentage
- Average profit per trade

## Configuration

The dashboard automatically connects to the database specified in `config/settings.py`:

```python
# settings.py
database_url = "sqlite+aiosqlite:///./arbitrage.db"
```

## Development

### Testing Locally

1. Start the dashboard server:
```bash
python -m src.api.dashboard_api
```

2. Open browser developer console to monitor WebSocket messages:
```
F12 → Console tab
```

3. Check WebSocket connection:
```javascript
// In browser console
dashboardWS.ws.readyState
// 0 = CONNECTING, 1 = OPEN, 2 = CLOSING, 3 = CLOSED
```

### Mock Data

If the database is not initialized, the dashboard will display zeros. To populate with test data, run the arbitrage bot or insert mock trades via the database manager.

## Troubleshooting

### WebSocket won't connect

Check that the FastAPI server is running:
```bash
curl http://localhost:8000/api/status
```

### Charts not rendering

Ensure Chart.js CDN is accessible:
```html
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
```

### Static files not loading

Verify frontend directory structure:
```bash
ls frontend/
# Should show: index.html, css/, js/
```

## Integration with Main Bot

The dashboard is designed to run independently but can integrate with the main bot:

1. **Broadcast trade updates**:
```python
from src.api.dashboard_api import broadcast_trade_update

# In executor after trade completes
await broadcast_trade_update(execution_result.to_dict())
```

2. **Share bot status**:
Create a shared state object that both the bot and dashboard can access.

## Future Enhancements

Potential improvements for later iterations:

- [ ] Historical trade filtering (by date, profit, status)
- [ ] Live opportunity feed (currently detected opportunities)
- [ ] Manual pause/resume button
- [ ] Email/Telegram alerts for large profits/losses
- [ ] Backtest comparison overlay
- [ ] Position risk breakdown
- [ ] Light/dark theme toggle
- [ ] Export trade history to CSV

## Dependencies

```
fastapi>=0.104.0
uvicorn[standard]>=0.24.0
websockets>=12.0
```

Chart.js is loaded from CDN (no local install needed).

## Notes for Other Agents

- **Agent A (Detector)**: Dashboard displays opportunities found but not yet executed
- **Agent B (Executor)**: Call `broadcast_trade_update()` after each trade to push to UI
- **Agent C (Database)**: Database manager is already integrated, no changes needed
- **Agent D (Position Manager)**: Open positions are displayed from database queries
- **Agent E (Orchestrator)**: Can optionally start dashboard via `--dashboard` flag

## License

Part of the Polymarket Arbitrage System. Internal use only.

---

**Agent F - Web UI Frontend**
Created: 2026-01-15
Status: ✅ MVP Complete
