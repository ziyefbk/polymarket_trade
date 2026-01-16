"""
Configuration settings for Polymarket Arbitrage System
"""
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional
import os


class PolymarketConfig(BaseSettings):
    """Polymarket API Configuration"""
    api_base_url: str = "https://clob.polymarket.com"
    gamma_api_url: str = "https://gamma-api.polymarket.com"
    chain_id: int = 137  # Polygon mainnet

    # Private key for trading (load from env)
    private_key: Optional[str] = Field(default=None, env="POLYMARKET_PRIVATE_KEY")

    class Config:
        env_prefix = "POLYMARKET_"


class NewsConfig(BaseSettings):
    """News API Configuration"""
    newsapi_key: Optional[str] = Field(default=None, env="NEWSAPI_KEY")
    twitter_bearer_token: Optional[str] = Field(default=None, env="TWITTER_BEARER_TOKEN")

    class Config:
        env_prefix = ""


class TradingConfig(BaseSettings):
    """Trading Parameters"""
    # Minimum profit threshold (percentage)
    min_profit_threshold: float = 0.02  # 2%

    # Maximum position size (USDC)
    max_position_size: float = 1000.0

    # Risk limits
    max_daily_loss: float = 100.0
    max_open_positions: int = 10

    # Slippage tolerance
    slippage_tolerance: float = 0.01  # 1%

    class Config:
        env_prefix = "TRADING_"


class ArbitrageConfig(BaseSettings):
    """Arbitrage Detection Parameters"""
    # Minimum price discrepancy to consider
    min_discrepancy: float = 0.03  # 3%

    # Event correlation threshold
    correlation_threshold: float = 0.8

    # Scan interval (seconds)
    scan_interval: int = 30

    class Config:
        env_prefix = "ARBITRAGE_"


class Settings(BaseSettings):
    """Main Settings"""
    polymarket: PolymarketConfig = PolymarketConfig()
    news: NewsConfig = NewsConfig()
    trading: TradingConfig = TradingConfig()
    arbitrage: ArbitrageConfig = ArbitrageConfig()

    # Database
    database_url: str = "sqlite+aiosqlite:///./data/arbitrage.db"

    # Logging
    log_level: str = "INFO"
    log_file: str = "./logs/arbitrage.log"


settings = Settings()
