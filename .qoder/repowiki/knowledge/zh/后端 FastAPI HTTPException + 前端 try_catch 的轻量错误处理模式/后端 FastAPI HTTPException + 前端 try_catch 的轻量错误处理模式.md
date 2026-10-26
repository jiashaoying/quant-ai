---
kind: error_handling
name: 后端 FastAPI HTTPException + 前端 try/catch 的轻量错误处理模式
slug: error_handling
category: error_handling
scope:
    - '**'
---

## 1. 总体方案

该仓库是一个 FastAPI + React/Vite 的前后端聚合项目，**没有统一的异常类体系、错误码枚举或全局异常处理器**。错误处理是分散在每个 API 路由中的：

- **后端**：使用 FastAPI 内置的 `HTTPException`（来自 `fastapi`）将业务异常转换为 HTTP 响应；服务层抛出 Python 原生异常（`ValueError`、`Exception`），由上层 `try/except Exception` 捕获后转为 `HTTPException(status_code=400, detail=str(e))`。
- **前端**：在 `App.tsx` 和 `StrategyList.tsx` 中使用 `try/catch` 包裹 `fetch` 调用，非 `response.ok` 时抛出自定义 `Error('回测失败')`，并在 `catch` 中 `console.error` + `alert` 提示用户。
- **无全局中间件**：`backend/main.py` 仅注册了 `CORSMiddleware`，未注册自定义异常处理中间件或 `@app.exception_handler`。

## 2. 关键文件与位置

| 文件 | 作用 |
|---|---|
| `backend/main.py` | FastAPI 应用入口，仅配置 CORS，无全局异常处理 |
| `backend/app/api/backtest.py` | 回测路由，统一 `try/except Exception` → `HTTPException(400)` |
| `backend/app/api/market.py` | 市场数据路由，同上模式 |
| `backend/app/api/strategies.py` | 策略路由，显式 `raise HTTPException(404, ...)` 表示资源不存在 |
| `backend/app/services/data_source_manager.py` | 多数据源管理器，抛出 `ValueError` / `Exception`，内部各数据源 `try/except` 降级为 mock |
| `backend/app/db/database.py` | SQLAlchemy 会话管理，用 `try/finally` 确保 `db.close()` |
| `frontend/src/App.tsx` | 前端回测请求的错误捕获与用户提示 |
| `frontend/src/components/StrategyList.tsx` | 前端策略列表获取的错误捕获 |

## 3. 架构与约定

### 后端

- **API 层统一兜底**：`backtest.py` 与 `market.py` 中每个可能失败的端点都包裹 `try: ... except Exception as e: raise HTTPException(status_code=400, detail=str(e))`，把任意底层异常统一映射为 400 Bad Request。
- **资源缺失用 404**：`strategies.py` 中找不到策略时直接 `raise HTTPException(status_code=404, detail="Strategy not found")`，这是仓库中唯一使用 404 的地方。
- **参数校验走 Pydantic**：`BacktestRequest` 等模型通过 Pydantic 自动校验，非法输入会触发 FastAPI 默认的 422 响应，无需手动检查。
- **服务层抛原生异常**：`data_source_manager.py` 中未知数据源抛 `ValueError(f"Unknown data source: {source}")`，股票代码转换失败抛 `ValueError(f"无法转换股票代码: {symbol}")`，外部 API 返回错误抛 `Exception(...)`。这些异常最终被 API 层的 `except Exception` 捕获并转成 400。
- **数据源容错降级**：`DataSourceManager._auto_fetch` 依次尝试 tencent → yfinance → akshare → baostock，任一失败 `print` 日志后继续下一个，全部失败则回退到 `_generate_mock_data`，并以 `is_mock=True` 标记返回给前端。
- **数据库连接清理**：`get_db()` 生成器使用 `try/finally` 保证 session 关闭。

### 前端

- **统一 catch 模式**：`App.tsx` 中 `handleBacktest` 对 `fetch` 调用 `try/catch`，`!response.ok` 时 `throw new Error('回测失败')`，`catch` 中 `console.error('回测错误:', error)` + `alert('回测失败，请检查参数')`，并在 `finally` 中重置 loading。
- **组件级错误处理**：`StrategyList.tsx` 中对策略列表获取做同样的 `try/catch` + `console.error` + `alert` 模式。
- **无集中错误边界**：未发现 React Error Boundary 或全局 axios/fetch 拦截器。

## 4. 观察到的约定与约束

- **API 层不直接暴露原始异常**：所有可能抛异常的逻辑都被 `try/except Exception` 包裹，并通过 `HTTPException` 返回结构化 JSON（FastAPI 默认格式 `{"detail": "..."}`）。
- **业务异常类型有限**：目前只使用了 `ValueError`（参数非法）和通用 `Exception`（外部依赖失败），没有自定义异常基类或错误码枚举。
- **HTTP 状态码约定**：400 用于参数/运行时错误，404 用于资源不存在，其余（如 500）依赖 FastAPI 默认行为。
- **前端不解析后端 detail**：前端仅判断 `response.ok`，不读取 `detail` 字段展示给用户，而是显示固定文案 `alert('回测失败，请检查参数')`。
- **无全局异常处理器**：`main.py` 中没有 `@app.exception_handler(Exception)` 或自定义 `exception_handlers`，因此未匹配的异常仍走 FastAPI 默认 500 处理。
- **无 panic/recover 等价物**：Python 侧无 panic；`data_source_manager.py` 使用 try/except 实现“软降级”而非崩溃恢复。
- **CORS 已开启但宽松**：`allow_origins=["*"]`，允许任何来源跨域访问，这在本地开发环境中常见但生产环境需注意安全。