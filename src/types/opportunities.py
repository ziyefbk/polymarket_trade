"""
Arbitrage opportunity data structures
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import sys
sys.path.append("../..")
from src.api.polymarket_client import OrderBook


@dataclass
class ArbitrageOpportunity:
    """
    Represents an intra-market arbitrage opportunity where YES + NO prices != 1.0

    This is the core data structure passed from the Detector to the Executor.
    """
    # Unique identifiers
    opportunity_id: str
    event_id: str
    event_title: str

    # YES market information
    yes_token_id: str
    yes_price: float  # Current price (0-1)
    yes_liquidity: float  # Available liquidity in USDC
    yes_order_book: Optional[OrderBook] = None

    # NO market information
    no_token_id: str
    no_price: float  # Current price (0-1)
    no_liquidity: float  # Available liquidity in USDC
    no_order_book: Optional[OrderBook] = None

    # Arbitrage metrics
    price_sum: float  # yes_price + no_price
    spread: float  # abs(price_sum - 1.0)
    arbitrage_type: str  # "OVERPRICED" (sum > 1) or "UNDERPRICED" (sum < 1)

    # Profit estimation
    expected_profit_pct: float  # Expected profit as percentage
    expected_profit_usd: float  # Expected profit in USD for given capital
    estimated_fees: float  # Estimated trading fees
    estimated_slippage: float  # Estimated slippage cost
    net_profit_pct: float  # Net profit after fees and slippage

    # Executability assessment
    is_executable: bool  # Whether this opportunity can be executed
    required_capital: float  # Minimum capital needed
    confidence_score: float  # 0-1 confidence score

    # Timestamps
    detected_at: datetime
    valid_until: datetime  # When this opportunity expires

    def __post_init__(self):
        """Validate the opportunity after initialization"""
        assert 0 < self.yes_price < 1, f"YES price must be between 0 and 1, got {self.yes_price}"
        assert 0 < self.no_price < 1, f"NO price must be between 0 and 1, got {self.no_price}"
        assert 0 <= self.confidence_score <= 1, f"Confidence must be 0-1, got {self.confidence_score}"
        assert self.arbitrage_type in ["OVERPRICED", "UNDERPRICED"], f"Invalid type: {self.arbitrage_type}"

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "opportunity_id": self.opportunity_id,
            "event_id": self.event_id,
            "event_title": self.event_title,
            "yes_token_id": self.yes_token_id,
            "yes_price": self.yes_price,
            "no_token_id": self.no_token_id,
            "no_price": self.no_price,
            "spread": self.spread,
            "arbitrage_type": self.arbitrage_type,
            "net_profit_pct": self.net_profit_pct,
            "confidence_score": self.confidence_score,
            "detected_at": self.detected_at.isoformat(),
        }
