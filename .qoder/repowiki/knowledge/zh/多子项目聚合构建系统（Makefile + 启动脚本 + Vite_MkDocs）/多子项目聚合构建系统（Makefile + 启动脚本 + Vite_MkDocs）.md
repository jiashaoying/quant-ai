---
kind: build_system
name: 多子项目聚合构建系统（Makefile + 启动脚本 + Vite/MkDocs）
category: build_system
scope:
    - '**'
source_files:
    - Makefile
    - start.sh
    - start.bat
    - backend/requirements.txt
    - backend/pytest.ini
    - frontend/package.json
    - frontend/vite.config.ts
    - wiki-site/build.py
    - wiki-site/mkdocs.yml
---

## 1. 总体方案

仓库采用**多子项目聚合构建**：后端 Python FastAPI、前端 React+Vite、文档站 MkDocs 各自独立管理依赖，由顶层 `Makefile` 与 `start.sh`/`start.bat` 统一编排。

- 后端：`backend/requirements.txt` 通过 `pip` 安装，运行入口 `uvicorn main:app --reload --port 8000`。
- 前端：`frontend/package.json` 通过 `npm` 管理，开发服务器 `vite`，构建命令 `tsc && vite build`。
- 文档站：`wiki-site/build.py` 是 MkDocs 的自定义构建管线，负责把 `.qoder/repowiki/zh/content` 下的 Markdown 转换为静态站点。

没有 Dockerfile、CI 配置或发布流水线文件；部署说明仅存在于已生成的 wiki 静态页面中。