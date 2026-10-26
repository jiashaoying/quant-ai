---
kind: configuration_system
name: 基于 pydantic-settings 的环境配置系统
slug: configuration_system
category: configuration_system
scope:
    - '**'
---

## 1. 使用的系统与工具

后端采用 **pydantic-settings**（`BaseSettings`）作为统一的配置加载器，前端通过 Vite 的 `vite.config.ts` 进行构建期配置。项目没有使用 `.env` 文件以外的外部配置文件格式（如 YAML/TOML），也没有引入环境变量注入框架或密钥管理服务。

## 2. 关键文件

- `backend/app/core/config.py` — 唯一的配置定义入口，导出全局 `settings` 单例
- `backend/main.py` — FastAPI 应用启动，导入并使用 `settings`
- `backend/app/db/database.py` — 通过 `settings.DATABASE_URL` 创建 SQLAlchemy engine
- `frontend/vite.config.ts` — 前端开发服务器端口与 API 代理配置
- `backend/requirements.txt` — 声明依赖 `pydantic-settings==2.1.0`

## 3. 架构与设计约定

### 3.1 配置类结构

`app.core.config.Settings` 继承自 `pydantic_settings.BaseSettings`，所有字段均为可选默认值：

| 字段 | 类型 | 默认值 | 用途 |
|---|---|---:|---|
| `APP_NAME` | `str` | `"量化策略查看系统"` | 应用名称 |
| `APP_VERSION` | `str` | `"1.0.0"` | 应用版本 |
| `DEBUG` | `bool` | `True` | 调试开关 |
| `DATABASE_URL` | `str` | `"sqlite:///./quant.db"` | SQLite 数据库连接串 |
| `DEFAULT_MARKET` | `str` | `"CN"` | 默认市场（CN / US / HK） |

`class Config.env_file = ".env"` 指定从同目录下的 `.env` 文件读取环境变量覆盖。

### 3.2 加载顺序

pydantic-settings 遵循标准优先级：**`.env` 文件 < 进程环境中的同名变量**。新增配置项只需在 `Settings` 中声明字段即可自动支持两种来源。

### 3.3 消费方式

模块通过 `from app.core.config import settings` 获取全局单例，当前被以下位置引用：
- `backend/main.py`：FastAPI 初始化时传入 title/description/version
- `backend/app/db/database.py`：构造 SQLAlchemy `create_engine(settings.DATABASE_URL, ...)`，并附带 SQLite 专用 `connect_args={"check_same_thread": False}`

### 3.4 前端配置

`frontend/vite.config.ts` 将开发服务器端口固定为 `3000`，并通过 Vite proxy 将 `/api` 请求转发到 `http://localhost:8000`（后端默认端口）。该配置是硬编码的，未暴露为可覆盖的环境变量。

## 4. 约定与约束

- **单一配置源**：所有运行时配置集中在 `app.core.config.Settings` 一个类中，其他模块不得自行解析环境变量。
- **默认值优先**：每个配置字段都提供合理默认值，使项目无需 `.env` 文件即可直接运行（SQLite + DEBUG=True）。
- **`.env` 文件约定**：位于 `backend/` 目录下，键名与 `Settings` 字段名一一对应（如 `DATABASE_URL=...`、`DEFAULT_MARKET=HK`）。
- **数据库 URL 规范**：通过 SQLAlchemy 的 `create_engine` 接受任意连接字符串；默认值为 SQLite 本地文件 `./quant.db`，并在连接参数中显式开启 `check_same_thread=False` 以适配多线程访问。
- **市场枚举约定**：`DEFAULT_MARKET` 仅允许 `CN`、`US`、`HK` 三个值（由注释说明），但当前代码层面无运行时校验，属于文档型约定。
- **前端代理路径约定**：前端只代理 `/api` 前缀的请求到后端，因此后端路由必须以 `/api/...` 开头（当前 `strategies`、`backtest`、`market` 路由均遵守此约定）。
- **无 secrets 管理**：未发现任何加密密钥、第三方服务凭据或 secret 管理集成；敏感信息若需接入，应按现有模式添加到 `Settings` 并通过 `.env` 注入。
- **无 feature flag 机制**：当前没有功能开关或灰度发布相关的配置项。