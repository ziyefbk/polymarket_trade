"""
Arbitrage Executor - Task 2 Implementation

Handles the execution of arbitrage opportunities by:
1. Verifying prices are still valid
2. Executing both legs simultaneously using asyncio.gather()
3. Handling partial fills and errors
4. Returning ExecutionResult with detailed metrics
"""
import asyncio
import time
from typing import Tuple, Optional
from datetime import datetime
from loguru import logger

import sys
sys.path.append("../..")

from src.api.trader import PolymarketTrader, OrderSide, TradeResult
from src.api.polymarket_client import PolymarketClient
from src.types.opportunities import ArbitrageOpportunity
from src.types.orders import ExecutionResult
from src.types.common import (
    ExecutionFailedError,
    PriceStaleError,
    InsufficientLiquidityError
)
from config.settings import settings


class ArbitrageExecutor:
    """
    Executes arbitrage opportunities on Polymarket.

    This executor implements the strategy defined in INTERFACE_SPEC.md section 4.2:
    - Verifies prices before execution
    - Executes both legs simultaneously to minimize timing risk
    - Handles partial fills and errors gracefully
    - Returns detailed ExecutionResult for database storage
    """

    def __init__(
        self,
        trader: PolymarketTrader,
        client: Optional[PolymarketClient] = None
    ):
        """
        Initialize the arbitrage executor.

        Args:
            trader: PolymarketTrader instance for order execution
            client: Optional PolymarketClient for price verification (will create one if None)
        """
        self.trader = trader
        self.client = client
        self.config = settings.trading

        logger.info(
            f"ArbitrageExecutor initialized with max position: ${self.config.max_position_size}, "
            f"slippage tolerance: {self.config.slippage_tolerance:.1%}"
        )

    async def execute_opportunity(
        self,
        opp: ArbitrageOpportunity,
        position_size: float
    ) -> ExecutionResult:
        """
        Execute an arbitrage opportunity.

        This is the main public method that orchestrates the entire execution flow:
        1. Validates position size
        2. Verifies prices are still valid
        3. Executes both legs simultaneously
        4. Handles results and calculates profit

        Args:
            opp: ArbitrageOpportunity object from the detector
            position_size: Size in USDC to execute (already calculated by PositionManager)

        Returns:
            ExecutionResult with execution details and profit metrics

        Raises:
            PriceStaleError: If prices have moved beyond tolerance
            InsufficientLiquidityError: If liquidity is insufficient
            ExecutionFailedError: If execution fails for other reasons
        """
        start_time = time.time()

        logger.info(
            f"Executing opportunity {opp.opportunity_id}: {opp.event_title}"
        )
        logger.info(
            f"Type: {opp.arbitrage_type}, Spread: {opp.spread:.4f}, "
            f"Expected profit: {opp.net_profit_pct:.2%}, Size: ${position_size:.2f}"
        )

        # Validate position size
        if position_size > self.config.max_position_size:
            error_msg = (
                f"Position size ${position_size:.2f} exceeds max "
                f"${self.config.max_position_size:.2f}"
            )
            logger.error(error_msg)
            return self._create_failed_result(opp, error_msg, start_time)

        if position_size <= 0:
            error_msg = f"Invalid position size: ${position_size:.2f}"
            logger.error(error_msg)
            return self._create_failed_result(opp, error_msg, start_time)

        try:
            # Step 1: Verify prices are still valid
            await self._verify_prices(opp)

            # Step 2: Execute both legs simultaneously
            yes_result, no_result = await self._execute_legs_simultaneously(
                opp=opp,
                size=position_size
            )

            # Step 3: Process results and calculate profit
            result = await self._process_execution_results(
                opp=opp,
                yes_result=yes_result,
                no_result=no_result,
                position_size=position_size,
                start_time=start_time
            )

            # Log result
            if result.success:
                logger.success(
                    f"✓ Opportunity {opp.opportunity_id} executed successfully! "
                    f"Profit: ${result.actual_profit_usd:.2f} ({result.actual_profit_pct:.2%}), "
                    f"Time: {result.execution_time_ms:.0f}ms"
                )
            else:
                logger.error(
                    f"✗ Opportunity {opp.opportunity_id} failed: {result.error_message}"
                )

            return result

        except (PriceStaleError, InsufficientLiquidityError) as e:
            logger.warning(f"Execution aborted: {e}")
            return self._create_failed_result(opp, str(e), start_time)

        except Exception as e:
            logger.exception(f"Unexpected error executing opportunity {opp.opportunity_id}")
            return self._create_failed_result(opp, f"Unexpected error: {e}", start_time)

    async def _verify_prices(self, opp: ArbitrageOpportunity) -> None:
        """
        Verify that prices haven't moved significantly since detection.

        This prevents executing stale opportunities where the arbitrage has disappeared.
        Uses a temporary client if one wasn't provided at initialization.

        Args:
            opp: The opportunity to verify

        Raises:
            PriceStaleError: If price movement exceeds slippage_tolerance
        """
        if not self.client:
            # Create temporary client for verification
            async with PolymarketClient() as temp_client:
                await self._do_price_verification(temp_client, opp)
        else:
            await self._do_price_verification(self.client, opp)

    async def _do_price_verification(
        self,
        client: PolymarketClient,
        opp: ArbitrageOpportunity
    ) -> None:
        """
        Perform the actual price verification logic.

        Args:
            client: The client to use for fetching current prices
            opp: The opportunity to verify

        Raises:
            PriceStaleError: If price movement exceeds tolerance
        """
        try:
            # Fetch current prices
            prices = await client.get_prices([opp.yes_token_id, opp.no_token_id])
            current_yes_price = prices.get(opp.yes_token_id)
            current_no_price = prices.get(opp.no_token_id)

            if current_yes_price is None or current_no_price is None:
                raise PriceStaleError("Could not fetch current prices")

            # Calculate price changes
            yes_price_change = abs(current_yes_price - opp.yes_price) / opp.yes_price
            no_price_change = abs(current_no_price - opp.no_price) / opp.no_price

            tolerance = self.config.slippage_tolerance

            if yes_price_change > tolerance:
                raise PriceStaleError(
                    f"YES price moved {yes_price_change:.2%} (>{tolerance:.2%}): "
                    f"{opp.yes_price:.4f} -> {current_yes_price:.4f}"
                )

            if no_price_change > tolerance:
                raise PriceStaleError(
                    f"NO price moved {no_price_change:.2%} (>{tolerance:.2%}): "
                    f"{opp.no_price:.4f} -> {current_no_price:.4f}"
                )

            logger.debug(
                f"Price verification passed. YES: {yes_price_change:.2%}, NO: {no_price_change:.2%}"
            )

        except Exception as e:
            if isinstance(e, PriceStaleError):
                raise
            raise PriceStaleError(f"Price verification failed: {e}")

    async def _execute_legs_simultaneously(
        self,
        opp: ArbitrageOpportunity,
        size: float
    ) -> Tuple[TradeResult, TradeResult]:
        """
        Execute both legs of the arbitrage simultaneously using asyncio.gather().

        For OVERPRICED opportunities (YES + NO > 1.0):
        - SELL both YES and NO tokens to collect premium

        For UNDERPRICED opportunities (YES + NO < 1.0):
        - BUY both YES and NO tokens at discount

        Args:
            opp: The arbitrage opportunity
            size: Position size in USDC

        Returns:
            Tuple of (yes_result, no_result) from trade execution

        Note:
            Uses return_exceptions=True to capture errors without stopping execution
        """
        if opp.arbitrage_type == "OVERPRICED":
            # Prices sum to > 1.0, so we SELL both to collect the premium
            logger.info(f"OVERPRICED arbitrage: SELLing both legs at size ${size:.2f}")

            yes_coro = self.trader.sell(
                token_id=opp.yes_token_id,
                price=opp.yes_price,
                size=size
            )
            no_coro = self.trader.sell(
                token_id=opp.no_token_id,
                price=opp.no_price,
                size=size
            )

        else:  # UNDERPRICED
            # Prices sum to < 1.0, so we BUY both at discount
            logger.info(f"UNDERPRICED arbitrage: BUYing both legs at size ${size:.2f}")

            yes_coro = self.trader.buy(
                token_id=opp.yes_token_id,
                price=opp.yes_price,
                size=size
            )
            no_coro = self.trader.buy(
                token_id=opp.no_token_id,
                price=opp.no_price,
                size=size
            )

        # Execute both orders simultaneously
        logger.debug("Executing both legs simultaneously...")
        results = await asyncio.gather(
            yes_coro,
            no_coro,
            return_exceptions=True  # Don't propagate exceptions, capture them
        )

        yes_result = results[0]
        no_result = results[1]

        # Convert exceptions to failed TradeResults
        if isinstance(yes_result, Exception):
            logger.error(f"YES leg raised exception: {yes_result}")
            yes_result = TradeResult(success=False, error=str(yes_result))

        if isinstance(no_result, Exception):
            logger.error(f"NO leg raised exception: {no_result}")
            no_result = TradeResult(success=False, error=str(no_result))

        logger.debug(
            f"Execution results - YES: {yes_result.success} "
            f"(filled {yes_result.filled_size:.2f}), "
            f"NO: {no_result.success} (filled {no_result.filled_size:.2f})"
        )

        return yes_result, no_result

    async def _process_execution_results(
        self,
        opp: ArbitrageOpportunity,
        yes_result: TradeResult,
        no_result: TradeResult,
        position_size: float,
        start_time: float
    ) -> ExecutionResult:
        """
        Process trade results and calculate profit metrics.

        Handles three scenarios:
        1. Both legs fully filled - SUCCESS
        2. Partial fills - PARTIAL_FILL_RISK
        3. One or both failed - FAILURE

        Args:
            opp: The original opportunity
            yes_result: Result from YES leg execution
            no_result: Result from NO leg execution
            position_size: Requested position size
            start_time: Execution start timestamp

        Returns:
            ExecutionResult with detailed metrics
        """
        execution_time_ms = (time.time() - start_time) * 1000

        # Determine status for each leg
        yes_status = self._determine_leg_status(yes_result, position_size)
        no_status = self._determine_leg_status(no_result, position_size)

        # Check for partial fill risk
        partial_fill_risk = self._check_partial_fill_risk(
            yes_status, no_status, yes_result, no_result
        )

        # Calculate overall success
        both_filled = (yes_status == "FILLED" and no_status == "FILLED")
        any_failed = (yes_status == "FAILED" or no_status == "FAILED")
        success = both_filled and not any_failed

        # Calculate actual capital used and profit
        capital_used, profit_usd, profit_pct = self._calculate_profit(
            opp=opp,
            yes_result=yes_result,
            no_result=no_result,
            yes_status=yes_status,
            no_status=no_status
        )

        # Determine error message
        error_message = None
        if not success:
            error_parts = []
            if yes_result.error:
                error_parts.append(f"YES: {yes_result.error}")
            if no_result.error:
                error_parts.append(f"NO: {no_result.error}")
            if partial_fill_risk:
                error_parts.append("Partial fill risk detected")
            error_message = "; ".join(error_parts) if error_parts else "Execution incomplete"

        return ExecutionResult(
            opportunity_id=opp.opportunity_id,
            success=success,
            yes_filled_size=yes_result.filled_size,
            yes_avg_price=yes_result.avg_price,
            yes_status=yes_status,
            no_filled_size=no_result.filled_size,
            no_avg_price=no_result.avg_price,
            no_status=no_status,
            total_capital_used=capital_used,
            actual_profit_usd=profit_usd,
            actual_profit_pct=profit_pct,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            partial_fill_risk=partial_fill_risk,
            executed_at=datetime.utcnow()
        )

    def _determine_leg_status(self, result: TradeResult, position_size: float) -> str:
        """
        Determine the status of a single leg.

        Args:
            result: TradeResult from execution
            position_size: Requested position size

        Returns:
            One of: "FILLED", "PARTIAL", "FAILED", "PENDING"
        """
        if not result.success:
            return "FAILED"

        if result.filled_size == 0:
            return "PENDING"

        # Consider filled if >= 95% of requested size
        fill_ratio = result.filled_size / position_size if position_size > 0 else 0

        if fill_ratio >= 0.95:
            return "FILLED"
        else:
            return "PARTIAL"

    def _check_partial_fill_risk(
        self,
        yes_status: str,
        no_status: str,
        yes_result: TradeResult,
        no_result: TradeResult
    ) -> bool:
        """
        Check if there's a partial fill risk (one leg filled but other didn't).

        This is dangerous because we're exposed to directional risk if only
        one side of the arbitrage executed.

        Args:
            yes_status: Status of YES leg
            no_status: Status of NO leg
            yes_result: YES leg result
            no_result: NO leg result

        Returns:
            True if partial fill risk exists
        """
        yes_has_fills = yes_result.filled_size > 0
        no_has_fills = no_result.filled_size > 0

        # Risk exists if one leg has fills and the other doesn't
        if yes_has_fills and not no_has_fills:
            logger.warning("⚠️  Partial fill risk: YES filled but NO didn't")
            return True

        if no_has_fills and not yes_has_fills:
            logger.warning("⚠️  Partial fill risk: NO filled but YES didn't")
            return True

        # Also check for significant imbalance in fill sizes
        if yes_has_fills and no_has_fills:
            ratio = yes_result.filled_size / no_result.filled_size
            if ratio < 0.9 or ratio > 1.1:  # More than 10% difference
                logger.warning(
                    f"⚠️  Fill size imbalance: YES={yes_result.filled_size:.2f}, "
                    f"NO={no_result.filled_size:.2f}"
                )
                return True

        return False

    def _calculate_profit(
        self,
        opp: ArbitrageOpportunity,
        yes_result: TradeResult,
        no_result: TradeResult,
        yes_status: str,
        no_status: str
    ) -> Tuple[float, float, float]:
        """
        Calculate actual capital used and profit realized.

        For OVERPRICED (SELL both):
        - We receive: (yes_price + no_price) * size
        - We pay out: 1.0 * size (one will win)
        - Profit: (yes_price + no_price - 1.0) * size

        For UNDERPRICED (BUY both):
        - We pay: (yes_price + no_price) * size
        - We receive: 1.0 * size (one will win)
        - Profit: (1.0 - yes_price - no_price) * size

        Args:
            opp: Original opportunity
            yes_result: YES leg result
            no_result: NO leg result
            yes_status: YES leg status
            no_status: NO leg status

        Returns:
            Tuple of (capital_used, profit_usd, profit_pct)
        """
        # Use actual filled sizes and prices
        yes_size = yes_result.filled_size
        no_size = no_result.filled_size
        yes_price = yes_result.avg_price if yes_result.avg_price > 0 else opp.yes_price
        no_price = no_result.avg_price if no_result.avg_price > 0 else opp.no_price

        # If neither leg filled, no profit
        if yes_size == 0 and no_size == 0:
            return 0.0, 0.0, 0.0

        # Use the smaller fill size for matched pairs
        matched_size = min(yes_size, no_size)

        if opp.arbitrage_type == "OVERPRICED":
            # SELL both: we collect premium
            received = (yes_price + no_price) * matched_size
            payout = 1.0 * matched_size
            profit_usd = received - payout
            capital_used = matched_size  # Capital at risk

        else:  # UNDERPRICED
            # BUY both: we pay discount
            paid = (yes_price + no_price) * matched_size
            received = 1.0 * matched_size
            profit_usd = received - paid
            capital_used = paid

        # Calculate profit percentage
        profit_pct = (profit_usd / capital_used) if capital_used > 0 else 0.0

        return capital_used, profit_usd, profit_pct

    def _create_failed_result(
        self,
        opp: ArbitrageOpportunity,
        error_message: str,
        start_time: float
    ) -> ExecutionResult:
        """
        Create a failed ExecutionResult with error details.

        Args:
            opp: The opportunity that failed
            error_message: Description of the failure
            start_time: When execution started

        Returns:
            ExecutionResult with success=False
        """
        execution_time_ms = (time.time() - start_time) * 1000

        return ExecutionResult(
            opportunity_id=opp.opportunity_id,
            success=False,
            yes_status="FAILED",
            no_status="FAILED",
            error_message=error_message,
            execution_time_ms=execution_time_ms,
            executed_at=datetime.utcnow()
        )
