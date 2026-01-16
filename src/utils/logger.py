"""
Logging configuration for the Polymarket Arbitrage System

This module configures the loguru logger with:
- Console output with color-coding
- File output with rotation
- Standardized formats following INTERFACE_SPEC.md section 6
"""
import sys
from pathlib import Path
from typing import Optional
from loguru import logger
from config import settings


def setup_logger(
    log_level: Optional[str] = None,
    log_file: Optional[str] = None,
    rotation: str = "100 MB",
    retention: str = "30 days",
    compression: str = "zip"
) -> None:
    """
    Configure the loguru logger for the arbitrage system

    Args:
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
                   Defaults to settings.log_level
        log_file: Path to log file. Defaults to settings.log_file
        rotation: When to rotate log files (default: "100 MB")
        retention: How long to keep old log files (default: "30 days")
        compression: Compression format for rotated logs (default: "zip")

    Returns:
        None

    Example:
        >>> setup_logger()
        >>> logger.info("System initialized")
    """
    # Use settings defaults if not provided
    log_level = log_level or settings.log_level
    log_file = log_file or settings.log_file

    # Remove default logger
    logger.remove()

    # Console handler with color-coding
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
            "<level>{message}</level>"
        ),
        level=log_level,
        colorize=True,
    )

    # File handler with rotation
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logger.add(
        log_file,
        format=(
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | "
            "{level: <8} | "
            "{name}:{function}:{line} | "
            "{message}"
        ),
        level=log_level,
        rotation=rotation,
        retention=retention,
        compression=compression,
        enqueue=True,  # Thread-safe
    )

    logger.info(f"Logger initialized: level={log_level}, file={log_file}")


def get_logger(name: str):
    """
    Get a logger instance with a specific name

    Args:
        name: Name for the logger (typically __name__)

    Returns:
        Logger instance

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module loaded")
    """
    return logger.bind(name=name)


# Convenience functions for standardized logging messages
def log_opportunity_found(opp: "ArbitrageOpportunity") -> None:
    """
    Log a discovered arbitrage opportunity

    Args:
        opp: The arbitrage opportunity to log
    """
    logger.info(f"Found arbitrage opportunity: {opp.event_title}")
    logger.info(
        f"  Type: {opp.arbitrage_type}, "
        f"Spread: {opp.spread:.2%}, "
        f"Net profit: {opp.net_profit_pct:.2%}"
    )
    logger.debug(
        f"  YES: ${opp.yes_price:.4f} (liquidity: ${opp.yes_liquidity:,.0f}), "
        f"NO: ${opp.no_price:.4f} (liquidity: ${opp.no_liquidity:,.0f})"
    )


def log_execution_start(opp_id: str, size: float) -> None:
    """
    Log the start of trade execution

    Args:
        opp_id: Opportunity ID being executed
        size: Position size in USDC
    """
    logger.info(f"Executing opportunity {opp_id} with size ${size:.2f}")


def log_execution_success(result: "ExecutionResult") -> None:
    """
    Log successful trade execution

    Args:
        result: Execution result to log
    """
    logger.success(
        f"✓ Trade executed successfully. "
        f"Profit: ${result.actual_profit_usd:.2f} ({result.actual_profit_pct:.2%}), "
        f"Time: {result.execution_time_ms:.0f}ms"
    )
    logger.debug(
        f"  YES: {result.yes_filled_size:.2f} @ ${result.yes_avg_price:.4f} ({result.yes_status}), "
        f"NO: {result.no_filled_size:.2f} @ ${result.no_avg_price:.4f} ({result.no_status})"
    )


def log_execution_failure(result: "ExecutionResult") -> None:
    """
    Log failed trade execution

    Args:
        result: Execution result to log
    """
    logger.error(f"✗ Trade failed: {result.error_message}")
    if result.partial_fill_risk:
        logger.warning("⚠ Partial fill risk detected - one leg may be exposed")


def log_risk_check(risk_status: dict) -> None:
    """
    Log risk limit check results

    Args:
        risk_status: Dictionary containing risk check results
    """
    if not risk_status.get("can_trade", False):
        logger.warning("Risk limits exceeded - trading paused")
        if not risk_status.get("daily_loss_ok"):
            logger.warning("  Daily loss limit reached")
        if not risk_status.get("position_count_ok"):
            logger.warning("  Max open positions reached")
        if not risk_status.get("capital_available"):
            logger.warning("  Insufficient capital available")
    else:
        logger.debug("Risk checks passed")


def log_scan_cycle_start(cycle_number: int) -> None:
    """
    Log the start of a scan cycle

    Args:
        cycle_number: Cycle number
    """
    logger.info(f"{'='*60}")
    logger.info(f"Starting scan cycle #{cycle_number}")


def log_scan_cycle_complete(cycle_number: int, opportunities_found: int, trades_executed: int) -> None:
    """
    Log the completion of a scan cycle

    Args:
        cycle_number: Cycle number
        opportunities_found: Number of opportunities found
        trades_executed: Number of trades executed
    """
    logger.info(
        f"Scan cycle #{cycle_number} complete: "
        f"{opportunities_found} opportunities found, "
        f"{trades_executed} trades executed"
    )
    logger.info(f"{'='*60}")


# Initialize logger on module import
setup_logger()
