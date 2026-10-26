---
kind: dependency_management
name: 依赖管理 — requirements.txt + package.json 双端声明式锁定
slug: dependency_management
category: dependency_management
scope:
    - '**'
---

## 1. 使用的系统/方案

仓库采用**前后端分离、各自独立声明依赖**的方式：
- 后端（Python/FastAPI）：使用 `pip` + `requirements.txt`，通过 `==` 精确锁定版本。
- 前端（React/Vite/TypeScript）：使用 `npm` + `package.json`，依赖版本以 `^` 语义化范围声明，并由 `package-lock.json` 生成锁文件固定实际解析结果。
- 顶层 `Makefile` 提供统一的 `install-deps` 入口，同时调用 `pip install -r requirements.txt` 与 `npm install`。

未使用任何私有注册表、vendor 目录或代理配置；也未见 `pyproject.toml`、`poetry.lock`、`pnpm-lock.yaml` 等替代工具。后端存在 `backend/venv/` 目录（虚拟环境），但不在版本控制中（被 `.gitignore` 忽略）。前端依赖位于 `frontend/node_modules/`，同样被忽略。

## 2. 关键文件

- `backend/requirements.txt`：后端全部运行时与测试依赖的声明与锁定。
- `frontend/package.json`：前端运行时依赖（`dependencies`）与开发依赖（`devDependencies`）的声明。
- `frontend/package-lock.json`：npm 生成的确定性锁文件。
- `Makefile`：统一安装与检查入口。

## 3. 架构与约定

### 后端（Python）
- 所有依赖集中在 `backend/requirements.txt`，无子包级 `requirements*.txt`。
- 依赖分为两类：
  - **精确锁定**（`==`）：FastAPI、Uvicorn、Pydantic、Pandas、NumPy、YFinance、Plotly、SQLAlchemy、python-multipart 等核心库均使用 `==` 固定到具体小版本。
  - **最小版本约束**（`>=`）：`akshare>=1.12.0`、`baostock>=0.8.8`、`torch>=2.0.0`、`scikit-learn>=1.3.0`、`pytest>=7.4.0`，允许上游补丁更新。
- 不存在 `setup.py` / `pyproject.toml` 中的 `install_requires`，项目以脚本方式运行（`main.py`），而非作为可安装包分发。
- 本地虚拟环境路径 `backend/venv/` 存在于工作区但被 `.gitignore` 排除，不纳入版本控制。

### 前端（Node.js）
- `package.json` 将依赖拆分为 `dependencies`（react、axios、recharts、lucide-react）与 `devDependencies`（@types/*、typescript、vite、@vitejs/plugin-react）。
- 所有版本均以 `^` 语义化范围声明，由 `package-lock.json` 在首次 `npm install` 时解析并锁定实际下载版本。
- 构建脚本 `build` 先执行 `tsc` 再 `vite build`，类型检查通过 `typecheck` / `check` 脚本单独触发。

### 顶层编排
- `Makefile` 定义 `install-deps`、`check-backend`（`cd backend && python -m pytest`）、`check-frontend`（`cd frontend && npx tsc --noEmit`）三个目标，作为跨语言依赖安装与验证的统一入口。

## 4. 约定与约束

- **后端依赖必须声明在 `backend/requirements.txt`**：这是 pip 安装的唯一清单，Makefile 的 `install-deps` 仅读取该文件。
- **后端核心库使用 `==` 精确版本锁定**：从 `requirements.txt` 可见 FastAPI、uvicorn、pydantic、pandas、numpy、yfinance、plotly、sqlalchemy、python-multipart 均使用 `==`，确保复现一致性。
- **数据源与 ML 库使用 `>=` 放宽约束**：`akshare`、`baostock`、`torch`、`scikit-learn`、`pytest` 使用 `>=`，以便获取上游修复而不阻塞升级。
- **前端依赖不得直接修改 `package-lock.json`**：应通过 `npm install` 让 npm 自动维护锁文件（npm 默认行为）。
- **虚拟环境与 node_modules 不被版本控制**：`backend/venv/` 与 `frontend/node_modules/` 均在 `.gitignore` 中，新克隆仓库需通过 `make install-deps` 重新安装。
- **无私有注册表或镜像配置**：未发现 `.pip.conf`、`pip.conf`、`.npmrc`、`registry` 字段等自定义源配置，依赖均来自 PyPI 与 npm 官方源。
- **无 vendoring**：未见 vendor 目录或源码内嵌第三方代码；所有第三方库通过包管理器拉取。