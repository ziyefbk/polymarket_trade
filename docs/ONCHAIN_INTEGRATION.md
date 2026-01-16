# 链上数据监控快速指南

## 概述

链上数据监控模块直接从 Polygon 区块链获取 Polymarket 的真实交易数据：
- 🐋 **巨鲸追踪**：识别和监控大户钱包
- 💰 **大额交易**：实时捕捉 $10k+ 的转账
- 📊 **资金流向**：分析存款/提款净流量
- ⚡ **实时监控**：追踪特定钱包的实时活动
- 🔍 **流动性监控**：检测市场流动性变化

**为什么链上数据最可靠？**
- ✅ 真金白银的投注，无法造假
- ✅ 实时透明，无延迟
- ✅ 可以追踪巨鲸行为
- ✅ 资金流向是最真实的市场信号

---

## 快速开始

### 1. 安装依赖
```bash
conda activate math
pip install web3
```

### 2. 基本使用

```python
from src.analyzer.onchain_intelligence import OnChainIntelligenceAnalyzer

# 初始化
analyzer = OnChainIntelligenceAnalyzer()

# 获取最近24小时活动
report = await analyzer.get_recent_activity(
    hours=24,
    min_amount=10000  # 只监控 >= $10k 的交易
)

# 打印报告
analyzer.print_report(report)
```

### 3. 报告示例

```
==============================================================================
ON-CHAIN INTELLIGENCE REPORT
==============================================================================
Period: 2024-01-15 10:00:00 to 2024-01-16 10:00:00

------------------------------------------------------------------------------
NETWORK ACTIVITY
------------------------------------------------------------------------------
Total Transactions: 342
Total Volume: $8,945,231.00 USDC
Unique Addresses: 187
Avg Transaction Size: $26,155.00

Whale Activity (>= $10,000):
  Whale Transactions: 156
  Whale Volume: $6,234,891.00 (69.7% of total)

------------------------------------------------------------------------------
TOP WHALE WALLETS
------------------------------------------------------------------------------
1. 0x1a2b3c4d5e...6f7g8h9i
   Total Volume: $1,234,567.00
   Transactions: 23
   Avg Size: $53,676.00
   Last Active: 2024-01-16 09:45:23

2. 0x9876543210...abcdefgh
   Total Volume: $987,654.00
   Transactions: 18
   Avg Size: $54,870.00
   Last Active: 2024-01-16 09:12:45

------------------------------------------------------------------------------
LARGE DEPOSITS (Top 5)
------------------------------------------------------------------------------
1. $250,000.00 USDC
   From: 0xaa11bb22cc...dd33ee44
   Time: 2024-01-16 08:30:12
   Tx: 0x1234567890abcdef...

2. $180,500.00 USDC
   From: 0xff00ee11dd...22bb33aa
   Time: 2024-01-16 07:15:45
   Tx: 0xabcdef1234567890...

------------------------------------------------------------------------------
LARGE WITHDRAWALS (Top 5)
------------------------------------------------------------------------------
1. $195,000.00 USDC
   To: 0xcc88dd77ee...66ff55aa
   Time: 2024-01-16 09:00:33
   Tx: 0x9876543210fedcba...
```

---

## 核心功能

### 1. 巨鲸钱包追踪

```python
# 获取活跃的巨鲸
report = await analyzer.get_recent_activity(hours=48)

for whale in report.top_whales:
    print(f"Whale: {whale.address}")
    print(f"  Volume: ${whale.total_volume:,.0f}")
    print(f"  Txs: {whale.transaction_count}")

    # 查询当前余额
    balance = await analyzer.get_usdc_balance(whale.address)
    print(f"  Current Balance: ${balance:,.0f}")
```

### 2. 大额交易监控

```python
# 监控指定区块范围的大额交易
transactions = await analyzer.monitor_large_transactions(
    from_block=50000000,
    to_block=50001000,
    min_amount=50000  # >= $50k
)

for tx in transactions:
    print(f"${tx.value:,.0f} - {tx.transaction_type}")
    print(f"  From: {tx.from_address}")
    print(f"  To: {tx.to_address}")
```

### 3. 实时钱包监控

```python
# 实时追踪巨鲸钱包
whale_address = "0x1234...5678"

async def alert(tx):
    print(f"🔔 Whale moved ${tx.value:,.0f}!")

await analyzer.track_wallet_in_realtime(
    wallet_address=whale_address,
    callback=alert,
    poll_interval=10  # 每10秒检查一次
)
```

---

## 交易信号解读

### 1. 资金净流量

```python
deposit_volume = sum(tx.value for tx in report.large_deposits)
withdrawal_volume = sum(tx.value for tx in report.large_withdrawals)
net_flow = deposit_volume - withdrawal_volume

if net_flow > 100000:
    signal = "BULLISH 📈"
    # 大量资金流入 → 市场看涨
elif net_flow < -100000:
    signal = "BEARISH 📉"
    # 大量资金流出 → 市场看跌
else:
    signal = "NEUTRAL ➖"
```

### 2. 巨鲸占比

```python
whale_pct = (report.whale_volume / report.total_volume) * 100

if whale_pct > 70:
    # 巨鲸主导市场 → 跟随巨鲸
    strategy = "FOLLOW WHALES"
elif whale_pct < 40:
    # 散户主导 → 反向指标
    strategy = "CONTRARIAN"
```

### 3. 综合评分

```python
def calculate_onchain_signal(report):
    score = 0

    # 资金流向 (±30%)
    net_flow = sum(...) - sum(...)
    if net_flow > 100000:
        score += 0.3
    elif net_flow < -100000:
        score -= 0.3

    # 巨鲸活跃度 (+20%)
    if report.whale_transactions > 100:
        score += 0.2

    # 交易量 (+10%)
    if report.total_volume > 5000000:
        score += 0.1

    return score  # -1 to 1
```

---

## 与套利系统集成

### 增强置信度

```python
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector

# 1. 获取链上数据
onchain_report = await onchain_analyzer.get_recent_activity(hours=24)

# 2. 获取套利机会
async with PolymarketClient() as client:
    detector = IntraMarketArbitrageDetector(client)
    opportunities = await detector.scan_all_markets()

# 3. 用链上数据增强置信度
for opp in opportunities:
    # 计算链上信号强度
    onchain_signal = calculate_onchain_signal(onchain_report)

    # 增强置信度
    enhanced_confidence = opp.confidence_score + (onchain_signal * 0.2)

    # 决策
    if enhanced_confidence > 0.75:
        print(f"STRONG BUY: {opp.event_title}")
        # 执行交易
```

---

## 重要参数

### 巨鲸阈值
```python
# 默认：$10,000
analyzer = OnChainIntelligenceAnalyzer(usdc_threshold=10000)

# 大户标准：$50,000+
analyzer = OnChainIntelligenceAnalyzer(usdc_threshold=50000)

# 超级巨鲸：$100,000+
analyzer = OnChainIntelligenceAnalyzer(usdc_threshold=100000)
```

### RPC 端点
```python
# 公共端点（可能较慢）
analyzer = OnChainIntelligenceAnalyzer()

# 私有端点（更快更稳定）
analyzer = OnChainIntelligenceAnalyzer(
    rpc_url="https://polygon-mainnet.infura.io/v3/YOUR_KEY"
)

# Alchemy（推荐）
analyzer = OnChainIntelligenceAnalyzer(
    rpc_url="https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY"
)
```

---

## RPC 服务商

| 服务商 | 免费额度 | 费用 | 推荐 |
|--------|---------|------|------|
| **公共端点** | 无限 | 免费 | 测试 |
| **Infura** | 100k/天 | $50/月 | ⭐⭐⭐ |
| **Alchemy** | 300M/月 | $49/月 | ⭐⭐⭐⭐⭐ |
| **QuickNode** | 无限 | $9/月起 | ⭐⭐⭐⭐ |

**推荐**：Alchemy（免费层足够用）
- 注册：https://www.alchemy.com/
- 选择 Polygon Network
- 获取 API Key

---

## 性能优化

### 1. 批量查询
```python
# ❌ 逐个查询（慢）
for address in addresses:
    balance = await analyzer.get_usdc_balance(address)

# ✅ 使用 Multicall（快）
from web3 import Web3
# 一次查询多个余额
```

### 2. 缓存结果
```python
# 缓存区块数据
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_block_cached(block_number):
    return w3.eth.get_block(block_number)
```

### 3. 并发处理
```python
# 并发查询多个区块范围
async def analyze_multiple_ranges(ranges):
    tasks = [
        analyzer.monitor_large_transactions(start, end)
        for start, end in ranges
    ]
    return await asyncio.gather(*tasks)
```

---

## 故障排除

### 1. 连接失败
```
Failed to connect to Polygon RPC
```
**解决**：
- 检查网络连接
- 尝试其他 RPC 端点
- 使用付费 RPC 服务（Alchemy/Infura）

### 2. 查询超时
```
Timeout waiting for response
```
**解决**：
- 减小区块范围
- 使用更快的 RPC 端点
- 增加超时时间

### 3. 速率限制
```
Rate limit exceeded
```
**解决**：
- 增加查询间隔
- 升级 RPC 服务层级
- 使用多个 RPC 端点轮询

---

## 完整示例

```python
import asyncio
from src.analyzer.onchain_intelligence import OnChainIntelligenceAnalyzer

async def main():
    # 初始化（使用 Alchemy RPC）
    analyzer = OnChainIntelligenceAnalyzer(
        rpc_url="https://polygon-mainnet.g.alchemy.com/v2/YOUR_KEY",
        usdc_threshold=10000
    )

    # 获取最近活动
    print("Analyzing on-chain activity...")
    report = await analyzer.get_recent_activity(hours=24)

    # 打印报告
    analyzer.print_report(report)

    # 计算交易信号
    deposit_vol = sum(tx.value for tx in report.large_deposits)
    withdraw_vol = sum(tx.value for tx in report.large_withdrawals)
    net_flow = deposit_vol - withdraw_vol

    print(f"\n💰 NET FLOW: ${net_flow:,.0f}")

    if net_flow > 100000:
        print("📈 SIGNAL: BULLISH (large inflow)")
    elif net_flow < -100000:
        print("📉 SIGNAL: BEARISH (large outflow)")
    else:
        print("➖ SIGNAL: NEUTRAL")

    # 追踪最活跃的巨鲸
    if report.top_whales:
        top_whale = report.top_whales[0]
        print(f"\n🐋 TOP WHALE: {top_whale.address}")
        print(f"   Volume: ${top_whale.total_volume:,.0f}")

        # 查询余额
        balance = await analyzer.get_usdc_balance(top_whale.address)
        print(f"   Current Balance: ${balance:,.0f}")

asyncio.run(main())
```

---

## 相关资源

- [Web3.py 文档](https://web3py.readthedocs.io/)
- [Polygon 浏览器](https://polygonscan.com/)
- [Alchemy API](https://www.alchemy.com/)
- [主项目文档](../CLAUDE.md)

---

**下一步**：运行示例
```bash
conda activate math
python examples\onchain_integration_example.py
```
