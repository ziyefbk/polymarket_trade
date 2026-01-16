# Windows 下 Robin 集成快速使用指南

## 📋 一键安装配置

### 方法 1：使用批处理脚本（推荐）

打开 **Command Prompt (CMD)**，运行：

```cmd
cd c:\Users\28275\Desktop\polymarket
setup_robin.bat
```

这个脚本会自动：
1. 激活 conda math 环境
2. 安装 Robin 依赖
3. 创建 .env 配置文件
4. 运行配置测试

### 方法 2：手动安装

```cmd
cd c:\Users\28275\Desktop\polymarket

# 1. 激活 conda 环境
conda activate math

# 2. 安装 Robin 依赖
cd robin_signals
pip install -r requirements.txt
cd ..

# 3. 创建配置文件
copy robin_signals\.env.example robin_signals\.env

# 4. 编辑 robin_signals\.env，添加你的 API Key
notepad robin_signals\.env

# 5. 测试配置
python test_robin_setup.py
```

## 🔑 配置 API 密钥

编辑 `robin_signals\.env` 文件，至少添加一个 API 密钥：

```bash
# OpenAI (推荐)
OPENAI_API_KEY=sk-your-key-here

# 或者 Anthropic Claude
ANTHROPIC_API_KEY=sk-ant-your-key-here

# 或者 Google Gemini
GOOGLE_API_KEY=your-google-key-here
```

## 🌐 安装 Tor（必需）

Robin 需要 Tor 来访问暗网。

### 方法 1：安装 Tor Browser（最简单）
1. 下载：https://www.torproject.org/download/
2. 安装并启动 Tor Browser
3. Tor 会自动运行在后台（端口 9050）

### 方法 2：安装 Tor 专家包
1. 下载：https://www.torproject.org/download/tor/
2. 解压并运行 `tor.exe`
3. 保持 tor.exe 运行在后台

## ✅ 测试配置

```cmd
conda activate math
python test_robin_setup.py
```

预期输出：
```
============================================================
Robin Integration Setup Test
============================================================
Testing Robin imports...
PASS: Robin core modules imported successfully

Testing Tor connection...
PASS: Tor is running on port 9050

Testing environment configuration...
PASS: OpenAI API key configured

Testing Robin integration module...
PASS: Robin integration module imported successfully

============================================================
Test Results Summary
============================================================
Robin imports................................ PASS
Tor connection............................... PASS
Environment config........................... PASS
Integration module........................... PASS

============================================================
SUCCESS: All tests passed! Robin integration is ready.
============================================================
```

## 🚀 开始使用

### 示例 1：基本搜索

```cmd
conda activate math
cd robin_signals
python main.py cli -m gpt-4o -q "cryptocurrency hacks 2024" -t 8
```

### 示例 2：使用 Python API

```python
from src.analyzer.robin_intelligence import RobinIntelligenceAnalyzer

# 初始化
analyzer = RobinIntelligenceAnalyzer(model="gpt-4o")

# 搜索情报
result = analyzer.search_intelligence("ransomware attacks")

if result["success"]:
    print(f"找到 {result['num_scraped']} 条情报")
    print(f"报告：{result['summary_file']}")
```

### 示例 3：运行完整示例

```cmd
conda activate math
python examples\robin_integration_example.py
```

## 🔧 故障排除

### 问题 1：conda activate 失败
```
ERROR: 'conda' 不是内部或外部命令
```

**解决：** 使用 Anaconda Prompt 或 Command Prompt，确保 conda 已添加到 PATH

### 问题 2：Tor 连接失败
```
FAIL: Tor is not running
```

**解决：**
1. 启动 Tor Browser 或 tor.exe
2. 等待几秒让 Tor 完全启动
3. 重新测试：`python test_robin_setup.py`

### 问题 3：依赖安装失败
```
ERROR: Failed to install dependencies
```

**解决：**
```cmd
conda activate math
cd robin_signals
pip install --upgrade pip
pip install -r requirements.txt --no-cache-dir
```

### 问题 4：API Key 未配置
```
WARN: No LLM API keys found in .env
```

**解决：**
1. 编辑 `robin_signals\.env`
2. 添加至少一个有效的 API Key
3. 确保没有 `your_` 前缀

## 📚 进阶使用

### 1. 为 Polymarket 事件收集情报

```python
from src.analyzer.robin_intelligence import RobinIntelligenceAnalyzer

analyzer = RobinIntelligenceAnalyzer(model="gpt-4o")

# 分析特定事件
event = "Will Trump win the 2024 election?"
intel = analyzer.analyze_event_intelligence(event)

print(intel["summary"])
```

### 2. 批量分析多个事件

```python
events = [
    "Will Bitcoin reach $100k in 2024?",
    "Will there be a major cyberattack in 2024?",
    "Will Russia use nuclear weapons?"
]

reports = analyzer.batch_analyze_events(events)
```

### 3. 结合套利检测

```python
from src.analyzer.arbitrage_detector import IntraMarketArbitrageDetector
from src.api.polymarket_client import PolymarketClient

async with PolymarketClient() as client:
    detector = IntraMarketArbitrageDetector(client)
    opportunities = await detector.scan_all_markets()

    # 为最佳机会收集情报
    for opp in opportunities[:3]:
        intel = analyzer.analyze_event_intelligence(opp.event_title)
        # 根据情报调整交易决策
```

## 📖 完整文档

- [Robin 集成文档](docs/ROBIN_INTEGRATION.md)
- [Robin 官方文档](robin_signals/README.md)
- [主项目文档](CLAUDE.md)

## ⚠️ 重要提醒

1. **费用**：LLM API 调用会产生费用（GPT-4o ~$0.01-0.05 每次搜索）
2. **速度**：暗网搜索较慢，单次可能需要 1-3 分钟
3. **合法性**：仅用于合法的研究和调查目的
4. **隐私**：注意 API 提供商可能记录你的查询

## 🎯 下一步

✅ 配置完成后，你可以：
1. 运行 `python examples\robin_integration_example.py` 查看示例
2. 将 Robin 情报集成到套利策略中
3. 构建自动化情报收集系统
4. 开发情报评分和风险评估功能
