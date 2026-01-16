"""
Polymarket CLOB API Client

Interfaces with Polymarket's Central Limit Order Book API to:
- Fetch market data and prices
- Get event information
- Monitor order book depth
- Execute trades
"""
import httpx
import asyncio
from typing import Optional, List, Dict, Any
from dataclasses import dataclass
from datetime import datetime
from loguru import logger

import sys
sys.path.append("../..")
from config.settings import settings


@dataclass
class Market:
    """Represents a Polymarket market (a specific outcome)"""
    token_id: str
    condition_id: str
    question: str
    outcome: str  # YES or NO
    price: float  # Current price (0-1)
    volume: float
    liquidity: float
    end_date: Optional[datetime] = None

    @property
    def implied_probability(self) -> float:
        """Price represents implied probability"""
        return self.price


@dataclass
class Event:
    """Represents a Polymarket event (contains multiple markets)"""
    event_id: str
    title: str
    description: str
    markets: List[Market]
    category: str
    end_date: Optional[datetime] = None

    @property
    def is_binary(self) -> bool:
        """Check if this is a simple YES/NO event"""
        return len(self.markets) == 2


@dataclass
class OrderBook:
    """Order book snapshot"""
    token_id: str
    bids: List[Dict[str, float]]  # [{"price": 0.5, "size": 100}, ...]
    asks: List[Dict[str, float]]
    timestamp: datetime

    @property
    def best_bid(self) -> Optional[float]:
        return self.bids[0]["price"] if self.bids else None

    @property
    def best_ask(self) -> Optional[float]:
        return self.asks[0]["price"] if self.asks else None

    @property
    def spread(self) -> Optional[float]:
        if self.best_bid and self.best_ask:
            return self.best_ask - self.best_bid
        return None


class PolymarketClient:
    """Async client for Polymarket CLOB API"""

    def __init__(self):
        self.base_url = settings.polymarket.api_base_url
        self.gamma_url = settings.polymarket.gamma_api_url
        self._client: Optional[httpx.AsyncClient] = None

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
    # Market Data
    # =========================================================================

    async def get_markets(
        self,
        limit: int = 100,
        offset: int = 0,
        active: bool = True
    ) -> List[Dict[str, Any]]:
        """Fetch list of markets from CLOB API"""
        params = {
            "limit": limit,
            "offset": offset,
            "active": active
        }
        response = await self.client.get(f"{self.base_url}/markets", params=params)
        response.raise_for_status()
        return response.json()

    async def get_market(self, token_id: str) -> Dict[str, Any]:
        """Fetch specific market by token ID"""
        response = await self.client.get(f"{self.base_url}/markets/{token_id}")
        response.raise_for_status()
        return response.json()

    async def get_prices(self, token_ids: List[str]) -> Dict[str, float]:
        """Fetch current prices for multiple tokens"""
        response = await self.client.get(
            f"{self.base_url}/prices",
            params={"token_ids": ",".join(token_ids)}
        )
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Event Data (Gamma API)
    # =========================================================================

    async def get_events(
        self,
        limit: int = 100,
        active: bool = True,
        closed: bool = False
    ) -> List[Dict[str, Any]]:
        """Fetch events from Gamma API"""
        params = {
            "limit": limit,
            "active": active,
            "closed": closed
        }
        response = await self.client.get(f"{self.gamma_url}/events", params=params)
        response.raise_for_status()
        return response.json()

    async def get_event(self, event_id: str) -> Dict[str, Any]:
        """Fetch specific event by ID"""
        response = await self.client.get(f"{self.gamma_url}/events/{event_id}")
        response.raise_for_status()
        return response.json()

    async def search_events(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search events by keyword"""
        params = {"q": query, "limit": limit}
        response = await self.client.get(f"{self.gamma_url}/events", params=params)
        response.raise_for_status()
        return response.json()

    # =========================================================================
    # Order Book
    # =========================================================================

    async def get_order_book(self, token_id: str) -> OrderBook:
        """Fetch order book for a market"""
        response = await self.client.get(f"{self.base_url}/book", params={"token_id": token_id})
        response.raise_for_status()
        data = response.json()

        return OrderBook(
            token_id=token_id,
            bids=data.get("bids", []),
            asks=data.get("asks", []),
            timestamp=datetime.now()
        )

    async def get_midpoint(self, token_id: str) -> Optional[float]:
        """Get midpoint price for a market"""
        response = await self.client.get(
            f"{self.base_url}/midpoint",
            params={"token_id": token_id}
        )
        response.raise_for_status()
        data = response.json()
        return data.get("mid")

    # =========================================================================
    # Bulk Operations
    # =========================================================================

    async def get_all_active_events(self) -> List[Event]:
        """Fetch all active events with their markets"""
        events = []
        offset = 0
        limit = 100

        while True:
            raw_events = await self.get_events(limit=limit, active=True)
            if not raw_events:
                break

            for raw in raw_events:
                markets = []
                for m in raw.get("markets", []):
                    markets.append(Market(
                        token_id=m.get("clobTokenIds", [""])[0] if m.get("clobTokenIds") else "",
                        condition_id=m.get("conditionId", ""),
                        question=m.get("question", ""),
                        outcome=m.get("outcome", ""),
                        price=float(m.get("outcomePrices", [0])[0]) if m.get("outcomePrices") else 0,
                        volume=float(m.get("volume", 0)),
                        liquidity=float(m.get("liquidity", 0)),
                    ))

                events.append(Event(
                    event_id=raw.get("id", ""),
                    title=raw.get("title", ""),
                    description=raw.get("description", ""),
                    markets=markets,
                    category=raw.get("category", ""),
                ))

            offset += limit
            if len(raw_events) < limit:
                break

        return events

    async def get_prices_batch(self, token_ids: List[str], batch_size: int = 50) -> Dict[str, float]:
        """Fetch prices in batches to avoid API limits"""
        all_prices = {}
        for i in range(0, len(token_ids), batch_size):
            batch = token_ids[i:i + batch_size]
            prices = await self.get_prices(batch)
            all_prices.update(prices)
            await asyncio.sleep(0.1)  # Rate limiting
        return all_prices


# Convenience function for quick usage
async def get_client() -> PolymarketClient:
    return PolymarketClient()
