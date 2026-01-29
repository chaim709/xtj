#!/bin/bash
# ============================================
# 服务器代码更新脚本
# 每次修改代码后，在服务器上运行此脚本更新
# ============================================

set -e

CODE_DIR="/home/ubuntu/gongkao"

echo "=========================================="
echo "公考系统 - 代码更新"
echo "=========================================="

# 1. 拉取最新代码
echo "[1/3] 拉取最新代码..."
cd $CODE_DIR
git pull origin main

# 2. 更新依赖（如果有新增）
echo "[2/3] 更新 Python 依赖..."
cd $CODE_DIR/gongkao-system
source venv/bin/activate
pip install -r requirements.txt

# 3. 重启服务
echo "[3/3] 重启服务..."
sudo systemctl restart gongkao

echo ""
echo "=========================================="
echo "✅ 更新完成！"
echo "=========================================="
echo "查看服务状态: sudo systemctl status gongkao"
echo "查看日志: sudo journalctl -u gongkao -f"
echo ""
