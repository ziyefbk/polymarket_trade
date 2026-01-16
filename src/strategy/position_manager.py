"""
Position Manager for Polymarket Arbitrage System

Manages position sizing and risk limits using Kelly Criterion and configured constraints.
"""
import sys
sys.path.append("../..")

from typing import Dict, Optional
from datetime import datetime, timedelta
from loguru import logger

from config.settings import TradingConfig
from src.types.opportunities import ArbitrageOpportunity
from src.types.common import RiskLimitExceededError
from src.utils.kelly import (
    calculate_position_size,
    estimate_execution_probability
)


class PositionManager:
    """
    Manages position sizing and risk limits for arbitrage trading

    The PositionManager is responsible for:
    1. Calculating optimal position sizes using Kelly Criterion
    2. Enforcing risk limits (max position size, daily loss limits)
    3. Tracking open positions and available capital
    4. Preventing over-leveraging

    Attributes:
        config: Trading configuration with risk parameters
        db: Database manager for tracking positions and P&L (optional)
    """

    def __init__(
        self,
        config: TradingConfig,
        db: Optional[object] = None,
        initial_capital: float = 10000.0
    ):
        """
        Initialize the Position Manager

        Args:
            config: Trading configuration with risk parameters
            db: Database manager (optional, for production use)
            initial_capital: Starting capital in USD (used if no DB available)
        """
        self.config = config
        self.db = db
        self._initial_capital = initial_capital
        self._simulated_capital = initial_capital  # For testing without DB

        # Risk tracking
        self._daily_loss_reset_time: Optional[datetime] = None
        self._cached_daily_loss: float = 0.0
        self._cached_open_positions_count: int = 0

        logger.info(
            f"PositionManager initialized with config: "
            f"max_position_size=${config.max_position_size:.2f}, "
            f"max_daily_loss=${config.max_daily_loss:.2f}, "
            f"max_open_positions={config.max_open_positions}"
        )

    async def calculate_position_size(
        self,
        opportunity: ArbitrageOpportunity,
        conservative_factor: float = 0.5
    ) -> float:
        """
        Calculate optimal position size using Kelly Criterion

        This method:
        1. Gets available capital
        2. Estimates execution probability based on liquidity and confidence
        3. Applies Kelly Criterion to calculate optimal size
        4. Enforces maximum position size limit
        5. Ensures we don't exceed risk limits

        Args:
            opportunity: The arbitrage opportunity to size
            conservative_factor: Kelly multiplier (0.5 = half-Kelly, recommended)

        Returns:
            Position size in USD (0 if risk limits exceeded)

        Raises:
            RiskLimitExceededError: If risk limits would be exceeded

        Examples:
            >>> manager = PositionManager(config)
            >>> opportunity = ArbitrageOpportunity(...)
            >>> size = await manager.calculate_position_size(opportunity)
            >>> print(f"Optimal position: ${size:.2f}")
        """
        # First check if we can trade at all
        risk_check = await self.check_risk_limits()
        if not risk_check["can_trade"]:
            reasons = []
            if not risk_check["daily_loss_ok"]:
                reasons.append("daily loss limit exceeded")
            if not risk_check["position_count_ok"]:
                reasons.append("max open positions reached")
            if not risk_check["capital_available"]:
                reasons.append("insufficient capital")

            error_msg = f"Cannot trade: {', '.join(reasons)}"
            logger.warning(error_msg)
            raise RiskLimitExceededError(error_msg)

        # Get available capital
        available_capital = await self.get_available_capital()

        if available_capital <= 0:
            logger.warning("No capital available for trading")
            return 0.0

        # Estimate execution probability based on market conditions
        min_liquidity = min(opportunity.yes_liquidity, opportunity.no_liquidity)
        execution_probability = estimate_execution_probability(
            liquidity=min_liquidity,
            required_size=opportunity.required_capital,
            confidence_score=opportunity.confidence_score,
            slippage_tolerance=self.config.slippage_tolerance
        )

        logger.debug(
            f"Execution probability for {opportunity.event_title}: "
            f"{execution_probability:.2%}"
        )

        # Calculate position size using Kelly Criterion
        position_size = calculate_position_size(
            available_capital=available_capital,
            win_probability=execution_probability,
            profit_ratio=opportunity.net_profit_pct,
            max_position_size=self.config.max_position_size,
            conservative_factor=conservative_factor
        )

        # Additional safety check: ensure we have enough for both legs
        # For arbitrage, we need capital for both YES and NO sides
        required_for_both_legs = position_size * 2

        if required_for_both_legs > available_capital:
            # Reduce position size to fit available capital
            position_size = available_capital / 2
            logger.warning(
                f"Position size reduced to ${position_size:.2f} "
                f"to fit available capital ${available_capital:.2f}"
            )

        # Final check against minimum trade size (prevent dust trades)
        min_trade_size = 10.0  # $10 minimum
        if position_size < min_trade_size:
            logger.info(
                f"Position size ${position_size:.2f} below minimum ${min_trade_size:.2f}, "
                "skipping trade"
            )
            return 0.0

        logger.success(
            f"✓ Position sized: ${position_size:.2f} for {opportunity.event_title} "
            f"(available: ${available_capital:.2f}, "
            f"kelly_factor: {conservative_factor}, "
            f"exec_prob: {execution_probability:.2%})"
        )

        return position_size

    async def check_risk_limits(self) -> Dict[str, bool]:
        """
        Check if all risk limits are within acceptable ranges

        Returns:
            Dictionary with risk check results:
            {
                "daily_loss_ok": bool,       # Daily loss within limit
                "position_count_ok": bool,   # Open positions within limit
                "capital_available": bool,   # Have available capital
                "can_trade": bool            # Overall OK to trade
            }

        Examples:
            >>> manager = PositionManager(config)
            >>> limits = await manager.check_risk_limits()
            >>> if limits["can_trade"]:
            ...     # Execute trade
        """
        # Check daily loss limit
        daily_loss = await self.get_daily_loss()
        daily_loss_ok = daily_loss < self.config.max_daily_loss

        if not daily_loss_ok:
            logger.warning(
                f"Daily loss limit reached: ${daily_loss:.2f} / ${self.config.max_daily_loss:.2f}"
            )

        # Check open positions count
        open_positions_count = await self.get_open_positions_count()
        position_count_ok = open_positions_count < self.config.max_open_positions

        if not position_count_ok:
            logger.warning(
                f"Max open positions reached: {open_positions_count} / {self.config.max_open_positions}"
            )

        # Check available capital
        available_capital = await self.get_available_capital()
        capital_available = available_capital > 0

        if not capital_available:
            logger.warning("No capital available for trading")

        # Overall check
        can_trade = daily_loss_ok and position_count_ok and capital_available

        result = {
            "daily_loss_ok": daily_loss_ok,
            "position_count_ok": position_count_ok,
            "capital_available": capital_available,
            "can_trade": can_trade
        }

        logger.debug(f"Risk limits check: {result}")

        return result

    async def get_available_capital(self) -> float:
        """
        Get available capital for trading

        If database is available, calculates: initial_capital - locked_in_positions + realized_pnl
        Otherwise, returns simulated capital (for testing)

        Returns:
            Available capital in USD
        """
        if self.db is None:
            # Testing mode: use simulated capital
            logger.debug(f"Using simulated capital: ${self._simulated_capital:.2f}")
            return self._simulated_capital

        try:
            # Production mode: get from database
            # This would call something like:
            # open_positions = await self.db.get_open_positions()
            # locked_capital = sum(p.capital_used for p in open_positions)
            # realized_pnl = await self.db.get_realized_pnl()
            # available = self._initial_capital - locked_capital + realized_pnl

            # For now, return initial capital (placeholder for DB integration)
            logger.warning("Database integration not complete, using initial capital")
            return self._initial_capital

        except Exception as e:
            logger.error(f"Error getting available capital from DB: {e}")
            return self._initial_capital

    async def get_daily_loss(self) -> float:
        """
        Get total loss for the current day

        Returns:
            Daily loss in USD (positive number represents loss)
        """
        # Reset daily loss counter if it's a new day
        now = datetime.utcnow()
        if self._daily_loss_reset_time is None or now.date() > self._daily_loss_reset_time.date():
            self._daily_loss_reset_time = now
            self._cached_daily_loss = 0.0
            logger.debug("Daily loss counter reset")

        if self.db is None:
            # Testing mode: use cached value
            return self._cached_daily_loss

        try:
            # Production mode: get from database
            # daily_loss = await self.db.get_daily_loss()
            # return daily_loss

            # Placeholder
            return self._cached_daily_loss

        except Exception as e:
            logger.error(f"Error getting daily loss from DB: {e}")
            return self._cached_daily_loss

    async def get_open_positions_count(self) -> int:
        """
        Get count of currently open positions

        Returns:
            Number of open positions
        """
        if self.db is None:
            # Testing mode: use cached value
            return self._cached_open_positions_count

        try:
            # Production mode: get from database
            # open_positions = await self.db.get_open_positions()
            # return len(open_positions)

            # Placeholder
            return self._cached_open_positions_count

        except Exception as e:
            logger.error(f"Error getting open positions from DB: {e}")
            return self._cached_open_positions_count

    async def record_trade_result(
        self,
        opportunity_id: str,
        capital_used: float,
        profit: float,
        success: bool
    ) -> None:
        """
        Record a trade result for risk tracking

        This updates internal counters for daily loss and open positions.
        In production, this would be handled by the database layer.

        Args:
            opportunity_id: ID of the executed opportunity
            capital_used: Capital used in the trade
            profit: Realized profit (negative for loss)
            success: Whether trade was successful
        """
        logger.debug(
            f"Recording trade result: {opportunity_id}, "
            f"capital=${capital_used:.2f}, profit=${profit:.2f}, success={success}"
        )

        # Update daily loss if trade resulted in loss
        if profit < 0:
            self._cached_daily_loss += abs(profit)
            logger.warning(f"Daily loss updated: ${self._cached_daily_loss:.2f}")

        # Update simulated capital (for testing)
        if self.db is None:
            self._simulated_capital += profit
            logger.debug(f"Simulated capital updated: ${self._simulated_capital:.2f}")

        # In production, this would save to database:
        # await self.db.save_trade(...)

    async def update_open_positions_count(self, delta: int) -> None:
        """
        Update the count of open positions

        Args:
            delta: Change in open positions (+1 for open, -1 for close)
        """
        self._cached_open_positions_count += delta
        self._cached_open_positions_count = max(0, self._cached_open_positions_count)

        logger.debug(f"Open positions count: {self._cached_open_positions_count}")

    def set_simulated_capital(self, capital: float) -> None:
        """
        Set simulated capital (for testing)

        Args:
            capital: Capital amount in USD
        """
        self._simulated_capital = capital
        logger.debug(f"Simulated capital set to: ${capital:.2f}")

    def reset_daily_metrics(self) -> None:
        """
        Reset daily tracking metrics (for testing or daily rollover)
        """
        self._cached_daily_loss = 0.0
        self._daily_loss_reset_time = datetime.utcnow()
        logger.info("Daily metrics reset")
