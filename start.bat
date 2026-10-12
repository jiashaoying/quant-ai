@echo off
echo ================================
echo 量化策略查看系统 - 启动脚本
echo ================================
echo.

REM 检查Python
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python
    pause
    exit /b 1
)

REM 检查Node
node --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Node，请先安装 Node.js
    pause
    exit /b 1
)

echo ✓ Python: 
python --version
echo ✓ Node: 
node --version
echo.

REM 启动后端
echo 正在启动后端服务...
cd backend

if not exist "venv" (
    echo 创建Python虚拟环境...
    python -m venv venv
)

call venv\Scripts\activate
pip install -r requirements.txt -q

echo 后端服务将在 http://localhost:8000 启动
start "Backend" cmd /c "uvicorn main:app --reload --port 8000"

cd ..

REM 启动前端
echo 正在启动前端服务...
cd frontend

if not exist "node_modules" (
    echo 安装前端依赖...
    call npm install
)

echo 前端服务将在 http://localhost:3000 启动
start "Frontend" cmd /c "npm run dev"

echo.
echo ================================
echo 系统启动完成！
echo ================================
echo 后端API: http://localhost:8000
echo API文档: http://localhost:8000/docs
echo 前端界面: http://localhost:3000
echo.
echo 关闭此窗口将停止所有服务
echo ================================
pause
