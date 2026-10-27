---
kind: configuration_system
name: 基于 pydantic-settings 的 .env 配置加载
category: configuration_system
scope:
    - '**'
source_files:
    - backend/app/core/config.py
    - backend/main.py
    - backend/app/db/database.py
---

## 概述

后端采用 **pydantic-settings**（`BaseSettings`）作为唯一的运行时配置入口，通过 `.env` 文件提供键值对覆盖。前端与 Wiki 站点各自使用其生态的标准配置文件（`vite.config.ts`、`mkdocs.yml`），不属于本仓库统一的“应用配置系统”。

## 核心文件

- `backend/app/core/config.py`：定义 `Settings(BaseSettings)` 类，集中声明所有可配置项。
- `backend/main.py`：FastAPI 应用入口，从 `app.core.config` 导入全局 `settings` 实例。
- `backend/app/db/database.py`：读取 `settings.DATABASE_URL` 创建 SQLAlchemy engine。

## 架构与约定

1. **单一 Settings 类**：`backend/app/core/config.py` 中仅有一个 `Settings` 子类 `BaseSettings`，所有配置字段以类属性形式声明，并提供默认值：
   - `APP_NAME: str = "量化策略查看系统"`
   - `APP_VERSION: str = "1.0.0"`
   - `DEBUG: bool = True`
   - `DATABASE_URL: str = "sqlite:///./quant.db"`
   - `DEFAULT_MARKET: str = "CN"`（可选值 CN / US / HK）

2. **环境变量来源**：在 `Settings.Config.env_file = ".env"` 指定根目录下的 `.env` 文件为额外源；除此之外没有显式调用 `os.environ`/`getenv`，因此 pydantic-settings 的默认行为（自动读取 `os.environ`）是实际生效的环境变量来源。

3. **模块级单例**：文件末尾 `settings = Settings()` 暴露一个模块级实例，被 `main.py`、`database.py` 等直接 import 使用，形成全局只读配置对象。

4. **数据库连接**：`database.py` 通过 `create_engine(settings.DATABASE_URL, connect_args={"check_same_thread": False})` 初始化 SQLite engine，并配合 `SessionLocal` 和 `get_db()` 生成器提供依赖注入会话。

5. **前端配置**：`frontend/vite.config.ts` 由 Vite 自行解析，未复用后端 `Settings`；`frontend/package.json`、`tsconfig.json` 属于构建期配置。
6. **Wiki 配置**：`wiki-site/mkdocs.yml` 由 MkDocs 解析，独立于后端配置。

## 约定与约束

- 新增配置项应在 `Settings` 中以类型化属性声明并提供默认值，而非散落在各处 `os.getenv` 调用。（依据：`backend/app/core/config.py` 是唯一集中声明处）
- 运行期覆盖通过 `.env` 文件或进程环境变量实现，因为 `BaseSettings` 同时读取 `os.environ` 且 `env_file = ".env"` 已声明。（依据：`backend/app/core/config.py` L20-L21）
- 数据库 URL 必须遵循 SQLAlchemy DSN 格式，当前默认值为 SQLite 路径 `sqlite:///./quant.db`。（依据：`backend/app/db/database.py` L9-L12）
- `DEFAULT_MARKET` 的取值域为 `CN`、`US`、`HK`，由注释说明。（依据：`backend/app/core/config.py` L18）
- 无多环境（dev/prod）切换机制，无 feature flag 或分层配置合并逻辑；`DEBUG` 默认为 `True`，生产部署需显式覆盖。（依据：`backend/app/core/config.py` L12）
- 无 secrets 管理集成（如 Vault、AWS Secrets Manager），敏感信息应通过环境变量注入。（依据：未发现任何 secrets 相关代码）
