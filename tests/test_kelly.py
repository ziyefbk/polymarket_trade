"""
Unit tests for Kelly Criterion position sizing utilities
"""
import pytest
import sys
sys.path.append("..")

from src.utils.kelly import (
    calculate_kelly_fraction,
    calculate_position_size,
    estimate_execution_probability
)


class TestCalculateKellyFraction:
    """Tests for Kelly Criterion fraction calculation"""

    def test_basic_kelly_calculation(self):
        """Test basic Kelly Criterion calculation with typical values"""
        # 90% win probability, 5% profit, half-Kelly
        fraction = calculate_kelly_fraction(
            win_probability=0.90,
            profit_ratio=0.05,
            conservative_factor=0.5
        )

        # Kelly formula: (bp - q) / b = (0.05 * 0.90 - 0.10) / 0.05 = -0.55
        # Since negative, should return 0
        # Actually with 90% win and 5% profit: (0.05 * 0.9 - 0.1) / 0.05 = (0.045 - 0.1) / 0.05 = -1.1
        # Wait, let me recalculate: if win_prob = 0.9, profit = 0.05
        # Kelly = (0.05 * 0.9 - 0.1) / 0.05 = -0.055 / 0.05 = -1.1
        # This is negative, so should be 0

        # Let's use a better example: 95% win, 3% profit
        fraction = calculate_kelly_fraction(
            win_probability=0.95,
            profit_ratio=0.03,
            conservative_factor=0.5
        )

        # Kelly = (0.03 * 0.95 - 0.05) / 0.03 = (0.0285 - 0.05) / 0.03 = -0.715
        # Still negative!

        # For arbitrage, we need high win probability relative to loss probability
        # Let's use 99% win, 2% profit
        fraction = calculate_kelly_fraction(
            win_probability=0.99,
            profit_ratio=0.02,
            conservative_factor=0.5
        )

        # Kelly = (0.02 * 0.99 - 0.01) / 0.02 = (0.0198 - 0.01) / 0.02 = 0.49
        # Half-Kelly = 0.245
        assert 0 < fraction <= 0.25
        assert isinstance(fraction, float)

    def test_perfect_arbitrage(self):
        """Test with 100% win probability (perfect arbitrage)"""
        fraction = calculate_kelly_fraction(
            win_probability=1.0,
            profit_ratio=0.05,
            conservative_factor=1.0
        )

        # Should return max_fraction (default 0.25)
        assert fraction == 0.25

    def test_zero_win_probability(self):
        """Test with 0% win probability"""
        fraction = calculate_kelly_fraction(
            win_probability=0.0,
            profit_ratio=0.05
        )

        assert fraction == 0.0

    def test_high_profit_ratio(self):
        """Test with high profit ratio"""
        fraction = calculate_kelly_fraction(
            win_probability=0.98,
            profit_ratio=0.10,  # 10% profit
            conservative_factor=0.5
        )

        # Kelly = (0.10 * 0.98 - 0.02) / 0.10 = 0.78
        # Half-Kelly = 0.39, but capped at max_fraction (0.25)
        assert fraction == 0.25

    def test_conservative_factor_application(self):
        """Test that conservative factor properly reduces position size"""
        # Full Kelly
        full_kelly = calculate_kelly_fraction(
            win_probability=0.99,
            profit_ratio=0.05,
            conservative_factor=1.0
        )

        # Half Kelly
        half_kelly = calculate_kelly_fraction(
            win_probability=0.99,
            profit_ratio=0.05,
            conservative_factor=0.5
        )

        # Quarter Kelly
        quarter_kelly = calculate_kelly_fraction(
            win_probability=0.99,
            profit_ratio=0.05,
            conservative_factor=0.25
        )

        assert half_kelly < full_kelly
        assert quarter_kelly < half_kelly
        assert quarter_kelly == pytest.approx(full_kelly * 0.25, rel=0.01)

    def test_max_fraction_cap(self):
        """Test that max_fraction caps the result"""
        fraction = calculate_kelly_fraction(
            win_probability=0.99,
            profit_ratio=0.20,  # Very high profit
            max_fraction=0.10,  # Cap at 10%
            conservative_factor=1.0
        )

        assert fraction <= 0.10

    def test_negative_kelly_returns_zero(self):
        """Test that negative Kelly (bad bet) returns 0"""
        # Low win probability, low profit = negative edge
        fraction = calculate_kelly_fraction(
            win_probability=0.50,
            profit_ratio=0.01,
            conservative_factor=1.0
        )

        # Kelly = (0.01 * 0.5 - 0.5) / 0.01 = -49.5
        assert fraction == 0.0

    def test_invalid_win_probability(self):
        """Test that invalid win probability raises ValueError"""
        with pytest.raises(ValueError, match="Win probability must be between 0 and 1"):
            calculate_kelly_fraction(
                win_probability=1.5,  # Invalid
                profit_ratio=0.05
            )

        with pytest.raises(ValueError, match="Win probability must be between 0 and 1"):
            calculate_kelly_fraction(
                win_probability=-0.1,  # Invalid
                profit_ratio=0.05
            )

    def test_invalid_profit_ratio(self):
        """Test that negative profit ratio raises ValueError"""
        with pytest.raises(ValueError, match="Profit ratio must be positive"):
            calculate_kelly_fraction(
                win_probability=0.9,
                profit_ratio=-0.05  # Invalid
            )

        with pytest.raises(ValueError, match="Profit ratio must be positive"):
            calculate_kelly_fraction(
                win_probability=0.9,
                profit_ratio=0.0  # Invalid
            )

    def test_invalid_max_fraction(self):
        """Test that invalid max_fraction raises ValueError"""
        with pytest.raises(ValueError, match="Max fraction must be between 0 and 1"):
            calculate_kelly_fraction(
                win_probability=0.9,
                profit_ratio=0.05,
                max_fraction=1.5  # Invalid
            )

    def test_invalid_conservative_factor(self):
        """Test that invalid conservative factor raises ValueError"""
        with pytest.raises(ValueError, match="Conservative factor must be between 0 and 1"):
            calculate_kelly_fraction(
                win_probability=0.9,
                profit_ratio=0.05,
                conservative_factor=1.5  # Invalid
            )


class TestCalculatePositionSize:
    """Tests for position size calculation in USD"""

    def test_basic_position_size(self):
        """Test basic position size calculation"""
        position_size = calculate_position_size(
            available_capital=10000.0,
            win_probability=0.95,
            profit_ratio=0.05,
            conservative_factor=0.5
        )

        # Kelly fraction should be calculated, then multiplied by capital
        assert 0 < position_size <= 10000.0
        assert isinstance(position_size, float)

    def test_position_size_with_max_cap(self):
        """Test that max_position_size caps the result"""
        position_size = calculate_position_size(
            available_capital=10000.0,
            win_probability=0.99,
            profit_ratio=0.10,
            max_position_size=500.0,  # Hard cap
            conservative_factor=1.0
        )

        assert position_size <= 500.0

    def test_zero_capital(self):
        """Test with zero available capital"""
        with pytest.raises(ValueError, match="Available capital must be positive"):
            calculate_position_size(
                available_capital=0.0,
                win_probability=0.95,
                profit_ratio=0.05
            )

    def test_small_capital(self):
        """Test with small capital amount"""
        position_size = calculate_position_size(
            available_capital=100.0,
            win_probability=0.95,
            profit_ratio=0.03,
            conservative_factor=0.5
        )

        # Should still work with small amounts
        assert 0 <= position_size <= 100.0

    def test_large_capital(self):
        """Test with large capital amount"""
        position_size = calculate_position_size(
            available_capital=1000000.0,  # $1M
            win_probability=0.99,
            profit_ratio=0.03,
            max_position_size=10000.0,  # Cap at $10k
            conservative_factor=0.5
        )

        # Should be capped at max_position_size
        assert position_size <= 10000.0

    def test_low_win_probability_gives_small_position(self):
        """Test that low win probability results in small/zero position"""
        position_size = calculate_position_size(
            available_capital=10000.0,
            win_probability=0.60,  # Relatively low
            profit_ratio=0.02,
            conservative_factor=0.5
        )

        # Should be very small or zero
        assert position_size < 1000.0  # Less than 10% of capital


class TestEstimateExecutionProbability:
    """Tests for execution probability estimation"""

    def test_high_liquidity_high_confidence(self):
        """Test with abundant liquidity and high confidence"""
        prob = estimate_execution_probability(
            liquidity=100000.0,  # $100k liquidity
            required_size=1000.0,  # $1k trade (1% of liquidity)
            confidence_score=0.9,
            slippage_tolerance=0.01
        )

        # Should be high probability
        assert 0.8 <= prob <= 1.0

    def test_low_liquidity(self):
        """Test with low liquidity relative to trade size"""
        prob = estimate_execution_probability(
            liquidity=5000.0,  # $5k liquidity
            required_size=2000.0,  # $2k trade (40% of liquidity)
            confidence_score=0.9,
            slippage_tolerance=0.01
        )

        # Should be lower probability due to liquidity constraints
        assert 0.3 <= prob <= 0.7

    def test_exact_liquidity_match(self):
        """Test when trade size equals liquidity"""
        prob = estimate_execution_probability(
            liquidity=1000.0,
            required_size=1000.0,  # Using 100% of liquidity
            confidence_score=0.9,
            slippage_tolerance=0.01
        )

        # Should be very low probability
        assert 0.0 <= prob <= 0.5

    def test_low_confidence_score(self):
        """Test with low confidence score"""
        prob = estimate_execution_probability(
            liquidity=100000.0,
            required_size=1000.0,
            confidence_score=0.3,  # Low confidence
            slippage_tolerance=0.01
        )

        # Should be reduced by low confidence
        assert 0.2 <= prob <= 0.6

    def test_high_slippage_tolerance(self):
        """Test with high slippage tolerance"""
        prob = estimate_execution_probability(
            liquidity=100000.0,
            required_size=1000.0,
            confidence_score=0.9,
            slippage_tolerance=0.05  # 5% slippage tolerance
        )

        # Should still be reasonable
        assert 0.5 <= prob <= 1.0

    def test_zero_liquidity(self):
        """Test with zero liquidity"""
        prob = estimate_execution_probability(
            liquidity=0.0,
            required_size=1000.0,
            confidence_score=0.9,
            slippage_tolerance=0.01
        )

        assert prob == 0.0

    def test_zero_required_size(self):
        """Test with zero required size"""
        prob = estimate_execution_probability(
            liquidity=100000.0,
            required_size=0.0,
            confidence_score=0.9,
            slippage_tolerance=0.01
        )

        assert prob == 0.0

    def test_probability_bounds(self):
        """Test that probability is always between 0 and 1"""
        # Test various combinations
        test_cases = [
            (100000.0, 500.0, 0.95, 0.01),
            (10000.0, 5000.0, 0.7, 0.02),
            (5000.0, 4000.0, 0.5, 0.05),
            (1000000.0, 1000.0, 0.99, 0.001),
        ]

        for liquidity, size, confidence, slippage in test_cases:
            prob = estimate_execution_probability(
                liquidity=liquidity,
                required_size=size,
                confidence_score=confidence,
                slippage_tolerance=slippage
            )
            assert 0.0 <= prob <= 1.0

    def test_small_vs_large_trade(self):
        """Test that larger trades (relative to liquidity) have lower probability"""
        # Small trade
        prob_small = estimate_execution_probability(
            liquidity=100000.0,
            required_size=1000.0,  # 1%
            confidence_score=0.9,
            slippage_tolerance=0.01
        )

        # Large trade
        prob_large = estimate_execution_probability(
            liquidity=100000.0,
            required_size=30000.0,  # 30%
            confidence_score=0.9,
            slippage_tolerance=0.01
        )

        assert prob_small > prob_large


class TestIntegration:
    """Integration tests combining multiple functions"""

    def test_full_position_sizing_workflow(self):
        """Test complete workflow from probability to position size"""
        # Step 1: Estimate execution probability
        execution_prob = estimate_execution_probability(
            liquidity=50000.0,
            required_size=5000.0,
            confidence_score=0.85,
            slippage_tolerance=0.01
        )

        # Step 2: Calculate position size
        position_size = calculate_position_size(
            available_capital=10000.0,
            win_probability=execution_prob,
            profit_ratio=0.03,
            max_position_size=2000.0,
            conservative_factor=0.5
        )

        # Assertions
        assert 0 <= execution_prob <= 1.0
        assert 0 <= position_size <= 2000.0

    def test_realistic_arbitrage_scenario(self):
        """Test with realistic arbitrage parameters"""
        # Typical arbitrage opportunity:
        # - High execution probability (95%)
        # - Small profit (3%)
        # - Good liquidity
        # - $10k available capital

        execution_prob = estimate_execution_probability(
            liquidity=100000.0,
            required_size=1000.0,
            confidence_score=0.9,
            slippage_tolerance=0.01
        )

        position_size = calculate_position_size(
            available_capital=10000.0,
            win_probability=execution_prob,
            profit_ratio=0.03,
            max_position_size=1000.0,
            conservative_factor=0.5  # Half-Kelly for safety
        )

        # Should suggest reasonable position
        assert 100 <= position_size <= 1000

    def test_risky_opportunity_small_position(self):
        """Test that risky opportunities get small positions"""
        # Risky opportunity:
        # - Lower execution probability
        # - Tight liquidity
        # - Lower confidence

        execution_prob = estimate_execution_probability(
            liquidity=10000.0,
            required_size=3000.0,  # Using 30% of liquidity
            confidence_score=0.6,
            slippage_tolerance=0.02
        )

        position_size = calculate_position_size(
            available_capital=10000.0,
            win_probability=execution_prob,
            profit_ratio=0.025,
            max_position_size=1000.0,
            conservative_factor=0.5
        )

        # Should be very small or zero
        assert position_size < 500.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
