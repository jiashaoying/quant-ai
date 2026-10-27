---
kind: error_handling
name: 后端基于 FastAPI HTTPException 的扁平错误处理模式
category: error_handling
scope:
    - '**'
source_files:
    - backend/main.py
    - backend/app/api/backtest.py
    - backend/app/api/market.py
    - backend/app/api/strategies.py
    - backend/app/services/data_source_manager.py
    - backend/app/strategies/engine.py
    - backend/app/backtest/engine.py
---

## 1. 采用的系统/方法

后端基于 FastAPI，**没有自定义异常类型、错误码枚举或全局异常处理器**。错误处理的实现方式是：
- 在 API 路由层用 `try/except Exception` 包裹业务调用，统一捕获后以 `HTTPException(status_code=400, detail=str(e))` 抛出。
- 对“资源不存在”等语义明确的场景直接 `raise HTTPException(status_code=404, detail="...")`。
- 业务层（策略引擎、数据源管理器）使用 Python 原生异常（`ValueError`、`ImportError`、`NotImplementedError`），由上层路由捕获并转成 HTTP 响应。
- 前端（React + TypeScript）未引入统一的错误拦截器；组件中通过 `fetch` / `axios` 的 Promise reject 分支自行处理错误（见 `src/components/BacktestForm.tsx`、`StrategyList.tsx` 等）。后端无全局中间件做错误转换。

## 2. 关键文件与位置

| 文件 | 作用 |
|---|---|
| `backend/main.py` | FastAPI 应用入口，仅注册 CORS 中间件，**未注册任何全局异常处理器** |
| `backend/app/api/backtest.py` | 回测路由，`run_backtest` 用 `try/except Exception` 捕获全部异常并以 400 返回 |
| `backend/app/api/market.py` | 市场数据路由，两个接口同样用 `try/except Exception` → `HTTPException(400)` |
| `backend/app/api/strategies.py` | 策略路由，找不到策略时直接 `raise HTTPException(404, "Strategy not found")` |
| `backend/app/services/data_source_manager.py` | 数据源选择逻辑，抛出 `ValueError("Unknown data source: ...")` 和 `ValueError("无法转换股票代码: ...")` |
| `backend/app/strategies/engine.py` | 策略工厂 `create_strategy` 对未知 strategy_id 抛 `ValueError`，对缺失 PyTorch 依赖抛 `ImportError` |
| `backend/app/backtest/engine.py` | 回测引擎内部不抛异常，而是用 `safe_round` 把 NaN/Inf 归一化为 0，保证 JSON 可序列化 |

## 3. 架构与约定

- **扁平式错误传播**：业务层抛出 Python 原生异常 → 路由层 `try/except Exception` 捕获 → 转为 `HTTPException`。没有在 service 层定义领域异常类。
- **错误码约定**：
  - 业务参数/上游失败 → `HTTPException(400, detail=str(e))`（backtest、market 路由一致）。
  - 资源不存在 → `HTTPException(404, detail="Strategy not found")`。
  - 未实现功能 → 直接返回 `{"message": "Not implemented yet"}`（如 `/api/backtest/history`）。
- **可选依赖降级**：`app/strategies/engine.py` 顶部 `try: from app.strategies.transformer_dl import ... except ImportError: DL_AVAILABLE = False`，并在 `create_strategy` 中根据 `DL_AVAILABLE` 决定是否抛出 `ImportError`，避免启动期依赖缺失导致整个服务不可用。
- **数值健壮性优先于错误上报**：`BacktestEngine._calculate_metrics` 中的 `safe_round` 将 NaN/Inf 替换为 0，而不是抛错——这是针对量化计算结果可能出现的数值异常的约定处理方式。
- **CORS 中间件**：`main.py` 配置了 `allow_origins=["*"]`，但**没有**注册 `CORSMiddleware` 之外的错误相关中间件（如请求日志、统一错误格式化）。

## 4. 观察到的约定与约束

- **约定（描述性）**：所有 API 路由中涉及外部 I/O（数据源、策略执行）的代码块都包裹在 `try/except Exception` 中，并以 `HTTPException(status_code=400, detail=str(e))` 作为兜底错误响应。该模式在 `backtest.py` 和 `market.py` 中重复出现。
- **约定（描述性）**：业务层的输入校验错误使用 `ValueError`（`data_source_manager.py`、`strategies/engine.py`），由路由层统一捕获并映射为 HTTP 400。
- **约定（描述性）**：FastAPI 内置的 Pydantic 验证错误（如必填字段缺失、类型不符）走框架默认路径，未经自定义处理；只有显式 `try/except` 内的异常才会被统一包装。
- **约束（由代码体现）**：`BaseStrategy.generate_signals` 定义为 `raise NotImplementedError`，子类必须重写；违反此约定的实现会在运行时抛出 `NotImplementedError`，由路由层捕获后返回 400。
- **约束（由代码体现）**：`create_strategy` 是策略实例化的唯一入口，新增策略必须在此函数中添加分支，否则传入未知 `strategy_id` 会抛出 `ValueError(f"Unknown strategy: {strategy_id}")`。
- **约束（由代码体现）**：`transformer_dl` 策略的导入采用 try/except ImportError 模式，使主进程可在缺少 PyTorch 的情况下正常启动；仅在调用该策略时才抛出 `ImportError`。
- **约束（由代码体现）**：`BacktestEngine.run` 对所有浮点列执行 `fillna(0).replace([np.inf, -np.inf], 0)`，确保返回给前端的 equity_curve/signal 数据不含 NaN/Inf，避免 JSON 序列化失败。

## 5. 不足与缺口

- 没有统一的错误码体系（如 `ErrorCode.NOT_FOUND`、`ErrorCode.DATA_SOURCE_ERROR`），错误信息以字符串形式散落。
- 没有全局异常处理器（`@app.exception_handler`），不同路由的错误响应格式不完全一致（有的返回 `detail`，有的返回裸字典）。
- 前端侧未发现统一的错误处理 hook 或 axios interceptor，错误提示分散在各组件中。
- 日志记录未见结构化日志框架（如 `logging`、`structlog`），错误上下文主要依赖 `str(e)` 透传。