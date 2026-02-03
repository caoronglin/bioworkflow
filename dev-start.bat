@echo off
REM BioWorkflow 开发启动脚本 (Windows)

setlocal enabledelayedexpansion

echo 🚀 启动 BioWorkflow 开发环境...

REM 检查 Python 版本
python --version
echo ✓ Python 环境检查完成

REM 检查 Node.js 版本
node --version
echo ✓ Node.js 环境检查完成

REM 创建虚拟环境
if not exist "venv" (
    echo 📦 创建 Python 虚拟环境...
    python -m venv venv
)

REM 激活虚拟环境
call venv\Scripts\activate.bat
echo ✓ 虚拟环境已激活

REM 安装后端依赖
echo 📦 安装后端依赖...
pip install -e ".[dev]"

REM 启动后端
echo 🚀 启动后端服务 (http://localhost:8000)...
cd src\backend
start cmd /k python -m uvicorn main:app --reload

REM 返回到项目根目录
cd ..\..

REM 安装前端依赖
if not exist "src\frontend\node_modules" (
    echo 📦 安装前端依赖...
    cd src\frontend
    call npm install
    cd ..\..
)

REM 启动前端
echo 🚀 启动前端开发服务 (http://localhost:5173)...
cd src\frontend
start cmd /k npm run dev

cd ..\..

echo.
echo ✨ 开发环境启动完成!
echo.
echo 📝 服务地址:
echo    后端 API: http://localhost:8000
echo    API 文档: http://localhost:8000/docs
echo    前端应用: http://localhost:5173
echo.
