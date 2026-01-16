# Robin Intelligence Integration Guide

## Overview

Robin 是一个暗网 OSINT (开源情报) 工具，已集成到 Polymarket 套利系统中，用于从暗网获取可能影响预测市场的情报信息。

## 使用场景

Robin 可以帮助你：
- **提前发现重大事件信号**：从暗网论坛、聊天室获取事件的早期信号
- **识别市场移动信息**：在信息公开披露前发现潜在的市场影响因素
- **关联暗网活动与市场结果**：分析暗网活动（如黑客论坛、勒索软件）与相关预测市场的相关性

## 系统要求

1. **Tor 服务**（必需）：Robin 需要通过 Tor 访问暗网
   ```bash
   # Linux/WSL
   sudo apt install tor
   sudo service tor start

   # macOS
   brew install tor
   brew services start tor
   ```

2. **LLM API 密钥**（至少一个）：
   - OpenAI API Key (推荐 GPT-4o)
   - Anthropic API Key (Claude 3.5 Sonnet)
   - Google API Key (Gemini 2.5 Flash)
   - 或本地 Ollama

## 配置步骤

### 1. 安装 Robin 依赖

```bash
conda activate math
cd robin_signals
pip install -r requirements.txt
```

### 2. 配置 API 密钥

```bash
cd robin_signals
cp .env.example .env
# 编辑 .env 文件，添加至少一个 LLM API 密钥
```

示例 `.env` 文件：
```bash
# 至少配置一个
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here
GOOGLE_API_KEY=your-google-key-here

# 可选：使用本地 Ollama
OLLAMA_BASE_URL=http://127.0.0.1:11434
```

### 3. 验证 Tor 连接

```bash
# 检查 Tor 是否运行
curl --socks5 localhost:9050 https://check.torproject.org/api/ip
```

## 使用方法

### Python API 使用

```python
from src.analyzer.robin_intelligence import RobinIntelligenceAnalyzer

# 初始化分析器
analyzer = RobinIntelligenceAnalyzer(model="gpt-4o", threads=5)

# 搜索特定主题的情报
result = analyzer.search_intelligence("ransomware attacks 2024")

if result["success"]:
    print(f"情报摘要：{result['summary']}")
    print(f"报告已保存到：{result['summary_file']}")
else:
    print(f"搜索失败：{result['error']}")

# 为 Polymarket 事件收集情报
event_title = "Will there be a major cyberattack on US infrastructure in 2024?"
intel = analyzer.analyze_event_intelligence(event_title)

# 批量分析多个事件
events = [
    "Will Trump win the 2024 election?",
    "Will Russia use nuclear weapons in 2024?",
    "Will Bitcoin reach $100k in 2024?"
]
reports = analyzer.batch_analyze_events(events, max_concurrent=2)
```

### CLI 使用

```bash
conda activate math
cd robin_signals

# 基本搜索
python main.py cli -m gpt-4o -q "ransomware payments" -t 12

# 保存到指定文件
python main.py cli -m gpt-4o -q "election fraud" -o my_report

# 使用 Claude 模型
python main.py cli -m claude-3-5-sonnet-latest -q "zero day exploits"

# 使用本地 Ollama 模型
python main.py cli -m llama3.1 -q "cryptocurrency hacks"
```

### Web UI 使用

```bash
conda activate math
cd robin_signals

# 启动 Web UI（浏览器访问 http://localhost:8501）
python main.py ui --ui-port 8501 --ui-host localhost
```

## 集成到交易策略

### 示例：结合情报和套利检测

```python
import asyncio
from src.analyzer.robin_intelligence import RobinIntelligenceAnalyzer
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.api.polymarket_client import PolymarketClient

async def enhanced_arbitrage_detection():
    """结合暗网情报增强套利检测"""

    # 初始化组件
    robin = RobinIntelligenceAnalyzer(model="gpt-4o")

    async with PolymarketClient() as client:
        detector = IntraMarketArbitrageDetector(client)

        # 1. 扫描套利机会
        opportunities = await detector.scan_all_markets()

        # 2. 为高价值机会收集情报
        for opp in opportunities[:5]:  # 前 5 个最佳机会
            print(f"\n分析事件：{opp.event_title}")

            # 搜索相关暗网情报
            intel = robin.analyze_event_intelligence(opp.event_title)

            if intel and intel["success"]:
                print(f"✓ 找到 {intel['num_scraped']} 条相关情报")
                print(f"摘要：{intel['summary'][:200]}...")

                # 根据情报调整置信度或决定是否交易
                # 这里可以添加你的逻辑
            else:
                print("✗ 未找到相关情报")

# 运行
asyncio.run(enhanced_arbitrage_detection())
```

## 情报类型示例

Robin 可以搜索以下类型的暗网情报：

1. **网络安全事件**
   - 数据泄露、黑客攻击
   - 勒索软件活动
   - 0day 漏洞交易

2. **政治事件**
   - 选举舞弊讨论
   - 政治阴谋论
   - 内部泄密

3. **经济/金融**
   - 加密货币黑市交易
   - 洗钱活动
   - 金融犯罪

4. **地缘政治**
   - 军事行动讨论
   - 制裁规避
   - 恐怖组织活动

## 注意事项

⚠️ **法律和道德警告**：
- 此工具仅用于**合法的调查和研究目的**
- 访问暗网内容在某些司法管辖区可能违法
- 使用前请确保遵守当地法律和机构政策
- 作者不对工具的滥用或通过工具获取的数据负责

⚠️ **隐私警告**：
- Robin 使用第三方 LLM API，请谨慎发送敏感查询
- 查看所用 API 提供商的服务条款

⚠️ **技术警告**：
- 暗网搜索可能很慢，取决于 Tor 连接速度
- LLM API 调用会产生费用
- 批量查询时注意 API 速率限制

## 故障排除

### Tor 连接失败
```bash
# 检查 Tor 状态
systemctl status tor  # Linux
brew services list | grep tor  # macOS

# 重启 Tor
sudo service tor restart  # Linux
brew services restart tor  # macOS
```

### LLM API 错误
- 检查 `.env` 文件中的 API 密钥是否正确
- 确认 API 密钥有足够的额度
- 检查网络连接

### 搜索结果为空
- 尝试更改搜索关键词
- 增加线程数（`threads` 参数）
- 检查 Tor 连接是否正常

## 进一步开发

你可以扩展 Robin 集成：

1. **自动化情报收集**：定期扫描暗网，建立情报数据库
2. **情报评分系统**：根据情报质量调整交易置信度
3. **实时监控**：监控特定暗网论坛的实时动态
4. **情报关联**：将暗网情报与公开新闻、社交媒体关联分析

## 相关文件

- [src/analyzer/robin_intelligence.py](../src/analyzer/robin_intelligence.py) - Robin 集成模块
- [robin_signals/](../robin_signals/) - Robin 原始工具
- [robin_signals/README.md](../robin_signals/README.md) - Robin 官方文档
