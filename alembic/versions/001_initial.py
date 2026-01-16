"""Initial database schema

Revision ID: 001_initial
Revises:
Create Date: 2026-01-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '001_initial'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Create initial database schema with trades and positions tables
    """
    # Create trades table
    op.create_table(
        'trades',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('opportunity_id', sa.String(length=50), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=True),
        sa.Column('event_title', sa.String(length=500), nullable=True),
        sa.Column('success', sa.Boolean(), nullable=False, default=False),
        sa.Column('yes_token_id', sa.String(length=100), nullable=True),
        sa.Column('yes_filled_size', sa.Float(), nullable=False, default=0.0),
        sa.Column('yes_avg_price', sa.Float(), nullable=False, default=0.0),
        sa.Column('yes_status', sa.String(length=20), nullable=False, default='PENDING'),
        sa.Column('no_token_id', sa.String(length=100), nullable=True),
        sa.Column('no_filled_size', sa.Float(), nullable=False, default=0.0),
        sa.Column('no_avg_price', sa.Float(), nullable=False, default=0.0),
        sa.Column('no_status', sa.String(length=20), nullable=False, default='PENDING'),
        sa.Column('total_capital_used', sa.Float(), nullable=False, default=0.0),
        sa.Column('actual_profit_usd', sa.Float(), nullable=False, default=0.0),
        sa.Column('actual_profit_pct', sa.Float(), nullable=False, default=0.0),
        sa.Column('execution_time_ms', sa.Float(), nullable=False, default=0.0),
        sa.Column('error_message', sa.String(length=1000), nullable=True),
        sa.Column('partial_fill_risk', sa.Boolean(), nullable=False, default=False),
        sa.Column('executed_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for trades table
    op.create_index('idx_executed_at', 'trades', ['executed_at'])
    op.create_index('idx_success', 'trades', ['success'])
    op.create_index('idx_opportunity_id', 'trades', ['opportunity_id'])

    # Create positions table
    op.create_table(
        'positions',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('trade_id', sa.Integer(), nullable=True),
        sa.Column('token_id', sa.String(length=100), nullable=False),
        sa.Column('event_id', sa.String(length=100), nullable=False),
        sa.Column('event_title', sa.String(length=500), nullable=True),
        sa.Column('side', sa.String(length=10), nullable=False),
        sa.Column('size', sa.Float(), nullable=False),
        sa.Column('entry_price', sa.Float(), nullable=False),
        sa.Column('current_price', sa.Float(), nullable=True),
        sa.Column('cost_basis', sa.Float(), nullable=False),
        sa.Column('current_value', sa.Float(), nullable=True),
        sa.Column('unrealized_pnl', sa.Float(), nullable=True),
        sa.Column('realized_pnl', sa.Float(), nullable=False, default=0.0),
        sa.Column('status', sa.String(length=20), nullable=False, default='OPEN'),
        sa.Column('opened_at', sa.DateTime(), nullable=False),
        sa.Column('closed_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['trade_id'], ['trades.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for positions table
    op.create_index('idx_status', 'positions', ['status'])
    op.create_index('idx_token_id', 'positions', ['token_id'])
    op.create_index('idx_event_id', 'positions', ['event_id'])
    op.create_index('idx_opened_at', 'positions', ['opened_at'])
    op.create_index(op.f('ix_positions_trade_id'), 'positions', ['trade_id'], unique=False)


def downgrade() -> None:
    """
    Drop all tables and indexes
    """
    # Drop positions table and its indexes
    op.drop_index(op.f('ix_positions_trade_id'), table_name='positions')
    op.drop_index('idx_opened_at', table_name='positions')
    op.drop_index('idx_event_id', table_name='positions')
    op.drop_index('idx_token_id', table_name='positions')
    op.drop_index('idx_status', table_name='positions')
    op.drop_table('positions')

    # Drop trades table and its indexes
    op.drop_index('idx_opportunity_id', table_name='trades')
    op.drop_index('idx_success', table_name='trades')
    op.drop_index('idx_executed_at', table_name='trades')
    op.drop_table('trades')
