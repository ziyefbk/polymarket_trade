"""
Twitter Intelligence Analyzer for Polymarket Trading

This module monitors Twitter for market-relevant intelligence:
- Tracks keywords related to Polymarket events
- Monitors influential accounts (politicians, analysts, journalists)
- Performs sentiment analysis on tweets
- Detects trending topics and sudden spikes in activity
- Correlates Twitter activity with market movements
"""
import asyncio
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger

try:
    import tweepy
    from textblob import TextBlob
    TWITTER_AVAILABLE = True
except ImportError:
    TWITTER_AVAILABLE = False
    logger.warning("Twitter integration not available. Install: pip install tweepy textblob")


@dataclass
class Tweet:
    """Represents a single tweet"""
    tweet_id: str
    author_username: str
    author_name: str
    author_followers: int
    text: str
    created_at: datetime
    retweet_count: int
    like_count: int
    reply_count: int
    quote_count: int
    url: str
    sentiment_score: float = 0.0
    sentiment_label: str = "neutral"
    engagement_score: float = 0.0
    keywords_matched: List[str] = field(default_factory=list)

    def calculate_engagement_score(self):
        """Calculate engagement score weighted by follower count"""
        # Engagement = (likes + retweets*2 + replies*1.5 + quotes*3) / followers^0.5
        total_engagement = (
            self.like_count +
            self.retweet_count * 2 +
            self.reply_count * 1.5 +
            self.quote_count * 3
        )

        # Normalize by follower count (square root to prevent huge accounts dominating)
        follower_factor = max(self.author_followers, 1) ** 0.5
        self.engagement_score = total_engagement / follower_factor
        return self.engagement_score


@dataclass
class TwitterIntelligence:
    """Intelligence report from Twitter monitoring"""
    query: str
    time_period_start: datetime
    time_period_end: datetime
    total_tweets: int
    unique_authors: int
    total_impressions: int
    avg_sentiment: float
    sentiment_distribution: Dict[str, int]
    top_tweets: List[Tweet]
    trending_keywords: List[tuple]
    influential_voices: List[Dict[str, Any]]
    activity_spike: bool
    spike_magnitude: float
    generated_at: datetime = field(default_factory=datetime.now)


class TwitterIntelligenceAnalyzer:
    """
    Monitors Twitter for intelligence related to Polymarket events.

    Features:
    - Keyword-based search
    - Influential account monitoring
    - Real-time stream monitoring (if using API v2)
    - Sentiment analysis
    - Trend detection
    - Engagement scoring
    """

    def __init__(
        self,
        bearer_token: Optional[str] = None,
        api_key: Optional[str] = None,
        api_secret: Optional[str] = None,
        access_token: Optional[str] = None,
        access_secret: Optional[str] = None
    ):
        """
        Initialize Twitter analyzer.

        Args:
            bearer_token: Twitter API v2 Bearer Token (recommended)
            api_key: Twitter API Key (v1.1)
            api_secret: Twitter API Secret (v1.1)
            access_token: Access Token (v1.1)
            access_secret: Access Secret (v1.1)
        """
        if not TWITTER_AVAILABLE:
            raise ImportError(
                "Twitter integration requires additional packages. "
                "Install with: pip install tweepy textblob"
            )

        self.bearer_token = bearer_token
        self.client = None

        # Initialize API v2 client (preferred)
        if bearer_token:
            self.client = tweepy.Client(
                bearer_token=bearer_token,
                wait_on_rate_limit=True
            )
            logger.info("Twitter API v2 client initialized")

        # Fallback to API v1.1 (limited functionality)
        elif all([api_key, api_secret, access_token, access_secret]):
            auth = tweepy.OAuth1UserHandler(api_key, api_secret, access_token, access_secret)
            self.api = tweepy.API(auth, wait_on_rate_limit=True)
            logger.info("Twitter API v1.1 initialized (limited features)")
        else:
            raise ValueError(
                "Either bearer_token (API v2) or all API v1.1 credentials required"
            )

    def search_tweets(
        self,
        query: str,
        max_results: int = 100,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Tweet]:
        """
        Search for tweets matching query.

        Args:
            query: Search query (supports Twitter operators like 'Trump OR Biden')
            max_results: Max tweets to retrieve (10-100 per request, max 500 total)
            start_time: Start of time range (default: 7 days ago)
            end_time: End of time range (default: now)

        Returns:
            List of Tweet objects
        """
        if not self.client:
            raise RuntimeError("API v2 required for search. Use bearer_token.")

        # Default time range: last 7 days
        if not start_time:
            start_time = datetime.utcnow() - timedelta(days=7)
        if not end_time:
            end_time = datetime.utcnow()

        logger.info(f"Searching Twitter: '{query}' (max {max_results} tweets)")

        tweets = []

        try:
            # Search with pagination
            for response in tweepy.Paginator(
                self.client.search_recent_tweets,
                query=query,
                tweet_fields=['created_at', 'public_metrics', 'author_id'],
                user_fields=['username', 'name', 'public_metrics'],
                expansions=['author_id'],
                start_time=start_time,
                end_time=end_time,
                max_results=min(max_results, 100)
            ).flatten(limit=max_results):

                # Get author info from includes
                author = self._get_author_from_includes(response, response.author_id)

                tweet = self._parse_tweet(response, author, query)
                tweets.append(tweet)

            logger.info(f"Retrieved {len(tweets)} tweets")
            return tweets

        except tweepy.TweepyException as e:
            logger.error(f"Twitter API error: {e}")
            return []

    def _get_author_from_includes(self, response, author_id):
        """Extract author info from API response includes"""
        # This is a simplified version - in real implementation,
        # you'd need to handle the includes properly from the response
        return {
            'username': 'unknown',
            'name': 'Unknown User',
            'followers_count': 0
        }

    def _parse_tweet(self, tweet_data: Any, author: Dict, query: str) -> Tweet:
        """Parse Twitter API response into Tweet object"""
        # Extract metrics
        metrics = getattr(tweet_data, 'public_metrics', {})

        tweet = Tweet(
            tweet_id=tweet_data.id,
            author_username=author.get('username', 'unknown'),
            author_name=author.get('name', 'Unknown'),
            author_followers=author.get('public_metrics', {}).get('followers_count', 0),
            text=tweet_data.text,
            created_at=tweet_data.created_at,
            retweet_count=metrics.get('retweet_count', 0),
            like_count=metrics.get('like_count', 0),
            reply_count=metrics.get('reply_count', 0),
            quote_count=metrics.get('quote_count', 0),
            url=f"https://twitter.com/{author.get('username', 'i')}/status/{tweet_data.id}",
        )

        # Analyze sentiment
        tweet.sentiment_score, tweet.sentiment_label = self._analyze_sentiment(tweet.text)

        # Calculate engagement
        tweet.calculate_engagement_score()

        # Extract matched keywords
        tweet.keywords_matched = self._extract_keywords(tweet.text, query)

        return tweet

    def _analyze_sentiment(self, text: str) -> tuple[float, str]:
        """
        Analyze sentiment of text using TextBlob.

        Returns:
            Tuple of (sentiment_score, sentiment_label)
            sentiment_score: -1 (negative) to 1 (positive)
            sentiment_label: "positive", "neutral", or "negative"
        """
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

    def _extract_keywords(self, text: str, query: str) -> List[str]:
        """Extract which keywords from query appear in text"""
        keywords = []
        text_lower = text.lower()

        # Parse query for keywords (simple version)
        query_terms = query.lower().replace('(', '').replace(')', '').split()

        for term in query_terms:
            if term not in ['or', 'and', 'not', '-'] and term in text_lower:
                keywords.append(term)

        return keywords

    def generate_intelligence_report(
        self,
        query: str,
        tweets: List[Tweet],
        baseline_volume: Optional[int] = None
    ) -> TwitterIntelligence:
        """
        Generate intelligence report from collected tweets.

        Args:
            query: The search query used
            tweets: List of tweets to analyze
            baseline_volume: Historical average volume for spike detection

        Returns:
            TwitterIntelligence report
        """
        if not tweets:
            logger.warning("No tweets to analyze")
            return None

        # Time range
        time_start = min(t.created_at for t in tweets)
        time_end = max(t.created_at for t in tweets)

        # Basic stats
        total_tweets = len(tweets)
        unique_authors = len(set(t.author_username for t in tweets))
        total_impressions = sum(t.author_followers for t in tweets)

        # Sentiment analysis
        sentiment_scores = [t.sentiment_score for t in tweets]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

        sentiment_dist = {
            "positive": sum(1 for t in tweets if t.sentiment_label == "positive"),
            "neutral": sum(1 for t in tweets if t.sentiment_label == "neutral"),
            "negative": sum(1 for t in tweets if t.sentiment_label == "negative"),
        }

        # Top tweets by engagement
        top_tweets = sorted(tweets, key=lambda t: t.engagement_score, reverse=True)[:10]

        # Trending keywords
        keyword_freq = defaultdict(int)
        for tweet in tweets:
            for keyword in tweet.keywords_matched:
                keyword_freq[keyword] += 1

        trending_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:10]

        # Influential voices
        author_stats = defaultdict(lambda: {
            'tweets': 0,
            'total_engagement': 0,
            'avg_sentiment': 0,
            'followers': 0,
            'name': ''
        })

        for tweet in tweets:
            stats = author_stats[tweet.author_username]
            stats['tweets'] += 1
            stats['total_engagement'] += tweet.engagement_score
            stats['avg_sentiment'] += tweet.sentiment_score
            stats['followers'] = tweet.author_followers
            stats['name'] = tweet.author_name

        influential_voices = []
        for username, stats in author_stats.items():
            if stats['tweets'] >= 2:  # At least 2 tweets
                influential_voices.append({
                    'username': username,
                    'name': stats['name'],
                    'followers': stats['followers'],
                    'tweets': stats['tweets'],
                    'avg_engagement': stats['total_engagement'] / stats['tweets'],
                    'avg_sentiment': stats['avg_sentiment'] / stats['tweets'],
                })

        influential_voices = sorted(
            influential_voices,
            key=lambda x: x['avg_engagement'],
            reverse=True
        )[:10]

        # Activity spike detection
        activity_spike = False
        spike_magnitude = 1.0

        if baseline_volume:
            spike_magnitude = total_tweets / baseline_volume
            activity_spike = spike_magnitude > 2.0  # 2x increase = spike

        # Create report
        report = TwitterIntelligence(
            query=query,
            time_period_start=time_start,
            time_period_end=time_end,
            total_tweets=total_tweets,
            unique_authors=unique_authors,
            total_impressions=total_impressions,
            avg_sentiment=avg_sentiment,
            sentiment_distribution=sentiment_dist,
            top_tweets=top_tweets,
            trending_keywords=trending_keywords,
            influential_voices=influential_voices,
            activity_spike=activity_spike,
            spike_magnitude=spike_magnitude,
        )

        logger.info(
            f"Generated intelligence report: {total_tweets} tweets, "
            f"sentiment={avg_sentiment:.2f}, spike={activity_spike}"
        )

        return report

    def monitor_event(
        self,
        event_title: str,
        keywords: List[str],
        influential_accounts: Optional[List[str]] = None,
        max_results: int = 100
    ) -> Optional[TwitterIntelligence]:
        """
        Monitor Twitter for a specific Polymarket event.

        Args:
            event_title: Polymarket event title
            keywords: Keywords to track
            influential_accounts: Specific accounts to monitor (optional)
            max_results: Max tweets to retrieve

        Returns:
            TwitterIntelligence report
        """
        # Build search query
        keyword_query = " OR ".join(keywords)

        if influential_accounts:
            account_query = " OR ".join(f"from:{acc}" for acc in influential_accounts)
            query = f"({keyword_query}) OR ({account_query})"
        else:
            query = keyword_query

        # Add filters for quality
        query += " -is:retweet lang:en"  # Exclude retweets, English only

        logger.info(f"Monitoring event: {event_title}")
        logger.info(f"Query: {query}")

        # Search tweets
        tweets = self.search_tweets(query, max_results=max_results)

        if not tweets:
            logger.warning(f"No tweets found for event: {event_title}")
            return None

        # Generate report
        report = self.generate_intelligence_report(query, tweets)

        return report

    def print_report(self, report: TwitterIntelligence):
        """Print intelligence report in readable format"""
        print("\n" + "="*80)
        print(f"TWITTER INTELLIGENCE REPORT")
        print("="*80)
        print(f"Query: {report.query}")
        print(f"Period: {report.time_period_start} to {report.time_period_end}")
        print(f"Generated: {report.generated_at}")
        print("\n" + "-"*80)
        print("OVERVIEW")
        print("-"*80)
        print(f"Total Tweets: {report.total_tweets}")
        print(f"Unique Authors: {report.unique_authors}")
        print(f"Total Impressions: {report.total_impressions:,}")
        print(f"Average Sentiment: {report.avg_sentiment:.3f} ", end="")

        if report.avg_sentiment > 0.1:
            print("(POSITIVE)")
        elif report.avg_sentiment < -0.1:
            print("(NEGATIVE)")
        else:
            print("(NEUTRAL)")

        print("\nSentiment Distribution:")
        for label, count in report.sentiment_distribution.items():
            pct = (count / report.total_tweets) * 100
            print(f"  {label.capitalize()}: {count} ({pct:.1f}%)")

        if report.activity_spike:
            print(f"\n⚠️  ACTIVITY SPIKE DETECTED: {report.spike_magnitude:.1f}x baseline")

        print("\n" + "-"*80)
        print("TOP TWEETS (by engagement)")
        print("-"*80)
        for i, tweet in enumerate(report.top_tweets[:5], 1):
            print(f"\n{i}. @{tweet.author_username} ({tweet.author_followers:,} followers)")
            print(f"   {tweet.text[:150]}...")
            print(f"   💚 {tweet.like_count} | 🔁 {tweet.retweet_count} | "
                  f"💬 {tweet.reply_count} | Sentiment: {tweet.sentiment_label}")
            print(f"   {tweet.url}")

        print("\n" + "-"*80)
        print("TRENDING KEYWORDS")
        print("-"*80)
        for keyword, count in report.trending_keywords[:10]:
            print(f"  {keyword}: {count} mentions")

        print("\n" + "-"*80)
        print("INFLUENTIAL VOICES")
        print("-"*80)
        for voice in report.influential_voices[:5]:
            print(f"\n@{voice['username']} - {voice['name']}")
            print(f"  Followers: {voice['followers']:,}")
            print(f"  Tweets: {voice['tweets']}")
            print(f"  Avg Engagement Score: {voice['avg_engagement']:.2f}")
            print(f"  Avg Sentiment: {voice['avg_sentiment']:.3f}")

        print("\n" + "="*80)


# Convenience function
def monitor_twitter_for_event(
    event_title: str,
    keywords: List[str],
    bearer_token: str,
    influential_accounts: Optional[List[str]] = None
) -> Optional[TwitterIntelligence]:
    """
    Quick function to monitor Twitter for an event.

    Args:
        event_title: Event title
        keywords: Keywords to track
        bearer_token: Twitter Bearer Token
        influential_accounts: Accounts to monitor (optional)

    Returns:
        TwitterIntelligence report
    """
    analyzer = TwitterIntelligenceAnalyzer(bearer_token=bearer_token)
    return analyzer.monitor_event(event_title, keywords, influential_accounts)
