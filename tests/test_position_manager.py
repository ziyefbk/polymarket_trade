"""
Unit tests for Position Manager
"""
import pytest
import sys
sys.path.append("..")

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch
import uuid

from config.settings import TradingConfig
from src.strategy.position_manager import PositionManager
from src.types.opportunities import ArbitrageOpportunity
from src.types.common import RiskLimitExceededError


def create_mock_opportunity(
    yes_price: float = 0.52,
    no_price: float = 0.52,
    liquidity: float = 50000.0,
    net_profit_pct: float = 0.03,
    confidence_score: float = 0.85
) -> ArbitrageOpportunity:
    """Helper function to create a mock arbitrage opportunity"""
    return ArbitrageOpportunity(
        opportunity_id=str(uuid.uuid4()),
        event_id="test_event_123",
        event_title="Test Event",
        yes_token_id="yes_token_123",
        yes_price=yes_price,
        yes_liquidity=liquidity,
        no_token_id="no_token_123",
        no_price=no_price,
        no_liquidity=liquidity,
        price_sum=yes_price + no_price,
        spread=abs(yes_price + no_price - 1.0),
        arbitrage_type="OVERPRICED" if yes_price + no_price > 1 else "UNDERPRICED",
        expected_profit_pct=net_profit_pct,
        expected_profit_usd=net_profit_pct * 1000,
        estimated_fees=10.0,
        estimated_slippage=5.0,
        net_profit_pct=net_profit_pct,
        is_executable=True,
        required_capital=1000.0,
        confidence_score=confidence_score,
        detected_at=datetime.utcnow(),
        valid_until=datetime.utcnow() + timedelta(minutes=5)
    )


@pytest.fixture
def trading_config():
    """Create a test trading configuration"""
    return TradingConfig(
        max_position_size=1000.0,
        max_daily_loss=100.0,
        max_open_positions=10,
        min_profit_threshold=0.02,
        slippage_tolerance=0.01
    )


@pytest.fixture
def position_manager(trading_config):
    """Create a position manager instance for testing"""
    return PositionManager(
        config=trading_config,
        db=None,  # No database for unit tests
        initial_capital=10000.0
    )


class TestPositionManagerInitialization:
    """Tests for PositionManager initialization"""

    def test_initialization_with_config(self, trading_config):
        """Test basic initialization"""
        manager = PositionManager(
            config=trading_config,
            initial_capital=5000.0
        )

        assert manager.config == trading_config
        assert manager._initial_capital == 5000.0
        assert manager._simulated_capital == 5000.0
        assert manager.db is None

    def test_initialization_with_database(self, trading_config):
        """Test initialization with database"""
        mock_db = MagicMock()
        manager = PositionManager(
            config=trading_config,
            db=mock_db,
            initial_capital=10000.0
        )

        assert manager.db == mock_db


class TestCalculatePositionSize:
    """Tests for position size calculation"""

    @pytest.mark.asyncio
    async def test_basic_position_size_calculation(self, position_manager):
        """Test basic position size calculation with typical opportunity"""
        opportunity = create_mock_opportunity(
            liquidity=100000.0,
            net_profit_pct=0.03,
            confidence_score=0.9
        )

        position_size = await position_manager.calculate_position_size(opportunity)

        # Should return a reasonable position size
        assert 0 < position_size <= 1000.0  # Max position size
        assert isinstance(position_size, float)

    @pytest.mark.asyncio
    async def test_position_size_respects_max_limit(self, position_manager):
        """Test that position size respects max_position_size config"""
        # Create very profitable opportunity with high confidence
        opportunity = create_mock_opportunity(
            liquidity=1000000.0,  # Abundant liquidity
            net_profit_pct=0.10,  # High profit
            confidence_score=0.99
        )

        position_size = await position_manager.calculate_position_size(opportunity)

        # Should be capped at max_position_size
        assert position_size <= position_manager.config.max_position_size

    @pytest.mark.asyncio
    async def test_low_liquidity_reduces_position_size(self, position_manager):
        """Test that low liquidity results in smaller position"""
        # Low liquidity opportunity
        opportunity = create_mock_opportunity(
            liquidity=5000.0,  # Low liquidity
            net_profit_pct=0.03,
            confidence_score=0.85
        )

        position_size = await position_manager.calculate_position_size(opportunity)

        # Should be smaller due to execution risk
        assert position_size < 1000.0

    @pytest.mark.asyncio
    async def test_low_confidence_reduces_position_size(self, position_manager):
        """Test that low confidence results in smaller position"""
        # Low confidence opportunity
        opportunity = create_mock_opportunity(
            liquidity=100000.0,
            net_profit_pct=0.03,
            confidence_score=0.5  # Low confidence
        )

        position_size = await position_manager.calculate_position_size(opportunity)

        # Should be smaller due to low confidence
        assert position_size < 500.0

    @pytest.mark.asyncio
    async def test_insufficient_capital(self, position_manager):
        """Test behavior when capital is insufficient"""
        # Deplete capital
        position_manager.set_simulated_capital(0.0)

        opportunity = create_mock_opportunity()

        position_size = await position_manager.calculate_position_size(opportunity)

        # Should return 0
        assert position_size == 0.0

    @pytest.mark.asyncio
    async def test_daily_loss_limit_exceeded(self, position_manager):
        """Test that position sizing fails when daily loss limit is exceeded"""
        # Simulate reaching daily loss limit
        position_manager._cached_daily_loss = 150.0  # Exceeds max of 100

        opportunity = create_mock_opportunity()

        # Should raise RiskLimitExceededError
        with pytest.raises(RiskLimitExceededError, match="daily loss limit"):
            await position_manager.calculate_position_size(opportunity)

    @pytest.mark.asyncio
    async def test_max_open_positions_exceeded(self, position_manager):
        """Test that position sizing fails when max open positions reached"""
        # Simulate max open positions
        position_manager._cached_open_positions_count = 10

        opportunity = create_mock_opportunity()

        # Should raise RiskLimitExceededError
        with pytest.raises(RiskLimitExceededError, match="max open positions"):
            await position_manager.calculate_position_size(opportunity)

    @pytest.mark.asyncio
    async def test_small_position_below_minimum(self, position_manager):
        """Test that very small positions are rejected"""
        # Create opportunity that would result in tiny position
        opportunity = create_mock_opportunity(
            liquidity=1000.0,
            net_profit_pct=0.001,  # Very low profit
            confidence_score=0.3
        )

        position_size = await position_manager.calculate_position_size(opportunity)

        # Should return 0 if below minimum trade size
        assert position_size == 0.0 or position_size >= 10.0

    @pytest.mark.asyncio
    async def test_position_size_with_conservative_factor(self, position_manager):
        """Test different conservative factors"""
        opportunity = create_mock_opportunity(
            liquidity=100000.0,
            net_profit_pct=0.05,
            confidence_score=0.95
        )

        # More conservative
        size_conservative = await position_manager.calculate_position_size(
            opportunity,
            conservative_factor=0.25
        )

        # Less conservative
        size_aggressive = await position_manager.calculate_position_size(
            opportunity,
            conservative_factor=0.75
        )

        # More conservative should be smaller
        assert size_conservative < size_aggressive


class TestCheckRiskLimits:
    """Tests for risk limit checking"""

    @pytest.mark.asyncio
    async def test_all_limits_ok(self, position_manager):
        """Test when all risk limits are within bounds"""
        result = await position_manager.check_risk_limits()

        assert result["daily_loss_ok"] is True
        assert result["position_count_ok"] is True
        assert result["capital_available"] is True
        assert result["can_trade"] is True

    @pytest.mark.asyncio
    async def test_daily_loss_limit_exceeded(self, position_manager):
        """Test when daily loss limit is exceeded"""
        position_manager._cached_daily_loss = 150.0  # Exceeds 100 limit

        result = await position_manager.check_risk_limits()

        assert result["daily_loss_ok"] is False
        assert result["can_trade"] is False

    @pytest.mark.asyncio
    async def test_position_count_limit_exceeded(self, position_manager):
        """Test when open positions limit is exceeded"""
        position_manager._cached_open_positions_count = 10  # Equals max

        result = await position_manager.check_risk_limits()

        assert result["position_count_ok"] is False
        assert result["can_trade"] is False

    @pytest.mark.asyncio
    async def test_no_capital_available(self, position_manager):
        """Test when no capital is available"""
        position_manager.set_simulated_capital(0.0)

        result = await position_manager.check_risk_limits()

        assert result["capital_available"] is False
        assert result["can_trade"] is False

    @pytest.mark.asyncio
    async def test_multiple_limits_exceeded(self, position_manager):
        """Test when multiple limits are exceeded"""
        position_manager._cached_daily_loss = 150.0
        position_manager._cached_open_positions_count = 10
        position_manager.set_simulated_capital(0.0)

        result = await position_manager.check_risk_limits()

        assert result["daily_loss_ok"] is False
        assert result["position_count_ok"] is False
        assert result["capital_available"] is False
        assert result["can_trade"] is False


class TestCapitalManagement:
    """Tests for capital management methods"""

    @pytest.mark.asyncio
    async def test_get_available_capital_without_db(self, position_manager):
        """Test getting available capital in testing mode"""
        capital = await position_manager.get_available_capital()

        assert capital == 10000.0

    @pytest.mark.asyncio
    async def test_set_simulated_capital(self, position_manager):
        """Test setting simulated capital"""
        position_manager.set_simulated_capital(5000.0)

        capital = await position_manager.get_available_capital()
        assert capital == 5000.0

    @pytest.mark.asyncio
    async def test_get_daily_loss(self, position_manager):
        """Test getting daily loss"""
        loss = await position_manager.get_daily_loss()

        assert loss == 0.0
        assert isinstance(loss, float)

    @pytest.mark.asyncio
    async def test_get_open_positions_count(self, position_manager):
        """Test getting open positions count"""
        count = await position_manager.get_open_positions_count()

        assert count == 0
        assert isinstance(count, int)


class TestTradeResultTracking:
    """Tests for trade result tracking"""

    @pytest.mark.asyncio
    async def test_record_profitable_trade(self, position_manager):
        """Test recording a profitable trade"""
        initial_capital = await position_manager.get_available_capital()

        await position_manager.record_trade_result(
            opportunity_id="test_123",
            capital_used=500.0,
            profit=15.0,  # $15 profit
            success=True
        )

        # Capital should increase
        new_capital = await position_manager.get_available_capital()
        assert new_capital == initial_capital + 15.0

        # Daily loss should still be 0
        daily_loss = await position_manager.get_daily_loss()
        assert daily_loss == 0.0

    @pytest.mark.asyncio
    async def test_record_losing_trade(self, position_manager):
        """Test recording a losing trade"""
        initial_capital = await position_manager.get_available_capital()

        await position_manager.record_trade_result(
            opportunity_id="test_123",
            capital_used=500.0,
            profit=-25.0,  # $25 loss
            success=False
        )

        # Capital should decrease
        new_capital = await position_manager.get_available_capital()
        assert new_capital == initial_capital - 25.0

        # Daily loss should increase
        daily_loss = await position_manager.get_daily_loss()
        assert daily_loss == 25.0

    @pytest.mark.asyncio
    async def test_multiple_losing_trades(self, position_manager):
        """Test recording multiple losing trades"""
        await position_manager.record_trade_result(
            opportunity_id="test_1",
            capital_used=500.0,
            profit=-20.0,
            success=False
        )

        await position_manager.record_trade_result(
            opportunity_id="test_2",
            capital_used=300.0,
            profit=-15.0,
            success=False
        )

        # Daily loss should accumulate
        daily_loss = await position_manager.get_daily_loss()
        assert daily_loss == 35.0

    @pytest.mark.asyncio
    async def test_update_open_positions_count(self, position_manager):
        """Test updating open positions count"""
        # Open a position
        await position_manager.update_open_positions_count(+1)
        count = await position_manager.get_open_positions_count()
        assert count == 1

        # Open another
        await position_manager.update_open_positions_count(+1)
        count = await position_manager.get_open_positions_count()
        assert count == 2

        # Close one
        await position_manager.update_open_positions_count(-1)
        count = await position_manager.get_open_positions_count()
        assert count == 1

        # Close another (should not go negative)
        await position_manager.update_open_positions_count(-1)
        await position_manager.update_open_positions_count(-1)
        count = await position_manager.get_open_positions_count()
        assert count == 0


class TestDailyMetricsReset:
    """Tests for daily metrics reset"""

    @pytest.mark.asyncio
    async def test_daily_loss_resets_on_new_day(self, position_manager):
        """Test that daily loss resets on new day"""
        # Record some losses
        await position_manager.record_trade_result(
            opportunity_id="test_1",
            capital_used=500.0,
            profit=-50.0,
            success=False
        )

        daily_loss = await position_manager.get_daily_loss()
        assert daily_loss == 50.0

        # Simulate new day by resetting
        position_manager.reset_daily_metrics()

        daily_loss = await position_manager.get_daily_loss()
        assert daily_loss == 0.0

    @pytest.mark.asyncio
    async def test_manual_reset(self, position_manager):
        """Test manual reset of daily metrics"""
        # Set some values
        position_manager._cached_daily_loss = 75.0

        position_manager.reset_daily_metrics()

        assert position_manager._cached_daily_loss == 0.0
        assert position_manager._daily_loss_reset_time is not None


class TestIntegrationScenarios:
    """Integration tests for realistic trading scenarios"""

    @pytest.mark.asyncio
    async def test_successful_trading_day(self, position_manager):
        """Test a successful trading day with multiple trades"""
        initial_capital = await position_manager.get_available_capital()

        # Trade 1: Profitable
        opportunity1 = create_mock_opportunity(liquidity=100000.0)
        size1 = await position_manager.calculate_position_size(opportunity1)
        assert size1 > 0

        await position_manager.update_open_positions_count(+1)
        await position_manager.record_trade_result(
            opportunity_id=opportunity1.opportunity_id,
            capital_used=size1,
            profit=size1 * 0.03,  # 3% profit
            success=True
        )
        await position_manager.update_open_positions_count(-1)

        # Trade 2: Profitable
        opportunity2 = create_mock_opportunity(liquidity=80000.0)
        size2 = await position_manager.calculate_position_size(opportunity2)
        assert size2 > 0

        await position_manager.record_trade_result(
            opportunity_id=opportunity2.opportunity_id,
            capital_used=size2,
            profit=size2 * 0.025,  # 2.5% profit
            success=True
        )

        # Check final state
        final_capital = await position_manager.get_available_capital()
        assert final_capital > initial_capital

        risk_check = await position_manager.check_risk_limits()
        assert risk_check["can_trade"] is True

    @pytest.mark.asyncio
    async def test_approaching_daily_loss_limit(self, position_manager):
        """Test behavior when approaching daily loss limit"""
        # Record losses approaching limit
        await position_manager.record_trade_result(
            opportunity_id="test_1",
            capital_used=500.0,
            profit=-80.0,  # Close to 100 limit
            success=False
        )

        # Should still be able to trade (not yet exceeded)
        risk_check = await position_manager.check_risk_limits()
        assert risk_check["can_trade"] is True

        # One more loss pushes over limit
        await position_manager.record_trade_result(
            opportunity_id="test_2",
            capital_used=300.0,
            profit=-25.0,
            success=False
        )

        # Now should not be able to trade
        risk_check = await position_manager.check_risk_limits()
        assert risk_check["can_trade"] is False

    @pytest.mark.asyncio
    async def test_capital_depletion(self, position_manager):
        """Test behavior as capital depletes"""
        # Record significant losses
        for i in range(5):
            await position_manager.record_trade_result(
                opportunity_id=f"test_{i}",
                capital_used=1000.0,
                profit=-1500.0,  # Significant loss
                success=False
            )

        # Capital should be significantly reduced
        capital = await position_manager.get_available_capital()
        assert capital < 5000.0

        # May hit daily loss limit first
        risk_check = await position_manager.check_risk_limits()
        assert risk_check["can_trade"] is False

    @pytest.mark.asyncio
    async def test_max_positions_management(self, position_manager):
        """Test managing maximum open positions"""
        # Open positions up to limit
        for i in range(10):
            await position_manager.update_open_positions_count(+1)

        # Should not be able to open more
        risk_check = await position_manager.check_risk_limits()
        assert risk_check["can_trade"] is False

        # Close some positions
        for i in range(3):
            await position_manager.update_open_positions_count(-1)

        # Should be able to trade again
        risk_check = await position_manager.check_risk_limits()
        assert risk_check["can_trade"] is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
