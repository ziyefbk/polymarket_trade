"""
Reddit Intelligence Analyzer for Polymarket Trading

This module monitors Reddit for market-relevant discussions and sentiment:
- Tracks relevant subreddits (r/politics, r/cryptocurrency, r/worldnews, etc.)
- Performs sentiment analysis on posts and comments
- Detects trending topics and viral discussions
- Identifies influential users and expert opinions
- Analyzes community consensus and disagreements
"""
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from collections import defaultdict
from loguru import logger

try:
    import praw
    from textblob import TextBlob
    REDDIT_AVAILABLE = True
except ImportError:
    REDDIT_AVAILABLE = False
    logger.warning("Reddit integration not available. Install: pip install praw textblob")


@dataclass
class RedditPost:
    """Represents a Reddit post"""
    post_id: str
    subreddit: str
    title: str
    author: str
    text: str
    score: int  # Upvotes - Downvotes
    upvote_ratio: float  # 0-1
    num_comments: int
    created_at: datetime
    url: str
    awards: int
    is_stickied: bool
    sentiment_score: float = 0.0
    sentiment_label: str = "neutral"
    engagement_score: float = 0.0


@dataclass
class RedditComment:
    """Represents a Reddit comment"""
    comment_id: str
    post_id: str
    author: str
    text: str
    score: int
    created_at: datetime
    is_top_level: bool
    sentiment_score: float = 0.0
    sentiment_label: str = "neutral"


@dataclass
class RedditIntelligence:
    """Intelligence report from Reddit monitoring"""
    query: str
    subreddits_monitored: List[str]
    time_period_start: datetime
    time_period_end: datetime
    total_posts: int
    total_comments: int
    avg_sentiment: float
    sentiment_distribution: Dict[str, int]
    top_posts: List[RedditPost]
    viral_discussions: List[RedditPost]  # High engagement
    expert_opinions: List[RedditComment]  # From high-karma users
    trending_keywords: List[tuple]
    community_consensus: str  # "BULLISH", "BEARISH", "DIVIDED"
    consensus_strength: float  # 0-1
    generated_at: datetime = field(default_factory=datetime.now)


class RedditIntelligenceAnalyzer:
    """
    Monitors Reddit for intelligence related to Polymarket events.

    Features:
    - Multi-subreddit monitoring
    - Sentiment analysis on posts and comments
    - Viral content detection
    - Expert opinion identification
    - Community consensus analysis
    """

    def __init__(
        self,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Initialize Reddit analyzer.

        Args:
            client_id: Reddit API client ID
            client_secret: Reddit API client secret
            user_agent: User agent string
        """
        if not REDDIT_AVAILABLE:
            raise ImportError(
                "Reddit integration requires praw. Install with: pip install praw textblob"
            )

        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent=user_agent or "PolymarketIntelligence/1.0"
        )

        # Verify connection
        try:
            # Test by accessing a subreddit
            self.reddit.subreddit("test").id
            logger.info("Reddit API connected successfully")
        except Exception as e:
            logger.error(f"Failed to connect to Reddit API: {e}")

        # High-karma threshold for "expert" users
        self.expert_karma_threshold = 10000

    def search_posts(
        self,
        query: str,
        subreddits: List[str],
        time_filter: str = "week",
        limit: int = 100
    ) -> List[RedditPost]:
        """
        Search for posts matching query across multiple subreddits.

        Args:
            query: Search query
            subreddits: List of subreddit names (without r/)
            time_filter: "hour", "day", "week", "month", "year", "all"
            limit: Max posts to retrieve per subreddit

        Returns:
            List of RedditPost objects
        """
        logger.info(f"Searching Reddit: '{query}' in {len(subreddits)} subreddits")

        all_posts = []

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                # Search within subreddit
                posts = subreddit.search(
                    query,
                    time_filter=time_filter,
                    limit=limit
                )

                for post in posts:
                    reddit_post = self._parse_post(post)
                    all_posts.append(reddit_post)

            except Exception as e:
                logger.error(f"Error searching r/{subreddit_name}: {e}")
                continue

        logger.info(f"Retrieved {len(all_posts)} posts from Reddit")
        return all_posts

    def get_hot_posts(
        self,
        subreddits: List[str],
        limit: int = 50
    ) -> List[RedditPost]:
        """
        Get currently hot posts from subreddits.

        Args:
            subreddits: List of subreddit names
            limit: Max posts per subreddit

        Returns:
            List of RedditPost objects
        """
        logger.info(f"Getting hot posts from {len(subreddits)} subreddits")

        all_posts = []

        for subreddit_name in subreddits:
            try:
                subreddit = self.reddit.subreddit(subreddit_name)

                for post in subreddit.hot(limit=limit):
                    reddit_post = self._parse_post(post)
                    all_posts.append(reddit_post)

            except Exception as e:
                logger.error(f"Error getting hot posts from r/{subreddit_name}: {e}")
                continue

        logger.info(f"Retrieved {len(all_posts)} hot posts")
        return all_posts

    def get_post_comments(
        self,
        post: RedditPost,
        limit: int = 100
    ) -> List[RedditComment]:
        """
        Get comments from a post.

        Args:
            post: RedditPost object
            limit: Max comments to retrieve

        Returns:
            List of RedditComment objects
        """
        try:
            submission = self.reddit.submission(id=post.post_id)
            submission.comments.replace_more(limit=0)  # Remove "load more" comments

            comments = []

            for comment in submission.comments.list()[:limit]:
                if isinstance(comment, praw.models.Comment):
                    reddit_comment = self._parse_comment(comment, post.post_id)
                    comments.append(reddit_comment)

            return comments

        except Exception as e:
            logger.error(f"Error getting comments for post {post.post_id}: {e}")
            return []

    def _parse_post(self, post: praw.models.Submission) -> RedditPost:
        """Parse PRAW post into RedditPost object"""
        reddit_post = RedditPost(
            post_id=post.id,
            subreddit=post.subreddit.display_name,
            title=post.title,
            author=str(post.author) if post.author else "[deleted]",
            text=post.selftext,
            score=post.score,
            upvote_ratio=post.upvote_ratio,
            num_comments=post.num_comments,
            created_at=datetime.fromtimestamp(post.created_utc),
            url=f"https://reddit.com{post.permalink}",
            awards=post.total_awards_received,
            is_stickied=post.stickied
        )

        # Analyze sentiment
        text_to_analyze = f"{post.title} {post.selftext}"
        reddit_post.sentiment_score, reddit_post.sentiment_label = self._analyze_sentiment(text_to_analyze)

        # Calculate engagement score
        reddit_post.engagement_score = self._calculate_engagement_score(reddit_post)

        return reddit_post

    def _parse_comment(self, comment: praw.models.Comment, post_id: str) -> RedditComment:
        """Parse PRAW comment into RedditComment object"""
        reddit_comment = RedditComment(
            comment_id=comment.id,
            post_id=post_id,
            author=str(comment.author) if comment.author else "[deleted]",
            text=comment.body,
            score=comment.score,
            created_at=datetime.fromtimestamp(comment.created_utc),
            is_top_level=(comment.parent_id.startswith("t3_"))  # t3_ = submission
        )

        # Analyze sentiment
        reddit_comment.sentiment_score, reddit_comment.sentiment_label = self._analyze_sentiment(comment.body)

        return reddit_comment

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

    def _calculate_engagement_score(self, post: RedditPost) -> float:
        """Calculate engagement score for a post"""
        # Weighted combination of metrics
        score = (
            post.score * 1.0 +
            post.num_comments * 2.0 +
            post.awards * 5.0 +
            (post.upvote_ratio - 0.5) * 100  # Controversial posts get penalty
        )

        return max(score, 0)

    def generate_intelligence_report(
        self,
        query: str,
        posts: List[RedditPost],
        comments: Optional[List[RedditComment]] = None
    ) -> RedditIntelligence:
        """
        Generate intelligence report from Reddit data.

        Args:
            query: Original search query
            posts: List of posts
            comments: Optional list of comments

        Returns:
            RedditIntelligence report
        """
        if not posts:
            logger.warning("No posts to analyze")
            return None

        # Time range
        time_start = min(p.created_at for p in posts)
        time_end = max(p.created_at for p in posts)

        # Subreddits
        subreddits = list(set(p.subreddit for p in posts))

        # Sentiment analysis
        sentiment_scores = [p.sentiment_score for p in posts]
        avg_sentiment = sum(sentiment_scores) / len(sentiment_scores)

        sentiment_dist = {
            "positive": sum(1 for p in posts if p.sentiment_label == "positive"),
            "neutral": sum(1 for p in posts if p.sentiment_label == "neutral"),
            "negative": sum(1 for p in posts if p.sentiment_label == "negative"),
        }

        # Top posts by engagement
        top_posts = sorted(posts, key=lambda p: p.engagement_score, reverse=True)[:10]

        # Viral discussions (high comment count)
        viral = sorted(posts, key=lambda p: p.num_comments, reverse=True)[:5]

        # Trending keywords
        keyword_freq = defaultdict(int)
        for post in posts:
            words = (post.title + " " + post.text).lower().split()
            for word in words:
                if len(word) > 4:  # Skip short words
                    keyword_freq[word] += 1

        trending_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:20]

        # Expert opinions (from high-karma users or highly-upvoted comments)
        expert_opinions = []
        if comments:
            expert_opinions = [
                c for c in comments
                if c.score >= 100 or c.is_top_level
            ][:10]

        # Community consensus
        consensus, strength = self._analyze_consensus(posts, comments or [])

        # Create report
        report = RedditIntelligence(
            query=query,
            subreddits_monitored=subreddits,
            time_period_start=time_start,
            time_period_end=time_end,
            total_posts=len(posts),
            total_comments=sum(p.num_comments for p in posts),
            avg_sentiment=avg_sentiment,
            sentiment_distribution=sentiment_dist,
            top_posts=top_posts,
            viral_discussions=viral,
            expert_opinions=expert_opinions,
            trending_keywords=trending_keywords,
            community_consensus=consensus,
            consensus_strength=strength
        )

        logger.info(
            f"Reddit report generated: {len(posts)} posts, "
            f"sentiment={avg_sentiment:.2f}, consensus={consensus}"
        )

        return report

    def _analyze_consensus(
        self,
        posts: List[RedditPost],
        comments: List[RedditComment]
    ) -> tuple:
        """
        Analyze community consensus.

        Returns:
            Tuple of (consensus_label, strength)
        """
        # Weighted sentiment (posts + comments)
        all_sentiments = [p.sentiment_score for p in posts]
        if comments:
            all_sentiments.extend([c.sentiment_score for c in comments])

        avg_sentiment = sum(all_sentiments) / len(all_sentiments)

        # Calculate standard deviation (lower = stronger consensus)
        variance = sum((s - avg_sentiment) ** 2 for s in all_sentiments) / len(all_sentiments)
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

    def monitor_event(
        self,
        event_title: str,
        keywords: List[str],
        subreddits: Optional[List[str]] = None,
        time_filter: str = "week"
    ) -> Optional[RedditIntelligence]:
        """
        Monitor Reddit for a specific Polymarket event.

        Args:
            event_title: Event title
            keywords: Keywords to search
            subreddits: Subreddits to monitor (default: auto-select)
            time_filter: Time range

        Returns:
            RedditIntelligence report
        """
        # Auto-select subreddits if not provided
        if not subreddits:
            subreddits = self._select_relevant_subreddits(event_title)

        # Build search query
        query = " OR ".join(keywords)

        logger.info(f"Monitoring Reddit for: {event_title}")
        logger.info(f"Subreddits: {subreddits}")
        logger.info(f"Keywords: {keywords}")

        # Search posts
        posts = self.search_posts(query, subreddits, time_filter=time_filter, limit=50)

        if not posts:
            logger.warning(f"No Reddit posts found for: {event_title}")
            return None

        # Get comments for top posts
        comments = []
        for post in posts[:5]:  # Top 5 posts
            post_comments = self.get_post_comments(post, limit=50)
            comments.extend(post_comments)
            time.sleep(1)  # Rate limiting

        # Generate report
        report = self.generate_intelligence_report(query, posts, comments)

        return report

    def _select_relevant_subreddits(self, event_title: str) -> List[str]:
        """Auto-select relevant subreddits based on event title"""
        title_lower = event_title.lower()

        subreddits = []

        # Politics
        if any(word in title_lower for word in ["election", "president", "trump", "biden", "political"]):
            subreddits.extend(["politics", "worldnews", "news"])

        # Crypto
        if any(word in title_lower for word in ["bitcoin", "crypto", "btc", "eth", "blockchain"]):
            subreddits.extend(["cryptocurrency", "bitcoin", "ethtrader"])

        # Tech
        if any(word in title_lower for word in ["tech", "ai", "software", "apple", "google"]):
            subreddits.extend(["technology", "tech", "programming"])

        # Economy
        if any(word in title_lower for word in ["economy", "market", "stock", "inflation"]):
            subreddits.extend(["economics", "stocks", "investing"])

        # Default fallback
        if not subreddits:
            subreddits = ["worldnews", "news"]

        return list(set(subreddits))  # Remove duplicates

    def print_report(self, report: RedditIntelligence):
        """Print Reddit intelligence report"""
        print("\n" + "="*80)
        print("REDDIT INTELLIGENCE REPORT")
        print("="*80)
        print(f"Query: {report.query}")
        print(f"Subreddits: {', '.join(f'r/{s}' for s in report.subreddits_monitored)}")
        print(f"Period: {report.time_period_start} to {report.time_period_end}")
        print(f"Generated: {report.generated_at}")

        print("\n" + "-"*80)
        print("OVERVIEW")
        print("-"*80)
        print(f"Total Posts: {report.total_posts}")
        print(f"Total Comments: {report.total_comments}")
        print(f"Avg Sentiment: {report.avg_sentiment:.3f} ", end="")

        if report.avg_sentiment > 0.1:
            print("(POSITIVE)")
        elif report.avg_sentiment < -0.1:
            print("(NEGATIVE)")
        else:
            print("(NEUTRAL)")

        print(f"\nSentiment Distribution:")
        for label, count in report.sentiment_distribution.items():
            pct = (count / report.total_posts) * 100
            print(f"  {label.capitalize()}: {count} ({pct:.1f}%)")

        print(f"\nCommunity Consensus: {report.community_consensus}")
        print(f"Consensus Strength: {report.consensus_strength:.2f}")

        print("\n" + "-"*80)
        print("TOP POSTS (by engagement)")
        print("-"*80)
        for i, post in enumerate(report.top_posts[:5], 1):
            print(f"\n{i}. r/{post.subreddit} - {post.title[:80]}")
            print(f"   Score: {post.score} | Comments: {post.num_comments} | "
                  f"Awards: {post.awards} | Sentiment: {post.sentiment_label}")
            print(f"   {post.url}")

        print("\n" + "-"*80)
        print("VIRAL DISCUSSIONS (most comments)")
        print("-"*80)
        for i, post in enumerate(report.viral_discussions[:3], 1):
            print(f"\n{i}. {post.title[:80]}")
            print(f"   {post.num_comments} comments | r/{post.subreddit}")

        print("\n" + "-"*80)
        print("TRENDING KEYWORDS")
        print("-"*80)
        for keyword, count in report.trending_keywords[:15]:
            print(f"  {keyword}: {count} mentions")

        print("\n" + "="*80)


# Convenience function
def monitor_reddit_for_event(
    event_title: str,
    keywords: List[str],
    client_id: str,
    client_secret: str
) -> Optional[RedditIntelligence]:
    """
    Quick function to monitor Reddit for an event.

    Args:
        event_title: Event title
        keywords: Keywords to search
        client_id: Reddit API client ID
        client_secret: Reddit API client secret

    Returns:
        RedditIntelligence report
    """
    analyzer = RedditIntelligenceAnalyzer(
        client_id=client_id,
        client_secret=client_secret
    )
    return analyzer.monitor_event(event_title, keywords)
