# 接口规范文档 (Interface Specification)

本文档定义Polymarket套利系统各模块间的接口标准，确保所有Agent并行开发时接口一致。

## 1. 数据结构规范

### 1.1 ArbitrageOpportunity (检测器 → 执行器 → 数据库)

**位置**: `src/types/opportunities.py`

**用途**: 从检测器传递到执行器，描述一个套利机会

**必需字段**:
```python
@dataclass
class ArbitrageOpportunity:
    opportunity_id: str          # 唯一标识符 (UUID)
    event_id: str                # Polymarket事件ID
    event_title: str             # 事件标题（便于日志）

    yes_token_id: str            # YES代币ID
    yes_price: float             # YES当前价格 (0-1)
    yes_liquidity: float         # YES流动性 (USDC)

    no_token_id: str             # NO代币ID
    no_price: float              # NO当前价格 (0-1)
    no_liquidity: float          # NO流动性 (USDC)

    price_sum: float             # yes_price + no_price
    spread: float                # abs(price_sum - 1.0)
    arbitrage_type: str          # "OVERPRICED" 或 "UNDERPRICED"

    net_profit_pct: float        # 扣除费用后的净利润百分比
    confidence_score: float      # 置信度 (0-1)
    is_executable: bool          # 是否可执行
    required_capital: float      # 所需资金

    detected_at: datetime        # 检测时间
    valid_until: datetime        # 过期时间
```

**验证规则**:
- `0 < yes_price < 1`
- `0 < no_price < 1`
- `0 <= confidence_score <= 1`
- `arbitrage_type in ["OVERPRICED", "UNDERPRICED"]`

---

### 1.2 ExecutionResult (执行器 → 数据库)

**位置**: `src/types/orders.py`

**用途**: 执行器返回交易结果给数据库层

**必需字段**:
```python
@dataclass
class ExecutionResult:
    opportunity_id: str          # 关联的套利机会ID
    success: bool                # 总体是否成功

    yes_filled_size: float       # YES实际成交量
    yes_avg_price: float         # YES平均成交价
    yes_status: str              # "FILLED" | "PARTIAL" | "FAILED"

    no_filled_size: float        # NO实际成交量
    no_avg_price: float          # NO平均成交价
    no_status: str               # "FILLED" | "PARTIAL" | "FAILED"

    total_capital_used: float    # 实际使用资金
    actual_profit_usd: float     # 实际利润 (USD)
    actual_profit_pct: float     # 实际利润百分比
    execution_time_ms: float     # 执行耗时 (毫秒)

    error_message: Optional[str] # 错误信息
    partial_fill_risk: bool      # 是否存在单边成交风险

    executed_at: datetime        # 执行时间
```

**状态值**:
- `PENDING`: 订单待处理
- `FILLED`: 完全成交
- `PARTIAL`: 部分成交
- `FAILED`: 失败

---

## 2. 异常处理规范

### 2.1 自定义异常层次

**位置**: `src/types/common.py`

```python
class ArbitrageError(Exception):
    """所有套利相关异常的基类"""
    pass

class InsufficientLiquidityError(ArbitrageError):
    """流动性不足"""
    pass

class ExecutionFailedError(ArbitrageError):
    """执行失败"""
    pass

class PriceStaleError(ArbitrageError):
    """价格过期"""
    pass

class RiskLimitExceededError(ArbitrageError):
    """超出风险限额"""
    pass
```

### 2.2 异常使用规则

1. **检测器 (Detector)**:
   - 遇到API错误时抛出 `ArbitrageError` 包装原始异常
   - 流动性不足时返回 `None` 而不是抛出异常

2. **执行器 (Executor)**:
   - 流动性不足: 抛出 `InsufficientLiquidityError`
   - 价格变动过大: 抛出 `PriceStaleError`
   - 订单执行失败: 抛出 `ExecutionFailedError`
   - 返回 `ExecutionResult` 时 `success=False` 并填充 `error_message`

3. **仓位管理器 (PositionManager)**:
   - 超出风险限额: 抛出 `RiskLimitExceededError`

4. **所有模块**:
   - 捕获异常后必须记录日志
   - 向上层返回明确的错误状态

---

## 3. 函数签名标准

### 3.1 类型注解要求

**强制规则**:
1. 所有函数必须有完整的类型注解
2. 使用 `typing` 模块类型 (`Optional`, `List`, `Dict` 等)
3. 异步函数使用 `async def`
4. 返回类型必须明确

**示例**:
```python
from typing import List, Optional, Tuple

async def scan_all_markets(
    self,
    limit: int = 100,
    min_liquidity: float = 50000.0
) -> List[ArbitrageOpportunity]:
    """
    扫描所有市场寻找套利机会

    Args:
        limit: 最大扫描市场数
        min_liquidity: 最小流动性过滤阈值

    Returns:
        套利机会列表，按置信度降序排列

    Raises:
        ArbitrageError: API调用失败时
    """
    pass
```

### 3.2 Docstring格式

使用 Google 风格 docstring:

```python
def function_name(param1: Type1, param2: Type2) -> ReturnType:
    """简短的一行描述

    更详细的描述（可选）

    Args:
        param1: 参数1的描述
        param2: 参数2的描述

    Returns:
        返回值的描述

    Raises:
        ExceptionType: 什么情况下抛出
    """
```

---

## 4. 模块接口定义

### 4.1 ArbitrageDetector 接口

**位置**: `src/analyzer/arbitrage_detector.py`

**公开方法**:
```python
class IntraMarketArbitrageDetector:
    def __init__(self, client: PolymarketClient, config: ArbitrageConfig):
        """初始化检测器"""

    async def scan_all_markets(self) -> List[ArbitrageOpportunity]:
        """扫描所有市场，返回套利机会列表（按置信度排序）"""

    async def analyze_event(self, event: Event) -> Optional[ArbitrageOpportunity]:
        """分析单个事件，如果有套利机会则返回，否则返回None"""
```

**私有方法建议**:
```python
    def calculate_spread(self, yes_price: float, no_price: float) -> float:
        """计算价格偏差"""

    def estimate_profit(self, spread: float, liquidity: float) -> dict:
        """估算利润（包括费用和滑点）"""

    def assess_liquidity(self, order_book: OrderBook, size: float) -> bool:
        """评估流动性是否足够"""

    def calculate_confidence_score(self, opp: ArbitrageOpportunity) -> float:
        """计算置信度分数"""
```

---

### 4.2 ArbitrageExecutor 接口

**位置**: `src/strategy/arbitrage_executor.py`

**公开方法**:
```python
class ArbitrageExecutor:
    def __init__(self, trader: PolymarketTrader, config: TradingConfig):
        """初始化执行器"""

    async def execute_opportunity(
        self,
        opp: ArbitrageOpportunity,
        position_size: float
    ) -> ExecutionResult:
        """执行套利机会，返回执行结果"""
```

**私有方法建议**:
```python
    async def verify_prices(self, opp: ArbitrageOpportunity) -> bool:
        """验证价格仍然有效（未过期）"""

    async def execute_legs_simultaneously(
        self,
        yes_token: str,
        no_token: str,
        side: OrderSide,
        yes_price: float,
        no_price: float,
        size: float
    ) -> Tuple[TradeResult, TradeResult]:
        """同时执行两条腿"""

    async def handle_partial_fill(
        self,
        yes_result: TradeResult,
        no_result: TradeResult
    ) -> ExecutionResult:
        """处理部分成交情况"""
```

---

### 4.3 PositionManager 接口

**位置**: `src/strategy/position_manager.py`

**公开方法**:
```python
class PositionManager:
    def __init__(self, config: TradingConfig, db: DatabaseManager):
        """初始化仓位管理器"""

    async def calculate_position_size(
        self,
        opportunity: ArbitrageOpportunity
    ) -> float:
        """计算最优仓位大小（使用Kelly准则）"""

    async def check_risk_limits(self) -> dict:
        """检查风险限额，返回检查结果字典"""

    async def get_available_capital(self) -> float:
        """获取可用资金"""
```

**返回格式** (check_risk_limits):
```python
{
    "daily_loss_ok": bool,
    "position_count_ok": bool,
    "capital_available": bool,
    "can_trade": bool  # 总体是否可以交易
}
```

---

### 4.4 DatabaseManager 接口

**位置**: `src/utils/database.py`

**公开方法**:
```python
class DatabaseManager:
    def __init__(self, db_url: str):
        """初始化数据库管理器"""

    async def initialize(self):
        """初始化数据库连接和表"""

    async def save_trade(self, execution_result: ExecutionResult) -> Trade:
        """保存交易记录，返回Trade对象"""

    async def update_trade_status(self, trade_id: str, status: str):
        """更新交易状态"""

    async def get_open_positions(self) -> List[Position]:
        """获取所有未平仓位"""

    async def get_daily_loss(self) -> float:
        """获取今日总亏损"""

    async def calculate_performance_metrics(self) -> dict:
        """计算性能指标"""
```

**返回格式** (calculate_performance_metrics):
```python
{
    "total_trades": int,
    "win_rate": float,
    "net_profit": float,
    "sharpe_ratio": float,
    "max_drawdown": float,
    "avg_profit_per_trade": float
}
```

---

## 5. 异步编程规范

### 5.1 Context Manager使用

所有API客户端必须支持异步上下文管理器:

```python
async with PolymarketClient() as client:
    markets = await client.get_markets()
```

### 5.2 并发执行

使用 `asyncio.gather()` 并发执行独立任务:

```python
# 同时执行两条腿
yes_result, no_result = await asyncio.gather(
    trader.sell(yes_token, yes_price, size),
    trader.sell(no_token, no_price, size),
    return_exceptions=True  # 捕获异常而不是传播
)
```

### 5.3 超时处理

使用 `asyncio.wait_for()` 设置超时:

```python
try:
    result = await asyncio.wait_for(
        long_running_task(),
        timeout=10.0  # 10秒超时
    )
except asyncio.TimeoutError:
    logger.error("Operation timed out")
```

---

## 6. 日志规范

### 6.1 日志级别使用

- `DEBUG`: 详细的调试信息（价格、订单簿快照）
- `INFO`: 正常操作流程（发现机会、开始执行）
- `SUCCESS`: 成功事件（loguru特有，交易成功）
- `WARNING`: 警告信息（风险限额接近、流动性不足）
- `ERROR`: 错误事件（执行失败、API错误）
- `CRITICAL`: 严重错误（数据库连接失败、系统崩溃）

### 6.2 日志格式

```python
from loguru import logger

# 发现机会
logger.info(f"Found arbitrage opportunity: {opp.event_title}")
logger.info(f"Spread: {opp.spread:.2%}, Expected profit: {opp.net_profit_pct:.2%}")

# 执行交易
logger.info(f"Executing opportunity {opp.opportunity_id} with size ${size:.2f}")

# 成功
logger.success(f"✓ Trade executed successfully. Profit: ${result.actual_profit_usd:.2f}")

# 失败
logger.error(f"✗ Trade failed: {result.error_message}")

# 异常
logger.exception(f"Unexpected error in scan_cycle")  # 自动包含堆栈跟踪
```

---

## 7. 配置访问规范

### 7.1 统一配置接口

所有模块通过 `settings` 对象访问配置:

```python
from config import settings

# 访问配置
min_spread = settings.arbitrage.min_discrepancy  # 0.03
max_position = settings.trading.max_position_size  # 1000.0
scan_interval = settings.arbitrage.scan_interval  # 30
```

### 7.2 不要硬编码

**错误**:
```python
if spread > 0.03:  # ❌ 硬编码
    ...
```

**正确**:
```python
if spread > settings.arbitrage.min_discrepancy:  # ✓ 使用配置
    ...
```

---

## 8. 测试规范

### 8.1 单元测试结构

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_detect_overpriced_opportunity():
    """测试检测溢价套利机会"""
    # Arrange
    mock_client = AsyncMock()
    mock_client.get_all_active_events.return_value = [...]

    detector = IntraMarketArbitrageDetector(mock_client, config)

    # Act
    opportunities = await detector.scan_all_markets()

    # Assert
    assert len(opportunities) > 0
    assert opportunities[0].arbitrage_type == "OVERPRICED"
```

### 8.2 测试覆盖率要求

- 每个模块单元测试覆盖率 > 80%
- 核心逻辑（利润计算、Kelly准则）覆盖率 > 95%
- 所有公开方法必须有测试

---

## 9. 代码风格规范

### 9.1 命名约定

- **类名**: PascalCase (`ArbitrageDetector`)
- **函数/变量**: snake_case (`calculate_spread`)
- **常量**: UPPER_SNAKE_CASE (`MAX_RETRIES`)
- **私有方法**: 前缀下划线 (`_internal_method`)

### 9.2 导入顺序

```python
# 1. 标准库
import asyncio
from typing import List, Optional
from datetime import datetime

# 2. 第三方库
from loguru import logger
import httpx

# 3. 本地模块
from config import settings
from src.types import ArbitrageOpportunity
```

### 9.3 行长度

- 最大行长度: 100字符
- 使用黑体 (Black) 格式化工具

---

## 10. 集成检查清单

在提交代码前，确保：

### 检测器 (Agent A)
- [ ] `ArbitrageOpportunity` 对象包含所有必需字段
- [ ] 返回的机会按 `confidence_score` 降序排列
- [ ] 所有价格在 0-1 范围内
- [ ] 有单元测试覆盖核心逻辑

### 执行器 (Agent B)
- [ ] `ExecutionResult` 对象包含所有必需字段
- [ ] 同时执行两条腿使用 `asyncio.gather()`
- [ ] 处理部分成交情况
- [ ] 有 Mock 测试

### 数据库 (Agent C)
- [ ] 数据库模型与 `ExecutionResult` 字段匹配
- [ ] 所有异步操作使用 `AsyncSession`
- [ ] 有 CRUD 操作测试

### 仓位管理器 (Agent D)
- [ ] Kelly 准则实现正确
- [ ] 应用所有配置限制 (`max_position_size` 等)
- [ ] `check_risk_limits()` 返回标准格式字典

### 主调度器 (Agent E)
- [ ] 正确初始化所有组件
- [ ] 定时任务按配置间隔运行
- [ ] 优雅关闭释放所有资源

---

## 11. 常见问题

### Q: 如果价格在检测和执行之间变化怎么办？
A: 执行器在下单前调用 `verify_prices()` 重新验证，如果偏差 > 2% 则放弃。

### Q: 如果只有一条腿成交怎么办？
A: 设置 `partial_fill_risk=True`，记录到数据库，尝试取消另一条腿或反向对冲。

### Q: 如何确保不超出风险限额？
A: 主循环在每次扫描前调用 `position_manager.check_risk_limits()`，如果 `can_trade=False` 则跳过本轮。

### Q: 多个Agent如何避免命名冲突？
A: 所有共享数据结构在 `src/types/` 中定义，各Agent只在自己的模块内定义私有类。

---

## 12. 联系与协调

**总指挥**: 负责审查和集成
- 审查所有提交的代码
- 解决接口冲突
- 运行集成测试

**各Agent**: 独立开发
- 严格遵循本规范
- 遇到接口问题立即沟通
- 定期向总指挥报告进度

---

## 附录: 快速参考

### 核心数据流

```
PolymarketClient → ArbitrageDetector → ArbitrageOpportunity
                                              ↓
                                      PositionManager (计算仓位)
                                              ↓
                                      ArbitrageExecutor → ExecutionResult
                                                               ↓
                                                        DatabaseManager
```

### 关键配置参数

```python
settings.arbitrage.min_discrepancy      # 0.03 (3%)
settings.arbitrage.scan_interval        # 30 seconds
settings.trading.max_position_size      # 1000 USDC
settings.trading.max_daily_loss         # 100 USDC
settings.trading.min_profit_threshold   # 0.02 (2%)
settings.trading.slippage_tolerance     # 0.01 (1%)
```

---

**版本**: 1.0
**最后更新**: 2026-01-15
**总指挥**: Main Orchestrator Claude
