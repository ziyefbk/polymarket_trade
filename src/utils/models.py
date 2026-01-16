"""
SQLAlchemy models for arbitrage trading database

These models store trade execution history, positions, and performance metrics.
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Float, Boolean, DateTime, Integer, ForeignKey, Index
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class Trade(Base):
    """
    Represents a completed arbitrage trade execution

    Maps to ExecutionResult from src/types/orders.py
    """
    __tablename__ = "trades"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys and identifiers
    opportunity_id = Column(String(50), nullable=False, index=True)
    event_id = Column(String(100), nullable=True)  # From ArbitrageOpportunity
    event_title = Column(String(500), nullable=True)

    # Execution outcome
    success = Column(Boolean, nullable=False, default=False)

    # YES leg details
    yes_token_id = Column(String(100), nullable=True)
    yes_filled_size = Column(Float, nullable=False, default=0.0)
    yes_avg_price = Column(Float, nullable=False, default=0.0)
    yes_status = Column(String(20), nullable=False, default="PENDING")  # FILLED/PARTIAL/FAILED

    # NO leg details
    no_token_id = Column(String(100), nullable=True)
    no_filled_size = Column(Float, nullable=False, default=0.0)
    no_avg_price = Column(Float, nullable=False, default=0.0)
    no_status = Column(String(20), nullable=False, default="PENDING")  # FILLED/PARTIAL/FAILED

    # Financial metrics
    total_capital_used = Column(Float, nullable=False, default=0.0)
    actual_profit_usd = Column(Float, nullable=False, default=0.0)
    actual_profit_pct = Column(Float, nullable=False, default=0.0)

    # Execution metrics
    execution_time_ms = Column(Float, nullable=False, default=0.0)

    # Error handling
    error_message = Column(String(1000), nullable=True)
    partial_fill_risk = Column(Boolean, nullable=False, default=False)

    # Timestamps
    executed_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    positions = relationship("Position", back_populates="trade", cascade="all, delete-orphan")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_executed_at', 'executed_at'),
        Index('idx_success', 'success'),
        Index('idx_opportunity_id', 'opportunity_id'),
    )

    def __repr__(self):
        return (f"<Trade(id={self.id}, opportunity_id={self.opportunity_id}, "
                f"success={self.success}, profit=${self.actual_profit_usd:.2f})>")

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "opportunity_id": self.opportunity_id,
            "event_id": self.event_id,
            "event_title": self.event_title,
            "success": self.success,
            "yes_token_id": self.yes_token_id,
            "yes_filled_size": self.yes_filled_size,
            "yes_avg_price": self.yes_avg_price,
            "yes_status": self.yes_status,
            "no_token_id": self.no_token_id,
            "no_filled_size": self.no_filled_size,
            "no_avg_price": self.no_avg_price,
            "no_status": self.no_status,
            "total_capital_used": self.total_capital_used,
            "actual_profit_usd": self.actual_profit_usd,
            "actual_profit_pct": self.actual_profit_pct,
            "execution_time_ms": self.execution_time_ms,
            "error_message": self.error_message,
            "partial_fill_risk": self.partial_fill_risk,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Position(Base):
    """
    Represents an open position in a specific market

    Used for tracking exposure and calculating risk limits.
    A position can be open or closed.
    """
    __tablename__ = "positions"

    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)

    # Foreign keys
    trade_id = Column(Integer, ForeignKey("trades.id"), nullable=True, index=True)

    # Position details
    token_id = Column(String(100), nullable=False, index=True)
    event_id = Column(String(100), nullable=False, index=True)
    event_title = Column(String(500), nullable=True)

    # Position side and size
    side = Column(String(10), nullable=False)  # "YES" or "NO"
    size = Column(Float, nullable=False)  # Number of shares held
    entry_price = Column(Float, nullable=False)  # Average entry price
    current_price = Column(Float, nullable=True)  # Latest market price

    # Financial tracking
    cost_basis = Column(Float, nullable=False)  # Total USDC invested
    current_value = Column(Float, nullable=True)  # Current market value
    unrealized_pnl = Column(Float, nullable=True)  # Unrealized profit/loss
    realized_pnl = Column(Float, nullable=False, default=0.0)  # Realized profit/loss on close

    # Position status
    status = Column(String(20), nullable=False, default="OPEN")  # OPEN/CLOSED/EXPIRED

    # Timestamps
    opened_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    closed_at = Column(DateTime, nullable=True)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    trade = relationship("Trade", back_populates="positions")

    # Indexes for common queries
    __table_args__ = (
        Index('idx_status', 'status'),
        Index('idx_token_id', 'token_id'),
        Index('idx_event_id', 'event_id'),
        Index('idx_opened_at', 'opened_at'),
    )

    def __repr__(self):
        return (f"<Position(id={self.id}, token_id={self.token_id}, "
                f"side={self.side}, size={self.size}, status={self.status})>")

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization"""
        return {
            "id": self.id,
            "trade_id": self.trade_id,
            "token_id": self.token_id,
            "event_id": self.event_id,
            "event_title": self.event_title,
            "side": self.side,
            "size": self.size,
            "entry_price": self.entry_price,
            "current_price": self.current_price,
            "cost_basis": self.cost_basis,
            "current_value": self.current_value,
            "unrealized_pnl": self.unrealized_pnl,
            "realized_pnl": self.realized_pnl,
            "status": self.status,
            "opened_at": self.opened_at.isoformat() if self.opened_at else None,
            "closed_at": self.closed_at.isoformat() if self.closed_at else None,
        }

    def update_market_value(self, current_price: float):
        """
        Update position value based on current market price

        Args:
            current_price: Current market price (0-1)
        """
        self.current_price = current_price
        self.current_value = self.size * current_price
        self.unrealized_pnl = self.current_value - self.cost_basis
        self.updated_at = datetime.utcnow()

    def close_position(self, exit_price: float):
        """
        Close the position and calculate realized P&L

        Args:
            exit_price: Exit price (0-1)
        """
        exit_value = self.size * exit_price
        self.realized_pnl = exit_value - self.cost_basis
        self.current_price = exit_price
        self.current_value = exit_value
        self.status = "CLOSED"
        self.closed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
