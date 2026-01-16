# Twitter Intelligence Integration Guide

## 概述

Twitter 监控模块为 Polymarket 套利系统提供实时社交媒体情报：
- 📊 **关键词追踪**：监控特定事件相关的推文
- 👤 **影响力账号**：追踪政客、分析师、新闻媒体
- 💭 **情感分析**：分析推文情绪（正面/负面/中性）
- 📈 **趋势检测**：识别活动激增和热门话题
- 🎯 **交易信号**：将 Twitter 情报转化为交易决策

---

## 🔑 获取 Twitter API 密钥

### 方法 1：Twitter API v2 Bearer Token（推荐）

1. 访问 https://developer.twitter.com/en/portal/dashboard
2. 创建一个新的 App（或使用现有的）
3. 进入 App 的 "Keys and Tokens" 页面
4. 生成 **Bearer Token**
5. 将 Token 添加到 `.env` 文件

### 方法 2：Twitter API v1.1（功能受限）

如果没有 API v2 访问权限，可以使用 v1.1：
1. 获取 API Key, API Secret, Access Token, Access Secret
2. 添加到 `.env` 文件

### API 访问层级

| 层级 | 费用 | 推文/月 | 推荐用途 |
|------|------|---------|----------|
| **Free** | $0 | 500 | 测试 |
| **Basic** | $100/月 | 10,000 | 小规模监控 |
| **Pro** | $5,000/月 | 1,000,000 | 专业交易 |

**推荐**：Basic 层级足够用于 Polymarket 监控

---

## 📦 安装依赖

```bash
# 激活 conda 环境
conda activate math

# 安装 Twitter 集成依赖
pip install tweepy textblob

# 下载 TextBlob 语料库（情感分析必需）
python -m textblob.download_corpora
```

---

## ⚙️ 配置

### 1. 编辑 `.env` 文件

```bash
# Twitter API v2（推荐）
TWITTER_BEARER_TOKEN=your_bearer_token_here

# 或者 Twitter API v1.1（备选）
TWITTER_API_KEY=your_api_key_here
TWITTER_API_SECRET=your_api_secret_here
TWITTER_ACCESS_TOKEN=your_access_token_here
TWITTER_ACCESS_SECRET=your_access_secret_here

# 监控配置
TWITTER_MONITOR_ENABLED=true
TWITTER_SCAN_INTERVAL=300  # 5 分钟
TWITTER_MAX_RESULTS=100

# 影响力账号（根据需要自定义）
TWITTER_INFLUENTIAL_POLITICS=realDonaldTrump,JoeBiden,nytimes,cnn,foxnews
TWITTER_INFLUENTIAL_CRYPTO=VitalikButerin,CZ_Binance,coinbase
TWITTER_INFLUENTIAL_TECH=elonmusk,sama,balajis
```

### 2. 测试配置

```python
from src.analyzer.twitter_intelligence import TwitterIntelligenceAnalyzer

# 测试连接
analyzer = TwitterIntelligenceAnalyzer(bearer_token="YOUR_TOKEN")
tweets = analyzer.search_tweets("test", max_results=10)
print(f"✓ Found {len(tweets)} tweets")
```

---

## 🚀 基本使用

### 示例 1：搜索关键词

```python
from src.analyzer.twitter_intelligence import TwitterIntelligenceAnalyzer

# 初始化
analyzer = TwitterIntelligenceAnalyzer(bearer_token=bearer_token)

# 搜索推文
tweets = analyzer.search_tweets(
    query="Trump 2024 election -is:retweet lang:en",
    max_results=100
)

# 生成情报报告
report = analyzer.generate_intelligence_report("Trump election", tweets)

# 打印报告
analyzer.print_report(report)
```

### 示例 2：监控 Polymarket 事件

```python
# 为特定事件收集情报
event_title = "Will Trump win the 2024 election?"
keywords = ["Trump", "election", "Biden"]
influential_accounts = ["realDonaldTrump", "JoeBiden", "nytimes"]

report = analyzer.monitor_event(
    event_title=event_title,
    keywords=keywords,
    influential_accounts=influential_accounts,
    max_results=100
)

if report:
    print(f"Twitter 情感: {report.avg_sentiment:.2f}")
    print(f"活动激增: {'是' if report.activity_spike else '否'}")
```

### 示例 3：结合套利检测

```python
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.api.polymarket_client import PolymarketClient

async with PolymarketClient() as client:
    detector = IntraMarketArbitrageDetector(client)
    opportunities = await detector.scan_all_markets()

    # 为最佳机会收集 Twitter 情报
    for opp in opportunities[:3]:
        keywords = extract_keywords(opp.event_title)

        twitter_report = analyzer.monitor_event(
            event_title=opp.event_title,
            keywords=keywords
        )

        # 根据 Twitter 情感调整置信度
        sentiment_boost = abs(twitter_report.avg_sentiment) * 0.2
        enhanced_confidence = opp.confidence_score + sentiment_boost

        print(f"原始置信度: {opp.confidence_score:.2f}")
        print(f"Twitter 增强: {enhanced_confidence:.2f}")
```

---

## 📊 数据结构

### Tweet 对象

```python
@dataclass
class Tweet:
    tweet_id: str                # 推文 ID
    author_username: str         # 作者用户名
    author_followers: int        # 粉丝数
    text: str                    # 推文内容
    created_at: datetime         # 发布时间
    like_count: int              # 点赞数
    retweet_count: int           # 转发数
    sentiment_score: float       # 情感分数 (-1 到 1)
    sentiment_label: str         # 情感标签 (positive/neutral/negative)
    engagement_score: float      # 互动分数
```

### TwitterIntelligence 报告

```python
@dataclass
class TwitterIntelligence:
    query: str                   # 搜索查询
    total_tweets: int            # 推文总数
    unique_authors: int          # 独特作者数
    total_impressions: int       # 总曝光量
    avg_sentiment: float         # 平均情感 (-1 到 1)
    sentiment_distribution: Dict # 情感分布
    top_tweets: List[Tweet]      # 高互动推文
    trending_keywords: List      # 热门关键词
    influential_voices: List     # 影响力账号
    activity_spike: bool         # 是否有活动激增
    spike_magnitude: float       # 激增倍数
```

---

## 🎯 交易信号解读

### 情感分数解读

| 分数范围 | 标签 | 交易信号 |
|---------|------|----------|
| > 0.2 | 强烈正面 | 看涨 📈 |
| 0.1 ~ 0.2 | 正面 | 轻微看涨 |
| -0.1 ~ 0.1 | 中性 | 无明确信号 ➖ |
| -0.2 ~ -0.1 | 负面 | 轻微看跌 |
| < -0.2 | 强烈负面 | 看跌 📉 |

### 活动激增检测

```python
if report.activity_spike:
    print(f"⚠️  活动激增: {report.spike_magnitude:.1f}x 正常水平")
    # 激增 > 2x = 重大事件发生
    # 激增 > 5x = 极度关注
```

### 影响力账号分析

```python
for voice in report.influential_voices:
    if voice['followers'] > 1_000_000:
        # 大V 的观点权重更高
        if voice['avg_sentiment'] > 0.3:
            print(f"大V @{voice['username']} 强烈看涨")
```

### 综合决策示例

```python
def evaluate_trading_signal(arbitrage_opp, twitter_report):
    """评估是否交易"""

    # 基础置信度
    confidence = arbitrage_opp.confidence_score

    # Twitter 情感加成
    if abs(twitter_report.avg_sentiment) > 0.2:
        confidence += 0.1

    # 活动激增加成
    if twitter_report.activity_spike and twitter_report.spike_magnitude > 3:
        confidence += 0.15

    # 影响力账号加成
    if any(v['followers'] > 1_000_000 for v in twitter_report.influential_voices):
        confidence += 0.05

    # 决策阈值
    if confidence > 0.7:
        return "STRONG BUY ✅"
    elif confidence > 0.5:
        return "MODERATE BUY ⚠️"
    else:
        return "SKIP ❌"
```

---

## 🔍 高级功能

### 1. 搜索查询语法

Twitter 支持强大的查询语法：

```python
# 布尔运算符
query = "Trump OR Biden"           # 或
query = "Trump Biden"              # 与（隐式）
query = "Trump -scandal"           # 排除

# 过滤器
query = "Trump -is:retweet"        # 排除转发
query = "Trump lang:en"            # 仅英文
query = "Trump has:images"         # 包含图片
query = "Trump min_faves:100"      # 至少100赞

# 组合使用
query = "(Trump OR Biden) election 2024 -is:retweet lang:en"
```

### 2. 监控特定账号

```python
# 监控特定账号的推文
accounts = ["realDonaldTrump", "JoeBiden"]
query = "from:realDonaldTrump OR from:JoeBiden"

tweets = analyzer.search_tweets(query, max_results=50)
```

### 3. 时间范围搜索

```python
from datetime import datetime, timedelta

# 最近24小时
start_time = datetime.utcnow() - timedelta(days=1)
tweets = analyzer.search_tweets(
    query="Bitcoin",
    start_time=start_time,
    max_results=100
)
```

### 4. 实时流监控（需要 Elevated Access）

```python
# 注意：需要 Twitter Elevated Access
# 实时监控推文流
stream = tweepy.StreamingClient(bearer_token)

def on_tweet(tweet):
    # 处理实时推文
    analyze_and_trade(tweet)

stream.add_rules(tweepy.StreamRule("Trump OR Biden"))
stream.filter()
```

---

## 💡 最佳实践

### 1. 关键词选择

```python
# ❌ 错误：关键词太宽泛
keywords = ["president", "election"]

# ✅ 正确：关键词具体且相关
keywords = ["Trump", "Biden", "2024 election", "swing states"]
```

### 2. 影响力账号策略

```python
# 按类别组织影响力账号
INFLUENTIAL_ACCOUNTS = {
    "politicians": ["realDonaldTrump", "JoeBiden"],
    "analysts": ["NateSilver538", "FiveThirtyEight"],
    "media": ["nytimes", "CNN", "FoxNews"],
    "crypto": ["VitalikButerin", "CZ_Binance"]
}
```

### 3. API 配额管理

```python
# 监控 API 使用情况
import time

def rate_limited_search(queries, delay=15):
    """批量搜索，避免超出配额"""
    results = []
    for query in queries:
        tweets = analyzer.search_tweets(query)
        results.append(tweets)
        time.sleep(delay)  # 15秒延迟
    return results
```

### 4. 数据存储

```python
# 保存历史数据用于趋势分析
import json

def save_report(report, filename):
    data = {
        'timestamp': report.generated_at.isoformat(),
        'query': report.query,
        'avg_sentiment': report.avg_sentiment,
        'total_tweets': report.total_tweets,
        'activity_spike': report.activity_spike
    }

    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
```

---

## 🐛 故障排除

### 问题 1：401 Unauthorized

```
tweepy.errors.Unauthorized: 401 Unauthorized
```

**解决：**
- 检查 Bearer Token 是否正确
- 确认 App 已启用适当的权限
- Token 可能已过期，重新生成

### 问题 2：429 Too Many Requests

```
tweepy.errors.TooManyRequests: 429 Too Many Requests
```

**解决：**
- 超出 API 配额限制
- 增加搜索间隔时间
- 升级到更高的 API 层级

### 问题 3：情感分析不准确

```python
# TextBlob 对短文本和俚语不太准确
# 可以尝试使用更好的模型

# 替代方案：使用 VADER（专为社交媒体设计）
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer

vader = SentimentIntensityAnalyzer()
sentiment = vader.polarity_scores(text)
```

### 问题 4：找不到推文

```
No tweets found
```

**解决：**
- 检查查询语法是否正确
- 扩大时间范围
- 关键词可能太具体
- 确认事件确实有人讨论

---

## 📈 性能优化

### 1. 批量处理

```python
# 批量分析多个事件
events = [
    ("Trump election", ["Trump", "Biden"]),
    ("Bitcoin $100k", ["Bitcoin", "BTC", "$100k"]),
    ("Russia Ukraine", ["Russia", "Ukraine", "war"])
]

for event_title, keywords in events:
    report = analyzer.monitor_event(event_title, keywords)
    # 处理报告...
    time.sleep(60)  # 避免配额限制
```

### 2. 缓存结果

```python
from functools import lru_cache

@lru_cache(maxsize=100)
def cached_search(query, timestamp):
    """缓存搜索结果（5分钟内重复查询使用缓存）"""
    return analyzer.search_tweets(query)

# 使用缓存
tweets = cached_search("Trump", datetime.now().replace(second=0, microsecond=0))
```

---

## 🎓 完整示例：自动化监控系统

```python
import asyncio
from datetime import datetime

async def automated_monitoring_loop():
    """自动化监控循环"""

    analyzer = TwitterIntelligenceAnalyzer(bearer_token=os.getenv('TWITTER_BEARER_TOKEN'))

    while True:
        print(f"\n[{datetime.now()}] Starting monitoring cycle...")

        # 1. 扫描套利机会
        async with PolymarketClient() as client:
            detector = IntraMarketArbitrageDetector(client)
            opportunities = await detector.scan_all_markets()

        # 2. 为每个机会收集 Twitter 情报
        for opp in opportunities:
            keywords = extract_keywords(opp.event_title)

            twitter_report = analyzer.monitor_event(
                opp.event_title,
                keywords,
                max_results=50
            )

            if twitter_report:
                # 3. 评估交易信号
                signal = evaluate_trading_signal(opp, twitter_report)

                if signal == "STRONG BUY":
                    # 4. 执行交易
                    print(f"✅ TRADING: {opp.event_title}")
                    # await execute_trade(opp)

        # 5. 等待下一个周期（5分钟）
        await asyncio.sleep(300)

# 运行
asyncio.run(automated_monitoring_loop())
```

---

## 📚 相关资源

- [Twitter API 文档](https://developer.twitter.com/en/docs)
- [Tweepy 文档](https://docs.tweepy.org/)
- [TextBlob 文档](https://textblob.readthedocs.io/)
- [主项目文档](../CLAUDE.md)
- [情报源汇总](INTELLIGENCE_SOURCES.md)

---

## 🤝 贡献

发现 bug 或有改进建议？欢迎提 Issue 或 PR！
