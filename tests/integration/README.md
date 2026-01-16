# Integration Test Suite - Serial Execution

## 📋 概述

这是Polymarket套利交易系统的**串行集成测试套件**。所有测试按顺序执行，一旦某个测试失败，立即停止并报告问题。

## 🎯 测试架构

```
串行测试流程 (按顺序执行，遇错即停)
├── T1: Environment Verification (环境验证) → 失败则停止
├── T2: Unit Tests (单元测试) → 失败则停止
├── T3: Database Integration (数据库集成) → 失败则停止
├── T4: API Integration (API集成) → 失败则停止
└── T5: End-to-End Integration (端到端集成) → 最终测试
```

## 🚀 快速开始

### 运行完整测试套件

```bash
# 在项目根目录下运行
python tests/integration/run_serial_tests.py
```

### 运行单个测试

```bash
# T1: 环境验证
python tests/integration/agent_t1_environment.py

# T2: 单元测试
python tests/integration/agent_t2_unit_tests.py

# T3: 数据库集成
python tests/integration/agent_t3_database.py

# T4: API集成
python tests/integration/agent_t4_api.py

# T5: 端到端集成
python tests/integration/agent_t5_e2e.py
```

## 📊 测试详情

### Agent T1: Environment Verification (环境验证)
**优先级**: 🔥 Critical
**时长**: ~1-2 分钟

**检查内容**:
- ✅ Python 3.7+ 版本
- ✅ 所有依赖包安装 (httpx, sqlalchemy, loguru, etc.)
- ✅ `.env` 文件存在
- ✅ 必需环境变量 (POLYMARKET_PRIVATE_KEY, DATABASE_URL)
- ✅ 项目文件结构完整
- ✅ 数据库连接可用

**输出**: `test_reports/t1_environment_report.txt`

---

### Agent T2: Unit Tests (单元测试)
**优先级**: 🔥 High
**时长**: ~3-5 分钟

**测试套件**:
1. `tests/test_kelly.py` - Kelly Criterion工具 (27 tests)
2. `tests/test_position_manager.py` - 仓位管理器 (29 tests)
3. `tests/test_arbitrage_detector.py` - 套利检测器 (13 tests)
4. `tests/test_database.py` - 数据库层 (19 tests)
5. `tests/test_orchestrator.py` - 主调度器 (15 tests)

**输出**: `test_reports/t2_unit_tests_report.txt`

---

### Agent T3: Database Integration (数据库集成)
**优先级**: 🔥 High
**时长**: ~2-3 分钟

**测试内容**:
1. ✅ Alembic迁移执行
2. ✅ 数据库连接测试
3. ✅ CRUD操作 (save_trade, create_position, get_open_positions)
4. ✅ 性能指标计算 (win_rate, sharpe_ratio, max_drawdown)

**输出**: `test_reports/t3_database_report.txt`

---

### Agent T4: API Integration (API集成)
**优先级**: 🔥 Medium
**时长**: ~3-5 分钟 (取决于网络)

**测试内容**:
1. ✅ PolymarketClient - 获取市场数据、事件、订单簿
2. ✅ ArbitrageDetector - 使用真实数据扫描市场
3. ✅ PolymarketTrader - 初始化和认证 (不执行真实交易)

**输出**: `test_reports/t4_api_report.txt`

---

### Agent T5: End-to-End Integration (端到端集成)
**优先级**: 🔥 Highest
**时长**: ~5-10 分钟

**测试场景**:
1. ✅ 完整扫描周期 (Detector → PositionManager → Database)
2. ✅ 主调度器干运行 (single cycle, dry-run mode)
3. ✅ 完整数据流 (API → 分析 → 执行 → 数据库 → 指标)

**输出**: `test_reports/t5_e2e_report.txt`

---

## 📈 测试报告

所有测试报告保存在 `test_reports/` 目录:

```
test_reports/
├── t1_environment_report.txt
├── t2_unit_tests_report.txt
├── t3_database_report.txt
├── t4_api_report.txt
├── t5_e2e_report.txt
└── integration_test_summary.txt  ← 总结报告
```

## 🔧 故障排除

### 常见问题

#### 1. Python版本不足
```
❌ Python 3.7+ required (found 3.6.5)
```
**解决方案**: 升级Python到3.7+
```bash
# Windows
# 从 https://www.python.org/downloads/ 下载安装

# Linux/Mac
pyenv install 3.9.0
pyenv global 3.9.0
```

#### 2. 依赖包缺失
```
❌ httpx not found
```
**解决方案**: 安装依赖
```bash
pip install -r requirements.txt
```

#### 3. 数据库连接失败
```
❌ Database connection failed
```
**解决方案**: 检查`.env`文件
```bash
# .env 文件必须包含
DATABASE_URL=sqlite+aiosqlite:///./arbitrage.db
```

#### 4. API测试失败
```
❌ PolymarketClient tests failed
```
**解决方案**: 检查网络连接和API状态
```bash
# 测试网络连接
curl https://clob.polymarket.com/
```

#### 5. 单元测试失败
```
❌ test_kelly.py FAILED
```
**解决方案**: 查看详细错误
```bash
# 直接运行失败的测试文件
pytest tests/test_kelly.py -v
```

## 📋 测试前检查清单

在运行测试前，确保:

- [ ] Python 3.7+ 已安装
- [ ] 所有依赖包已安装 (`pip install -r requirements.txt`)
- [ ] `.env` 文件已创建并配置
- [ ] 数据库文件路径可写
- [ ] 网络连接正常 (用于API测试)
- [ ] 没有其他进程占用数据库文件

## 🎯 测试成功标准

所有测试通过的输出:

```
========================================================================
                         FINAL SUMMARY
========================================================================

Total Tests Run: 5
✅ Passed: 5
❌ Failed: 0
⏱️  Total Time: 15m 30s

----------------------------------------------------------------------
Individual Test Results:
----------------------------------------------------------------------
✅ Agent T1: Environment Verification: PASS
✅ Agent T2: Unit Tests: PASS
✅ Agent T3: Database Integration: PASS
✅ Agent T4: API Integration: PASS
✅ Agent T5: End-to-End Integration: PASS
========================================================================

🎉 ALL INTEGRATION TESTS PASSED! System is ready for deployment.
```

## 🚦 下一步

### 测试全部通过后:
1. ✅ **Paper Trading测试** - 使用`--dry-run`模式运行系统
   ```bash
   python main.py --dry-run --once
   ```

2. ✅ **监控日志输出** - 检查`logs/`目录下的日志文件
   ```bash
   tail -f logs/arbitrage_YYYYMMDD.log
   ```

3. ✅ **启动Web界面** - 访问监控面板
   ```bash
   uvicorn src.api.dashboard_api:app --reload
   # 访问 http://localhost:8000
   ```

4. ✅ **生产部署** - 移除`--dry-run`标志，开始真实交易
   ```bash
   python main.py
   ```

## 📞 获取帮助

如果测试持续失败:

1. 查看详细报告: `test_reports/integration_test_summary.txt`
2. 检查各个agent的独立报告
3. 运行单个测试获取更多信息
4. 查看项目文档: `README.md`, `INTERFACE_SPEC.md`

## ⚠️ 重要提示

- **串行模式**: 测试按顺序执行，一旦失败立即停止
- **修复优先**: 必须修复失败的测试后才能继续
- **真实API**: T4和T5会连接真实的Polymarket API
- **无真实交易**: 所有测试都在dry-run模式下，不会执行真实交易
- **数据库隔离**: 测试使用独立的测试数据库，不影响生产数据

---

**版本**: 1.0.0
**最后更新**: 2026-01-15
**作者**: Polymarket Arbitrage System Team