#!/usr/bin/env bash

# BioWorkflow 开发启动脚本

set -e

echo "🚀 启动 BioWorkflow 开发环境..."

# 检查 Python 版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python 版本: $python_version"

# 检查 Node.js 版本
node_version=$(node --version)
echo "✓ Node.js 版本: $node_version"

# 创建后端环境
if [ ! -d "venv" ]; then
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv venv
fi

source venv/bin/activate
echo "✓ 激活虚拟环境"

# 安装后端依赖
echo "📦 安装后端依赖..."
pip install -e ".[dev]"

# 启动后端
echo "🚀 启动后端服务 (http://localhost:8000)..."
cd src/backend
python -m uvicorn main:app --reload &
BACKEND_PID=$!

# 返回到项目根目录
cd ../..

# 安装前端依赖
if [ ! -d "src/frontend/node_modules" ]; then
    echo "📦 安装前端依赖..."
    cd src/frontend
    npm install
    cd ../..
fi

# 启动前端
echo "🚀 启动前端开发服务 (http://localhost:5173)..."
cd src/frontend
npm run dev &
FRONTEND_PID=$!

cd ../..

echo ""
echo "✨ 开发环境启动完成!"
echo ""
echo "📝 服务地址:"
echo "   后端 API: http://localhost:8000"
echo "   API 文档: http://localhost:8000/docs"
echo "   前端应用: http://localhost:5173"
echo ""
echo "按 Ctrl+C 停止所有服务"
echo ""

# 等待进程
wait
