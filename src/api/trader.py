"""
Polymarket Trading Client

Handles order execution on Polymarket using the CLOB API.
Requires wallet authentication via private key.
"""
import httpx
import hashlib
import time
from typing import Optional, Dict, Any, Literal
from dataclasses import dataclass
from enum import Enum
from loguru import logger

from eth_account import Account
from eth_account.messages import encode_defunct
from web3 import Web3

import sys
sys.path.append("../..")
from config.settings import settings


class OrderSide(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class OrderType(str, Enum):
    LIMIT = "LIMIT"
    MARKET = "MARKET"


@dataclass
class Order:
    """Represents an order"""
    order_id: str
    token_id: str
    side: OrderSide
    price: float
    size: float
    status: str
    created_at: float


@dataclass
class TradeResult:
    """Result of a trade execution"""
    success: bool
    order_id: Optional[str] = None
    filled_size: float = 0
    avg_price: float = 0
    error: Optional[str] = None


class PolymarketTrader:
    """
    Trading client for Polymarket CLOB.

    Note: Actual trading requires:
    1. Valid Polygon wallet with USDC
    2. Approved spending on Polymarket contracts
    3. Valid API credentials
    """

    def __init__(self, private_key: Optional[str] = None):
        self.base_url = settings.polymarket.api_base_url
        self.private_key = private_key or settings.polymarket.private_key
        self._client: Optional[httpx.AsyncClient] = None
        self._account: Optional[Account] = None

        if self.private_key:
            self._account = Account.from_key(self.private_key)
            logger.info(f"Trading wallet initialized: {self._account.address}")

    @property
    def address(self) -> Optional[str]:
        return self._account.address if self._account else None

    async def __aenter__(self):
        self._client = httpx.AsyncClient(timeout=30.0)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._client:
            await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        if not self._client:
            raise RuntimeError("Client not initialized. Use 'async with' context manager.")
        return self._client

    # =========================================================================
    # Authentication
    # =========================================================================

    def _sign_message(self, message: str) -> str:
        """Sign a message with the private key"""
        if not self._account:
            raise ValueError("No private key configured")

        message_hash = encode_defunct(text=message)
        signed = self._account.sign_message(message_hash)
        return signed.signature.hex()

    def _create_auth_headers(self) -> Dict[str, str]:
        """Create authentication headers for API requests"""
        if not self._account:
            return {}

        timestamp = str(int(time.time() * 1000))
        message = f"polymarket:{timestamp}"
        signature = self._sign_message(message)

        return {
            "POLY_ADDRESS": self._account.address,
            "POLY_SIGNATURE": signature,
            "POLY_TIMESTAMP": timestamp,
        }

    # =========================================================================
    # Order Management
    # =========================================================================

    async def place_order(
        self,
        token_id: str,
        side: OrderSide,
        price: float,
        size: float,
        order_type: OrderType = OrderType.LIMIT
    ) -> TradeResult:
        """
        Place an order on Polymarket.

        Args:
            token_id: The market token ID
            side: BUY or SELL
            price: Limit price (0-1 for prediction markets)
            size: Size in shares
            order_type: LIMIT or MARKET

        Returns:
            TradeResult with order details
        """
        if not self._account:
            return TradeResult(success=False, error="No wallet configured")

        # Validate inputs
        if not 0 < price < 1:
            return TradeResult(success=False, error="Price must be between 0 and 1")

        if size <= 0:
            return TradeResult(success=False, error="Size must be positive")

        try:
            order_payload = {
                "tokenId": token_id,
                "side": side.value,
                "price": str(price),
                "size": str(size),
                "type": order_type.value,
            }

            headers = self._create_auth_headers()
            response = await self.client.post(
                f"{self.base_url}/order",
                json=order_payload,
                headers=headers
            )
            response.raise_for_status()
            data = response.json()

            return TradeResult(
                success=True,
                order_id=data.get("orderID"),
                filled_size=float(data.get("filledSize", 0)),
                avg_price=float(data.get("avgPrice", price)),
            )

        except httpx.HTTPStatusError as e:
            logger.error(f"Order failed: {e.response.text}")
            return TradeResult(success=False, error=str(e))
        except Exception as e:
            logger.error(f"Order error: {e}")
            return TradeResult(success=False, error=str(e))

    async def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order"""
        if not self._account:
            return False

        try:
            headers = self._create_auth_headers()
            response = await self.client.delete(
                f"{self.base_url}/order/{order_id}",
                headers=headers
            )
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Cancel order failed: {e}")
            return False

    async def get_open_orders(self) -> list[Order]:
        """Get all open orders for the wallet"""
        if not self._account:
            return []

        try:
            headers = self._create_auth_headers()
            response = await self.client.get(
                f"{self.base_url}/orders",
                headers=headers,
                params={"owner": self._account.address}
            )
            response.raise_for_status()
            data = response.json()

            return [
                Order(
                    order_id=o.get("id", ""),
                    token_id=o.get("tokenId", ""),
                    side=OrderSide(o.get("side", "BUY")),
                    price=float(o.get("price", 0)),
                    size=float(o.get("size", 0)),
                    status=o.get("status", ""),
                    created_at=float(o.get("createdAt", 0)),
                )
                for o in data
            ]
        except Exception as e:
            logger.error(f"Get orders failed: {e}")
            return []

    # =========================================================================
    # Convenience Methods
    # =========================================================================

    async def buy(self, token_id: str, price: float, size: float) -> TradeResult:
        """Place a buy order"""
        return await self.place_order(token_id, OrderSide.BUY, price, size)

    async def sell(self, token_id: str, price: float, size: float) -> TradeResult:
        """Place a sell order"""
        return await self.place_order(token_id, OrderSide.SELL, price, size)

    async def market_buy(self, token_id: str, size: float, max_price: float = 0.99) -> TradeResult:
        """Place a market buy order"""
        return await self.place_order(
            token_id, OrderSide.BUY, max_price, size, OrderType.MARKET
        )

    async def market_sell(self, token_id: str, size: float, min_price: float = 0.01) -> TradeResult:
        """Place a market sell order"""
        return await self.place_order(
            token_id, OrderSide.SELL, min_price, size, OrderType.MARKET
        )
