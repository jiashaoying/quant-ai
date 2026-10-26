---
kind: build_system
name: 构建与本地开发工作区（Makefile + 启动脚本 + Vite/Pytest）
slug: build_system
category: build_system
scope:
    - '**'
---

## 1. 使用的系统与工具

仓库采用**双端独立构建、根目录统一编排**的模式：
- 后端（Python/FastAPI）：依赖 `requirements.txt`，通过 `uvicorn` 运行，测试使用 `pytest`。
- 前端（React/Vite/TypeScript）：依赖 `package.json`，通过 `vite dev` 启动开发服务器，`tsc` 做类型检查。
- 根目录 `Makefile` 提供跨子项目的统一入口；`start.sh` / `start.bat` 提供一键启动前后端的本地开发流程。
- 无 Dockerfile、CI 流水线、发布脚本或版本化产物——当前构建系统仅覆盖本地开发与验证。

## 2. 关键文件

- `Makefile`：顶层任务入口（`check` / `check-backend` / `check-frontend` / `install-deps`）。
- `start.sh`（Linux/macOS）与 `start.bat`（Windows）：环境检测 → 创建 Python venv → 安装依赖 → 并行启动后端（`uvicorn main:app --reload --port 8000`）和前端（`npm run dev`），并在退出时清理子进程。
- `backend/requirements.txt`：后端依赖清单（fastapi、uvicorn、pydantic、pandas、yfinance、plotly、sqlalchemy、akshare、baostock、torch、scikit-learn、pytest）。
- `backend/pytest.ini`：pytest 配置（`testpaths=tests`，命名约定 `test_*.py` / `Test*`，默认 `-v --tb=short`）。
- `frontend/package.json`：Vite 脚本（`dev` / `build` / `preview` / `typecheck` / `check`）。
- `frontend/vite.config.ts`：开发服务器端口 `3000`，并将 `/api` 代理到 `http://localhost:8000`。

## 3. 架构与约定

### 3.1 分层职责
- **根层**：只放跨项目编排脚本（`Makefile`、`start.sh`、`start.bat`），不持有业务代码。
- **后端层**：`backend/` 内自包含 FastAPI 应用、策略引擎、数据源服务、SQLAlchemy 模型及 `tests/`。
- **前端层**：`frontend/` 内自包含 React 源码、Vite 配置、TS 配置。

### 3.2 依赖管理
- 后端使用固定版本锁定（`==`）+ 部分宽松下限（`>=`，如 akshare、baostock、torch、scikit-learn、pytest），由 `pip install -r requirements.txt` 安装。
- 前端使用 npm lockfile（`package-lock.json`），依赖以 `^` 语义化版本声明。
- `Makefile install-deps` 同时执行 `pip install -r requirements.txt` 与 `npm install`，作为首次初始化入口。

### 3.3 开发启动流程
`start.sh` / `start.bat` 的标准化步骤：
1. 检测 `python3` / `node` 是否存在，不存在则报错退出。
2. 进入 `backend/`，若 `venv` 不存在则 `python3 -m venv venv`，激活后 `pip install -r requirements.txt -q`。
3. 后台启动 `uvicorn main:app --reload --port 8000`。
4. 进入 `frontend/`，若 `node_modules` 不存在则 `npm install`。
5. 后台启动 `npm run dev`（监听 3000 端口）。
6. 通过 `trap`（sh）或 `start "Backend"/"Frontend" cmd /c ...`（bat）在用户中断时清理子进程。

### 3.4 验证流程
`make check` 串行执行：
- `check-backend`：`cd backend && python -m pytest`
- `check-frontend`：`cd frontend && npx tsc --noEmit`
两者均成功才输出 `✅ All checks passed.`。

### 3.5 前后端通信约定
- 后端默认监听 `http://localhost:8000`，OpenAPI 文档位于 `/docs`。
- 前端开发服务器监听 `http://localhost:3000`，并通过 Vite proxy 将 `/api` 请求转发到后端 8000 端口（`changeOrigin: true`）。
- 前端组件通过 axios 调用 `/api/...` 路径访问后端 API。

## 4. 约定与约束

- **约定（观察到的模式）**：
  - 所有可执行入口集中在根目录（`Makefile`、`start.sh`、`start.bat`），子项目不暴露自己的顶层 CLI。
  - 后端测试遵循 pytest 默认命名规范：文件 `test_*.py`、类 `Test*`、函数 `test_*`，存放于 `backend/tests/`。
  - 前端类型检查通过 `npm run typecheck`（即 `tsc --noEmit`），与 `make check-frontend` 等价。
  - 后端依赖使用 `requirements.txt` 而非 pyproject.toml / poetry。
  - 前端构建产物由 Vite 生成到 `frontend/dist/`（由 `vite build` 默认行为决定）。

- **规则（被强制或明确声明）**：
  - `pytest.ini` 显式规定测试路径为 `tests`、文件匹配 `test_*.py`、类名匹配 `Test*`、函数名匹配 `test_*`，并默认启用 `-v --tb=short`。
  - `start.sh` 在找不到 `python3` 或 `node` 时直接 `exit 1`，强制要求运行环境存在这两个解释器。
  - `start.sh` 通过 `trap` 在收到 `INT` 信号时 `kill $BACKEND_PID $FRONTEND_PID`，保证子进程随主脚本退出。
  - `vite.config.ts` 将 `/api` 代理目标硬编码为 `http://localhost:8000`，开发期前端必须与后端同机运行。
  - `Makefile` 中 `check-backend` 与 `check-frontend` 是 `.PHONY` 目标，每次都会重新执行，不会缓存上次结果。

- **缺失项（当前未实现）**：
  - 无 Dockerfile / docker-compose，无法容器化部署。
  - 无 CI 配置文件（GitHub Actions / GitLab CI 等），未在远端自动触发构建或测试。
  - 无发布脚本、版本号集中管理、产物签名或镜像推送流程。
  - 无跨平台编译（本项目不涉及 C/C++ 扩展编译）。