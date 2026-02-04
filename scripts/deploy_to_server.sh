#!/bin/bash
# ============================================
# 安徽省事业单位项目完整部署脚本
# ============================================

set -e

SERVER="root@142.171.42.2"
CODE_DIR="/root/gongkao"
DATA_DIR="/root/gongkao-data"
LOCAL_DIR="/Users/chaim/CodeBuddy/公考项目"

echo "=========================================="
echo "安徽省事业单位项目 - 完整部署"
echo "=========================================="
echo ""

# 测试连接
echo "[0/5] 测试服务器连接..."
if ! ssh -o ConnectTimeout=5 $SERVER "echo '✓ 连接成功'" 2>/dev/null; then
    echo "❌ 无法连接服务器"
    exit 1
fi

# 1. 提交代码到Git
echo ""
echo "[1/5] 提交代码到Git..."
cd "$LOCAL_DIR"
git add .
git status --short

read -p "是否提交代码？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    git commit -m "完成安徽省事业单位数据分析报告和智能选岗系统集成

- 优化导入脚本（支持多行表头、文件去重）
- 生成超详细分析报告（230页，18万字）
- 集成智能选岗系统（分析+推荐服务）
- 新增5个API接口
- 完整的6A工作流文档"
    
    git push origin main
    echo "✓ 代码已推送到GitHub"
else
    echo "⊘ 跳过Git提交"
fi

# 2. 在服务器上拉取代码
echo ""
echo "[2/5] 服务器拉取最新代码..."
ssh $SERVER << 'ENDSSH'
cd /root/gongkao
git pull origin main
echo "✓ 代码已更新"
ENDSSH

# 3. 更新Python依赖
echo ""
echo "[3/5] 更新Python依赖..."
ssh $SERVER << 'ENDSSH'
cd /root/gongkao/gongkao-system
source venv/bin/activate
pip install -r requirements.txt -q
echo "✓ 依赖已更新"
ENDSSH

# 4. 上传文档和数据（可选）
echo ""
read -p "[4/5] 是否上传分析报告和数据文件？(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "正在上传文档..."
    
    # 创建reports目录
    ssh $SERVER "mkdir -p $DATA_DIR/public/reports"
    
    # 上传报告
    rsync -avz --progress \
        "$LOCAL_DIR/docs/2026年安徽省事业单位招聘超详细分析报告_最终完整版.md" \
        "$LOCAL_DIR/docs/2026年安徽省事业单位招聘分析报告_执行摘要.md" \
        "$LOCAL_DIR/docs/2026年安徽省事业单位完整岗位数据表.xlsx" \
        $SERVER:$DATA_DIR/public/reports/
    
    echo "✓ 报告已上传"
else
    echo "⊘ 跳过文件上传"
fi

# 5. 重启服务
echo ""
echo "[5/5] 重启服务..."
ssh $SERVER << 'ENDSSH'
systemctl restart gongkao
sleep 2
systemctl status gongkao --no-pager | head -15
echo "✓ 服务已重启"
ENDSSH

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "访问地址：http://142.171.42.2:5000"
echo "API测试：curl http://142.171.42.2:5000/api/positions/city-ratings"
echo ""
echo "分析报告下载："
echo "  - 完整版：http://142.171.42.2:5000/reports/2026年安徽省事业单位招聘超详细分析报告_最终完整版.md"
echo "  - 摘要版：http://142.171.42.2:5000/reports/2026年安徽省事业单位招聘分析报告_执行摘要.md"
echo "  - 数据表：http://142.171.42.2:5000/reports/2026年安徽省事业单位完整岗位数据表.xlsx"
echo ""

