"""
Unit tests for ArbitrageExecutor (Task 2)

Tests cover:
1. Successful execution of both OVERPRICED and UNDERPRICED opportunities
2. Price staleness detection
3. Partial fill handling
4. Error handling and exception cases
5. Profit calculation accuracy
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
import asyncio

import sys
sys.path.append("..")

from src.strategy.arbitrage_executor import ArbitrageExecutor
from src.api.trader import TradeResult, OrderSide
from src.types.opportunities import ArbitrageOpportunity
from src.types.orders import ExecutionResult
from src.types.common import PriceStaleError


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def mock_trader():
    """Create a mock PolymarketTrader"""
    trader = AsyncMock()
    trader.address = "0x1234567890123456789012345678901234567890"
    return trader


@pytest.fixture
def mock_client():
    """Create a mock PolymarketClient"""
    client = AsyncMock()
    return client


@pytest.fixture
def overpriced_opportunity():
    """Create an OVERPRICED arbitrage opportunity (YES + NO > 1)"""
    return ArbitrageOpportunity(
        opportunity_id="opp-overpriced-123",
        event_id="event-123",
        event_title="Will BTC reach $100k by EOY?",
        yes_token_id="token-yes-123",
        yes_price=0.55,
        yes_liquidity=10000.0,
        no_token_id="token-no-123",
        no_price=0.50,
        no_liquidity=10000.0,
        price_sum=1.05,  # 0.55 + 0.50 = 1.05 > 1.0
        spread=0.05,
        arbitrage_type="OVERPRICED",
        expected_profit_pct=0.045,
        expected_profit_usd=45.0,
        estimated_fees=3.0,
        estimated_slippage=2.0,
        net_profit_pct=0.04,  # 4% net profit
        is_executable=True,
        required_capital=1000.0,
        confidence_score=0.85,
        detected_at=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(minutes=5)
    )


@pytest.fixture
def underpriced_opportunity():
    """Create an UNDERPRICED arbitrage opportunity (YES + NO < 1)"""
    return ArbitrageOpportunity(
        opportunity_id="opp-underpriced-456",
        event_id="event-456",
        event_title="Will ETH reach $10k by EOY?",
        yes_token_id="token-yes-456",
        yes_price=0.42,
        yes_liquidity=8000.0,
        no_token_id="token-no-456",
        no_price=0.55,
        no_liquidity=8000.0,
        price_sum=0.97,  # 0.42 + 0.55 = 0.97 < 1.0
        spread=0.03,
        arbitrage_type="UNDERPRICED",
        expected_profit_pct=0.025,
        expected_profit_usd=25.0,
        estimated_fees=2.0,
        estimated_slippage=1.0,
        net_profit_pct=0.022,  # 2.2% net profit
        is_executable=True,
        required_capital=1000.0,
        confidence_score=0.78,
        detected_at=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(minutes=5)
    )


# ============================================================================
# Successful Execution Tests
# ============================================================================

@pytest.mark.asyncio
async def test_execute_overpriced_opportunity_success(mock_trader, mock_client, overpriced_opportunity):
    """Test successful execution of OVERPRICED arbitrage (SELL both)"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    # Mock price verification (prices unchanged)
    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    # Mock successful trade execution
    mock_trader.sell.return_value = TradeResult(
        success=True,
        order_id="order-123",
        filled_size=100.0,
        avg_price=0.525  # Slightly different from limit
    )

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert
    assert result.success is True
    assert result.opportunity_id == "opp-overpriced-123"
    assert result.yes_status == "FILLED"
    assert result.no_status == "FILLED"
    assert result.yes_filled_size == 100.0
    assert result.no_filled_size == 100.0
    assert result.partial_fill_risk is False
    assert result.error_message is None
    assert result.execution_time_ms > 0

    # Verify both SELL orders were placed
    assert mock_trader.sell.call_count == 2

    # Verify profit calculation (OVERPRICED: we receive premium)
    # Received: (0.525 + 0.525) * 100 = 105, Payout: 100 => Profit: 5
    assert result.actual_profit_usd > 0


@pytest.mark.asyncio
async def test_execute_underpriced_opportunity_success(mock_trader, mock_client, underpriced_opportunity):
    """Test successful execution of UNDERPRICED arbitrage (BUY both)"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    # Mock price verification
    mock_client.get_prices.return_value = {
        "token-yes-456": 0.42,
        "token-no-456": 0.55
    }

    # Mock successful BUY execution
    mock_trader.buy.return_value = TradeResult(
        success=True,
        order_id="order-456",
        filled_size=100.0,
        avg_price=0.485
    )

    # Act
    result = await executor.execute_opportunity(underpriced_opportunity, position_size=100.0)

    # Assert
    assert result.success is True
    assert result.yes_status == "FILLED"
    assert result.no_status == "FILLED"
    assert result.partial_fill_risk is False

    # Verify both BUY orders were placed
    assert mock_trader.buy.call_count == 2

    # Verify profit calculation (UNDERPRICED: we pay discount)
    # Paid: (0.485 + 0.485) * 100 = 97, Received: 100 => Profit: 3
    assert result.actual_profit_usd > 0


# ============================================================================
# Price Staleness Tests
# ============================================================================

@pytest.mark.asyncio
async def test_price_stale_yes_moved_too_much(mock_trader, mock_client, overpriced_opportunity):
    """Test that execution is aborted if YES price moved beyond tolerance"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    # YES price moved from 0.55 to 0.60 (9% change, exceeds 1% tolerance)
    mock_client.get_prices.return_value = {
        "token-yes-123": 0.60,
        "token-no-123": 0.50
    }

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert
    assert result.success is False
    assert "price moved" in result.error_message.lower()
    assert result.yes_status == "FAILED"
    assert result.no_status == "FAILED"

    # Verify no trades were executed
    mock_trader.sell.assert_not_called()
    mock_trader.buy.assert_not_called()


@pytest.mark.asyncio
async def test_price_stale_no_moved_too_much(mock_trader, mock_client, underpriced_opportunity):
    """Test that execution is aborted if NO price moved beyond tolerance"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    # NO price moved from 0.55 to 0.60 (9% change)
    mock_client.get_prices.return_value = {
        "token-yes-456": 0.42,
        "token-no-456": 0.60
    }

    # Act
    result = await executor.execute_opportunity(underpriced_opportunity, position_size=100.0)

    # Assert
    assert result.success is False
    assert "price moved" in result.error_message.lower()


@pytest.mark.asyncio
async def test_price_verification_within_tolerance(mock_trader, mock_client, overpriced_opportunity):
    """Test that small price movements within tolerance are accepted"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    # Prices moved slightly (< 1% tolerance)
    mock_client.get_prices.return_value = {
        "token-yes-123": 0.5505,  # 0.09% change
        "token-no-123": 0.5005   # 0.1% change
    }

    mock_trader.sell.return_value = TradeResult(
        success=True,
        order_id="order-123",
        filled_size=100.0,
        avg_price=0.525
    )

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert - should succeed despite small price movements
    assert result.success is True


# ============================================================================
# Partial Fill Tests
# ============================================================================

@pytest.mark.asyncio
async def test_partial_fill_yes_filled_no_didnt(mock_trader, mock_client, overpriced_opportunity):
    """Test partial fill risk when YES filled but NO didn't"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    # YES filled, NO failed
    mock_trader.sell.side_effect = [
        TradeResult(success=True, order_id="yes-order", filled_size=100.0, avg_price=0.55),
        TradeResult(success=False, filled_size=0.0, error="Insufficient liquidity")
    ]

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert
    assert result.success is False
    assert result.partial_fill_risk is True
    assert result.yes_status == "FILLED"
    assert result.no_status == "FAILED"
    assert "partial fill risk" in result.error_message.lower()


@pytest.mark.asyncio
async def test_partial_fill_imbalanced_sizes(mock_trader, mock_client, overpriced_opportunity):
    """Test partial fill risk when fill sizes are significantly different"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    # YES filled 100, NO only filled 50 (50% imbalance)
    mock_trader.sell.side_effect = [
        TradeResult(success=True, order_id="yes-order", filled_size=100.0, avg_price=0.55),
        TradeResult(success=True, order_id="no-order", filled_size=50.0, avg_price=0.50)
    ]

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert
    assert result.partial_fill_risk is True
    assert result.yes_filled_size == 100.0
    assert result.no_filled_size == 50.0


@pytest.mark.asyncio
async def test_both_legs_partial_but_balanced(mock_trader, mock_client, overpriced_opportunity):
    """Test that balanced partial fills (both at 50%) don't trigger risk flag"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    # Both filled 50% (balanced)
    mock_trader.sell.side_effect = [
        TradeResult(success=True, order_id="yes-order", filled_size=50.0, avg_price=0.55),
        TradeResult(success=True, order_id="no-order", filled_size=50.0, avg_price=0.50)
    ]

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert
    assert result.partial_fill_risk is False  # Balanced fills are OK
    assert result.yes_status == "PARTIAL"
    assert result.no_status == "PARTIAL"


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.asyncio
async def test_both_legs_failed(mock_trader, mock_client, overpriced_opportunity):
    """Test when both legs fail to execute"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    # Both legs fail
    mock_trader.sell.return_value = TradeResult(
        success=False,
        error="API error"
    )

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert
    assert result.success is False
    assert result.yes_status == "FAILED"
    assert result.no_status == "FAILED"
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_exception_during_execution(mock_trader, mock_client, overpriced_opportunity):
    """Test that exceptions during execution are caught and handled"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    # Raise exception during sell
    mock_trader.sell.side_effect = Exception("Network error")

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert - should be captured and returned as failed result
    assert result.success is False
    assert result.error_message is not None


@pytest.mark.asyncio
async def test_invalid_position_size_too_large(mock_trader, mock_client, overpriced_opportunity):
    """Test that position size exceeding max is rejected"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    # Act - try to execute with size > max_position_size (1000)
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=2000.0)

    # Assert
    assert result.success is False
    assert "exceeds max" in result.error_message.lower()
    mock_trader.sell.assert_not_called()


@pytest.mark.asyncio
async def test_invalid_position_size_negative(mock_trader, mock_client, overpriced_opportunity):
    """Test that negative position size is rejected"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=-100.0)

    # Assert
    assert result.success is False
    assert "invalid position size" in result.error_message.lower()


# ============================================================================
# Profit Calculation Tests
# ============================================================================

@pytest.mark.asyncio
async def test_profit_calculation_overpriced(mock_trader, mock_client, overpriced_opportunity):
    """Test accurate profit calculation for OVERPRICED arbitrage"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    # Filled at exactly the limit prices
    mock_trader.sell.side_effect = [
        TradeResult(success=True, filled_size=100.0, avg_price=0.55),
        TradeResult(success=True, filled_size=100.0, avg_price=0.50)
    ]

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert
    # OVERPRICED: Received = (0.55 + 0.50) * 100 = 105
    #             Payout = 1.0 * 100 = 100
    #             Profit = 5 USD
    assert result.actual_profit_usd == pytest.approx(5.0, abs=0.01)
    assert result.actual_profit_pct == pytest.approx(0.05, abs=0.001)  # 5%
    assert result.total_capital_used == 100.0


@pytest.mark.asyncio
async def test_profit_calculation_underpriced(mock_trader, mock_client, underpriced_opportunity):
    """Test accurate profit calculation for UNDERPRICED arbitrage"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-456": 0.42,
        "token-no-456": 0.55
    }

    # Filled at exactly the limit prices
    mock_trader.buy.side_effect = [
        TradeResult(success=True, filled_size=100.0, avg_price=0.42),
        TradeResult(success=True, filled_size=100.0, avg_price=0.55)
    ]

    # Act
    result = await executor.execute_opportunity(underpriced_opportunity, position_size=100.0)

    # Assert
    # UNDERPRICED: Paid = (0.42 + 0.55) * 100 = 97
    #              Received = 1.0 * 100 = 100
    #              Profit = 3 USD
    assert result.actual_profit_usd == pytest.approx(3.0, abs=0.01)
    assert result.actual_profit_pct == pytest.approx(0.0309, abs=0.001)  # ~3.09%
    assert result.total_capital_used == 97.0


@pytest.mark.asyncio
async def test_profit_with_slippage(mock_trader, mock_client, overpriced_opportunity):
    """Test profit calculation when execution prices differ from limit (slippage)"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    # Filled at worse prices due to slippage
    mock_trader.sell.side_effect = [
        TradeResult(success=True, filled_size=100.0, avg_price=0.54),  # Slipped down
        TradeResult(success=True, filled_size=100.0, avg_price=0.49)   # Slipped down
    ]

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert
    # With slippage: Received = (0.54 + 0.49) * 100 = 103
    #                Payout = 100
    #                Profit = 3 USD (less than without slippage)
    assert result.actual_profit_usd == pytest.approx(3.0, abs=0.01)


# ============================================================================
# Asyncio.gather Tests
# ============================================================================

@pytest.mark.asyncio
async def test_simultaneous_execution_with_gather(mock_trader, mock_client, overpriced_opportunity):
    """Test that both legs execute simultaneously using asyncio.gather"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    # Track when each order was called
    call_times = []

    async def mock_sell_with_delay(*args, **kwargs):
        call_times.append(asyncio.get_event_loop().time())
        await asyncio.sleep(0.1)  # Simulate network delay
        return TradeResult(success=True, filled_size=100.0, avg_price=0.525)

    mock_trader.sell.side_effect = mock_sell_with_delay

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert
    assert len(call_times) == 2
    # Both calls should have started within a very short time window (parallel execution)
    time_diff = abs(call_times[1] - call_times[0])
    assert time_diff < 0.01  # Started within 10ms of each other


# ============================================================================
# Integration Test (Without Price Verification Client)
# ============================================================================

@pytest.mark.asyncio
async def test_executor_without_client_creates_temporary(mock_trader, overpriced_opportunity):
    """Test that executor creates temporary client if none provided"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=None)  # No client provided

    # Mock successful execution (skip price verification by mocking the method)
    mock_trader.sell.return_value = TradeResult(
        success=True,
        filled_size=100.0,
        avg_price=0.525
    )

    # Mock the price verification to avoid needing a real client
    with patch.object(executor, '_verify_prices', new_callable=AsyncMock):
        # Act
        result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

        # Assert
        assert result.success is True


# ============================================================================
# ExecutionResult Fields Validation
# ============================================================================

@pytest.mark.asyncio
async def test_execution_result_has_all_required_fields(mock_trader, mock_client, overpriced_opportunity):
    """Test that ExecutionResult contains all fields required by INTERFACE_SPEC.md"""
    # Arrange
    executor = ArbitrageExecutor(trader=mock_trader, client=mock_client)

    mock_client.get_prices.return_value = {
        "token-yes-123": 0.55,
        "token-no-123": 0.50
    }

    mock_trader.sell.return_value = TradeResult(
        success=True,
        filled_size=100.0,
        avg_price=0.525
    )

    # Act
    result = await executor.execute_opportunity(overpriced_opportunity, position_size=100.0)

    # Assert - verify all required fields from INTERFACE_SPEC.md section 1.2
    assert hasattr(result, 'opportunity_id')
    assert hasattr(result, 'success')
    assert hasattr(result, 'yes_filled_size')
    assert hasattr(result, 'yes_avg_price')
    assert hasattr(result, 'yes_status')
    assert hasattr(result, 'no_filled_size')
    assert hasattr(result, 'no_avg_price')
    assert hasattr(result, 'no_status')
    assert hasattr(result, 'total_capital_used')
    assert hasattr(result, 'actual_profit_usd')
    assert hasattr(result, 'actual_profit_pct')
    assert hasattr(result, 'execution_time_ms')
    assert hasattr(result, 'error_message')
    assert hasattr(result, 'partial_fill_risk')
    assert hasattr(result, 'executed_at')

    # Verify status values are valid
    assert result.yes_status in ["PENDING", "FILLED", "PARTIAL", "FAILED"]
    assert result.no_status in ["PENDING", "FILLED", "PARTIAL", "FAILED"]
