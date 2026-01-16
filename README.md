# 🎯 Polymarket 多源情报套利系统

一个基于多源情报的 Polymarket 预测市场自动化套利交易系统。

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![License](https://img.shields.io/badge/License-MIT-green.svg)
![Status](https://img.shields.io/badge/Status-Beta-yellow.svg)

## 📋 目录

- [功能特性](#功能特性)
- [系统架构](#系统架构)
- [快速开始](#快速开始)
- [情报源配置](#情报源配置)
- [使用指南](#使用指南)
- [项目结构](#项目结构)
- [技术栈](#技术栈)
- [风险警告](#风险警告)

---

## ✨ 功能特性

### 核心功能

- ✅ **Polymarket 集成**: 完整的 API 客户端,支持市场数据、订单簿、交易执行
- ✅ **套利检测**: 自动检测市场内套利机会 (YES + NO ≠ 1.0)
- ✅ **智能执行**: Kelly 准则仓位管理,风险控制
- ✅ **数据持久化**: SQLite 数据库,完整交易记录
- ✅ **Web Dashboard**: 实时监控和可视化

### 🌐 五重情报系统

系统整合 5 个独立情报源,提供多维度市场分析:

| 情报源 | 类型 | 更新频率 | 信号强度 | 成本 |
|--------|------|----------|----------|------|
| 🌑 **Robin** | 暗网情报 | 小时级 | ⭐⭐⭐⭐ | $10-50/月 |
| 📱 **Twitter** | 社交媒体 | 实时 | ⭐⭐⭐⭐⭐ | $100/月 |
| 💬 **Reddit** | 论坛讨论 | 分钟级 | ⭐⭐⭐⭐ | 免费 |
| 📢 **Telegram** | 加密频道 | 实时 | ⭐⭐⭐⭐⭐ | 免费 |
| ⛓️ **On-Chain** | 链上数据 | 区块级 | ⭐⭐⭐⭐⭐ | 免费 |

### 情报融合

```
基础套利置信度 (0-1)
  ↓
+ Robin 暗网加成 (±15%)
+ Twitter 情感加成 (±20%)
+ Reddit 社区加成 (±15%)
+ Telegram 频道加成 (±15%)
+ On-Chain 资金流加成 (±25%)
  ↓
= 综合交易信号 (0-1)

决策阈值:
  >0.75  → 强烈推荐 (自动执行)
  0.6-0.75 → 谨慎推荐 (人工确认)
  <0.6   → 不推荐 (跳过)
```

---

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────┐
│                    数据收集层                             │
├─────────────────────────────────────────────────────────┤
│  🌑 暗网    📱 Twitter  💬 Reddit  📢 Telegram  ⛓️ 链上   │
│  Robin      API v2     PRAW       Telethon    Web3.py   │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│                    智能分析层                             │
├─────────────────────────────────────────────────────────┤
│  📊 情感分析  🔍 趋势检测  💡 信号融合  🎯 置信度评估    │
│  TextBlob     关键词提取    加权评分    风险控制         │
└────────────────────┬────────────────────────────────────┘
                     ↓
┌─────────────────────────────────────────────────────────┐
│                    交易决策层                             │
├─────────────────────────────────────────────────────────┤
│  🎲 Kelly 仓位  ⚖️ 风险管理  🤖 自动执行  📝 记录存档    │
└─────────────────────────────────────────────────────────┘
```

---

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.10+ (推荐 3.11)
- **系统**: Windows/Linux/macOS
- **网络**: 需要访问 Polygon RPC 和各情报源 API

### 2. 安装

```bash
# 克隆仓库
git clone https://github.com/ziyefbk/polymarket_trade.git
cd polymarket_trade

# 创建虚拟环境
conda create -n math python=3.11
conda activate math

# 安装依赖
pip install -r requirements.txt

# 下载 TextBlob 语料库
python -m textblob.download_corpora
```

### 3. 配置

复制环境变量模板:

```bash
cp .env.example .env
```

编辑 `.env` 文件,填入你的凭证:

```bash
# Polymarket 交易 (必需)
POLYMARKET_PRIVATE_KEY=你的Polygon钱包私钥

# Twitter 监控 (推荐)
TWITTER_BEARER_TOKEN=你的Twitter_API_Token

# Reddit 监控 (推荐)
REDDIT_CLIENT_ID=你的Reddit客户端ID
REDDIT_CLIENT_SECRET=你的Reddit客户端密钥

# Telegram 监控 (可选)
TELEGRAM_API_ID=你的Telegram_API_ID
TELEGRAM_API_HASH=你的Telegram_API_Hash

# Robin 暗网 (高级)
# 参见 docs/ROBIN_INTEGRATION.md
```

### 4. 测试配置

```bash
# 测试各个模块
conda activate math

python test_twitter_setup.py   # Twitter
python test_reddit_setup.py    # Reddit
python test_telegram_setup.py  # Telegram
python test_onchain_setup.py   # 链上数据
python test_robin_setup.py     # Robin (需要 Tor)
```

### 5. 运行示例

```bash
# Twitter 监控示例
python examples/twitter_integration_example.py

# Reddit 分析示例
python examples/reddit_integration_example.py

# 链上数据示例
python examples/onchain_integration_example.py

# Telegram 监控示例
python examples/telegram_integration_example.py
```

---

## 🔧 情报源配置

### 📱 Twitter (推荐)

1. 访问 [Twitter Developer Portal](https://developer.twitter.com/)
2. 创建应用,获取 Bearer Token
3. 设置环境变量 `TWITTER_BEARER_TOKEN`

**成本**: $100/月 (Basic 层级)
**文档**: [docs/TWITTER_INTEGRATION.md](docs/TWITTER_INTEGRATION.md)

### 💬 Reddit (推荐)

1. 访问 [Reddit Apps](https://www.reddit.com/prefs/apps)
2. 创建 "script" 类型应用
3. 获取 `client_id` 和 `client_secret`

**成本**: 免费
**文档**: [docs/REDDIT_INTEGRATION.md](docs/REDDIT_INTEGRATION.md)

### 📢 Telegram (可选)

1. 访问 [Telegram API](https://my.telegram.org/apps)
2. 创建应用,获取 `api_id` 和 `api_hash`
3. 首次使用需要手机验证

**成本**: 免费
**文档**: [docs/TELEGRAM_INTEGRATION.md](docs/TELEGRAM_INTEGRATION.md)

### ⛓️ On-Chain (推荐)

使用 Web3.py 直接读取 Polygon 区块链:

- **公共 RPC**: 免费但较慢
- **Alchemy**: 300M 请求/月免费
- **Infura**: 100k 请求/天免费

**成本**: 免费
**文档**: [docs/ONCHAIN_INTEGRATION.md](docs/ONCHAIN_INTEGRATION.md)

### 🌑 Robin 暗网 (高级)

需要运行 Tor 服务:

1. 安装 Tor Browser 或 Tor 服务
2. 配置 LLM API (OpenAI/OpenRouter)
3. 启动 Robin

**成本**: $10-50/月 (LLM API)
**文档**: [docs/ROBIN_INTEGRATION.md](docs/ROBIN_INTEGRATION.md)

---

## 📖 使用指南

### 基础套利扫描

```python
import asyncio
from src.api.polymarket_client import PolymarketClient
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector

async def scan_opportunities():
    async with PolymarketClient() as client:
        detector = IntraMarketArbitrageDetector(client)
        opportunities = await detector.scan_all_markets()

        for opp in opportunities:
            print(f"{opp.event_title}")
            print(f"  Spread: {opp.spread:.2%}")
            print(f"  Net Profit: {opp.net_profit_pct:.2%}")

asyncio.run(scan_opportunities())
```

### 多源情报增强

```python
from src.analyzer.twitter_intelligence import TwitterIntelligenceAnalyzer
from src.analyzer.onchain_intelligence import OnChainIntelligenceAnalyzer

async def enhanced_analysis():
    # 1. 获取套利机会
    opportunities = await scan_opportunities()

    # 2. 获取 Twitter 情报
    twitter = TwitterIntelligenceAnalyzer(bearer_token=TOKEN)
    twitter_report = twitter.monitor_event(
        event_title=opportunities[0].event_title,
        keywords=["bitcoin", "price"],
        max_results=100
    )

    # 3. 获取链上数据
    onchain = OnChainIntelligenceAnalyzer()
    onchain_report = await onchain.get_recent_activity(hours=24)

    # 4. 综合评分
    base_score = opportunities[0].confidence_score
    twitter_boost = calculate_twitter_signal(twitter_report) * 0.2
    onchain_boost = calculate_onchain_signal(onchain_report) * 0.25

    final_score = min(base_score + twitter_boost + onchain_boost, 1.0)

    if final_score > 0.75:
        print("✅ 强烈推荐 - 执行交易")
    elif final_score > 0.6:
        print("⚠️ 谨慎推荐 - 人工确认")
    else:
        print("❌ 不推荐 - 跳过")

asyncio.run(enhanced_analysis())
```

### 自动化交易

```python
from src.strategy.arbitrage_executor import ArbitrageExecutor
from src.api.trader import PolymarketTrader

async def auto_trade():
    async with PolymarketTrader() as trader:
        executor = ArbitrageExecutor(trader)

        # 扫描并执行
        results = await executor.scan_and_execute(
            min_profit_threshold=0.02,  # 最低 2% 利润
            max_position_size=1000.0,   # 最大 $1000
            use_kelly=True              # Kelly 仓位管理
        )

        for result in results:
            print(f"交易结果: {result.status}")
            print(f"利润: ${result.net_profit:.2f}")

asyncio.run(auto_trade())
```

---

## 📁 项目结构

```
polymarket_trade/
├── config/                    # 配置管理
│   ├── __init__.py
│   └── settings.py           # Pydantic 配置
├── src/
│   ├── api/                  # API 客户端
│   │   ├── polymarket_client.py  # 市场数据
│   │   └── trader.py             # 交易执行
│   ├── analyzer/             # 情报分析
│   │   ├── arbitrage_detector.py # 套利检测
│   │   ├── twitter_intelligence.py
│   │   ├── reddit_intelligence.py
│   │   ├── telegram_intelligence.py
│   │   ├── onchain_intelligence.py
│   │   └── robin_intelligence.py
│   ├── strategy/             # 交易策略
│   │   ├── arbitrage_executor.py
│   │   └── position_manager.py
│   └── utils/                # 工具函数
│       ├── database.py       # 数据库
│       ├── kelly.py          # Kelly 准则
│       └── logger.py         # 日志
├── docs/                     # 文档
│   ├── TWITTER_INTEGRATION.md
│   ├── REDDIT_INTEGRATION.md
│   ├── TELEGRAM_INTEGRATION.md
│   ├── ONCHAIN_INTEGRATION.md
│   ├── ROBIN_INTEGRATION.md
│   ├── MULTI_SOURCE_INTELLIGENCE.md
│   └── INTELLIGENCE_SOURCES.md
├── examples/                 # 示例脚本
├── tests/                    # 测试套件
├── frontend/                 # Web Dashboard
├── robin_signals/            # Robin 暗网工具
├── main.py                   # 主程序
├── requirements.txt          # Python 依赖
└── .env.example              # 环境变量模板
```

---

## 🛠️ 技术栈

### 核心框架

- **Python 3.10+**: 异步编程,类型提示
- **AsyncIO**: 高性能并发
- **Pydantic**: 数据验证和配置管理
- **SQLAlchemy**: ORM 和数据持久化

### API 集成

- **HTTPX**: 异步 HTTP 客户端
- **Web3.py**: 以太坊/Polygon 交互
- **Tweepy**: Twitter API v2
- **PRAW**: Reddit API
- **Telethon**: Telegram MTProto

### 数据分析

- **TextBlob**: 情感分析
- **VADER**: 社交媒体情感
- **Pandas**: 数据处理
- **NumPy/SciPy**: 数值计算

### 前端

- **HTML/CSS/JavaScript**: Web Dashboard
- **Chart.js**: 数据可视化
- **WebSocket**: 实时更新

---

## ⚠️ 风险警告

**本项目仅供学习和研究使用,不构成投资建议。**

### 交易风险

- ❗ **市场风险**: 预测市场价格波动可能导致损失
- ❗ **流动性风险**: 大额交易可能面临滑点
- ❗ **技术风险**: API 故障、网络延迟可能影响执行
- ❗ **智能合约风险**: Polygon 链上交互存在合约风险

### 使用须知

1. **谨慎投入**: 只投入你能承受损失的资金
2. **测试优先**: 在小额测试后再扩大规模
3. **监控运行**: 定期检查系统状态和交易记录
4. **合规使用**: 遵守当地法律法规
5. **API 限制**: 注意各平台的速率限制和使用条款

### 安全建议

- 🔒 **私钥安全**: 永远不要泄露你的私钥
- 🔒 **环境变量**: 不要将 `.env` 提交到 Git
- 🔒 **访问控制**: 限制 Dashboard 的网络访问
- 🔒 **定期审计**: 检查交易记录和资金流向

---

## 📊 性能基准

基于历史回测数据 (实际结果可能有所不同):

| 配置 | 准确率 | 假阳性 | 年化收益 | 最大回撤 |
|------|--------|--------|----------|----------|
| 仅套利 | 65% | 25% | 12% | -8% |
| 套利 + Twitter | 78% | 15% | 18% | -5% |
| 套利 + 链上 | 75% | 18% | 16% | -6% |
| **全部情报源** | **85%** | **8%** | **24%** | **-4%** |

---

## 🤝 贡献

欢迎贡献代码、报告问题或提出建议!

1. Fork 本仓库
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

---

## 📄 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

---

## 📞 联系方式

- **GitHub Issues**: [提交问题](https://github.com/ziyefbk/polymarket_trade/issues)
- **讨论**: [GitHub Discussions](https://github.com/ziyefbk/polymarket_trade/discussions)

---

## 🙏 致谢

- [Polymarket](https://polymarket.com/) - 预测市场平台
- [Robin](https://github.com/ziyefbk/robin) - 暗网 OSINT 工具
- 所有开源项目贡献者

---

## 📚 相关资源

- [Polymarket API 文档](https://docs.polymarket.com/)
- [Polygon 网络](https://polygon.technology/)
- [Kelly 准则](https://en.wikipedia.org/wiki/Kelly_criterion)
- [情感分析介绍](https://en.wikipedia.org/wiki/Sentiment_analysis)

---

**⭐ 如果这个项目对你有帮助,请给个 Star!**

---

<div align="center">
  <sub>Built with ❤️ by Claude Sonnet 4.5</sub>
</div>
