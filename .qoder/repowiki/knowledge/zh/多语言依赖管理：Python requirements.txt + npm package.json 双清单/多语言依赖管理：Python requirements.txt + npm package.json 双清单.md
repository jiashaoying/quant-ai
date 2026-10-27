---
kind: dependency_management
name: 多语言依赖管理：Python requirements.txt + npm package.json 双清单
category: dependency_management
scope:
    - '**'
source_files:
    - backend/requirements.txt
    - frontend/package.json
    - frontend/package-lock.json
    - wiki-site/requirements.txt
    - Makefile
---

## 1. 使用的系统与工具

仓库采用**多语言、分模块的依赖声明方式**，每个子项目各自维护独立的包清单与锁文件：

- **后端（Python/FastAPI）**：使用 `pip` + `requirements.txt` 进行依赖声明。
- **前端（React/Vite/TypeScript）**：使用 `npm` + `package.json` + `package-lock.json` 进行依赖声明。
- **Wiki 文档站（MkDocs）**：复用后端 Python 环境中的 `mkdocs-material`，通过顶层 `Makefile` 调用 `backend/venv/bin/python` 执行构建。

没有发现统一的依赖聚合工具（如 `pip-tools`、`poetry`、`pnpm`、`yarn`、`bundler`），也没有私有 PyPI 或 npm registry 的配置（无 `.pypirc`、`.npmrc`、`GOPRIVATE` 等）。

## 2. 关键文件

- `backend/requirements.txt` — 后端 Python 依赖清单。
- `frontend/package.json` — 前端 npm 依赖与脚本定义。
- `frontend/package-lock.json` — npm 依赖锁定文件（已提交到仓库）。
- `wiki-site/requirements.txt` — Wiki 构建所需的 MkDocs 依赖。
- `Makefile` — 统一的依赖安装入口（`install-deps`）与构建/检查命令。

## 3. 架构与约定

### Python 依赖（backend/requirements.txt）

- 依赖以 `==` 精确版本锁定为主（如 `fastapi==0.109.0`、`pydantic==2.5.3`、`pandas==2.1.4`、`numpy==1.26.3`、`plotly==5.18.0`、`sqlalchemy==2.0.25`、`pytest>=7.4.0`）。
- 部分数据源库使用 `>=` 宽松版本约束（`akshare>=1.12.0`、`baostock>=0.8.8`、`torch>=2.0.0`、`scikit-learn>=1.3.0`），以便适配不同硬件环境下的二进制轮子。
- 未使用 `pipenv` / `poetry` / `Pipfile`；虚拟环境目录 `backend/venv/` 存在于仓库中（通常不应被提交，但当前 `.gitignore` 可能未排除它）。
- 没有 `setup.py` / `pyproject.toml` / `requirements-dev.txt`，所有依赖集中在单一 `requirements.txt`。

### Node.js 依赖（frontend/package.json）

- 运行时依赖（`dependencies`）：`react`、`react-dom`、`axios`、`recharts`、`lucide-react`，均使用 `^` 语义化版本范围。
- 开发依赖（`devDependencies`）：`@types/react`、`@types/react-dom`、`@vitejs/plugin-react`、`typescript`、`vite`，同样使用 `^` 范围。
- 提供标准脚本：`dev`、`build`（先 `tsc` 再 `vite build`）、`preview`、`typecheck`、`check`。
- `package-lock.json` 已提交，用于锁定第三方包的精确版本树。

### Wiki 站点依赖

- `wiki-site/requirements.txt` 仅声明 `mkdocs>=1.6.1` 和 `mkdocs-material>=9.5`。
- 构建时不单独创建独立 Python 环境，而是直接复用 `backend/venv/bin/python`（见 `Makefile` 中 `wiki` 和 `wiki-serve` 目标）。

### 统一入口（Makefile）

- `make install-deps` 依次执行 `cd backend && pip install -r requirements.txt` 与 `cd frontend && npm install`，是仓库首次安装依赖的标准入口。
- `make check-backend` 运行 `python -m pytest`，`make check-frontend` 运行 `npx tsc --noEmit`。
- `make wiki` 通过 `../backend/venv/bin/python build.py` 构建静态文档站。

## 4. 约定与约束

- **每个子项目自管依赖**：后端用 `requirements.txt`，前端用 `package.json` + `package-lock.json`，Wiki 用独立的 `requirements.txt`，不存在跨子项目的依赖共享机制。
- **Python 依赖以精确版本为主**：除 akshare/baostock/torch/scikit-learn/pytest 外，其余核心库均使用 `==` 锁定，保证可复现安装。
- **npm 依赖使用语义化版本范围**：全部使用 `^` 前缀，允许小版本升级，由 `package-lock.json` 在 CI/本地安装时解析为确定版本。
- **无私有注册表配置**：未发现 `.pypirc`、`.npmrc`、`pip.conf`、`PYPI_URL` 等私有源配置，默认使用官方 PyPI 与 npm registry。
- **无 vendoring**：未发现 `vendor/`、`third_party/`、`lib/` 等第三方源码内嵌目录；Node 依赖位于 `node_modules/`，Python 依赖通过 pip 安装。
- **依赖安装必须通过 Makefile**：顶层 `Makefile` 是唯一对外暴露的安装入口，直接运行 `pip install` 或 `npm install` 不在文档约定的流程内。