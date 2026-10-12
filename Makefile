.PHONY: check check-backend check-frontend install-deps

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
