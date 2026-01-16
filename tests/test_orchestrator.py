"""
Unit tests for the main orchestrator

Tests the ArbitrageOrchestrator class which coordinates:
- Market scanning
- Risk limit checking
- Position sizing
- Trade execution
- Database recording
"""
import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from main import ArbitrageOrchestrator
from src.types.opportunities import ArbitrageOpportunity
from src.types.orders import ExecutionResult
from src.types.common import RiskLimitExceededError
from config import settings


# Test Fixtures
@pytest.fixture
def mock_opportunity():
    """Create a mock arbitrage opportunity"""
    return ArbitrageOpportunity(
        opportunity_id="test-opp-123",
        event_id="event-456",
        event_title="Will Bitcoin reach $100k by EOY?",
        yes_token_id="yes-token-789",
        yes_price=0.52,
        yes_liquidity=10000.0,
        no_token_id="no-token-789",
        no_price=0.50,
        no_liquidity=10000.0,
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
        valid_until=datetime.utcnow() + timedelta(minutes=5),
    )


@pytest.fixture
def mock_execution_result():
    """Create a mock successful execution result"""
    return ExecutionResult(
        opportunity_id="test-opp-123",
        success=True,
        yes_filled_size=100.0,
        yes_avg_price=0.52,
        yes_status="FILLED",
        no_filled_size=100.0,
        no_avg_price=0.50,
        no_status="FILLED",
        total_capital_used=102.0,
        actual_profit_usd=8.0,
        actual_profit_pct=0.0078,
        execution_time_ms=250.0,
        error_message=None,
        partial_fill_risk=False,
        executed_at=datetime.utcnow(),
    )


@pytest.fixture
async def orchestrator():
    """Create an orchestrator instance in dry-run mode"""
    orch = ArbitrageOrchestrator(dry_run=True)
    yield orch
    # Cleanup
    if orch.running:
        await orch.shutdown()


# Test Initialization
@pytest.mark.asyncio
async def test_orchestrator_initialization():
    """Test orchestrator can be initialized"""
    orch = ArbitrageOrchestrator(dry_run=True)
    assert orch.dry_run is True
    assert orch.cycle_count == 0
    assert orch.running is False
    assert orch.stats["total_opportunities"] == 0


@pytest.mark.asyncio
async def test_orchestrator_setup():
    """Test orchestrator setup initializes all components"""
    orch = ArbitrageOrchestrator(dry_run=True)

    with patch('main.DatabaseManager') as mock_db, \
         patch('main.PolymarketClient') as mock_client, \
         patch('main.IntraMarketArbitrageDetector') as mock_detector:

        # Configure mocks
        mock_db_instance = AsyncMock()
        mock_db.return_value = mock_db_instance

        await orch.setup()

        # Verify components were initialized
        assert orch.db is not None
        assert orch.client is not None
        assert orch.detector is not None
        assert orch.scheduler is not None

        # In dry-run mode, trader and executor should be None
        assert orch.trader is None
        assert orch.executor is None

        await orch.shutdown()


# Test Risk Limit Checking
@pytest.mark.asyncio
async def test_check_risk_limits_ok():
    """Test risk limits check when all limits are OK"""
    orch = ArbitrageOrchestrator(dry_run=True)

    # Mock database
    orch.db = AsyncMock()
    orch.db.get_daily_loss.return_value = -50.0  # Within limit of 100
    orch.db.get_open_positions.return_value = [MagicMock() for _ in range(5)]  # 5 < 10

    risk_status = await orch.check_risk_limits()

    assert risk_status["daily_loss_ok"] is True
    assert risk_status["position_count_ok"] is True
    assert risk_status["capital_available"] is True
    assert risk_status["can_trade"] is True


@pytest.mark.asyncio
async def test_check_risk_limits_daily_loss_exceeded():
    """Test risk limits check when daily loss limit is exceeded"""
    orch = ArbitrageOrchestrator(dry_run=True)

    # Mock database
    orch.db = AsyncMock()
    orch.db.get_daily_loss.return_value = -150.0  # Exceeds limit of 100
    orch.db.get_open_positions.return_value = []

    risk_status = await orch.check_risk_limits()

    assert risk_status["daily_loss_ok"] is False
    assert risk_status["can_trade"] is False


@pytest.mark.asyncio
async def test_check_risk_limits_max_positions_reached():
    """Test risk limits check when max positions is reached"""
    orch = ArbitrageOrchestrator(dry_run=True)

    # Mock database
    orch.db = AsyncMock()
    orch.db.get_daily_loss.return_value = 0.0
    # Create 10 open positions (max is 10)
    orch.db.get_open_positions.return_value = [MagicMock() for _ in range(10)]

    risk_status = await orch.check_risk_limits()

    assert risk_status["position_count_ok"] is False
    assert risk_status["can_trade"] is False


# Test Position Sizing
@pytest.mark.asyncio
async def test_calculate_position_size(mock_opportunity):
    """Test position size calculation using Kelly criterion"""
    orch = ArbitrageOrchestrator(dry_run=True)

    position_size = orch.calculate_position_size(mock_opportunity)

    # Position size should be positive and within limits
    assert position_size > 0
    assert position_size <= settings.trading.max_position_size
    assert position_size <= mock_opportunity.required_capital


@pytest.mark.asyncio
async def test_calculate_position_size_respects_limits(mock_opportunity):
    """Test position size respects max_position_size limit"""
    orch = ArbitrageOrchestrator(dry_run=True)

    # Create opportunity with very high confidence and profit
    high_opportunity = mock_opportunity
    high_opportunity.confidence_score = 0.99
    high_opportunity.net_profit_pct = 0.10  # 10% profit
    high_opportunity.required_capital = 10000.0  # High capital

    position_size = orch.calculate_position_size(high_opportunity)

    # Should still be capped at max_position_size
    assert position_size <= settings.trading.max_position_size


# Test Scan Cycle
@pytest.mark.asyncio
async def test_scan_cycle_no_opportunities():
    """Test scan cycle when no opportunities are found"""
    orch = ArbitrageOrchestrator(dry_run=True)

    # Setup mocks
    orch.db = AsyncMock()
    orch.db.get_daily_loss.return_value = 0.0
    orch.db.get_open_positions.return_value = []

    orch.detector = AsyncMock()
    orch.detector.scan_all_markets.return_value = []  # No opportunities

    await orch.scan_cycle()

    # Cycle should complete without errors
    assert orch.cycle_count == 1
    assert orch.stats["total_opportunities"] == 0


@pytest.mark.asyncio
async def test_scan_cycle_with_opportunities_dry_run(mock_opportunity):
    """Test scan cycle finds opportunities in dry-run mode"""
    orch = ArbitrageOrchestrator(dry_run=True)

    # Setup mocks
    orch.db = AsyncMock()
    orch.db.get_daily_loss.return_value = 0.0
    orch.db.get_open_positions.return_value = []

    orch.detector = AsyncMock()
    orch.detector.scan_all_markets.return_value = [mock_opportunity]

    await orch.scan_cycle()

    # Should detect opportunity but not execute (dry-run)
    assert orch.cycle_count == 1
    assert orch.stats["total_opportunities"] == 1
    assert orch.stats["total_trades"] == 0  # No trades in dry-run


@pytest.mark.asyncio
async def test_scan_cycle_with_execution(mock_opportunity, mock_execution_result):
    """Test scan cycle executes trades when not in dry-run"""
    orch = ArbitrageOrchestrator(dry_run=False)

    # Setup mocks
    orch.db = AsyncMock()
    orch.db.get_daily_loss.return_value = 0.0
    orch.db.get_open_positions.return_value = []
    orch.db.save_trade = AsyncMock()

    orch.detector = AsyncMock()
    orch.detector.scan_all_markets.return_value = [mock_opportunity]

    orch.executor = AsyncMock()
    orch.executor.execute_opportunity.return_value = mock_execution_result

    await orch.scan_cycle()

    # Should execute trade and record result
    assert orch.cycle_count == 1
    assert orch.stats["total_opportunities"] == 1
    assert orch.stats["total_trades"] == 1
    assert orch.stats["successful_trades"] == 1
    assert orch.stats["total_profit_usd"] == 8.0

    # Verify database save was called
    orch.db.save_trade.assert_called_once()


@pytest.mark.asyncio
async def test_scan_cycle_skips_when_risk_limits_exceeded():
    """Test scan cycle skips execution when risk limits are exceeded"""
    orch = ArbitrageOrchestrator(dry_run=False)

    # Setup mocks - daily loss exceeded
    orch.db = AsyncMock()
    orch.db.get_daily_loss.return_value = -200.0  # Exceeds limit
    orch.db.get_open_positions.return_value = []

    orch.detector = AsyncMock()

    await orch.scan_cycle()

    # Should not call detector since risk limits are exceeded
    orch.detector.scan_all_markets.assert_not_called()


@pytest.mark.asyncio
async def test_scan_cycle_handles_executor_failure(mock_opportunity):
    """Test scan cycle handles executor failures gracefully"""
    orch = ArbitrageOrchestrator(dry_run=False)

    # Setup mocks
    orch.db = AsyncMock()
    orch.db.get_daily_loss.return_value = 0.0
    orch.db.get_open_positions.return_value = []

    orch.detector = AsyncMock()
    orch.detector.scan_all_markets.return_value = [mock_opportunity]

    # Executor raises an exception
    orch.executor = AsyncMock()
    orch.executor.execute_opportunity.side_effect = Exception("Execution failed")

    # Should not crash
    await orch.scan_cycle()

    # Cycle completed but no successful trades
    assert orch.cycle_count == 1
    assert orch.stats["total_trades"] == 0


# Test Statistics
@pytest.mark.asyncio
async def test_success_rate_calculation():
    """Test success rate calculation"""
    orch = ArbitrageOrchestrator(dry_run=True)

    # No trades yet
    assert orch._get_success_rate() == 0.0

    # Add some stats
    orch.stats["total_trades"] = 10
    orch.stats["successful_trades"] = 8

    assert orch._get_success_rate() == 0.8


# Test Run Once
@pytest.mark.asyncio
async def test_run_once():
    """Test run_once method executes single cycle"""
    orch = ArbitrageOrchestrator(dry_run=True)

    with patch.object(orch, 'setup') as mock_setup, \
         patch.object(orch, 'scan_cycle') as mock_scan, \
         patch.object(orch, 'shutdown') as mock_shutdown:

        mock_setup.return_value = asyncio.coroutine(lambda: None)()
        mock_scan.return_value = asyncio.coroutine(lambda: None)()
        mock_shutdown.return_value = asyncio.coroutine(lambda: None)()

        await orch.run_once()

        mock_setup.assert_called_once()
        mock_scan.assert_called_once()
        mock_shutdown.assert_called_once()


# Test Shutdown
@pytest.mark.asyncio
async def test_shutdown_closes_all_connections():
    """Test shutdown closes all connections properly"""
    orch = ArbitrageOrchestrator(dry_run=True)

    # Create mock components
    orch.client = AsyncMock()
    orch.trader = AsyncMock()
    orch.db = AsyncMock()
    orch.scheduler = MagicMock()
    orch.scheduler.running = True
    orch.running = True

    await orch.shutdown()

    # Verify all components were closed
    orch.client.close.assert_called_once()
    orch.trader.close.assert_called_once()
    orch.db.close.assert_called_once()
    orch.scheduler.shutdown.assert_called_once()
    assert orch.running is False


# Integration Test
@pytest.mark.asyncio
async def test_full_cycle_integration(mock_opportunity, mock_execution_result):
    """Integration test for a complete scan-execute-record cycle"""
    orch = ArbitrageOrchestrator(dry_run=False)

    # Setup all mocks
    orch.db = AsyncMock()
    orch.db.get_daily_loss.return_value = 0.0
    orch.db.get_open_positions.return_value = []
    orch.db.save_trade = AsyncMock()

    orch.detector = AsyncMock()
    orch.detector.scan_all_markets.return_value = [mock_opportunity]

    orch.executor = AsyncMock()
    orch.executor.execute_opportunity.return_value = mock_execution_result

    # Run cycle
    await orch.scan_cycle()

    # Verify full flow
    orch.detector.scan_all_markets.assert_called_once()
    orch.executor.execute_opportunity.assert_called_once()
    orch.db.save_trade.assert_called_once()

    # Verify statistics
    assert orch.stats["total_opportunities"] == 1
    assert orch.stats["total_trades"] == 1
    assert orch.stats["successful_trades"] == 1
    assert orch.stats["total_profit_usd"] == 8.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
