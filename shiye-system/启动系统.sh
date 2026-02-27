#!/bin/bash

# 安徽事业单位智能选岗系统 - 一键启动脚本

echo "=================================="
echo "安徽事业单位智能选岗系统"
echo "=================================="
echo ""

# 进入backend目录
cd "$(dirname "$0")/backend"

# 检查虚拟环境
if [ ! -d "venv" ]; then
    echo "❌ 虚拟环境不存在，正在创建..."
    python3 -m venv venv
    echo "✅ 虚拟环境创建完成"
fi

# 激活虚拟环境
echo "🔄 激活虚拟环境..."
source venv/bin/activate

# 检查依赖
echo "🔄 检查依赖包..."
pip list | grep -q Flask
if [ $? -ne 0 ]; then
    echo "📦 安装依赖包..."
    pip install -r requirements.txt
fi

# 检查数据库
if [ ! -f "../data/database/shiye_dev.db" ]; then
    echo "⚠️ 数据库不存在，正在导入数据..."
    python3 ../scripts/import_positions_simple.py
    python3 ../scripts/optimize_database.py
fi

# 启动服务
echo ""
echo "🚀 启动系统..."
echo "访问地址: http://localhost:5002"
echo "按 Ctrl+C 停止服务"
echo ""

python3 run.py
