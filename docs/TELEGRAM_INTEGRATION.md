# Telegram 频道监控快速指南

## 概述

Telegram 监控模块从 Telegram 频道和群组获取实时市场讨论和情报:
- 📱 **频道监控**: 追踪加密货币、政治、新闻频道
- 💬 **消息分析**: 实时情感分析和关键词检测
- 🔥 **病毒内容**: 识别高浏览量和转发的热门消息
- 📊 **社区共识**: 分析频道整体情绪(看涨/看跌/分歧)
- ⚡ **实时监控**: 持续追踪新消息

**为什么 Telegram 重要?**
- ✅ 加密货币社区的主要聚集地
- ✅ 消息实时性强,传播快
- ✅ 很多内幕消息首先在 Telegram 出现
- ✅ 可以追踪意见领袖和影响力账号

---

## 快速开始

### 1. 获取 Telegram API 凭证

访问 https://my.telegram.org/apps

1. 登录你的 Telegram 账号
2. 点击 "API development tools"
3. 填写应用信息:
   - App title: Polymarket Intelligence
   - Short name: polymarket_bot
   - Platform: Desktop
4. 获得 **api_id** 和 **api_hash**

### 2. 安装依赖

```bash
conda activate math
pip install telethon textblob
python -m textblob.download_corpora
```

### 3. 配置环境变量

在 `.env` 文件中添加:

```bash
# Telegram API Credentials
TELEGRAM_API_ID=12345678
TELEGRAM_API_HASH=your_api_hash_here

# Optional: Session name
TELEGRAM_SESSION_NAME=polymarket_monitor
```

或者在 Windows CMD 中设置:

```cmd
set TELEGRAM_API_ID=12345678
set TELEGRAM_API_HASH=your_api_hash_here
```

### 4. 首次使用

第一次运行需要手机验证:

```python
import asyncio
from src.analyzer.telegram_intelligence import TelegramIntelligenceAnalyzer

async def first_run():
    async with TelegramIntelligenceAnalyzer(
        api_id=12345678,
        api_hash="your_api_hash"
    ) as analyzer:
        print("Connected to Telegram!")

asyncio.run(first_run())
```

**验证流程**:
1. 程序会要求输入手机号(带国家代码,如 +1234567890)
2. Telegram 会发送验证码到你的手机
3. 输入验证码
4. 如果启用了两步验证,输入密码
5. 完成后会保存 session,下次不需要验证

---

## 基本使用

### 1. 监控单个频道

```python
from src.analyzer.telegram_intelligence import TelegramIntelligenceAnalyzer
import asyncio

async def monitor_channel():
    async with TelegramIntelligenceAnalyzer(
        api_id=YOUR_API_ID,
        api_hash="YOUR_API_HASH"
    ) as analyzer:
        # 获取最近100条消息
        messages = await analyzer.get_channel_messages(
            channel_username="cryptonews",
            limit=100
        )

        for msg in messages[:5]:
            print(f"{msg.posted_at}: {msg.text[:100]}")
            print(f"  Views: {msg.views:,}, Sentiment: {msg.sentiment_label}\n")

asyncio.run(monitor_channel())
```

### 2. 搜索多个频道

```python
async def search_channels():
    async with TelegramIntelligenceAnalyzer(
        api_id=YOUR_API_ID,
        api_hash="YOUR_API_HASH"
    ) as analyzer:
        # 搜索包含关键词的消息
        messages = await analyzer.search_messages(
            channels=["cryptonews", "bitcoin", "ethereum"],
            keywords=["bitcoin", "btc", "surge", "pump"],
            limit=50,
            hours=24  # 最近24小时
        )

        print(f"Found {len(messages)} matching messages")

asyncio.run(search_channels())
```

### 3. 生成情报报告

```python
async def generate_report():
    async with TelegramIntelligenceAnalyzer(
        api_id=YOUR_API_ID,
        api_hash="YOUR_API_HASH"
    ) as analyzer:
        # 监控特定事件
        report = await analyzer.monitor_event(
            event_title="Bitcoin to $100k by 2024?",
            keywords=["bitcoin", "100k", "btc", "price"],
            hours=48
        )

        if report:
            analyzer.print_report(report)

            # 获取交易信号
            print(f"\n🎯 Trading Signal:")
            print(f"Consensus: {report.channel_consensus}")
            print(f"Strength: {report.consensus_strength:.2f}")

asyncio.run(generate_report())
```

---

## 报告示例

```
==============================================================================
TELEGRAM INTELLIGENCE REPORT
==============================================================================
Query: bitcoin OR btc OR 100k OR price
Channels: @cryptonews, @bitcoin, @ethereum
Period: 2024-01-14 10:00:00 to 2024-01-16 10:00:00
Generated: 2024-01-16 10:15:30

------------------------------------------------------------------------------
OVERVIEW
------------------------------------------------------------------------------
Total Messages: 234
Avg Sentiment: 0.342 (POSITIVE)

Sentiment Distribution:
  Positive: 156 (66.7%)
  Neutral: 54 (23.1%)
  Negative: 24 (10.3%)

Channel Consensus: BULLISH
Consensus Strength: 0.78

------------------------------------------------------------------------------
TOP MESSAGES (by engagement)
------------------------------------------------------------------------------
1. @bitcoin - 2024-01-16 08:30:12
   Bitcoin breaks through $45k resistance! Next stop $50k? 🚀
   Views: 245,891 | Forwards: 1,234 | Replies: 567 | Sentiment: positive

2. @cryptonews - 2024-01-16 07:15:45
   Major institutional buyer accumulating BTC, on-chain data shows...
   Views: 187,432 | Forwards: 891 | Replies: 345 | Sentiment: positive

------------------------------------------------------------------------------
VIRAL MESSAGES (most views)
------------------------------------------------------------------------------
1. Bitcoin breaks through $45k resistance! Next stop $50k? 🚀
   245,891 views | @bitcoin

2. Major institutional buyer accumulating BTC, on-chain data shows...
   187,432 views | @cryptonews

------------------------------------------------------------------------------
TRENDING KEYWORDS
------------------------------------------------------------------------------
  bitcoin: 234 mentions
  price: 189 mentions
  surge: 123 mentions
  bullish: 98 mentions
  target: 87 mentions
```

---

## 核心功能

### 1. 频道自动选择

系统会根据事件类型自动选择相关频道:

```python
# 政治事件 → 政治频道
event = "2024 Presidential Election"
# 自动选择: breaking247, politicalnews, worldpoliticsnews

# 加密货币事件 → 加密频道
event = "Bitcoin to $100k?"
# 自动选择: cryptonews, bitcoin, ethereum, coindesk

# 科技事件 → 科技频道
event = "Apple AI announcement"
# 自动选择: technews, ainews, techcrunch
```

### 2. 情感分析

```python
# 自动分析每条消息的情感
for msg in messages:
    print(f"Text: {msg.text}")
    print(f"Sentiment: {msg.sentiment_label} ({msg.sentiment_score:.2f})")
    # sentiment_score: -1(极度消极) 到 +1(极度积极)
    # sentiment_label: "positive", "neutral", "negative"
```

### 3. 社区共识分析

```python
report = await analyzer.monitor_event(...)

# 共识类型
if report.channel_consensus == "BULLISH":
    # 社区整体看涨
    signal = "BUY"
elif report.channel_consensus == "BEARISH":
    # 社区整体看跌
    signal = "SELL"
elif report.channel_consensus == "DIVIDED":
    # 社区意见分歧严重
    signal = "WAIT"
else:  # NEUTRAL
    # 社区中立
    signal = "HOLD"

# 共识强度 (0-1)
if report.consensus_strength > 0.7:
    # 强共识 → 可信度高
    confidence = "HIGH"
elif report.consensus_strength > 0.4:
    # 中等共识
    confidence = "MEDIUM"
else:
    # 弱共识 → 可信度低
    confidence = "LOW"
```

---

## 交易信号解读

### 1. 消息量激增

```python
# 正常: 50-100 条/天
# 激增: 200+ 条/天
if report.total_messages > 200:
    # 说明事件引起广泛关注
    # 市场波动可能加大
    signal = "HIGH_VOLATILITY"
```

### 2. 情感极端化

```python
if abs(report.avg_sentiment) > 0.3:
    # 情感极端(非常积极或非常消极)
    # 可能是市场转折点
    if report.avg_sentiment > 0.3:
        signal = "EXTREME_BULLISH"
    else:
        signal = "EXTREME_BEARISH"
```

### 3. 病毒传播

```python
# 检查是否有病毒传播的消息
for msg in report.viral_messages:
    if msg.views > 100000:
        # 超过10万浏览 → 影响力巨大
        print(f"Viral message: {msg.text[:100]}")
        print(f"Impact: HIGH - {msg.views:,} views")
```

### 4. 综合评分

```python
def calculate_telegram_signal(report):
    score = 0

    # 情感 (±30%)
    if report.avg_sentiment > 0.2:
        score += 0.3
    elif report.avg_sentiment < -0.2:
        score -= 0.3

    # 共识强度 (+20%)
    if report.consensus_strength > 0.7:
        score += 0.2

    # 消息量 (+10%)
    if report.total_messages > 150:
        score += 0.1

    # 病毒传播 (+15%)
    max_views = max(msg.views for msg in report.viral_messages)
    if max_views > 100000:
        score += 0.15

    return score  # -1 to 1
```

---

## 与套利系统集成

### 增强置信度

```python
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.analyzer.telegram_intelligence import TelegramIntelligenceAnalyzer

async def enhanced_trading():
    # 1. 获取 Telegram 情报
    async with TelegramIntelligenceAnalyzer(
        api_id=API_ID,
        api_hash=API_HASH
    ) as tg:
        tg_report = await tg.monitor_event(
            event_title="Bitcoin to $100k?",
            keywords=["bitcoin", "100k", "btc"],
            hours=24
        )

    # 2. 获取套利机会
    async with PolymarketClient() as client:
        detector = IntraMarketArbitrageDetector(client)
        opportunities = await detector.scan_all_markets()

    # 3. 用 Telegram 数据增强
    for opp in opportunities:
        telegram_boost = calculate_telegram_signal(tg_report)

        enhanced_confidence = min(
            opp.confidence_score + telegram_boost * 0.2,
            1.0
        )

        if enhanced_confidence > 0.75:
            print(f"STRONG BUY: {opp.event_title}")
            # 执行交易
```

---

## 推荐频道列表

### 加密货币

| 频道 | 用户名 | 类型 | 推荐度 |
|------|--------|------|--------|
| Crypto News | @cryptonews | 新闻 | ⭐⭐⭐⭐⭐ |
| Bitcoin | @bitcoin | 社区 | ⭐⭐⭐⭐⭐ |
| Ethereum | @ethereum | 社区 | ⭐⭐⭐⭐ |
| CoinDesk | @coindesk | 媒体 | ⭐⭐⭐⭐ |
| Binance | @binance | 交易所 | ⭐⭐⭐ |

### 政治

| 频道 | 用户名 | 类型 | 推荐度 |
|------|--------|------|--------|
| Breaking News | @breaking247 | 新闻 | ⭐⭐⭐⭐⭐ |
| Political News | @politicalnews | 政治 | ⭐⭐⭐⭐ |
| World Politics | @worldpoliticsnews | 国际 | ⭐⭐⭐⭐ |

### 科技

| 频道 | 用户名 | 类型 | 推荐度 |
|------|--------|------|--------|
| Tech News | @technews | 新闻 | ⭐⭐⭐⭐ |
| AI News | @ainews | AI | ⭐⭐⭐⭐ |
| TechCrunch | @techcrunch | 媒体 | ⭐⭐⭐ |

---

## 性能优化

### 1. Session 缓存

```python
# Session 文件会保存登录状态
# 默认: polymarket_monitor.session
# 自定义:
analyzer = TelegramIntelligenceAnalyzer(
    api_id=API_ID,
    api_hash=API_HASH,
    session_name="my_custom_session"
)
```

### 2. 批量查询

```python
# 并发查询多个频道
async def batch_query():
    async with TelegramIntelligenceAnalyzer(...) as analyzer:
        tasks = [
            analyzer.get_channel_messages(channel, limit=50)
            for channel in ["cryptonews", "bitcoin", "ethereum"]
        ]
        results = await asyncio.gather(*tasks)
```

### 3. 限制消息数量

```python
# 不要一次获取太多消息
# ✅ 好: limit=100
# ❌ 差: limit=10000

messages = await analyzer.get_channel_messages(
    "cryptonews",
    limit=100  # 足够分析,不会太慢
)
```

---

## 故障排除

### 1. 首次登录验证失败

```
Phone code invalid
```

**解决**:
- 确保手机号格式正确(+国家代码)
- 检查验证码是否正确
- 验证码有时效性,超时需重新获取

### 2. Session 过期

```
Unauthorized: The user is not authorized
```

**解决**:
- 删除 session 文件重新登录
- 检查账号是否被限制

### 3. 频道访问失败

```
Cannot find entity
```

**解决**:
- 确认频道用户名正确
- 确认频道是公开的
- 尝试先在 Telegram 客户端加入该频道

### 4. 速率限制

```
FloodWait: Too many requests
```

**解决**:
- 增加请求间隔
- 减少批量查询数量
- 等待限制解除(通常几分钟到几小时)

---

## 最佳实践

### 1. 选择高质量频道

```python
# 优先监控:
# - 官方频道(验证标记)
# - 大型社区(>10万订阅)
# - 活跃频道(每天10+条消息)
# - 相关性高的频道
```

### 2. 合理设置时间范围

```python
# 实时事件: 1-6 小时
report = await analyzer.monitor_event(..., hours=6)

# 趋势分析: 24-48 小时
report = await analyzer.monitor_event(..., hours=24)

# 长期研究: 7 天
report = await analyzer.monitor_event(..., hours=168)
```

### 3. 关键词优化

```python
# ✅ 好的关键词
keywords = ["bitcoin", "btc", "surge", "pump", "dump"]

# ❌ 差的关键词(太泛泛)
keywords = ["crypto", "news", "today"]
```

### 4. 定期监控

```python
# 每小时检查一次
while True:
    report = await analyzer.monitor_event(...)

    if report.channel_consensus != previous_consensus:
        # 共识变化 → 发送告警
        send_alert(report)

    await asyncio.sleep(3600)  # 1小时
```

---

## 隐私和安全

1. **API 凭证安全**:
   - 不要提交 `.env` 到 Git
   - 不要在代码中硬编码凭证
   - 使用环境变量

2. **Session 文件**:
   - `.session` 文件包含登录信息
   - 添加到 `.gitignore`
   - 不要分享给他人

3. **遵守 Telegram 规则**:
   - 不要发送垃圾消息
   - 不要频繁请求(遵守速率限制)
   - 只监控公开频道

---

## 完整示例

```python
import asyncio
import os
from src.analyzer.telegram_intelligence import TelegramIntelligenceAnalyzer

async def main():
    # 从环境变量获取凭证
    api_id = int(os.getenv("TELEGRAM_API_ID"))
    api_hash = os.getenv("TELEGRAM_API_HASH")

    async with TelegramIntelligenceAnalyzer(
        api_id=api_id,
        api_hash=api_hash
    ) as analyzer:
        # 监控事件
        report = await analyzer.monitor_event(
            event_title="Bitcoin to $100k by 2024?",
            keywords=["bitcoin", "100k", "btc", "price"],
            channels=["cryptonews", "bitcoin"],
            hours=24
        )

        if report:
            # 打印报告
            analyzer.print_report(report)

            # 交易决策
            if report.channel_consensus == "BULLISH" and \
               report.consensus_strength > 0.7:
                print("\n✅ STRONG BUY SIGNAL")
                print("   → High community confidence")
                print(f"   → {report.total_messages} messages analyzed")
            elif report.channel_consensus == "BEARISH" and \
                 report.consensus_strength > 0.7:
                print("\n⚠️  STRONG SELL SIGNAL")
            else:
                print("\n➖ NEUTRAL - Wait for clearer signal")

asyncio.run(main())
```

---

## 相关资源

- [Telegram API 文档](https://core.telegram.org/api)
- [Telethon 文档](https://docs.telethon.dev/)
- [获取 API 凭证](https://my.telegram.org/apps)
- [主项目文档](../CLAUDE.md)

---

**下一步**: 运行测试

```bash
conda activate math
python test_telegram_setup.py
```

如果测试通过,运行示例:

```bash
python examples\telegram_integration_example.py
```
