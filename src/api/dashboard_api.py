"""
Dashboard API Server for Polymarket Arbitrage Bot

Provides REST API endpoints and WebSocket for real-time monitoring.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from typing import List
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import json

from config import settings
from src.utils.database import DatabaseManager

app = FastAPI(
    title="Polymarket Arbitrage Dashboard",
    description="Real-time monitoring dashboard for arbitrage trading bot",
    version="1.0.0"
)

# Initialize database manager
db = DatabaseManager(settings.database_url)

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to client: {e}")

manager = ConnectionManager()


# =========================================================================
# REST API Endpoints
# =========================================================================

@app.get("/")
async def root():
    """Serve the main dashboard HTML page"""
    frontend_path = Path(__file__).parent.parent.parent / "frontend" / "index.html"
    if frontend_path.exists():
        return FileResponse(frontend_path)
    return HTMLResponse(content="<h1>Dashboard frontend not found</h1><p>Please create frontend/index.html</p>")


@app.get("/api/status")
async def get_bot_status():
    """Get current bot status"""
    # TODO: Connect to actual bot instance to get real status
    # For now, return mock data
    return {
        "is_running": True,
        "uptime": "2h 15m",
        "last_scan": datetime.utcnow().isoformat(),
        "opportunities_found_today": 42,
        "trades_executed_today": 12
    }


@app.get("/api/performance")
async def get_performance_metrics():
    """Get performance metrics"""
    try:
        metrics = await db.calculate_performance_metrics()
        return metrics
    except Exception as e:
        # Return default values if database not initialized
        return {
            "total_trades": 0,
            "win_rate": 0.0,
            "net_profit": 0.0,
            "sharpe_ratio": 0.0,
            "max_drawdown": 0.0,
            "avg_profit_per_trade": 0.0
        }


@app.get("/api/trades/recent")
async def get_recent_trades(limit: int = 20):
    """Get recent trade records"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        trades = await db.get_trade_history(start_date, end_date)

        return [
            {
                "trade_id": t.trade_id,
                "event_title": t.event_title,
                "executed_at": t.executed_at.isoformat() if t.executed_at else None,
                "actual_profit": float(t.actual_profit) if t.actual_profit else 0.0,
                "status": t.status,
                "arbitrage_type": t.arbitrage_type
            }
            for t in trades[:limit]
        ]
    except Exception as e:
        print(f"Error fetching trades: {e}")
        return []


@app.get("/api/positions/open")
async def get_open_positions():
    """Get current open positions"""
    try:
        positions = await db.get_open_positions()

        return [
            {
                "position_id": p.position_id,
                "token_id": p.token_id,
                "size": float(p.size),
                "entry_price": float(p.entry_price),
                "current_price": float(p.current_price) if p.current_price else 0.0,
                "unrealized_pnl": float(p.unrealized_pnl) if p.unrealized_pnl else 0.0
            }
            for p in positions
        ]
    except Exception as e:
        print(f"Error fetching positions: {e}")
        return []


@app.get("/api/equity_curve")
async def get_equity_curve(days: int = 30):
    """Get equity curve data for chart rendering"""
    try:
        # TODO: Implement daily equity calculation
        # For now, return mock data
        end_date = datetime.utcnow()
        dates = []
        equity = []

        base_equity = 10000.0
        for i in range(days):
            date = end_date - timedelta(days=days - i - 1)
            dates.append(date.strftime("%Y-%m-%d"))
            # Mock progressive growth
            equity.append(base_equity + (i * 50) + (i % 5) * 20)

        return {
            "dates": dates,
            "equity": equity
        }
    except Exception as e:
        print(f"Error generating equity curve: {e}")
        return {"dates": [], "equity": []}


# =========================================================================
# WebSocket for Real-time Updates
# =========================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket connection for real-time dashboard updates"""
    await manager.connect(websocket)

    try:
        # Send initial data
        status = await get_bot_status()
        metrics = await get_performance_metrics()

        await websocket.send_json({
            "type": "connected",
            "timestamp": datetime.utcnow().isoformat(),
            "message": "Connected to dashboard"
        })

        # Keep connection alive and send periodic updates
        while True:
            await asyncio.sleep(5)  # Update every 5 seconds

            # Fetch latest data
            status = await get_bot_status()
            metrics = await get_performance_metrics()

            # Send update to client
            await websocket.send_json({
                "type": "update",
                "timestamp": datetime.utcnow().isoformat(),
                "status": status,
                "metrics": metrics
            })

    except WebSocketDisconnect:
        manager.disconnect(websocket)
        print("Client disconnected")
    except Exception as e:
        print(f"WebSocket error: {e}")
        manager.disconnect(websocket)


async def broadcast_trade_update(trade_data: dict):
    """
    Broadcast new trade update to all connected clients.

    This function should be called from the main bot when a new trade is executed.
    """
    await manager.broadcast({
        "type": "new_trade",
        "timestamp": datetime.utcnow().isoformat(),
        "trade": trade_data
    })


# =========================================================================
# Static Files
# =========================================================================

# Mount static files directory
frontend_dir = Path(__file__).parent.parent.parent / "frontend"
if frontend_dir.exists():
    app.mount("/static", StaticFiles(directory=str(frontend_dir)), name="static")


# =========================================================================
# Startup/Shutdown Events
# =========================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup"""
    try:
        await db.initialize()
        print("✓ Database initialized")
    except Exception as e:
        print(f"Warning: Could not initialize database: {e}")
        print("Dashboard will run with mock data")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    print("Dashboard server shutting down")


# =========================================================================
# Main Entry Point
# =========================================================================

if __name__ == "__main__":
    import uvicorn

    print("🚀 Starting Polymarket Arbitrage Dashboard")
    print(f"📊 Access dashboard at: http://localhost:8000")
    print(f"📡 WebSocket endpoint: ws://localhost:8000/ws")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
