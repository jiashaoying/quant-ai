.PHONY: check check-backend check-frontend install-deps wiki wiki-serve

# 运行全部验证
check: check-backend check-frontend
	@echo "✅ All checks passed."

# 后端：pytest 测试
check-backend:
	@echo "▶ Running backend tests..."
	cd backend && python -m pytest

# 前端：TypeScript 类型检查
check-frontend:
	@echo "▶ Running frontend type check..."
	cd frontend && npx tsc --noEmit

# 安装依赖（首次使用）
install-deps:
	cd backend && pip install -r requirements.txt
	cd frontend && npm install

# 构建 Repo Wiki 静态文档站（依赖 backend/venv 中的 mkdocs-material）
wiki:
	cd wiki-site && ../backend/venv/bin/python build.py

# 本地预览文档站（http://127.0.0.1:8001）
wiki-serve:
	cd wiki-site && ../backend/venv/bin/python -m mkdocs serve -f mkdocs.yml -a 127.0.0.1:8001
