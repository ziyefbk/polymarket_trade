"""
Order execution result data structures
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
import sys
sys.path.append("../..")
from src.api.trader import Order


@dataclass
class ExecutionResult:
    """
    Result of executing an arbitrage opportunity

    This is the core data structure passed from the Executor to the Database.
    """
    # Link to the opportunity
    opportunity_id: str
    success: bool

    # YES leg execution details
    yes_order: Optional[Order] = None
    yes_filled_size: float = 0.0
    yes_avg_price: float = 0.0
    yes_status: str = "PENDING"  # "FILLED", "PARTIAL", "FAILED"

    # NO leg execution details
    no_order: Optional[Order] = None
    no_filled_size: float = 0.0
    no_avg_price: float = 0.0
    no_status: str = "PENDING"  # "FILLED", "PARTIAL", "FAILED"

    # Overall execution metrics
    total_capital_used: float = 0.0
    actual_profit_usd: float = 0.0
    actual_profit_pct: float = 0.0
    execution_time_ms: float = 0.0

    # Error handling
    error_message: Optional[str] = None
    partial_fill_risk: bool = False  # True if one leg filled but other didn't

    # Timestamps
    executed_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate execution result"""
        assert self.yes_status in ["PENDING", "FILLED", "PARTIAL", "FAILED"], \
            f"Invalid YES status: {self.yes_status}"
        assert self.no_status in ["PENDING", "FILLED", "PARTIAL", "FAILED"], \
            f"Invalid NO status: {self.no_status}"

    @property
    def both_legs_filled(self) -> bool:
        """Check if both legs were fully filled"""
        return self.yes_status == "FILLED" and self.no_status == "FILLED"

    @property
    def any_leg_failed(self) -> bool:
        """Check if any leg failed"""
        return self.yes_status == "FAILED" or self.no_status == "FAILED"

    def to_dict(self) -> dict:
        """Convert to dictionary for database storage"""
        return {
            "opportunity_id": self.opportunity_id,
            "success": self.success,
            "yes_filled_size": self.yes_filled_size,
            "yes_avg_price": self.yes_avg_price,
            "yes_status": self.yes_status,
            "no_filled_size": self.no_filled_size,
            "no_avg_price": self.no_avg_price,
            "no_status": self.no_status,
            "total_capital_used": self.total_capital_used,
            "actual_profit_usd": self.actual_profit_usd,
            "actual_profit_pct": self.actual_profit_pct,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "partial_fill_risk": self.partial_fill_risk,
            "executed_at": self.executed_at.isoformat(),
        }
