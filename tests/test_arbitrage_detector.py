"""
Unit tests for IntraMarketArbitrageDetector

Tests cover:
- Overpriced and underpriced opportunity detection
- Threshold filtering (spread, liquidity, profit)
- Profit calculation accuracy (fees, slippage)
- Non-binary event rejection
- Invalid price handling
- Multiple market scanning with proper sorting
"""
import pytest
from unittest.mock import MagicMock, Mock
from datetime import datetime
import sys
sys.path.append("..")

from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.api.polymarket_client import Event, Market, OrderBook
from config import settings


# AsyncMock not available in Python 3.6, create a simple replacement
class AsyncMock(Mock):
    """Simple AsyncMock for Python 3.6 compatibility"""
    def __call__(self, *args, **kwargs):
        async def async_func(*args, **kwargs):
            return super(AsyncMock, self).__call__(*args, **kwargs)
        return async_func(*args, **kwargs)


@pytest.fixture
def mock_client():
    """Create a mock PolymarketClient"""
    client = MagicMock()
    client.get_all_active_events = AsyncMock(return_value=[])
    return client


@pytest.fixture
def detector(mock_client):
    """Create an IntraMarketArbitrageDetector instance with mock client"""
    return IntraMarketArbitrageDetector(mock_client)


def create_test_event(
    event_id: str,
    title: str,
    yes_price: float,
    no_price: float,
    yes_liquidity: float = 50000.0,
    no_liquidity: float = 50000.0,
    yes_token_id: str = "token_yes",
    no_token_id: str = "token_no"
) -> Event:
    """Helper to create test Event objects"""
    yes_market = Market(
        token_id=yes_token_id,
        condition_id="condition_1",
        question=title,
        outcome="YES",
        price=yes_price,
        volume=10000.0,
        liquidity=yes_liquidity
    )

    no_market = Market(
        token_id=no_token_id,
        condition_id="condition_1",
        question=title,
        outcome="NO",
        price=no_price,
        volume=10000.0,
        liquidity=no_liquidity
    )

    return Event(
        event_id=event_id,
        title=title,
        description="Test event",
        markets=[yes_market, no_market],
        category="politics"
    )


@pytest.mark.asyncio
async def test_detect_overpriced_opportunity(detector):
    """
    Test detection of OVERPRICED opportunity where YES + NO > 1.0

    Setup: YES=0.55, NO=0.50, sum=1.05 (5% spread)
    Expected: Valid opportunity with OVERPRICED type
    """
    event = create_test_event(
        event_id="event_1",
        title="Will BTC hit 100k?",
        yes_price=0.55,
        no_price=0.50,
        yes_liquidity=50000.0,
        no_liquidity=50000.0
    )

    opportunity = await detector.analyze_event(event)

    assert opportunity is not None
    assert opportunity.arbitrage_type == "OVERPRICED"
    assert opportunity.price_sum == 1.05
    assert opportunity.spread == 0.05
    assert opportunity.yes_price == 0.55
    assert opportunity.no_price == 0.50
    assert opportunity.is_executable is True
    assert 0 < opportunity.confidence_score <= 1
    assert opportunity.net_profit_pct > 0


@pytest.mark.asyncio
async def test_detect_underpriced_opportunity(detector):
    """
    Test detection of UNDERPRICED opportunity where YES + NO < 1.0

    Setup: YES=0.45, NO=0.48, sum=0.93 (7% spread)
    Expected: Valid opportunity with UNDERPRICED type
    """
    event = create_test_event(
        event_id="event_2",
        title="Will ETH flip BTC?",
        yes_price=0.45,
        no_price=0.48,
        yes_liquidity=60000.0,
        no_liquidity=60000.0
    )

    opportunity = await detector.analyze_event(event)

    assert opportunity is not None
    assert opportunity.arbitrage_type == "UNDERPRICED"
    assert opportunity.price_sum == 0.93
    assert opportunity.spread == 0.07
    assert opportunity.net_profit_pct > settings.trading.min_profit_threshold
    assert opportunity.is_executable is True


@pytest.mark.asyncio
async def test_no_opportunity_below_threshold(detector):
    """
    Test that spreads below min_discrepancy threshold are rejected

    Setup: YES=0.51, NO=0.50, sum=1.01 (1% spread < 3% threshold)
    Expected: No opportunity returned
    """
    event = create_test_event(
        event_id="event_3",
        title="Small spread event",
        yes_price=0.51,
        no_price=0.50,
        yes_liquidity=50000.0,
        no_liquidity=50000.0
    )

    opportunity = await detector.analyze_event(event)

    assert opportunity is None


@pytest.mark.asyncio
async def test_insufficient_liquidity(detector):
    """
    Test that events with insufficient liquidity are rejected

    Setup: Good spread (5%) but very low liquidity ($100)
    Expected: No opportunity due to insufficient capital requirement
    """
    event = create_test_event(
        event_id="event_4",
        title="Low liquidity event",
        yes_price=0.55,
        no_price=0.50,
        yes_liquidity=100.0,  # Very low
        no_liquidity=100.0    # Very low
    )

    opportunity = await detector.analyze_event(event)

    # Should be rejected due to insufficient liquidity
    assert opportunity is None


@pytest.mark.asyncio
async def test_scan_multiple_markets(mock_client):
    """
    Test scanning multiple events and verify sorting by confidence score

    Setup: 3 events with varying spreads and liquidity
    Expected: Opportunities sorted by confidence (highest first)
    """
    events = [
        # High spread, high liquidity → highest confidence
        create_test_event("event_1", "Event 1", 0.56, 0.50, 80000.0, 80000.0),

        # Medium spread, medium liquidity → medium confidence
        create_test_event("event_2", "Event 2", 0.54, 0.50, 30000.0, 30000.0),

        # High spread, low liquidity → lower confidence
        create_test_event("event_3", "Event 3", 0.55, 0.49, 15000.0, 15000.0),

        # Below threshold - should be filtered out
        create_test_event("event_4", "Event 4", 0.51, 0.50, 50000.0, 50000.0),
    ]

    # Create new detector with mock that returns events
    async def mock_get_events():
        return events

    mock_client.get_all_active_events = mock_get_events
    detector = IntraMarketArbitrageDetector(mock_client)

    opportunities = await detector.scan_all_markets()

    # Should have 3 opportunities (event_4 filtered out)
    assert len(opportunities) == 3

    # Verify sorted by confidence score (descending)
    for i in range(len(opportunities) - 1):
        assert opportunities[i].confidence_score >= opportunities[i + 1].confidence_score

    # Highest confidence should be event_1 (best spread + liquidity)
    assert opportunities[0].event_id == "event_1"


@pytest.mark.asyncio
async def test_profit_calculation_accuracy(detector):
    """
    Test profit calculation including fees and slippage

    Setup: Known spread and capital, verify calculations
    Expected: Accurate fee and slippage deductions
    """
    event = create_test_event(
        event_id="event_5",
        title="Profit calc test",
        yes_price=0.54,
        no_price=0.50,
        yes_liquidity=50000.0,
        no_liquidity=50000.0
    )

    opportunity = await detector.analyze_event(event)

    assert opportunity is not None

    # Spread should be 4%
    assert opportunity.spread == 0.04

    # Gross profit = capital × spread
    expected_gross = opportunity.required_capital * 0.04
    assert abs(opportunity.expected_profit_usd - expected_gross) < 0.01

    # Fees should be approximately 0.8% of capital (0.4% per leg × 2 legs)
    expected_fees = opportunity.required_capital * 0.008
    assert abs(opportunity.estimated_fees - expected_fees) < 0.01

    # Slippage should be positive
    assert opportunity.estimated_slippage > 0

    # Net profit should be less than gross profit
    assert opportunity.net_profit_pct < opportunity.expected_profit_pct

    # Net profit should still be positive and above threshold
    assert opportunity.net_profit_pct > settings.trading.min_profit_threshold


@pytest.mark.asyncio
async def test_non_binary_event_rejected(detector):
    """
    Test that events with more than 2 markets are rejected

    Setup: Event with 3 markets (not binary)
    Expected: No opportunity returned
    """
    market1 = Market(
        token_id="token_1",
        condition_id="condition_1",
        question="Who will win?",
        outcome="Candidate A",
        price=0.40,
        volume=10000.0,
        liquidity=30000.0
    )

    market2 = Market(
        token_id="token_2",
        condition_id="condition_1",
        question="Who will win?",
        outcome="Candidate B",
        price=0.35,
        volume=10000.0,
        liquidity=30000.0
    )

    market3 = Market(
        token_id="token_3",
        condition_id="condition_1",
        question="Who will win?",
        outcome="Candidate C",
        price=0.25,
        volume=10000.0,
        liquidity=30000.0
    )

    event = Event(
        event_id="event_multi",
        title="Multi-candidate election",
        description="Three-way race",
        markets=[market1, market2, market3],
        category="politics"
    )

    opportunity = await detector.analyze_event(event)

    assert opportunity is None


@pytest.mark.asyncio
async def test_invalid_prices(detector):
    """
    Test handling of invalid prices (outside 0-1 range)

    Setup: Prices at boundaries and outside valid range
    Expected: Invalid prices rejected gracefully
    """
    # Test price = 0 (invalid)
    event_zero = create_test_event(
        event_id="event_zero",
        title="Zero price",
        yes_price=0.0,  # Invalid
        no_price=0.50
    )
    opportunity = await detector.analyze_event(event_zero)
    assert opportunity is None

    # Test price = 1 (invalid, must be < 1)
    event_one = create_test_event(
        event_id="event_one",
        title="One price",
        yes_price=1.0,  # Invalid
        no_price=0.50
    )
    opportunity = await detector.analyze_event(event_one)
    assert opportunity is None

    # Test price > 1 (invalid)
    event_over = create_test_event(
        event_id="event_over",
        title="Over one",
        yes_price=1.1,  # Invalid
        no_price=0.50
    )
    opportunity = await detector.analyze_event(event_over)
    assert opportunity is None

    # Test negative price (invalid)
    event_negative = create_test_event(
        event_id="event_neg",
        title="Negative price",
        yes_price=-0.1,  # Invalid
        no_price=0.50
    )
    opportunity = await detector.analyze_event(event_negative)
    assert opportunity is None


@pytest.mark.asyncio
async def test_missing_token_ids(detector):
    """
    Test that events with missing token IDs are rejected

    Setup: Event with empty token IDs
    Expected: No opportunity returned
    """
    event = create_test_event(
        event_id="event_no_tokens",
        title="Missing tokens",
        yes_price=0.55,
        no_price=0.50,
        yes_token_id="",  # Empty token ID
        no_token_id=""    # Empty token ID
    )

    opportunity = await detector.analyze_event(event)

    assert opportunity is None


@pytest.mark.asyncio
async def test_confidence_score_components(detector):
    """
    Test that confidence score properly weights all components

    Setup: Events with different characteristics
    Expected: Confidence scores reflect spread, liquidity, and balance
    """
    # High everything → high confidence
    event_high = create_test_event(
        event_id="high",
        title="High confidence",
        yes_price=0.56,  # 6% spread
        no_price=0.50,
        yes_liquidity=100000.0,  # Very high liquidity
        no_liquidity=100000.0
    )
    opp_high = await detector.analyze_event(event_high)

    # Medium spread, lower liquidity → medium confidence
    event_medium = create_test_event(
        event_id="medium",
        title="Medium confidence",
        yes_price=0.54,  # 4% spread
        no_price=0.50,
        yes_liquidity=20000.0,  # Medium liquidity
        no_liquidity=20000.0
    )
    opp_medium = await detector.analyze_event(event_medium)

    # Good spread but imbalanced liquidity → lower confidence
    event_imbalanced = create_test_event(
        event_id="imbalanced",
        title="Imbalanced liquidity",
        yes_price=0.55,  # 5% spread
        no_price=0.50,
        yes_liquidity=80000.0,  # Imbalanced
        no_liquidity=10000.0
    )
    opp_imbalanced = await detector.analyze_event(event_imbalanced)

    assert opp_high is not None
    assert opp_medium is not None
    assert opp_imbalanced is not None

    # High confidence should be highest
    assert opp_high.confidence_score > opp_medium.confidence_score

    # Imbalanced liquidity should have lower confidence despite good spread
    assert opp_imbalanced.confidence_score < opp_high.confidence_score


@pytest.mark.asyncio
async def test_scan_handles_errors_gracefully(mock_client):
    """
    Test that scan continues even if individual events fail

    Setup: Mix of valid events and one that raises an exception
    Expected: Valid opportunities returned, error logged, no crash
    """
    good_event_1 = create_test_event("good_1", "Good Event 1", 0.55, 0.50)
    good_event_2 = create_test_event("good_2", "Good Event 2", 0.54, 0.49)

    # Create a malformed event that will cause an error
    bad_event = Event(
        event_id="bad_event",
        title="Bad Event",
        description="Will cause error",
        markets=[],  # Empty markets - will fail is_binary check
        category="test"
    )

    async def mock_get_events():
        return [good_event_1, bad_event, good_event_2]

    mock_client.get_all_active_events = mock_get_events
    detector = IntraMarketArbitrageDetector(mock_client)

    opportunities = await detector.scan_all_markets()

    # Should have 2 opportunities (bad_event skipped)
    assert len(opportunities) == 2
    assert opportunities[0].event_id in ["good_1", "good_2"]
    assert opportunities[1].event_id in ["good_1", "good_2"]


@pytest.mark.asyncio
async def test_opportunity_validation(detector):
    """
    Test that ArbitrageOpportunity objects pass validation

    Setup: Create valid opportunity
    Expected: All fields properly set and pass __post_init__ validation
    """
    event = create_test_event(
        event_id="validate_test",
        title="Validation Test",
        yes_price=0.55,
        no_price=0.50
    )

    opportunity = await detector.analyze_event(event)

    assert opportunity is not None

    # Verify all required fields are set
    assert opportunity.opportunity_id
    assert opportunity.event_id == "validate_test"
    assert opportunity.event_title == "Validation Test"
    assert opportunity.yes_token_id
    assert opportunity.no_token_id
    assert 0 < opportunity.yes_price < 1
    assert 0 < opportunity.no_price < 1
    assert opportunity.price_sum > 0
    assert opportunity.spread > 0
    assert opportunity.arbitrage_type in ["OVERPRICED", "UNDERPRICED"]
    assert opportunity.required_capital > 0
    assert 0 <= opportunity.confidence_score <= 1
    assert opportunity.detected_at
    assert opportunity.valid_until
    assert opportunity.valid_until > opportunity.detected_at
