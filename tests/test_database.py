"""
Tests for database layer (DatabaseManager and models)

Tests cover:
- Trade saving and retrieval
- Position management
- Performance metrics calculation
- Risk monitoring queries
"""
import pytest
import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

from src.utils.database import DatabaseManager
from src.utils.models import Base, Trade, Position
from src.types.orders import ExecutionResult
from src.types.opportunities import ArbitrageOpportunity


# Test database URL (in-memory SQLite)
TEST_DB_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def db_manager():
    """Create a test database manager with in-memory SQLite"""
    db = DatabaseManager(TEST_DB_URL)
    await db.initialize()
    yield db
    await db.close()


@pytest.fixture
def sample_opportunity():
    """Create a sample arbitrage opportunity"""
    return ArbitrageOpportunity(
        opportunity_id="test-opp-001",
        event_id="event-123",
        event_title="Will BTC reach $100k by EOY?",
        yes_token_id="token-yes-123",
        yes_price=0.55,
        yes_liquidity=10000.0,
        no_token_id="token-no-123",
        no_price=0.48,
        no_liquidity=8000.0,
        price_sum=1.03,
        spread=0.03,
        arbitrage_type="OVERPRICED",
        expected_profit_pct=2.5,
        expected_profit_usd=25.0,
        estimated_fees=5.0,
        estimated_slippage=2.0,
        net_profit_pct=1.8,
        is_executable=True,
        required_capital=1000.0,
        confidence_score=0.85,
        detected_at=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(minutes=5),
    )


@pytest.fixture
def sample_execution_result():
    """Create a sample successful execution result"""
    return ExecutionResult(
        opportunity_id="test-opp-001",
        success=True,
        yes_filled_size=100.0,
        yes_avg_price=0.55,
        yes_status="FILLED",
        no_filled_size=100.0,
        no_avg_price=0.48,
        no_status="FILLED",
        total_capital_used=1030.0,
        actual_profit_usd=18.5,
        actual_profit_pct=1.8,
        execution_time_ms=234.5,
        error_message=None,
        partial_fill_risk=False,
        executed_at=datetime.utcnow(),
    )


@pytest.fixture
def sample_failed_execution():
    """Create a sample failed execution result"""
    return ExecutionResult(
        opportunity_id="test-opp-002",
        success=False,
        yes_filled_size=100.0,
        yes_avg_price=0.55,
        yes_status="FILLED",
        no_filled_size=0.0,
        no_avg_price=0.0,
        no_status="FAILED",
        total_capital_used=550.0,
        actual_profit_usd=-5.0,
        actual_profit_pct=-0.9,
        execution_time_ms=120.0,
        error_message="Insufficient liquidity on NO leg",
        partial_fill_risk=True,
        executed_at=datetime.utcnow(),
    )


# ==================== Trade Tests ====================

@pytest.mark.asyncio
async def test_save_trade_success(db_manager, sample_execution_result, sample_opportunity):
    """Test saving a successful trade to database"""
    trade = await db_manager.save_trade(sample_execution_result, sample_opportunity)

    assert trade.id is not None
    assert trade.opportunity_id == "test-opp-001"
    assert trade.success is True
    assert trade.yes_filled_size == 100.0
    assert trade.no_filled_size == 100.0
    assert trade.actual_profit_usd == 18.5
    assert trade.event_id == "event-123"
    assert trade.event_title == "Will BTC reach $100k by EOY?"


@pytest.mark.asyncio
async def test_save_trade_failed(db_manager, sample_failed_execution):
    """Test saving a failed trade to database"""
    trade = await db_manager.save_trade(sample_failed_execution)

    assert trade.id is not None
    assert trade.success is False
    assert trade.partial_fill_risk is True
    assert trade.error_message == "Insufficient liquidity on NO leg"
    assert trade.actual_profit_usd == -5.0


@pytest.mark.asyncio
async def test_update_trade_status(db_manager, sample_execution_result, sample_opportunity):
    """Test updating trade status"""
    trade = await db_manager.save_trade(sample_execution_result, sample_opportunity)

    await db_manager.update_trade_status(trade.id, "FAILED", "Post-execution error")

    updated_trade = await db_manager.get_trade_by_opportunity_id("test-opp-001")
    assert updated_trade.success is False
    assert updated_trade.error_message == "Post-execution error"


@pytest.mark.asyncio
async def test_get_trade_by_opportunity_id(db_manager, sample_execution_result, sample_opportunity):
    """Test retrieving trade by opportunity ID"""
    await db_manager.save_trade(sample_execution_result, sample_opportunity)

    trade = await db_manager.get_trade_by_opportunity_id("test-opp-001")
    assert trade is not None
    assert trade.opportunity_id == "test-opp-001"

    # Test non-existent opportunity
    trade = await db_manager.get_trade_by_opportunity_id("non-existent")
    assert trade is None


@pytest.mark.asyncio
async def test_get_recent_trades(db_manager, sample_opportunity):
    """Test retrieving recent trades"""
    # Create multiple trades
    for i in range(5):
        result = ExecutionResult(
            opportunity_id=f"test-opp-{i:03d}",
            success=True,
            yes_filled_size=100.0,
            yes_avg_price=0.55,
            yes_status="FILLED",
            no_filled_size=100.0,
            no_avg_price=0.45,
            no_status="FILLED",
            total_capital_used=1000.0,
            actual_profit_usd=10.0 + i,
            actual_profit_pct=1.0,
            execution_time_ms=200.0,
            executed_at=datetime.utcnow() - timedelta(minutes=i),
        )
        await db_manager.save_trade(result, sample_opportunity)

    recent_trades = await db_manager.get_recent_trades(limit=3)
    assert len(recent_trades) == 3
    # Most recent should be first
    assert recent_trades[0].opportunity_id == "test-opp-000"


# ==================== Position Tests ====================

@pytest.mark.asyncio
async def test_create_position(db_manager, sample_execution_result, sample_opportunity):
    """Test creating a new position"""
    trade = await db_manager.save_trade(sample_execution_result, sample_opportunity)

    position = await db_manager.create_position(
        trade_id=trade.id,
        token_id="token-yes-123",
        event_id="event-123",
        event_title="Test Event",
        side="YES",
        size=100.0,
        entry_price=0.55,
        cost_basis=550.0,
    )

    assert position.id is not None
    assert position.trade_id == trade.id
    assert position.token_id == "token-yes-123"
    assert position.side == "YES"
    assert position.size == 100.0
    assert position.status == "OPEN"
    assert position.unrealized_pnl == 0.0


@pytest.mark.asyncio
async def test_get_open_positions(db_manager, sample_execution_result, sample_opportunity):
    """Test retrieving open positions"""
    trade = await db_manager.save_trade(sample_execution_result, sample_opportunity)

    # Create multiple positions
    await db_manager.create_position(
        trade_id=trade.id,
        token_id="token-yes-1",
        event_id="event-1",
        event_title="Event 1",
        side="YES",
        size=100.0,
        entry_price=0.5,
        cost_basis=500.0,
    )
    await db_manager.create_position(
        trade_id=trade.id,
        token_id="token-no-1",
        event_id="event-1",
        event_title="Event 1",
        side="NO",
        size=100.0,
        entry_price=0.5,
        cost_basis=500.0,
    )

    open_positions = await db_manager.get_open_positions()
    assert len(open_positions) == 2
    assert all(p.status == "OPEN" for p in open_positions)


@pytest.mark.asyncio
async def test_update_position_value(db_manager, sample_execution_result, sample_opportunity):
    """Test updating position market value"""
    trade = await db_manager.save_trade(sample_execution_result, sample_opportunity)

    position = await db_manager.create_position(
        trade_id=trade.id,
        token_id="token-yes-123",
        event_id="event-123",
        event_title="Test Event",
        side="YES",
        size=100.0,
        entry_price=0.50,
        cost_basis=500.0,
    )

    # Update to higher price (profit)
    await db_manager.update_position_value(position.id, 0.60)

    # Retrieve and verify
    positions = await db_manager.get_open_positions()
    updated_position = next(p for p in positions if p.id == position.id)

    assert updated_position.current_price == 0.60
    assert updated_position.current_value == 60.0  # 100 * 0.60
    assert updated_position.unrealized_pnl == -440.0  # 60 - 500


@pytest.mark.asyncio
async def test_close_position(db_manager, sample_execution_result, sample_opportunity):
    """Test closing a position"""
    trade = await db_manager.save_trade(sample_execution_result, sample_opportunity)

    position = await db_manager.create_position(
        trade_id=trade.id,
        token_id="token-yes-123",
        event_id="event-123",
        event_title="Test Event",
        side="YES",
        size=100.0,
        entry_price=0.50,
        cost_basis=500.0,
    )

    # Close at higher price (profit)
    await db_manager.close_position(position.id, 0.60)

    # Retrieve and verify
    async with db_manager.SessionLocal() as session:
        from sqlalchemy import select
        result = await session.execute(select(Position).where(Position.id == position.id))
        closed_position = result.scalar_one()

    assert closed_position.status == "CLOSED"
    assert closed_position.closed_at is not None
    assert closed_position.current_price == 0.60
    assert closed_position.realized_pnl == -440.0  # 60 - 500


# ==================== Risk & Metrics Tests ====================

@pytest.mark.asyncio
async def test_get_daily_loss(db_manager, sample_opportunity):
    """Test calculating daily loss"""
    # Create trades with losses today
    today = datetime.utcnow()

    for i in range(3):
        result = ExecutionResult(
            opportunity_id=f"loss-opp-{i}",
            success=False,
            yes_filled_size=100.0,
            yes_avg_price=0.55,
            yes_status="FILLED",
            no_filled_size=100.0,
            no_avg_price=0.50,
            no_status="FILLED",
            total_capital_used=1050.0,
            actual_profit_usd=-10.0 - i,  # Losses: -10, -11, -12
            actual_profit_pct=-1.0,
            execution_time_ms=200.0,
            executed_at=today - timedelta(hours=i),
        )
        await db_manager.save_trade(result, sample_opportunity)

    # Also create a winning trade (should not count)
    winning_result = ExecutionResult(
        opportunity_id="winning-opp",
        success=True,
        yes_filled_size=100.0,
        yes_avg_price=0.55,
        yes_status="FILLED",
        no_filled_size=100.0,
        no_avg_price=0.45,
        no_status="FILLED",
        total_capital_used=1000.0,
        actual_profit_usd=20.0,  # Profit
        actual_profit_pct=2.0,
        execution_time_ms=200.0,
        executed_at=today,
    )
    await db_manager.save_trade(winning_result, sample_opportunity)

    daily_loss = await db_manager.get_daily_loss()
    assert daily_loss == 33.0  # abs(-10 + -11 + -12)


@pytest.mark.asyncio
async def test_get_total_capital_at_risk(db_manager, sample_execution_result, sample_opportunity):
    """Test calculating total capital at risk"""
    trade = await db_manager.save_trade(sample_execution_result, sample_opportunity)

    # Create open positions
    await db_manager.create_position(
        trade_id=trade.id,
        token_id="token-1",
        event_id="event-1",
        event_title="Event 1",
        side="YES",
        size=100.0,
        entry_price=0.5,
        cost_basis=500.0,
    )
    await db_manager.create_position(
        trade_id=trade.id,
        token_id="token-2",
        event_id="event-2",
        event_title="Event 2",
        side="NO",
        size=200.0,
        entry_price=0.4,
        cost_basis=800.0,
    )

    total_at_risk = await db_manager.get_total_capital_at_risk()
    assert total_at_risk == 1300.0  # 500 + 800


@pytest.mark.asyncio
async def test_get_trade_count_today(db_manager, sample_opportunity):
    """Test counting trades executed today"""
    today = datetime.utcnow()

    # Create trades today
    for i in range(3):
        result = ExecutionResult(
            opportunity_id=f"today-opp-{i}",
            success=True,
            yes_filled_size=100.0,
            yes_avg_price=0.55,
            yes_status="FILLED",
            no_filled_size=100.0,
            no_avg_price=0.45,
            no_status="FILLED",
            total_capital_used=1000.0,
            actual_profit_usd=10.0,
            actual_profit_pct=1.0,
            execution_time_ms=200.0,
            executed_at=today - timedelta(hours=i),
        )
        await db_manager.save_trade(result, sample_opportunity)

    # Create trade yesterday (should not count)
    yesterday_result = ExecutionResult(
        opportunity_id="yesterday-opp",
        success=True,
        yes_filled_size=100.0,
        yes_avg_price=0.55,
        yes_status="FILLED",
        no_filled_size=100.0,
        no_avg_price=0.45,
        no_status="FILLED",
        total_capital_used=1000.0,
        actual_profit_usd=10.0,
        actual_profit_pct=1.0,
        execution_time_ms=200.0,
        executed_at=today - timedelta(days=1),
    )
    await db_manager.save_trade(yesterday_result, sample_opportunity)

    count = await db_manager.get_trade_count_today()
    assert count == 3


@pytest.mark.asyncio
async def test_calculate_performance_metrics(db_manager, sample_opportunity):
    """Test calculating performance metrics"""
    # Create a mix of winning and losing trades
    trades_data = [
        (True, 20.0),   # Win
        (True, 15.0),   # Win
        (False, -10.0), # Loss
        (True, 25.0),   # Win
        (False, -5.0),  # Loss
    ]

    for i, (success, profit) in enumerate(trades_data):
        result = ExecutionResult(
            opportunity_id=f"metrics-opp-{i}",
            success=success,
            yes_filled_size=100.0,
            yes_avg_price=0.55,
            yes_status="FILLED" if success else "PARTIAL",
            no_filled_size=100.0,
            no_avg_price=0.45,
            no_status="FILLED" if success else "FAILED",
            total_capital_used=1000.0,
            actual_profit_usd=profit,
            actual_profit_pct=profit / 10.0,
            execution_time_ms=200.0,
            executed_at=datetime.utcnow() - timedelta(hours=i),
        )
        await db_manager.save_trade(result, sample_opportunity)

    metrics = await db_manager.calculate_performance_metrics(days=1)

    assert metrics["total_trades"] == 5
    assert metrics["successful_trades"] == 3
    assert metrics["failed_trades"] == 2
    assert metrics["win_rate"] == 60.0  # 3/5 * 100
    assert metrics["net_profit"] == 45.0  # 20 + 15 - 10 + 25 - 5
    assert metrics["avg_profit_per_trade"] == 9.0  # 45 / 5
    assert "sharpe_ratio" in metrics
    assert "max_drawdown" in metrics


@pytest.mark.asyncio
async def test_calculate_performance_metrics_no_trades(db_manager):
    """Test performance metrics with no trades"""
    metrics = await db_manager.calculate_performance_metrics(days=30)

    assert metrics["total_trades"] == 0
    assert metrics["win_rate"] == 0.0
    assert metrics["net_profit"] == 0.0
    assert metrics["sharpe_ratio"] == 0.0
    assert metrics["max_drawdown"] == 0.0


# ==================== Context Manager Tests ====================

@pytest.mark.asyncio
async def test_database_context_manager():
    """Test DatabaseManager as async context manager"""
    async with DatabaseManager(TEST_DB_URL) as db:
        assert db.engine is not None
        assert db.SessionLocal is not None

        # Verify we can perform operations
        result = ExecutionResult(
            opportunity_id="context-test",
            success=True,
            yes_filled_size=100.0,
            yes_avg_price=0.55,
            yes_status="FILLED",
            no_filled_size=100.0,
            no_avg_price=0.45,
            no_status="FILLED",
            total_capital_used=1000.0,
            actual_profit_usd=10.0,
            actual_profit_pct=1.0,
            execution_time_ms=200.0,
        )
        trade = await db.save_trade(result)
        assert trade.id is not None

    # After exiting context, engine should be disposed
    # (We can't easily test this without accessing internals)


# ==================== Model Tests ====================

def test_trade_model_to_dict():
    """Test Trade model to_dict conversion"""
    trade = Trade(
        opportunity_id="test-opp",
        success=True,
        yes_filled_size=100.0,
        yes_avg_price=0.55,
        yes_status="FILLED",
        no_filled_size=100.0,
        no_avg_price=0.45,
        no_status="FILLED",
        total_capital_used=1000.0,
        actual_profit_usd=10.0,
        actual_profit_pct=1.0,
        execution_time_ms=200.0,
    )

    trade_dict = trade.to_dict()

    assert trade_dict["opportunity_id"] == "test-opp"
    assert trade_dict["success"] is True
    assert trade_dict["actual_profit_usd"] == 10.0
    assert "executed_at" in trade_dict


def test_position_model_to_dict():
    """Test Position model to_dict conversion"""
    position = Position(
        token_id="token-123",
        event_id="event-123",
        event_title="Test Event",
        side="YES",
        size=100.0,
        entry_price=0.5,
        cost_basis=500.0,
    )

    position_dict = position.to_dict()

    assert position_dict["token_id"] == "token-123"
    assert position_dict["side"] == "YES"
    assert position_dict["size"] == 100.0
    assert position_dict["status"] == "OPEN"


def test_position_update_market_value():
    """Test Position.update_market_value method"""
    position = Position(
        token_id="token-123",
        event_id="event-123",
        event_title="Test Event",
        side="YES",
        size=100.0,
        entry_price=0.50,
        cost_basis=500.0,
    )

    position.update_market_value(0.60)

    assert position.current_price == 0.60
    assert position.current_value == 60.0
    assert position.unrealized_pnl == -440.0  # 60 - 500


def test_position_close_position():
    """Test Position.close_position method"""
    position = Position(
        token_id="token-123",
        event_id="event-123",
        event_title="Test Event",
        side="YES",
        size=100.0,
        entry_price=0.50,
        cost_basis=500.0,
    )

    position.close_position(0.65)

    assert position.status == "CLOSED"
    assert position.closed_at is not None
    assert position.current_price == 0.65
    assert position.realized_pnl == -435.0  # 65 - 500


# ==================== Run Tests ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
