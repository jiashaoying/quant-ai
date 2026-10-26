---
kind: external_dependency
name: SQLite 本地数据库
slug: sqlite-本地数据库
category: external_dependency
scope:
    - '**'
---

默认 DATABASE_URL=sqlite:///./quant.db，文件位于 backend/quant.db，无需额外数据库服务器；当前主要用于存储策略信息与回测结果，SQLAlchemy ORM 抽象便于后续切换到 PostgreSQL/MySQL。