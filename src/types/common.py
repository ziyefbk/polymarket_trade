"""
Common data types and exceptions for the arbitrage system
"""


class ArbitrageError(Exception):
    """Base exception for arbitrage-related errors"""
    pass


class InsufficientLiquidityError(ArbitrageError):
    """Raised when market liquidity is insufficient for trade execution"""
    pass


class ExecutionFailedError(ArbitrageError):
    """Raised when trade execution fails"""
    pass


class PriceStaleError(ArbitrageError):
    """Raised when prices have moved significantly since opportunity detection"""
    pass


class RiskLimitExceededError(ArbitrageError):
    """Raised when risk limits are exceeded"""
    pass
