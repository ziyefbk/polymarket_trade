# Reddit 论坛监控快速指南

## 概述

Reddit 监控模块从 Reddit 论坛获取社区讨论和情感分析:
- 🔍 **多版块搜索**: 同时监控多个 subreddit
- 💬 **帖子和评论**: 分析帖子及其下的评论
- 🏆 **专家意见**: 识别高 karma 用户和高分评论
- 📊 **社区共识**: 分析整体情绪(看涨/看跌/分歧)
- 🔥 **病毒内容**: 识别高赞和热门讨论

**为什么 Reddit 重要?**
- ✅ 全球最大的社区讨论平台
- ✅ 深度讨论,不只是短消息
- ✅ 专业人士和专家聚集地
- ✅ 社区投票系统自然过滤低质内容

---

## 快速开始

### 1. 获取 Reddit API 凭证

访问 https://www.reddit.com/prefs/apps

1. 登录 Reddit 账号
2. 滚动到底部,点击 "Create App" 或 "Create Another App"
3. 填写信息:
   - **name**: Polymarket Intelligence
   - **App type**: 选择 "script"
   - **description**: Market intelligence monitoring
   - **about url**: (留空)
   - **redirect uri**: http://localhost:8080
4. 点击 "Create app"
5. 记录凭证:
   - **client_id**: 在 "personal use script" 下方的字符串
   - **client_secret**: "secret" 字段的值

### 2. 安装依赖

```bash
conda activate math
pip install praw textblob
python -m textblob.download_corpora
```

### 3. 配置环境变量

在 `.env` 文件中添加:

```bash
# Reddit API Credentials
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=PolymarketIntelligence/1.0
```

或者在 Windows CMD 中设置:

```cmd
set REDDIT_CLIENT_ID=your_client_id
set REDDIT_CLIENT_SECRET=your_client_secret
```

---

## 基本使用

### 1. 搜索帖子

```python
from src.analyzer.reddit_intelligence import RedditIntelligenceAnalyzer

analyzer = RedditIntelligenceAnalyzer(
    client_id="YOUR_CLIENT_ID",
    client_secret="YOUR_CLIENT_SECRET"
)

# 搜索 r/cryptocurrency
posts = analyzer.search_posts(
    query="bitcoin",
    subreddits=["cryptocurrency", "bitcoin"],
    time_filter="week",  # "hour", "day", "week", "month", "year", "all"
    limit=50
)

for post in posts[:5]:
    print(f"{post.title}")
    print(f"  r/{post.subreddit} | Score: {post.score:,}")
    print(f"  Sentiment: {post.sentiment_label}\n")
```

### 2. 获取帖子评论

```python
# 获取热门帖子
posts = analyzer.get_hot_posts(
    subreddits=["cryptocurrency"],
    limit=10
)

# 获取第一个帖子的评论
if posts:
    comments = analyzer.get_post_comments(posts[0], limit=100)

    print(f"Found {len(comments)} comments")

    for comment in comments[:5]:
        print(f"u/{comment.author}: {comment.text[:80]}...")
        print(f"  Score: {comment.score} | Sentiment: {comment.sentiment_label}\n")
```

### 3. 生成情报报告

```python
# 监控特定事件
report = analyzer.monitor_event(
    event_title="Bitcoin to $100k by 2024?",
    keywords=["bitcoin", "100k", "btc", "price target"],
    time_filter="week"
)

if report:
    analyzer.print_report(report)

    # 获取交易信号
    print(f"\n🎯 Trading Signal:")
    print(f"Consensus: {report.community_consensus}")
    print(f"Strength: {report.consensus_strength:.2f}")
```

---

## 报告示例

```
==============================================================================
REDDIT INTELLIGENCE REPORT
==============================================================================
Query: bitcoin OR btc OR 100k
Subreddits: r/cryptocurrency, r/bitcoin, r/ethtrader
Period: 2024-01-09 10:00:00 to 2024-01-16 10:00:00
Generated: 2024-01-16 10:15:30

------------------------------------------------------------------------------
OVERVIEW
------------------------------------------------------------------------------
Total Posts: 156
Total Comments: 4,823
Avg Sentiment: 0.284 (POSITIVE)

Sentiment Distribution:
  Positive: 98 (62.8%)
  Neutral: 42 (26.9%)
  Negative: 16 (10.3%)

Community Consensus: BULLISH
Consensus Strength: 0.72

------------------------------------------------------------------------------
TOP POSTS (by engagement)
------------------------------------------------------------------------------
1. r/cryptocurrency - Bitcoin breaks $45k - Is $100k next?
   Score: 8,954 | Comments: 1,234 | Awards: 45 | Sentiment: positive
   https://reddit.com/r/cryptocurrency/comments/abc123...

2. r/bitcoin - Major institutional adoption wave incoming
   Score: 6,782 | Comments: 892 | Awards: 32 | Sentiment: positive
   https://reddit.com/r/bitcoin/comments/def456...

------------------------------------------------------------------------------
VIRAL DISCUSSIONS (most comments)
------------------------------------------------------------------------------
1. Bitcoin breaks $45k - Is $100k next?
   1,234 comments | r/cryptocurrency

2. Realistic price targets for BTC in 2024
   987 comments | r/bitcoin

------------------------------------------------------------------------------
TRENDING KEYWORDS
------------------------------------------------------------------------------
  bitcoin: 156 mentions
  price: 132 mentions
  bullish: 89 mentions
  target: 78 mentions
  institutional: 67 mentions
```

---

## 核心功能

### 1. 自动版块选择

系统根据事件类型自动选择相关 subreddit:

```python
# 政治事件 → 政治版块
event = "2024 Presidential Election"
# 自动选择: r/politics, r/worldnews, r/news

# 加密货币事件 → 加密版块
event = "Bitcoin to $100k?"
# 自动选择: r/cryptocurrency, r/bitcoin, r/ethtrader

# 科技事件 → 科技版块
event = "Apple AI announcement"
# 自动选择: r/technology, r/tech, r/programming

# 经济事件 → 经济版块
event = "Federal Reserve rate decision"
# 自动选择: r/economics, r/stocks, r/investing
```

### 2. 情感分析

```python
for post in posts:
    print(f"Title: {post.title}")
    print(f"Sentiment: {post.sentiment_label} ({post.sentiment_score:.2f})")
    # sentiment_score: -1(极度消极) 到 +1(极度积极)
    # sentiment_label: "positive", "neutral", "negative"
```

### 3. 专家意见识别

```python
# 系统自动识别"专家"意见
# 标准:
# - karma >= 10,000 的用户
# - 评论分数 >= 100
# - 顶级评论(直接回复帖子)

if report.expert_opinions:
    print("Expert Opinions:")
    for expert in report.expert_opinions:
        print(f"  u/{expert.author}: {expert.text[:100]}...")
        print(f"  Score: {expert.score} | Sentiment: {expert.sentiment_label}")
```

### 4. 社区共识分析

```python
# 共识类型
if report.community_consensus == "BULLISH":
    # 社区整体看涨
    signal = "BUY"
    confidence = report.consensus_strength

elif report.community_consensus == "BEARISH":
    # 社区整体看跌
    signal = "SELL"
    confidence = report.consensus_strength

elif report.community_consensus == "DIVIDED":
    # 社区意见分歧严重
    signal = "WAIT"
    confidence = 0.5

else:  # NEUTRAL
    # 社区中立
    signal = "HOLD"
    confidence = report.consensus_strength

# 共识强度解释
if report.consensus_strength > 0.7:
    # 强共识 → 大多数人观点一致
    reliability = "HIGH"
elif report.consensus_strength > 0.4:
    # 中等共识
    reliability = "MEDIUM"
else:
    # 弱共识 → 意见分散
    reliability = "LOW"
```

---

## 交易信号解读

### 1. 讨论热度

```python
# 判断事件受关注程度
if report.total_posts > 50:
    # 高热度 → 市场关注度高
    attention = "HIGH"
elif report.total_posts > 20:
    attention = "MEDIUM"
else:
    attention = "LOW"

# 评论数量
if report.total_comments > 1000:
    # 深度讨论 → 社区高度参与
    engagement = "HIGH"
```

### 2. 情感极端化

```python
# 检查情感是否极端
if abs(report.avg_sentiment) > 0.3:
    # 极端情感(过度乐观或悲观)
    # 可能是市场转折点
    if report.avg_sentiment > 0.3:
        signal = "EXTREME_BULLISH"
        warning = "可能过热,注意回调"
    else:
        signal = "EXTREME_BEARISH"
        warning = "可能恐慌,注意反弹"
```

### 3. 专家vs散户

```python
# 对比专家意见和普通用户
expert_sentiment = sum(
    e.sentiment_score for e in report.expert_opinions
) / len(report.expert_opinions)

all_sentiment = report.avg_sentiment

if expert_sentiment > 0.2 and all_sentiment < 0:
    # 专家乐观但大众悲观 → 可能是买入机会
    signal = "CONTRARIAN_BUY"

elif expert_sentiment < -0.2 and all_sentiment > 0:
    # 专家悲观但大众乐观 → 可能是卖出机会
    signal = "CONTRARIAN_SELL"
```

### 4. 综合评分

```python
def calculate_reddit_signal(report):
    score = 0

    # 情感 (±25%)
    if report.avg_sentiment > 0.2:
        score += 0.25
    elif report.avg_sentiment < -0.2:
        score -= 0.25

    # 共识强度 (+15%)
    if report.consensus_strength > 0.7:
        score += 0.15

    # 讨论热度 (+10%)
    if report.total_posts > 50:
        score += 0.1

    # 评论深度 (+10%)
    if report.total_comments > 1000:
        score += 0.1

    return score  # -1 to 1
```

---

## 与套利系统集成

### 增强置信度

```python
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.analyzer.reddit_intelligence import RedditIntelligenceAnalyzer
from src.api.polymarket_client import PolymarketClient

async def enhanced_trading():
    # 1. 获取 Reddit 情报
    reddit = RedditIntelligenceAnalyzer(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET
    )

    reddit_report = reddit.monitor_event(
        event_title="Bitcoin to $100k?",
        keywords=["bitcoin", "100k", "btc"],
        time_filter="week"
    )

    # 2. 获取套利机会
    async with PolymarketClient() as client:
        detector = IntraMarketArbitrageDetector(client)
        opportunities = await detector.scan_all_markets()

    # 3. 用 Reddit 数据增强
    for opp in opportunities:
        reddit_boost = calculate_reddit_signal(reddit_report)

        enhanced_confidence = min(
            opp.confidence_score + reddit_boost * 0.15,
            1.0
        )

        if enhanced_confidence > 0.75:
            print(f"STRONG BUY: {opp.event_title}")
            # 执行交易
```

---

## 推荐 Subreddit 列表

### 加密货币

| Subreddit | 订阅数 | 活跃度 | 推荐度 |
|-----------|--------|--------|--------|
| r/cryptocurrency | 7.0M | 极高 | ⭐⭐⭐⭐⭐ |
| r/bitcoin | 5.2M | 高 | ⭐⭐⭐⭐⭐ |
| r/ethtrader | 1.8M | 高 | ⭐⭐⭐⭐ |
| r/cryptomarkets | 800K | 中 | ⭐⭐⭐ |

### 政治

| Subreddit | 订阅数 | 活跃度 | 推荐度 |
|-----------|--------|--------|--------|
| r/politics | 8.5M | 极高 | ⭐⭐⭐⭐⭐ |
| r/worldnews | 35M | 极高 | ⭐⭐⭐⭐⭐ |
| r/news | 28M | 极高 | ⭐⭐⭐⭐ |

### 科技

| Subreddit | 订阅数 | 活跃度 | 推荐度 |
|-----------|--------|--------|--------|
| r/technology | 14M | 极高 | ⭐⭐⭐⭐⭐ |
| r/tech | 1.2M | 高 | ⭐⭐⭐⭐ |
| r/programming | 6.5M | 高 | ⭐⭐⭐ |

### 经济/金融

| Subreddit | 订阅数 | 活跃度 | 推荐度 |
|-----------|--------|--------|--------|
| r/economics | 3.2M | 高 | ⭐⭐⭐⭐⭐ |
| r/stocks | 5.8M | 极高 | ⭐⭐⭐⭐ |
| r/investing | 2.5M | 高 | ⭐⭐⭐⭐ |

---

## 性能优化

### 1. 限制数量

```python
# ✅ 好的做法
posts = analyzer.search_posts(..., limit=50)

# ❌ 不好的做法
posts = analyzer.search_posts(..., limit=1000)  # 太慢
```

### 2. 选择合适的时间范围

```python
# 实时事件: "hour" 或 "day"
posts = analyzer.search_posts(..., time_filter="day")

# 趋势分析: "week"
posts = analyzer.search_posts(..., time_filter="week")

# 历史研究: "month" 或 "year"
posts = analyzer.search_posts(..., time_filter="month")
```

### 3. 批量处理

```python
# 并发搜索多个版块
from concurrent.futures import ThreadPoolExecutor

def search_subreddit(subreddit):
    return analyzer.search_posts(
        query="bitcoin",
        subreddits=[subreddit],
        limit=25
    )

with ThreadPoolExecutor(max_workers=3) as executor:
    results = list(executor.map(
        search_subreddit,
        ["cryptocurrency", "bitcoin", "ethtrader"]
    ))
```

---

## 故障排除

### 1. 凭证错误

```
invalid_grant error processing request
```

**解决**:
- 检查 client_id 和 client_secret 是否正确
- 确认应用类型是 "script"
- 重新创建应用

### 2. 速率限制

```
Too many requests
```

**解决**:
- Reddit API 限制: 60 请求/分钟
- 增加请求间隔 `time.sleep(1)`
- 使用 Reddit Premium 提高限制

### 3. Subreddit 不存在

```
Redirect to /subreddits/search
```

**解决**:
- 检查 subreddit 名称拼写
- 确认 subreddit 存在且公开
- 不要包含 "r/" 前缀

### 4. 帖子/评论为空

```
No posts/comments found
```

**解决**:
- 扩大时间范围
- 调整搜索关键词
- 增加 limit 数量
- 检查 subreddit 是否活跃

---

## 最佳实践

### 1. 关键词优化

```python
# ✅ 好的关键词(具体且相关)
keywords = ["bitcoin", "btc", "100k", "price target", "prediction"]

# ❌ 差的关键词(太泛泛)
keywords = ["crypto", "coin", "money"]
```

### 2. 版块选择

```python
# ✅ 选择相关且活跃的版块
subreddits = ["cryptocurrency", "bitcoin"]  # 明确相关

# ❌ 选择不相关的版块
subreddits = ["aww", "funny"]  # 不相关
```

### 3. 时间范围

```python
# 短期交易: "day"
report = analyzer.monitor_event(..., time_filter="day")

# 中期分析: "week"
report = analyzer.monitor_event(..., time_filter="week")

# 长期研究: "month"
report = analyzer.monitor_event(..., time_filter="month")
```

### 4. 评论深度

```python
# 快速扫描: 50 评论
comments = analyzer.get_post_comments(post, limit=50)

# 深度分析: 200 评论
comments = analyzer.get_post_comments(post, limit=200)
```

---

## 隐私和安全

1. **API 凭证安全**:
   - 不要提交 `.env` 到 Git
   - 不要在代码中硬编码凭证
   - 使用环境变量

2. **遵守 Reddit 规则**:
   - 不要爬取个人信息
   - 遵守速率限制
   - 只访问公开内容

3. **User Agent**:
   - 使用描述性的 user agent
   - 格式: `<platform>:<app ID>:<version> (by u/<Reddit username>)`

---

## 完整示例

```python
from src.analyzer.reddit_intelligence import RedditIntelligenceAnalyzer
import os

def main():
    # 初始化
    analyzer = RedditIntelligenceAnalyzer(
        client_id=os.getenv("REDDIT_CLIENT_ID"),
        client_secret=os.getenv("REDDIT_CLIENT_SECRET")
    )

    # 监控事件
    report = analyzer.monitor_event(
        event_title="Bitcoin to $100k by 2024?",
        keywords=["bitcoin", "100k", "btc", "price"],
        subreddits=["cryptocurrency", "bitcoin"],
        time_filter="week"
    )

    if report:
        # 打印报告
        analyzer.print_report(report)

        # 交易决策
        if report.community_consensus == "BULLISH" and \
           report.consensus_strength > 0.7:
            print("\n✅ STRONG BUY SIGNAL")
            print(f"   → {report.total_posts} posts analyzed")
            print(f"   → {report.total_comments:,} comments reviewed")
            print(f"   → Community {report.consensus_strength:.0%} confident")
        elif report.community_consensus == "BEARISH" and \
             report.consensus_strength > 0.7:
            print("\n⚠️  STRONG SELL SIGNAL")
        else:
            print("\n➖ NEUTRAL - Mixed community signals")

if __name__ == "__main__":
    main()
```

---

## 相关资源

- [PRAW 文档](https://praw.readthedocs.io/)
- [Reddit API 文档](https://www.reddit.com/dev/api/)
- [获取 API 凭证](https://www.reddit.com/prefs/apps)
- [主项目文档](../CLAUDE.md)

---

**下一步**: 运行测试

```bash
conda activate math
python test_reddit_setup.py
```

如果测试通过,运行示例:

```bash
python examples\reddit_integration_example.py
```
