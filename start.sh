#!/bin/bash

echo "================================"
echo "量化策略查看系统 - 启动脚本"
echo "================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "错误: 未找到 Python3，请先安装 Python3"
    exit 1
fi

# 检查Node
if ! command -v node &> /dev/null; then
    echo "错误: 未找到 Node，请先安装 Node.js"
    exit 1
fi

echo "✓ Python3: $(python3 --version)"
echo "✓ Node: $(node --version)"
echo ""

# 启动后端
echo "正在启动后端服务..."
cd backend

if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
pip install -r requirements.txt -q

echo "后端服务将在 http://localhost:8000 启动"
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!

cd ..

# 启动前端
echo "正在启动前端服务..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi

echo "前端服务将在 http://localhost:3000 启动"
npm run dev &
FRONTEND_PID=$!

echo ""
echo "================================"
echo "系统启动完成！"
echo "================================"
echo "后端API: http://localhost:8000"
echo "API文档: http://localhost:8000/docs"
echo "前端界面: http://localhost:3000"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo "================================"

# 等待用户中断
trap "kill $BACKEND_PID $FRONTEND_PID 2>/dev/null; exit" INT
wait
