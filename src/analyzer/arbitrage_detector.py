"""
Intra-Market Arbitrage Detector for Polymarket

Detects arbitrage opportunities within single events where YES + NO prices deviate from 1.0.
This module implements the detection logic for finding profitable price discrepancies.
"""
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import List, Optional, Dict
import logging

# Setup logging
logger = logging.getLogger(__name__)

import sys
sys.path.append("../..")
from config import settings
from src.api.polymarket_client import PolymarketClient, Event, Market, OrderBook
from src.types.opportunities import ArbitrageOpportunity


class IntraMarketArbitrageDetector:
    """
    Detects intra-market arbitrage opportunities in Polymarket events.

    Analyzes binary YES/NO markets where price_sum != 1.0, calculating expected
    profits after fees and slippage, and assigning confidence scores.
    """

    def __init__(self, client: PolymarketClient):
        """
        Initialize the arbitrage detector.

        Args:
            client: Initialized PolymarketClient for API access
        """
        self.client = client
        self.config = settings.arbitrage
        self.trading_config = settings.trading

        # Trading fees (Polymarket charges 0.2% maker + 0.2% taker per side)
        self.MAKER_FEE = 0.002  # 0.2%
        self.TAKER_FEE = 0.002  # 0.2%
        self.TOTAL_FEE_PER_LEG = self.MAKER_FEE + self.TAKER_FEE  # 0.4%

        logger.info(f"Initialized ArbitrageDetector with min_discrepancy={self.config.min_discrepancy}")

    async def scan_all_markets(self) -> List[ArbitrageOpportunity]:
        """
        Scan all active markets for arbitrage opportunities.

        Fetches all active events, analyzes each for arbitrage potential,
        and returns opportunities sorted by confidence score (highest first).

        Returns:
            List of ArbitrageOpportunity objects, sorted by confidence_score descending

        Raises:
            Exception: If API call fails critically (wrapped in try-except with logging)
        """
        logger.info("Starting market scan for arbitrage opportunities")
        opportunities = []

        try:
            events = await self.client.get_all_active_events()
            logger.info(f"Fetched {len(events)} active events")

            for event in events:
                try:
                    opportunity = await self.analyze_event(event)
                    if opportunity:
                        opportunities.append(opportunity)
                        logger.info(
                            f"Found opportunity: {event.title} | "
                            f"Spread: {opportunity.spread:.2%} | "
                            f"Net profit: {opportunity.net_profit_pct:.2%} | "
                            f"Confidence: {opportunity.confidence_score:.2f}"
                        )
                except Exception as e:
                    logger.error(f"Error analyzing event {event.event_id}: {str(e)}")
                    continue

            # Sort by confidence score (highest first)
            opportunities.sort(key=lambda x: x.confidence_score, reverse=True)

            logger.info(f"Scan complete. Found {len(opportunities)} opportunities")
            return opportunities

        except Exception as e:
            logger.error(f"Failed to scan markets: {str(e)}")
            raise

    async def analyze_event(self, event: Event) -> Optional[ArbitrageOpportunity]:
        """
        Analyze a single event for arbitrage opportunities.

        Checks if the event is binary (YES/NO), calculates price deviation,
        estimates profit, and returns an opportunity if it meets thresholds.

        Args:
            event: Event object from Polymarket API

        Returns:
            ArbitrageOpportunity if valid opportunity exists, None otherwise
        """
        # Filter 1: Must be binary event (exactly 2 markets)
        if not event.is_binary or len(event.markets) != 2:
            return None

        # Extract YES and NO markets
        yes_market = None
        no_market = None

        for market in event.markets:
            if market.outcome.upper() == "YES":
                yes_market = market
            elif market.outcome.upper() == "NO":
                no_market = market

        if not yes_market or not no_market:
            logger.debug(f"Event {event.event_id} missing YES or NO market")
            return None

        # Filter 2: Validate prices are in valid range
        if not (0 < yes_market.price < 1 and 0 < no_market.price < 1):
            logger.warning(
                f"Invalid prices for event {event.event_id}: "
                f"YES={yes_market.price}, NO={no_market.price}"
            )
            return None

        # Filter 3: Check for valid token IDs
        if not yes_market.token_id or not no_market.token_id:
            logger.debug(f"Event {event.event_id} has missing token IDs")
            return None

        # Calculate spread
        price_sum = yes_market.price + no_market.price
        spread = abs(price_sum - 1.0)

        # Filter 4: Spread must exceed minimum discrepancy threshold
        if spread < self.config.min_discrepancy:
            return None

        # Determine arbitrage type
        arbitrage_type = self._determine_arbitrage_type(price_sum)

        # Estimate capital requirement based on minimum liquidity
        min_liquidity = min(yes_market.liquidity, no_market.liquidity)
        required_capital = min(
            min_liquidity * 0.5,  # Use at most 50% of available liquidity
            self.trading_config.max_position_size
        )

        # Filter 5: Must have sufficient liquidity
        if required_capital < 100:  # Minimum $100 position
            return None

        # Calculate profit metrics
        profit_metrics = self._estimate_profit(
            spread=spread,
            arbitrage_type=arbitrage_type,
            capital=required_capital,
            yes_liquidity=yes_market.liquidity,
            no_liquidity=no_market.liquidity
        )

        # Filter 6: Net profit must exceed minimum threshold
        if profit_metrics["net_profit_pct"] < self.trading_config.min_profit_threshold:
            return None

        # Create opportunity object
        opportunity_id = str(uuid.uuid4())
        detected_at = datetime.now()
        valid_until = detected_at + timedelta(seconds=60)  # Valid for 60 seconds

        opportunity = ArbitrageOpportunity(
            opportunity_id=opportunity_id,
            event_id=event.event_id,
            event_title=event.title,
            yes_token_id=yes_market.token_id,
            yes_price=yes_market.price,
            yes_liquidity=yes_market.liquidity,
            no_token_id=no_market.token_id,
            no_price=no_market.price,
            no_liquidity=no_market.liquidity,
            price_sum=price_sum,
            spread=spread,
            arbitrage_type=arbitrage_type,
            expected_profit_pct=profit_metrics["gross_profit_pct"],
            expected_profit_usd=profit_metrics["expected_profit_usd"],
            estimated_fees=profit_metrics["fees"],
            estimated_slippage=profit_metrics["slippage"],
            net_profit_pct=profit_metrics["net_profit_pct"],
            is_executable=True,
            required_capital=required_capital,
            confidence_score=0.0,  # Will be calculated next
            detected_at=detected_at,
            valid_until=valid_until
        )

        # Calculate and assign confidence score
        opportunity.confidence_score = self._calculate_confidence_score(opportunity)

        return opportunity

    def _calculate_spread(self, yes_price: float, no_price: float) -> float:
        """
        Calculate the price spread (deviation from 1.0).

        Args:
            yes_price: YES market price (0-1)
            no_price: NO market price (0-1)

        Returns:
            Absolute difference from 1.0
        """
        return abs((yes_price + no_price) - 1.0)

    def _determine_arbitrage_type(self, price_sum: float) -> str:
        """
        Determine the type of arbitrage opportunity.

        Args:
            price_sum: Sum of YES and NO prices

        Returns:
            "OVERPRICED" if sum > 1, "UNDERPRICED" if sum < 1
        """
        return "OVERPRICED" if price_sum > 1.0 else "UNDERPRICED"

    def _estimate_profit(
        self,
        spread: float,
        arbitrage_type: str,
        capital: float,
        yes_liquidity: float,
        no_liquidity: float
    ) -> Dict[str, float]:
        """
        Estimate profit metrics including fees and slippage.

        Args:
            spread: Price deviation from 1.0
            arbitrage_type: "OVERPRICED" or "UNDERPRICED"
            capital: Capital to deploy
            yes_liquidity: YES market liquidity
            no_liquidity: NO market liquidity

        Returns:
            Dictionary with profit calculations:
            - gross_profit_pct: Gross profit percentage
            - expected_profit_usd: Expected profit in USD
            - fees: Total trading fees
            - slippage: Estimated slippage cost
            - net_profit_pct: Net profit percentage after costs
        """
        # Gross profit (before fees and slippage)
        gross_profit_pct = spread
        gross_profit_usd = capital * spread

        # Calculate fees (0.4% per leg × 2 legs = 0.8% total)
        total_fee_rate = self.TOTAL_FEE_PER_LEG * 2  # Both YES and NO legs
        fees = capital * total_fee_rate

        # Estimate slippage based on liquidity depth
        # Lower liquidity → higher slippage
        min_liquidity = min(yes_liquidity, no_liquidity)
        position_ratio = capital / min_liquidity if min_liquidity > 0 else 1.0

        # Slippage estimation: starts at 0.1% and increases with position size
        base_slippage = 0.001  # 0.1%
        slippage_rate = base_slippage + (position_ratio * 0.005)  # Add 0.5% per liquidity ratio
        slippage_rate = min(slippage_rate, self.trading_config.slippage_tolerance)
        slippage = capital * slippage_rate

        # Net profit
        net_profit_usd = gross_profit_usd - fees - slippage
        net_profit_pct = net_profit_usd / capital if capital > 0 else 0

        return {
            "gross_profit_pct": gross_profit_pct,
            "expected_profit_usd": gross_profit_usd,
            "fees": fees,
            "slippage": slippage,
            "net_profit_pct": net_profit_pct
        }

    def _calculate_confidence_score(self, opportunity: ArbitrageOpportunity) -> float:
        """
        Calculate confidence score for an opportunity (0-1 scale).

        Weighted scoring based on:
        - Spread magnitude (40%): Larger spread → higher confidence
        - Liquidity depth (30%): More liquidity → higher confidence
        - Order book balance (20%): Similar YES/NO liquidity → higher confidence
        - Time to expiry (10%): More time → higher confidence (placeholder)

        Args:
            opportunity: ArbitrageOpportunity to score

        Returns:
            Confidence score between 0 and 1
        """
        scores = []
        weights = []

        # 1. Spread magnitude (40% weight)
        spread_pct = opportunity.spread
        if spread_pct >= 0.05:  # ≥5%
            spread_score = 1.0
        elif spread_pct >= 0.03:  # 3-5%
            spread_score = 0.3 + (spread_pct - 0.03) / 0.02 * 0.7  # Linear interpolation
        else:
            spread_score = 0.0
        scores.append(spread_score)
        weights.append(0.4)

        # 2. Liquidity depth (30% weight)
        min_liquidity = min(opportunity.yes_liquidity, opportunity.no_liquidity)
        if min_liquidity >= 50000:  # ≥$50k
            liquidity_score = 1.0
        elif min_liquidity >= 10000:  # $10k-$50k
            liquidity_score = 0.6 + (min_liquidity - 10000) / 40000 * 0.4
        else:  # <$10k
            liquidity_score = 0.3 + (min_liquidity / 10000) * 0.3
        scores.append(liquidity_score)
        weights.append(0.3)

        # 3. Order book balance (20% weight)
        liquidity_ratio = min(
            opportunity.yes_liquidity / opportunity.no_liquidity,
            opportunity.no_liquidity / opportunity.yes_liquidity
        ) if opportunity.no_liquidity > 0 and opportunity.yes_liquidity > 0 else 0

        # Closer to 1.0 → better balance
        balance_score = liquidity_ratio
        scores.append(balance_score)
        weights.append(0.2)

        # 4. Time to expiry (10% weight) - placeholder since we don't have expiry data
        # Assume moderate time available
        time_score = 0.7
        scores.append(time_score)
        weights.append(0.1)

        # Calculate weighted average
        confidence = sum(s * w for s, w in zip(scores, weights))

        return round(confidence, 3)
