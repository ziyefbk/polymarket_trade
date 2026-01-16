"""
Database manager for arbitrage trading system

Provides async interface for storing and retrieving trade data, positions, and metrics.
"""
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.exc import SQLAlchemyError
from loguru import logger

from src.utils.models import Base, Trade, Position
from src.types.orders import ExecutionResult
from src.types.opportunities import ArbitrageOpportunity


class DatabaseManager:
    """
    Manages database operations for the arbitrage trading system

    Handles:
    - Trade execution history
    - Position tracking
    - Performance metrics calculation
    - Risk monitoring

    Usage:
        db = DatabaseManager("sqlite+aiosqlite:///./arbitrage.db")
        await db.initialize()
        trade = await db.save_trade(execution_result, opportunity)
    """

    def __init__(self, db_url: str = "sqlite+aiosqlite:///./arbitrage.db"):
        """
        Initialize database manager

        Args:
            db_url: SQLAlchemy database URL (async driver required)
                   Default: SQLite with aiosqlite driver
        """
        self.db_url = db_url
        self.engine = None
        self.SessionLocal = None

    async def initialize(self):
        """
        Initialize database connection and create tables

        Creates:
        - Database engine
        - Session factory
        - All tables from models

        Raises:
            SQLAlchemyError: If database initialization fails
        """
        try:
            self.engine = create_async_engine(
                self.db_url,
                echo=False,  # Set to True for SQL debugging
                pool_pre_ping=True,  # Verify connections before using
            )
            self.SessionLocal = async_sessionmaker(
                self.engine,
                class_=AsyncSession,
                expire_on_commit=False,
            )

            # Create all tables
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)

            logger.info(f"Database initialized successfully: {self.db_url}")

        except SQLAlchemyError as e:
            logger.critical(f"Failed to initialize database: {e}")
            raise

    async def close(self):
        """Close database connection and cleanup resources"""
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed")

    async def save_trade(
        self,
        execution_result: ExecutionResult,
        opportunity: Optional[ArbitrageOpportunity] = None
    ) -> Trade:
        """
        Save trade execution result to database

        Args:
            execution_result: Result from ArbitrageExecutor
            opportunity: Original opportunity (optional, for additional context)

        Returns:
            Trade object with assigned ID

        Raises:
            SQLAlchemyError: If database operation fails
        """
        async with self.SessionLocal() as session:
            try:
                # Create Trade record
                trade = Trade(
                    opportunity_id=execution_result.opportunity_id,
                    event_id=opportunity.event_id if opportunity else None,
                    event_title=opportunity.event_title if opportunity else None,
                    success=execution_result.success,
                    yes_token_id=opportunity.yes_token_id if opportunity else None,
                    yes_filled_size=execution_result.yes_filled_size,
                    yes_avg_price=execution_result.yes_avg_price,
                    yes_status=execution_result.yes_status,
                    no_token_id=opportunity.no_token_id if opportunity else None,
                    no_filled_size=execution_result.no_filled_size,
                    no_avg_price=execution_result.no_avg_price,
                    no_status=execution_result.no_status,
                    total_capital_used=execution_result.total_capital_used,
                    actual_profit_usd=execution_result.actual_profit_usd,
                    actual_profit_pct=execution_result.actual_profit_pct,
                    execution_time_ms=execution_result.execution_time_ms,
                    error_message=execution_result.error_message,
                    partial_fill_risk=execution_result.partial_fill_risk,
                    executed_at=execution_result.executed_at,
                )

                session.add(trade)
                await session.commit()
                await session.refresh(trade)

                logger.info(
                    f"Trade saved: ID={trade.id}, opportunity={trade.opportunity_id}, "
                    f"profit=${trade.actual_profit_usd:.2f}"
                )
                return trade

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Failed to save trade: {e}")
                raise

    async def update_trade_status(self, trade_id: int, status: str, error_message: Optional[str] = None):
        """
        Update trade status (for post-execution updates)

        Args:
            trade_id: Database ID of the trade
            status: New status value
            error_message: Optional error message

        Raises:
            SQLAlchemyError: If database operation fails
        """
        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Trade).where(Trade.id == trade_id)
                )
                trade = result.scalar_one_or_none()

                if trade:
                    trade.success = (status == "SUCCESS")
                    if error_message:
                        trade.error_message = error_message
                    trade.updated_at = datetime.utcnow()

                    await session.commit()
                    logger.info(f"Trade {trade_id} status updated to {status}")
                else:
                    logger.warning(f"Trade {trade_id} not found for status update")

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Failed to update trade status: {e}")
                raise

    async def create_position(
        self,
        trade_id: int,
        token_id: str,
        event_id: str,
        event_title: str,
        side: str,
        size: float,
        entry_price: float,
        cost_basis: float
    ) -> Position:
        """
        Create a new open position

        Args:
            trade_id: Related trade ID
            token_id: Token/market ID
            event_id: Event ID
            event_title: Event title
            side: "YES" or "NO"
            size: Position size (number of shares)
            entry_price: Entry price (0-1)
            cost_basis: Total USDC invested

        Returns:
            Created Position object

        Raises:
            SQLAlchemyError: If database operation fails
        """
        async with self.SessionLocal() as session:
            try:
                position = Position(
                    trade_id=trade_id,
                    token_id=token_id,
                    event_id=event_id,
                    event_title=event_title,
                    side=side,
                    size=size,
                    entry_price=entry_price,
                    current_price=entry_price,
                    cost_basis=cost_basis,
                    current_value=cost_basis,
                    unrealized_pnl=0.0,
                    status="OPEN",
                )

                session.add(position)
                await session.commit()
                await session.refresh(position)

                logger.info(f"Position created: ID={position.id}, token={token_id}, side={side}, size={size}")
                return position

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Failed to create position: {e}")
                raise

    async def get_open_positions(self) -> List[Position]:
        """
        Get all open positions

        Returns:
            List of open Position objects

        Raises:
            SQLAlchemyError: If database operation fails
        """
        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Position).where(Position.status == "OPEN")
                )
                positions = result.scalars().all()
                logger.debug(f"Retrieved {len(positions)} open positions")
                return list(positions)

            except SQLAlchemyError as e:
                logger.error(f"Failed to get open positions: {e}")
                raise

    async def update_position_value(self, position_id: int, current_price: float):
        """
        Update position market value based on current price

        Args:
            position_id: Position database ID
            current_price: Current market price (0-1)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Position).where(Position.id == position_id)
                )
                position = result.scalar_one_or_none()

                if position:
                    position.update_market_value(current_price)
                    await session.commit()
                    logger.debug(f"Position {position_id} value updated: price={current_price:.4f}")
                else:
                    logger.warning(f"Position {position_id} not found for value update")

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Failed to update position value: {e}")
                raise

    async def close_position(self, position_id: int, exit_price: float):
        """
        Close a position and calculate realized P&L

        Args:
            position_id: Position database ID
            exit_price: Exit price (0-1)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Position).where(Position.id == position_id)
                )
                position = result.scalar_one_or_none()

                if position:
                    position.close_position(exit_price)
                    await session.commit()
                    logger.info(
                        f"Position {position_id} closed: exit_price={exit_price:.4f}, "
                        f"realized_pnl=${position.realized_pnl:.2f}"
                    )
                else:
                    logger.warning(f"Position {position_id} not found for closing")

            except SQLAlchemyError as e:
                await session.rollback()
                logger.error(f"Failed to close position: {e}")
                raise

    async def get_daily_loss(self, date: Optional[datetime] = None) -> float:
        """
        Calculate total loss for a specific day

        Args:
            date: Date to calculate for (default: today)

        Returns:
            Total loss amount (positive number) for the day

        Raises:
            SQLAlchemyError: If database operation fails
        """
        if date is None:
            date = datetime.utcnow()

        start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)

        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(func.sum(Trade.actual_profit_usd))
                    .where(
                        and_(
                            Trade.executed_at >= start_of_day,
                            Trade.executed_at < end_of_day,
                            Trade.actual_profit_usd < 0  # Only losses
                        )
                    )
                )
                total_loss = result.scalar()
                daily_loss = abs(total_loss) if total_loss else 0.0

                logger.debug(f"Daily loss for {date.date()}: ${daily_loss:.2f}")
                return daily_loss

            except SQLAlchemyError as e:
                logger.error(f"Failed to calculate daily loss: {e}")
                raise

    async def get_total_capital_at_risk(self) -> float:
        """
        Calculate total capital currently at risk in open positions

        Returns:
            Total capital at risk (sum of cost_basis for open positions)

        Raises:
            SQLAlchemyError: If database operation fails
        """
        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(func.sum(Position.cost_basis))
                    .where(Position.status == "OPEN")
                )
                total_at_risk = result.scalar()
                capital_at_risk = total_at_risk if total_at_risk else 0.0

                logger.debug(f"Total capital at risk: ${capital_at_risk:.2f}")
                return capital_at_risk

            except SQLAlchemyError as e:
                logger.error(f"Failed to calculate capital at risk: {e}")
                raise

    async def get_trade_count_today(self) -> int:
        """
        Get number of trades executed today

        Returns:
            Number of trades today

        Raises:
            SQLAlchemyError: If database operation fails
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(func.count(Trade.id))
                    .where(Trade.executed_at >= today_start)
                )
                count = result.scalar()
                logger.debug(f"Trades executed today: {count}")
                return count

            except SQLAlchemyError as e:
                logger.error(f"Failed to get trade count: {e}")
                raise

    async def calculate_performance_metrics(self, days: int = 30) -> Dict[str, Any]:
        """
        Calculate performance metrics for the trading system

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Dictionary containing:
            - total_trades: Total number of trades
            - win_rate: Percentage of profitable trades
            - net_profit: Total net profit
            - sharpe_ratio: Risk-adjusted return metric
            - max_drawdown: Maximum drawdown percentage
            - avg_profit_per_trade: Average profit per trade

        Raises:
            SQLAlchemyError: If database operation fails
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        async with self.SessionLocal() as session:
            try:
                # Get all trades in the period
                result = await session.execute(
                    select(Trade)
                    .where(Trade.executed_at >= cutoff_date)
                    .order_by(Trade.executed_at)
                )
                trades = result.scalars().all()

                if not trades:
                    return {
                        "total_trades": 0,
                        "win_rate": 0.0,
                        "net_profit": 0.0,
                        "sharpe_ratio": 0.0,
                        "max_drawdown": 0.0,
                        "avg_profit_per_trade": 0.0,
                        "successful_trades": 0,
                        "failed_trades": 0,
                    }

                # Calculate metrics
                total_trades = len(trades)
                successful_trades = sum(1 for t in trades if t.success and t.actual_profit_usd > 0)
                failed_trades = sum(1 for t in trades if not t.success or t.actual_profit_usd < 0)
                win_rate = (successful_trades / total_trades * 100) if total_trades > 0 else 0.0

                profits = [t.actual_profit_usd for t in trades]
                net_profit = sum(profits)
                avg_profit = net_profit / total_trades if total_trades > 0 else 0.0

                # Calculate Sharpe ratio (simplified: assumes risk-free rate = 0)
                if len(profits) > 1:
                    profit_std = (sum((p - avg_profit) ** 2 for p in profits) / (len(profits) - 1)) ** 0.5
                    sharpe_ratio = (avg_profit / profit_std) if profit_std > 0 else 0.0
                else:
                    sharpe_ratio = 0.0

                # Calculate max drawdown
                cumulative = 0.0
                peak = 0.0
                max_drawdown = 0.0

                for profit in profits:
                    cumulative += profit
                    if cumulative > peak:
                        peak = cumulative
                    drawdown = peak - cumulative
                    if drawdown > max_drawdown:
                        max_drawdown = drawdown

                max_drawdown_pct = (max_drawdown / peak * 100) if peak > 0 else 0.0

                metrics = {
                    "total_trades": total_trades,
                    "successful_trades": successful_trades,
                    "failed_trades": failed_trades,
                    "win_rate": round(win_rate, 2),
                    "net_profit": round(net_profit, 2),
                    "sharpe_ratio": round(sharpe_ratio, 3),
                    "max_drawdown": round(max_drawdown_pct, 2),
                    "avg_profit_per_trade": round(avg_profit, 2),
                }

                logger.info(f"Performance metrics calculated: {metrics}")
                return metrics

            except SQLAlchemyError as e:
                logger.error(f"Failed to calculate performance metrics: {e}")
                raise

    async def get_recent_trades(self, limit: int = 10) -> List[Trade]:
        """
        Get most recent trades

        Args:
            limit: Maximum number of trades to return

        Returns:
            List of Trade objects, most recent first

        Raises:
            SQLAlchemyError: If database operation fails
        """
        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Trade)
                    .order_by(desc(Trade.executed_at))
                    .limit(limit)
                )
                trades = result.scalars().all()
                logger.debug(f"Retrieved {len(trades)} recent trades")
                return list(trades)

            except SQLAlchemyError as e:
                logger.error(f"Failed to get recent trades: {e}")
                raise

    async def get_trade_by_opportunity_id(self, opportunity_id: str) -> Optional[Trade]:
        """
        Find trade by opportunity ID

        Args:
            opportunity_id: Opportunity identifier

        Returns:
            Trade object if found, None otherwise

        Raises:
            SQLAlchemyError: If database operation fails
        """
        async with self.SessionLocal() as session:
            try:
                result = await session.execute(
                    select(Trade).where(Trade.opportunity_id == opportunity_id)
                )
                trade = result.scalar_one_or_none()
                return trade

            except SQLAlchemyError as e:
                logger.error(f"Failed to get trade by opportunity ID: {e}")
                raise

    async def __aenter__(self):
        """Async context manager entry"""
        await self.initialize()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
