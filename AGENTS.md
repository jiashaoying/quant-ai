# AGENTS.md — 量化策略查看系统 (quant-ai)

## 1. 项目架构概述

全栈股票量化策略回测系统。后端 FastAPI 提供策略管理、回测执行、市场数据 API；前端 React + TypeScript 提供可视化交互界面。

### 1.1 后端 — `backend/`

| 路径 | 职责 |
|---|---|
| `main.py` | FastAPI 入口，注册路由、CORS 配置 |
| `app/core/config.py` | 全局配置（Pydantic BaseSettings），数据库 URL、默认市场等 |
| `app/db/database.py` | SQLAlchemy 引擎、Session 管理、`init_db()` 建表 |
| `app/models/models.py` | ORM 模型：`Strategy`（策略表）、`BacktestResult`（回测结果表） |
| **`app/api/`** | **API 路由层** |
| `app/api/strategies.py` | `GET /api/strategies/` 列表、`GET /{id}` 详情 |
| `app/api/backtest.py` | `POST /api/backtest/run` 执行回测、`GET /history` 历史记录 |
| `app/api/market.py` | `GET /api/market/stock/{symbol}` 行情、`/info` 基本信息、`/search` 搜索 |
| **`app/strategies/`** | **策略引擎** |
| `app/strategies/engine.py` | 策略基类 `BaseStrategy` + 8 个策略实现（均线交叉、动量、均值回归、RSI、布林带、多因子、Transformer 预测、Transformer 深度学习）；`get_available_strategies()` 返回策略元数据；`create_strategy()` 工厂函数 |
| `app/strategies/transformer_dl.py` | 基于 PyTorch 的完整 Transformer 深度学习策略（位置编码 + 多头注意力 + 前馈网络） |
| **`app/backtest/`** | **回测引擎** |
| `app/backtest/engine.py` | `BacktestEngine`：接收 OHLCV 数据 + 交易信号，计算资金曲线、交易记录、绩效指标（年化收益、最大回撤、夏普比率、胜率、盈亏比） |
| **`app/services/`** | **服务层** |
| `app/services/market_data.py` | `MarketDataService`：对外统一数据接口，内部委托 `DataSourceManager` |
| `app/services/data_source_manager.py` | `DataSourceManager`：多数据源管理器，实现智能降级策略（详见 §2.2） |

### 1.2 前端 — `frontend/src/`

| 路径 | 职责 |
|---|---|
| `main.tsx` | React 入口 |
| `App.tsx` | 主页面布局：侧边栏策略列表 + 回测表单 + 结果展示；调用 `/api/backtest/run`；根据 `is_mock` 标识显示模拟数据提示 |
| `components/StrategyList.tsx` | 策略列表组件，从 `/api/strategies/` 加载，支持选中高亮 |
| `components/BacktestForm.tsx` | 回测表单组件：股票代码、周期、初始资金、**数据源选择器**（6 选项）、策略参数动态表单 |
| `components/BacktestResult.tsx` | 回测结果展示：绩效指标卡片、资金曲线图（Recharts）、交易记录表格、数据源标识；模拟数据时显示橙色警告横幅 |

### 1.3 数据库

- 引擎：SQLite（`sqlite:///./quant.db`），开发阶段本地文件
- ORM：SQLAlchemy，模型定义在 `app/models/models.py`
- 表：`strategies`（策略配置）、`backtest_results`（回测结果快照）

---

## 2. 关键约定

### 2.1 API 路由前缀

所有 API 路由统一使用 `/api/` 前缀，在 `main.py` 中注册：

```
/api/strategies/*   → 策略管理
/api/backtest/*     → 回测执行
/api/market/*       → 市场数据
/api/health         → 健康检查
```

前端通过 Vite 代理将 `/api/*` 转发至后端 `http://localhost:8000`。

### 2.2 数据源降级策略

`DataSourceManager._auto_fetch()` 实现智能降级，返回 `(DataFrame, actual_source)` 元组：

| 市场 | 优先级 1 | 优先级 2 | 优先级 3 | 优先级 4 | 兜底 |
|---|---|---|---|---|---|
| A 股 (`.SS`/`.SZ`/`.BJ`) | 腾讯财经（内置 HTTP） | YFinance | AKShare | BaoStock | 模拟数据 |
| 港股 (`.HK`) | 腾讯财经 | YFinance | — | — | 模拟数据 |
| 美股/其他 | YFinance | — | — | — | 模拟数据 |

- 腾讯财经 API 无需额外 pip 依赖，是 A 股最稳定的首选
- 用户可在前端指定数据源（`source` 参数），跳过自动降级
- **所有数据源失败时必定降级到模拟数据**，确保系统始终可用

### 2.3 模拟数据标识

后端回测结果包含两个关键字段：

- `data_source: string` — 实际使用的数据源名称（`tencent`/`yfinance`/`akshare`/`baostock`/`mock`）
- `is_mock: boolean` — `actual_source == "mock"` 时为 `true`

前端消费规则：
- `App.tsx`：`is_mock === true` 时标题显示 "回测结果（模拟数据）"
- `BacktestResult.tsx`：`is_mock === true` 时顶部显示橙色警告横幅 + 数据源标识

### 2.4 数据格式约定

- OHLCV DataFrame 列名统一为：`Date, Open, High, Low, Close, Volume`
- 策略信号 DataFrame 列名：`signal`（1=买入, -1=卖出, 0=持有）、`position`（信号差分，仅在变化时非零）
- 回测引擎返回 JSON 中所有浮点数必须清理 NaN/Inf（使用 `safe_round()` 或等效逻辑）
- 日期字段必须转为字符串格式（`strftime('%Y-%m-%d')`），不可直接序列化 datetime 对象

### 2.5 策略接口约定

所有策略继承 `BaseStrategy`，必须实现：

```python
def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
    """输入 OHLCV DataFrame，返回附加 signal/position 列的 DataFrame"""
```

新增策略需同步：
1. 在 `engine.py` 中实现策略类
2. 在 `get_available_strategies()` 中注册元数据（id、名称、描述、参数范围）
3. 在 `create_strategy()` 工厂函数中添加分支

---

## 3. 变更影响边界

### 3.1 修改策略引擎 → 同步回测引擎

| 变更类型 | 影响范围 | 检查项 |
|---|---|---|
| 修改 `generate_signals()` 信号逻辑 | `backtest/engine.py` 的 `run()` 方法 | 确认信号值仍为 1/-1/0，`position` 差分逻辑兼容 |
| 新增策略参数 | `api/backtest.py` 的 `BacktestRequest.parameters` | 确认参数通过 `**params` 正确传递到 `create_strategy()` |
| 新增策略 | `engine.py` 三处（类、列表、工厂） | 前端 `BacktestForm.tsx` 参数动态表单自动适配，无需改动 |
| 修改策略返回的 DataFrame 列 | `backtest/engine.py` 列引用 | 确认 `signal`、`position` 列名一致 |

### 3.2 修改数据源 → 检查降级逻辑

| 变更类型 | 影响范围 | 检查项 |
|---|---|---|
| 新增数据源 | `data_source_manager.py` | 在 `_auto_fetch()` 中插入正确的优先级位置；添加 `_fetch_xxx()` 静态方法 |
| 修改现有数据源获取逻辑 | `data_source_manager.py` | 确认返回 `(DataFrame, source_name)` 元组格式不变；确认异常被捕获可触发降级 |
| 修改数据源名称/ID | 前端 `BacktestForm.tsx` + `BacktestResult.tsx` | 同步更新 `DATA_SOURCES` 数组和 `dataSourceNames` 映射 |
| 修改 DataFrame 列名 | `data_source_manager.py` 所有 `_fetch_*` 方法 | 所有数据源必须输出统一的 `Date, Open, High, Low, Close, Volume` 列名 |

### 3.3 修改回测引擎 → 检查前端展示

| 变更类型 | 影响范围 | 检查项 |
|---|---|---|
| 修改 `metrics` 字段 | `BacktestResult.tsx` 指标展示 | 前端按固定 key 读取，新增/删除字段需同步前端 |
| 修改 `equity_curve` / `signals_data` 结构 | `BacktestResult.tsx` 图表 | Recharts 按固定字段名绑定，结构变更需同步 |
| 修改 `trades` 结构 | `BacktestResult.tsx` 交易表格 | 列定义需同步更新 |

### 3.4 修改 API 路由 → 检查前后端

| 变更类型 | 影响范围 | 检查项 |
|---|---|---|
| 修改路由前缀 | `main.py` + 前端 `fetch()` URL | 前后端路径必须一致 |
| 修改请求/响应模型 | `api/backtest.py` Pydantic 模型 + 前端表单 | 字段名、类型、默认值需前后端一致 |
| 新增 API 端点 | `main.py` 注册路由 | 确认 CORS 配置覆盖新路由 |

### 3.5 修改数据库模型

| 变更类型 | 影响范围 | 检查项 |
|---|---|---|
| 修改 `models.py` 表结构 | `database.py` 建表逻辑 | SQLite 不支持 ALTER，需删除旧库重建或写迁移脚本 |
| 修改字段类型 | 所有读写该字段的代码 | 确认 JSON 序列化/反序列化兼容 |
