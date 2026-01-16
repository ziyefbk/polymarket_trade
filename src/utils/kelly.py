"""
Kelly Criterion calculator for position sizing

The Kelly Criterion determines the optimal fraction of capital to risk on a bet
given the probability of winning and the payout odds.

Formula: f* = (bp - q) / b
Where:
- f* = optimal fraction of capital to bet
- b = odds received on the bet (net odds, i.e., payout / stake - 1)
- p = probability of winning
- q = probability of losing (1 - p)

For arbitrage trading, we adapt this to account for:
- Risk-free profit (arbitrage opportunities have no loss scenario if executed correctly)
- Slippage and execution risk
- Capital efficiency
"""
from typing import Optional
from loguru import logger


def calculate_kelly_fraction(
    win_probability: float,
    profit_ratio: float,
    max_fraction: float = 0.25,
    conservative_factor: float = 0.5
) -> float:
    """
    Calculate the optimal position size using Kelly Criterion

    Args:
        win_probability: Probability of successful execution (0-1)
        profit_ratio: Expected profit as a ratio (e.g., 0.05 for 5% profit)
        max_fraction: Maximum fraction of capital to risk (default: 0.25 = 25%)
        conservative_factor: Reduction factor for conservative betting (default: 0.5 = half-Kelly)

    Returns:
        Optimal fraction of capital to allocate (0-1)

    Raises:
        ValueError: If parameters are out of valid range

    Examples:
        >>> calculate_kelly_fraction(0.95, 0.03)  # 95% win prob, 3% profit
        0.125  # 12.5% of capital (half-Kelly with defaults)

        >>> calculate_kelly_fraction(0.80, 0.05, conservative_factor=1.0)  # Full Kelly
        0.15  # 15% of capital
    """
    # Validate inputs
    if not 0 <= win_probability <= 1:
        raise ValueError(f"Win probability must be between 0 and 1, got {win_probability}")

    if profit_ratio <= 0:
        raise ValueError(f"Profit ratio must be positive, got {profit_ratio}")

    if not 0 < max_fraction <= 1:
        raise ValueError(f"Max fraction must be between 0 and 1, got {max_fraction}")

    if not 0 < conservative_factor <= 1:
        raise ValueError(f"Conservative factor must be between 0 and 1, got {conservative_factor}")

    # Handle edge cases
    if win_probability == 0:
        logger.warning("Win probability is 0, returning 0 position size")
        return 0.0

    if win_probability == 1:
        # Perfect arbitrage - but still apply conservative factor
        kelly_fraction = max_fraction
    else:
        # Kelly Criterion formula: f* = (bp - q) / b
        # For our case:
        # - b (odds) = profit_ratio (the "odds" we get on our bet)
        # - p = win_probability
        # - q = 1 - win_probability

        loss_probability = 1 - win_probability
        kelly_fraction = (profit_ratio * win_probability - loss_probability) / profit_ratio

        # Kelly can be negative if edge is negative (bad bet)
        if kelly_fraction < 0:
            logger.warning(
                f"Negative Kelly fraction ({kelly_fraction:.2%}). "
                f"Win prob: {win_probability:.2%}, Profit ratio: {profit_ratio:.2%}"
            )
            return 0.0

    # Apply conservative factor (e.g., half-Kelly)
    adjusted_fraction = kelly_fraction * conservative_factor

    # Cap at maximum fraction
    final_fraction = min(adjusted_fraction, max_fraction)

    logger.debug(
        f"Kelly calculation: win_prob={win_probability:.2%}, "
        f"profit_ratio={profit_ratio:.2%}, "
        f"raw_kelly={kelly_fraction:.2%}, "
        f"adjusted={adjusted_fraction:.2%}, "
        f"final={final_fraction:.2%}"
    )

    return final_fraction


def calculate_position_size(
    available_capital: float,
    win_probability: float,
    profit_ratio: float,
    max_position_size: Optional[float] = None,
    conservative_factor: float = 0.5
) -> float:
    """
    Calculate the optimal position size in USD using Kelly Criterion

    Args:
        available_capital: Total available capital in USD
        win_probability: Probability of successful execution (0-1)
        profit_ratio: Expected profit as a ratio (e.g., 0.05 for 5% profit)
        max_position_size: Maximum position size in USD (optional hard cap)
        conservative_factor: Reduction factor for conservative betting (default: 0.5)

    Returns:
        Position size in USD

    Examples:
        >>> calculate_position_size(10000, 0.95, 0.03)  # $10k capital, 95% win, 3% profit
        1250.0  # $1,250 position

        >>> calculate_position_size(10000, 0.90, 0.05, max_position_size=1000)
        1000.0  # Capped at $1,000
    """
    if available_capital <= 0:
        raise ValueError(f"Available capital must be positive, got {available_capital}")

    # Calculate Kelly fraction (capped at 25% by default)
    kelly_fraction = calculate_kelly_fraction(
        win_probability=win_probability,
        profit_ratio=profit_ratio,
        max_fraction=0.25,
        conservative_factor=conservative_factor
    )

    # Calculate position size
    position_size = available_capital * kelly_fraction

    # Apply hard cap if specified
    if max_position_size is not None:
        position_size = min(position_size, max_position_size)

        if position_size == max_position_size:
            logger.debug(
                f"Position size capped at max_position_size: ${max_position_size:.2f}"
            )

    logger.info(
        f"Position sizing: capital=${available_capital:.2f}, "
        f"kelly_fraction={kelly_fraction:.2%}, "
        f"position_size=${position_size:.2f}"
    )

    return position_size


def estimate_execution_probability(
    liquidity: float,
    required_size: float,
    confidence_score: float,
    slippage_tolerance: float = 0.01
) -> float:
    """
    Estimate the probability of successful execution based on market conditions

    This function combines multiple factors to estimate win probability:
    1. Liquidity adequacy (is there enough depth?)
    2. Opportunity confidence (how reliable is the signal?)
    3. Slippage risk (will price move against us?)

    Args:
        liquidity: Available liquidity in the market (USD)
        required_size: Required position size (USD)
        confidence_score: Confidence score of the opportunity (0-1)
        slippage_tolerance: Maximum acceptable slippage (default: 1%)

    Returns:
        Estimated probability of successful execution (0-1)

    Examples:
        >>> estimate_execution_probability(100000, 1000, 0.9)
        0.85  # High liquidity, small size, high confidence

        >>> estimate_execution_probability(5000, 1000, 0.7)
        0.42  # Lower probability due to tight liquidity
    """
    if liquidity <= 0 or required_size <= 0:
        return 0.0

    # Factor 1: Liquidity ratio (how much of available liquidity we're using)
    liquidity_ratio = required_size / liquidity

    # Penalize heavily if we're using too much liquidity
    if liquidity_ratio > 0.5:
        liquidity_factor = 0.3  # Very risky
    elif liquidity_ratio > 0.3:
        liquidity_factor = 0.6  # Risky
    elif liquidity_ratio > 0.1:
        liquidity_factor = 0.8  # Moderate
    else:
        liquidity_factor = 0.95  # Safe

    # Factor 2: Confidence score (from opportunity detection)
    confidence_factor = confidence_score

    # Factor 3: Slippage risk (inverse relationship with slippage tolerance)
    # Lower slippage tolerance = higher execution risk
    slippage_factor = 1 - (slippage_tolerance * 2)  # 1% tolerance -> 0.98 factor
    slippage_factor = max(0.7, min(slippage_factor, 1.0))  # Clamp between 0.7 and 1.0

    # Combine factors (weighted geometric mean for conservative estimate)
    execution_probability = (
        liquidity_factor ** 0.4 *
        confidence_factor ** 0.4 *
        slippage_factor ** 0.2
    )

    logger.debug(
        f"Execution probability estimation: "
        f"liquidity_ratio={liquidity_ratio:.2%}, "
        f"liquidity_factor={liquidity_factor:.2f}, "
        f"confidence_factor={confidence_factor:.2f}, "
        f"slippage_factor={slippage_factor:.2f}, "
        f"result={execution_probability:.2%}"
    )

    return execution_probability
