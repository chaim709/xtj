#!/bin/bash
# ============================================
# 题库数据上传脚本
# 在本地电脑（Mac）上运行此脚本上传数据到服务器
# ============================================

# ⚠️ 使用前请修改以下配置 ⚠️
SERVER_IP="你的服务器IP"           # 例如: 123.45.67.89
SERVER_USER="ubuntu"               # 服务器用户名
SERVER_DATA_DIR="/home/ubuntu/gongkao-data"

# 本地数据目录（相对于项目根目录）
LOCAL_PROJECT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "=========================================="
echo "公考系统 - 题库数据上传"
echo "=========================================="
echo "服务器: $SERVER_USER@$SERVER_IP"
echo "本地目录: $LOCAL_PROJECT_DIR"
echo ""

# 检查配置
if [ "$SERVER_IP" = "你的服务器IP" ]; then
    echo "❌ 错误：请先编辑此脚本，修改 SERVER_IP 为你的服务器IP"
    echo "   运行: nano scripts/deploy/upload-data.sh"
    exit 1
fi

echo "选择要上传的内容："
echo "1) 上传解析后的题目数据 (parsed/)"
echo "2) 上传原始题库文件 (公考培训机构管理系统/)"
echo "3) 上传全部数据"
echo "4) 退出"
echo ""
read -p "请选择 [1-4]: " choice

case $choice in
    1)
        echo ""
        echo "正在上传解析后的题目数据..."
        rsync -avz --progress \
            "$LOCAL_PROJECT_DIR/cuoti-system/data/parsed/" \
            "$SERVER_USER@$SERVER_IP:$SERVER_DATA_DIR/parsed/"
        ;;
    2)
        echo ""
        echo "正在上传原始题库文件..."
        rsync -avz --progress \
            "$LOCAL_PROJECT_DIR/公考培训机构管理系统/" \
            "$SERVER_USER@$SERVER_IP:$SERVER_DATA_DIR/question-bank/"
        ;;
    3)
        echo ""
        echo "正在上传全部数据..."
        
        echo "[1/2] 上传解析后的题目数据..."
        rsync -avz --progress \
            "$LOCAL_PROJECT_DIR/cuoti-system/data/parsed/" \
            "$SERVER_USER@$SERVER_IP:$SERVER_DATA_DIR/parsed/"
        
        echo "[2/2] 上传原始题库文件..."
        rsync -avz --progress \
            "$LOCAL_PROJECT_DIR/公考培训机构管理系统/" \
            "$SERVER_USER@$SERVER_IP:$SERVER_DATA_DIR/question-bank/"
        ;;
    4)
        echo "已退出"
        exit 0
        ;;
    *)
        echo "无效选择"
        exit 1
        ;;
esac

echo ""
echo "=========================================="
echo "✅ 上传完成！"
echo "=========================================="
