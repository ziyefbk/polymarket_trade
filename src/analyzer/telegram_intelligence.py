"""
Telegram Intelligence Analyzer for Polymarket Trading

This module monitors Telegram channels and groups for market-relevant discussions:
- Tracks crypto/political/news channels
- Performs sentiment analysis on messages
- Detects trending topics and viral discussions
- Identifies influential channel admins
- Analyzes message frequency and engagement
"""
import asyncio
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger

try:
    from telethon import TelegramClient
    from telethon.tl.types import Message as TelegramMessage
    from textblob import TextBlob
    TELEGRAM_AVAILABLE = True
except ImportError:
    TELEGRAM_AVAILABLE = False
    logger.warning("Telegram integration not available. Install: pip install telethon textblob")


@dataclass
class TelegramChannelMessage:
    """Represents a Telegram message"""
    message_id: int
    channel_name: str
    channel_username: str
    author: str
    text: str
    views: int
    forwards: int
    replies: int
    posted_at: datetime
    sentiment_score: float = 0.0
    sentiment_label: str = "neutral"
    engagement_score: float = 0.0


@dataclass
class TelegramIntelligence:
    """Intelligence report from Telegram monitoring"""
    query: str
    channels_monitored: List[str]
    time_period_start: datetime
    time_period_end: datetime
    total_messages: int
    avg_sentiment: float
    sentiment_distribution: Dict[str, int]
    top_messages: List[TelegramChannelMessage]
    viral_messages: List[TelegramChannelMessage]  # High engagement
    trending_keywords: List[tuple]
    channel_consensus: str  # "BULLISH", "BEARISH", "DIVIDED"
    consensus_strength: float  # 0-1
    generated_at: datetime = field(default_factory=datetime.now)


class TelegramIntelligenceAnalyzer:
    """
    Monitors Telegram channels for intelligence related to Polymarket events.

    Features:
    - Multi-channel monitoring
    - Sentiment analysis on messages
    - Viral content detection
    - Real-time message streaming
    - Channel consensus analysis
    """

    def __init__(
        self,
        api_id: Optional[int] = None,
        api_hash: Optional[str] = None,
        session_name: str = "polymarket_monitor"
    ):
        """
        Initialize Telegram analyzer.

        Args:
            api_id: Telegram API ID (from my.telegram.org)
            api_hash: Telegram API hash
            session_name: Session file name
        """
        if not TELEGRAM_AVAILABLE:
            raise ImportError(
                "Telegram integration requires telethon. Install with: pip install telethon textblob"
            )

        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client = None

    async def __aenter__(self):
        """Async context manager entry"""
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.disconnect()

    async def connect(self):
        """Connect to Telegram"""
        if not self.client:
            self.client = TelegramClient(
                self.session_name,
                self.api_id,
                self.api_hash
            )
            await self.client.start()
            logger.info("Telegram client connected")

    async def disconnect(self):
        """Disconnect from Telegram"""
        if self.client:
            await self.client.disconnect()
            logger.info("Telegram client disconnected")

    async def get_channel_messages(
        self,
        channel_username: str,
        limit: int = 100,
        offset_date: Optional[datetime] = None
    ) -> List[TelegramChannelMessage]:
        """
        Get messages from a Telegram channel.

        Args:
            channel_username: Channel username (with or without @)
            limit: Max messages to retrieve
            offset_date: Get messages before this date

        Returns:
            List of TelegramChannelMessage objects
        """
        if not self.client:
            await self.connect()

        # Remove @ if present
        channel = channel_username.lstrip('@')

        logger.info(f"Fetching messages from @{channel}")

        try:
            entity = await self.client.get_entity(channel)
            messages = []

            async for message in self.client.iter_messages(
                entity,
                limit=limit,
                offset_date=offset_date
            ):
                if message.message:  # Skip empty messages
                    tg_message = self._parse_message(message, channel)
                    messages.append(tg_message)

            logger.info(f"Retrieved {len(messages)} messages from @{channel}")
            return messages

        except Exception as e:
            logger.error(f"Error fetching messages from @{channel}: {e}")
            return []

    async def search_messages(
        self,
        channels: List[str],
        keywords: List[str],
        limit: int = 100,
        hours: int = 24
    ) -> List[TelegramChannelMessage]:
        """
        Search for messages containing keywords across multiple channels.

        Args:
            channels: List of channel usernames
            keywords: Keywords to search for
            limit: Max messages per channel
            hours: Time period to search

        Returns:
            List of matching messages
        """
        logger.info(f"Searching Telegram: {keywords} in {len(channels)} channels")

        offset_date = datetime.now() - timedelta(hours=hours)
        all_messages = []

        for channel in channels:
            messages = await self.get_channel_messages(
                channel,
                limit=limit,
                offset_date=offset_date
            )

            # Filter by keywords
            for message in messages:
                text_lower = message.text.lower()
                if any(keyword.lower() in text_lower for keyword in keywords):
                    all_messages.append(message)

        logger.info(f"Found {len(all_messages)} matching messages")
        return all_messages

    def _parse_message(
        self,
        message: TelegramMessage,
        channel_username: str
    ) -> TelegramChannelMessage:
        """Parse Telegram message into TelegramChannelMessage object"""
        # Get author
        author = "Channel"
        if message.post_author:
            author = message.post_author
        elif message.from_id:
            author = str(message.from_id)

        tg_message = TelegramChannelMessage(
            message_id=message.id,
            channel_name=getattr(message.chat, 'title', channel_username),
            channel_username=channel_username,
            author=author,
            text=message.message,
            views=message.views or 0,
            forwards=message.forwards or 0,
            replies=getattr(message.replies, 'replies', 0) if message.replies else 0,
            posted_at=message.date
        )

        # Analyze sentiment
        tg_message.sentiment_score, tg_message.sentiment_label = self._analyze_sentiment(
            message.message
        )

        # Calculate engagement score
        tg_message.engagement_score = self._calculate_engagement_score(tg_message)

        return tg_message

    def _analyze_sentiment(self, text: str) -> tuple:
        """Analyze sentiment using TextBlob"""
        try:
            analysis = TextBlob(text)
            polarity = analysis.sentiment.polarity

            if polarity > 0.1:
                label = "positive"
            elif polarity < -0.1:
                label = "negative"
            else:
                label = "neutral"

            return polarity, label

        except Exception as e:
            logger.warning(f"Sentiment analysis failed: {e}")
            return 0.0, "neutral"

    def _calculate_engagement_score(self, message: TelegramChannelMessage) -> float:
        """Calculate engagement score for a message"""
        # Weighted combination of metrics
        score = (
            message.views * 1.0 +
            message.forwards * 10.0 +
            message.replies * 5.0
        )

        return max(score, 0)

    def generate_intelligence_report(
        self,
        query: str,
        messages: List[TelegramChannelMessage]
    ) -> Optional[TelegramIntelligence]:
        """
        Generate intelligence report from Telegram data.

        Args:
            query: Original search query
            messages: List of messages

        Returns:
            TelegramIntelligence report
        """
        if not messages:
            logger.warning("No messages to analyze")
            return None

        # Time range
        time_start = min(m.posted_at for m in messages)
        time_end = max(m.posted_at for m in messages)

        # Channels
        channels = list(set(m.channel_username for m in messages))

        # Sentiment analysis
        sentiment_scores = [m.sentiment_score for m in messages]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

        sentiment_dist = {
            "positive": sum(1 for m in messages if m.sentiment_label == "positive"),
            "neutral": sum(1 for m in messages if m.sentiment_label == "neutral"),
            "negative": sum(1 for m in messages if m.sentiment_label == "negative"),
        }

        # Top messages by engagement
        top_messages = sorted(
            messages,
            key=lambda m: m.engagement_score,
            reverse=True
        )[:10]

        # Viral messages (high views)
        viral = sorted(
            messages,
            key=lambda m: m.views,
            reverse=True
        )[:5]

        # Trending keywords
        keyword_freq = defaultdict(int)
        for message in messages:
            words = message.text.lower().split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    keyword_freq[word] += 1

        trending_keywords = sorted(
            keyword_freq.items(),
            key=lambda x: x[1],
            reverse=True
        )[:20]

        # Channel consensus
        consensus, strength = self._analyze_consensus(messages)

        # Create report
        report = TelegramIntelligence(
            query=query,
            channels_monitored=channels,
            time_period_start=time_start,
            time_period_end=time_end,
            total_messages=len(messages),
            avg_sentiment=avg_sentiment,
            sentiment_distribution=sentiment_dist,
            top_messages=top_messages,
            viral_messages=viral,
            trending_keywords=trending_keywords,
            channel_consensus=consensus,
            consensus_strength=strength
        )

        logger.info(
            f"Telegram report generated: {len(messages)} messages, "
            f"sentiment={avg_sentiment:.2f}, consensus={consensus}"
        )

        return report

    def _analyze_consensus(
        self,
        messages: List[TelegramChannelMessage]
    ) -> tuple:
        """
        Analyze channel consensus.

        Returns:
            Tuple of (consensus_label, strength)
        """
        # Calculate sentiment statistics
        sentiments = [m.sentiment_score for m in messages]
        avg_sentiment = sum(sentiments) / len(sentiments)

        # Calculate standard deviation (lower = stronger consensus)
        variance = sum((s - avg_sentiment) ** 2 for s in sentiments) / len(sentiments)
        std_dev = variance ** 0.5

        # Consensus strength (inverse of std dev, normalized)
        strength = max(0, 1 - (std_dev / 0.5))  # Assume max std_dev = 0.5

        # Consensus label
        if avg_sentiment > 0.15:
            consensus = "BULLISH"
        elif avg_sentiment < -0.15:
            consensus = "BEARISH"
        elif std_dev > 0.3:
            consensus = "DIVIDED"
        else:
            consensus = "NEUTRAL"

        return consensus, strength

    async def monitor_event(
        self,
        event_title: str,
        keywords: List[str],
        channels: Optional[List[str]] = None,
        hours: int = 24
    ) -> Optional[TelegramIntelligence]:
        """
        Monitor Telegram for a specific Polymarket event.

        Args:
            event_title: Event title
            keywords: Keywords to search
            channels: Channels to monitor (default: auto-select)
            hours: Time period to monitor

        Returns:
            TelegramIntelligence report
        """
        # Auto-select channels if not provided
        if not channels:
            channels = self._select_relevant_channels(event_title)

        logger.info(f"Monitoring Telegram for: {event_title}")
        logger.info(f"Channels: {channels}")
        logger.info(f"Keywords: {keywords}")

        # Search messages
        messages = await self.search_messages(
            channels,
            keywords,
            limit=100,
            hours=hours
        )

        if not messages:
            logger.warning(f"No Telegram messages found for: {event_title}")
            return None

        # Generate report
        query = " OR ".join(keywords)
        report = self.generate_intelligence_report(query, messages)

        return report

    def _select_relevant_channels(self, event_title: str) -> List[str]:
        """Auto-select relevant channels based on event title"""
        title_lower = event_title.lower()

        channels = []

        # Politics
        if any(word in title_lower for word in ["election", "president", "trump", "biden", "political"]):
            channels.extend(["breaking247", "politicalnews", "worldpoliticsnews"])

        # Crypto
        if any(word in title_lower for word in ["bitcoin", "crypto", "btc", "eth", "blockchain"]):
            channels.extend(["cryptonews", "bitcoin", "ethereum", "coindesk"])

        # Tech
        if any(word in title_lower for word in ["tech", "ai", "software", "apple", "google"]):
            channels.extend(["technews", "ainews", "techcrunch"])

        # Economy/Markets
        if any(word in title_lower for word in ["economy", "market", "stock", "inflation"]):
            channels.extend(["financialnews", "wallstreetbets", "markets"])

        # Default fallback
        if not channels:
            channels = ["breakingnews", "worldnews"]

        return list(set(channels))  # Remove duplicates

    def print_report(self, report: TelegramIntelligence):
        """Print Telegram intelligence report"""
        print("\n" + "="*80)
        print("TELEGRAM INTELLIGENCE REPORT")
        print("="*80)
        print(f"Query: {report.query}")
        print(f"Channels: {', '.join(f'@{c}' for c in report.channels_monitored)}")
        print(f"Period: {report.time_period_start} to {report.time_period_end}")
        print(f"Generated: {report.generated_at}")

        print("\n" + "-"*80)
        print("OVERVIEW")
        print("-"*80)
        print(f"Total Messages: {report.total_messages}")
        print(f"Avg Sentiment: {report.avg_sentiment:.3f} ", end="")

        if report.avg_sentiment > 0.1:
            print("(POSITIVE)")
        elif report.avg_sentiment < -0.1:
            print("(NEGATIVE)")
        else:
            print("(NEUTRAL)")

        print(f"\nSentiment Distribution:")
        for label, count in report.sentiment_distribution.items():
            pct = (count / report.total_messages) * 100
            print(f"  {label.capitalize()}: {count} ({pct:.1f}%)")

        print(f"\nChannel Consensus: {report.channel_consensus}")
        print(f"Consensus Strength: {report.consensus_strength:.2f}")

        print("\n" + "-"*80)
        print("TOP MESSAGES (by engagement)")
        print("-"*80)
        for i, msg in enumerate(report.top_messages[:5], 1):
            print(f"\n{i}. @{msg.channel_username} - {msg.posted_at}")
            print(f"   {msg.text[:100]}...")
            print(f"   Views: {msg.views:,} | Forwards: {msg.forwards} | "
                  f"Replies: {msg.replies} | Sentiment: {msg.sentiment_label}")

        print("\n" + "-"*80)
        print("VIRAL MESSAGES (most views)")
        print("-"*80)
        for i, msg in enumerate(report.viral_messages[:3], 1):
            print(f"\n{i}. {msg.text[:80]}...")
            print(f"   {msg.views:,} views | @{msg.channel_username}")

        print("\n" + "-"*80)
        print("TRENDING KEYWORDS")
        print("-"*80)
        for keyword, count in report.trending_keywords[:15]:
            print(f"  {keyword}: {count} mentions")

        print("\n" + "="*80)


# Convenience function
async def monitor_telegram_for_event(
    event_title: str,
    keywords: List[str],
    api_id: int,
    api_hash: str
) -> Optional[TelegramIntelligence]:
    """
    Quick function to monitor Telegram for an event.

    Args:
        event_title: Event title
        keywords: Keywords to search
        api_id: Telegram API ID
        api_hash: Telegram API hash

    Returns:
        TelegramIntelligence report
    """
    async with TelegramIntelligenceAnalyzer(api_id=api_id, api_hash=api_hash) as analyzer:
        return await analyzer.monitor_event(event_title, keywords)
