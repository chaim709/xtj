#!/bin/bash
# ============================================
# 服务器首次部署脚本
# 在服务器上运行此脚本完成初始化
# ============================================

set -e

echo "=========================================="
echo "公考系统 - 服务器首次部署"
echo "=========================================="

# 配置（根据你的实际情况修改）
GITHUB_REPO="https://github.com/chaim709/xtj.git"
CODE_DIR="/home/ubuntu/gongkao"
DATA_DIR="/home/ubuntu/gongkao-data"

# 1. 安装基础依赖
echo "[1/6] 安装系统依赖..."
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx

# 2. 创建目录
echo "[2/6] 创建项目目录..."
mkdir -p $CODE_DIR
mkdir -p $DATA_DIR/{question-bank,parsed,uploads,images,database}

# 3. 克隆代码
echo "[3/6] 克隆代码仓库..."
if [ -d "$CODE_DIR/.git" ]; then
    echo "代码已存在，执行更新..."
    cd $CODE_DIR && git pull
else
    git clone $GITHUB_REPO $CODE_DIR
fi

# 4. 创建 Python 虚拟环境
echo "[4/6] 配置 Python 环境..."
cd $CODE_DIR/gongkao-system
python3.11 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # 生产服务器

# 5. 创建环境变量文件
echo "[5/6] 创建配置文件..."
if [ ! -f "$CODE_DIR/.env" ]; then
    cat > $CODE_DIR/.env << 'ENVFILE'
# Flask 配置
FLASK_ENV=production
SECRET_KEY=change-this-to-a-random-string-in-production

# 数据目录
DATA_ROOT=/home/ubuntu/gongkao-data
QUESTION_BANK_PATH=/home/ubuntu/gongkao-data/question-bank
PARSED_DATA_PATH=/home/ubuntu/gongkao-data/parsed
UPLOAD_PATH=/home/ubuntu/gongkao-data/uploads
DATABASE_PATH=/home/ubuntu/gongkao-data/database
ENVFILE
    echo "已创建 .env 文件，请编辑修改 SECRET_KEY"
fi

# 6. 创建 systemd 服务
echo "[6/6] 创建系统服务..."
sudo tee /etc/systemd/system/gongkao.service > /dev/null << 'SERVICE'
[Unit]
Description=公考培训管理系统
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/gongkao/gongkao-system
Environment="PATH=/home/ubuntu/gongkao/gongkao-system/venv/bin"
ExecStart=/home/ubuntu/gongkao/gongkao-system/venv/bin/gunicorn -w 4 -b 0.0.0.0:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

sudo systemctl daemon-reload
sudo systemctl enable gongkao

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 编辑配置: nano $CODE_DIR/.env"
echo "2. 上传题库数据（在本地电脑运行上传脚本）"
echo "3. 启动服务: sudo systemctl start gongkao"
echo "4. 查看状态: sudo systemctl status gongkao"
echo "5. 访问系统: http://服务器IP:5000"
echo ""
