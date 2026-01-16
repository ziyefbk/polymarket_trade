# 🚀 Polymarket套利系统 - Agent启动指南

## 已完成 ✅

**总指挥 (Task 0)** 已完成接口规范：
- ✅ 创建 `src/types/` 共享数据结构
- ✅ 创建 `INTERFACE_SPEC.md` 接口规范文档
- ✅ 创建 `CLAUDE.md` 项目文档

## 🎯 6个并行Agent任务

### Agent A - 套利检测器
**负责**: 实现市场扫描和套利机会识别
**文件**: `src/analyzer/arbitrage_detector.py`, `tests/test_arbitrage_detector.py`
**提示词**:
```
我是Agent A，负责实现套利检测器。请阅读以下文件：
1. C:\Users\28275\Desktop\polymarket\INTERFACE_SPEC.md
2. C:\Users\28275\Desktop\polymarket\src\types\opportunities.py

然后按照 C:\Users\28275\.claude\plans\zippy-petting-flurry.md 中 Task 1 的要求实现套利检测器。
```

---

### Agent B - 交易执行引擎
**负责**: 接收套利机会并执行交易
**文件**: `src/strategy/arbitrage_executor.py`, `tests/test_arbitrage_executor.py`
**提示词**:
```
我是Agent B，负责实现交易执行引擎。请阅读以下文件：
1. C:\Users\28275\Desktop\polymarket\INTERFACE_SPEC.md
2. C:\Users\28275\Desktop\polymarket\src\types\orders.py

然后按照 C:\Users\28275\.claude\plans\zippy-petting-flurry.md 中 Task 2 的要求实现交易执行引擎。
```

---

### Agent C - 数据库层
**负责**: 数据持久化和查询
**文件**: `src/utils/database.py`, `src/utils/models.py`, `tests/test_database.py`
**提示词**:
```
我是Agent C，负责实现数据库层。请阅读以下文件：
1. C:\Users\28275\Desktop\polymarket\INTERFACE_SPEC.md
2. C:\Users\28275\Desktop\polymarket\src\types\orders.py

然后按照 C:\Users\28275\.claude\plans\zippy-petting-flurry.md 中 Task 3 的要求实现数据库层，包括SQLAlchemy模型和Alembic迁移。
```

---

### Agent D - 仓位管理器
**负责**: 计算最优仓位大小和风险管理
**文件**: `src/strategy/position_manager.py`, `src/utils/kelly.py`, `tests/test_position_manager.py`
**提示词**:
```
我是Agent D，负责实现仓位管理器。请阅读以下文件：
1. C:\Users\28275\Desktop\polymarket\INTERFACE_SPEC.md
2. C:\Users\28275\Desktop\polymarket\src\types\opportunities.py

然后按照 C:\Users\28275\.claude\plans\zippy-petting-flurry.md 中 Task 4 的要求实现仓位管理器和Kelly准则。
```

---

### Agent E - 主调度器
**负责**: 协调所有组件，实现自动化循环
**文件**: `main.py`, `src/utils/logger.py`, `tests/test_orchestrator.py`
**提示词**:
```
我是Agent E，负责实现主调度器。请阅读以下文件：
1. C:\Users\28275\Desktop\polymarket\INTERFACE_SPEC.md
2. C:\Users\28275\Desktop\polymarket\src\types\opportunities.py
3. C:\Users\28275\Desktop\polymarket\src\types\orders.py

然后按照 C:\Users\28275\.claude\plans\zippy-petting-flurry.md 中 Task 5 的要求实现主调度器ArbitrageBot。
```

---

### 🆕 Agent F - Web UI 前端 (新增)
**负责**: 构建实时监控仪表板，可视化套利机器人状态和性能
**文件**: `frontend/`, `src/api/dashboard_api.py`
**提示词**:
```
我是Agent F，负责实现Web UI前端仪表板。请阅读以下文件：
1. C:\Users\28275\Desktop\polymarket\INTERFACE_SPEC.md
2. C:\Users\28275\Desktop\polymarket\src\types\orders.py

然后按照 C:\Users\28275\.claude\plans\zippy-petting-flurry.md 中 Task 6 的要求实现：

1. FastAPI后端API服务器 (src/api/dashboard_api.py)
   - REST API端点：/api/status, /api/performance, /api/trades/recent 等
   - WebSocket实时推送

2. 前端单页应用 (frontend/)
   - HTML界面：顶部状态栏、指标卡片、资金曲线图、实时交易流
   - JavaScript：WebSocket客户端、图表渲染、数据更新
   - CSS：暗色主题、响应式设计

技术栈：
- 后端：FastAPI + WebSocket + uvicorn
- 前端：原生HTML/CSS/JavaScript + Chart.js
- 实时通信：WebSocket
- 样式：暗色主题 (#0f172a背景色)

关键功能：
✓ 实时状态显示（运行/停止）
✓ 4个关键指标卡片（今日利润、胜率、交易数、未平仓）
✓ 资金曲线图（Chart.js渲染）
✓ 实时交易流（WebSocket推送新交易）
✓ 性能指标详情（总利润、夏普比率、最大回撤等）

启动方式：
```bash
# 开发环境
python -m src.api.dashboard_api

# 或集成到main.py
python main.py --dashboard
```

访问: http://localhost:8000
```

---

## 📊 开发进度追踪

| Agent | 任务 | 状态 | 负责文件 |
|-------|------|------|----------|
| Task 0 | 总指挥 | ✅ 完成 | 接口规范、共享类型 |
| Agent A | 套利检测器 | ⏳ 待开始 | `src/analyzer/` |
| Agent B | 交易执行引擎 | ⏳ 待开始 | `src/strategy/arbitrage_executor.py` |
| Agent C | 数据库层 | ⏳ 待开始 | `src/utils/database.py` |
| Agent D | 仓位管理器 | ⏳ 待开始 | `src/strategy/position_manager.py` |
| Agent E | 主调度器 | ⏳ 待开始 | `main.py` |
| Agent F | Web UI前端 | ✅ 完成 | `frontend/`, `src/api/dashboard_api.py` |

---

## 🔄 工作流程

1. **第1天**: ✅ 总指挥创建接口规范（已完成）
2. **第2-7天**: 6个Agent **并行开发**各自模块
3. **第8-10天**: 总指挥集成所有模块并运行测试
4. **第11-14天**: Paper trading干运行测试

---

## ✅ 完成标准

### Agent F (UI前端) 检查清单
- [x] FastAPI后端API实现 (`src/api/dashboard_api.py`)
  - [x] GET `/api/status` - 机器人状态
  - [x] GET `/api/performance` - 性能指标
  - [x] GET `/api/trades/recent` - 最近交易
  - [x] GET `/api/positions/open` - 未平仓位
  - [x] GET `/api/equity_curve` - 资金曲线数据
  - [x] WebSocket `/ws` - 实时推送

- [x] 前端界面完成 (`frontend/`)
  - [x] `index.html` - 主页面结构
  - [x] `css/style.css` - 暗色主题样式
  - [x] `js/websocket.js` - WebSocket客户端
  - [x] `js/charts.js` - Chart.js图表渲染
  - [x] `js/main.js` - 主逻辑和数据更新

- [x] 核心功能实现
  - [x] 实时状态指示器（运行中/已断开/错误）
  - [x] 4个关键指标卡片（实时更新）
  - [x] 资金曲线折线图
  - [x] 实时交易流（新交易自动显示）
  - [x] 性能指标详情展示

- [ ] 测试要求
  - [ ] WebSocket连接稳定性测试
  - [ ] API端点集成测试
  - [ ] 跨浏览器测试（Chrome、Firefox）
  - [ ] 响应式设计测试（移动端、桌面）

---
---

## 📁 项目结构预览

```
polymarket/
├── config/
│   └── settings.py                 ✅ (已存在)
├── src/
│   ├── types/                      ✅ (已创建 - 共享)
│   │   ├── common.py
│   │   ├── opportunities.py
│   │   └── orders.py
│   ├── api/
│   │   ├── polymarket_client.py    ✅ (已存在)
│   │   ├── trader.py               ✅ (已存在)
│   │   └── dashboard_api.py        ⏳ (Agent F)
│   ├── analyzer/
│   │   └── arbitrage_detector.py   ⏳ (Agent A)
│   ├── strategy/
│   │   ├── arbitrage_executor.py   ⏳ (Agent B)
│   │   └── position_manager.py     ⏳ (Agent D)
│   └── utils/
│       ├── database.py             ⏳ (Agent C)
│       ├── models.py               ⏳ (Agent C)
│       ├── kelly.py                ⏳ (Agent D)
│       └── logger.py               ⏳ (Agent E)
├── frontend/                       ⏳ (Agent F)
│   ├── index.html
│   ├── css/
│   │   └── style.css
│   └── js/
│       ├── main.js
│       ├── charts.js
│       └── websocket.js
├── tests/
│   ├── test_arbitrage_detector.py  ⏳ (Agent A)
│   ├── test_arbitrage_executor.py  ⏳ (Agent B)
│   ├── test_database.py            ⏳ (Agent C)
│   ├── test_position_manager.py    ⏳ (Agent D)
│   └── test_orchestrator.py        ⏳ (Agent E)
├── main.py                         ⏳ (Agent E)
├── INTERFACE_SPEC.md               ✅ (已创建)
├── CLAUDE.md                       ✅ (已创建)
└── requirements.txt                ✅ (已存在)
```

---

## 🎯 下一步行动

1. **复制上面对应的提示词**
2. **打开6个新的Claude对话窗口**
3. **粘贴提示词，启动各Agent**
4. **所有Agent完全并行工作，无依赖阻塞**

准备好开始了吗？🚀
