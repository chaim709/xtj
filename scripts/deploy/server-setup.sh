#!/bin/bash
# ============================================
# 服务器首次部署脚本
# 在服务器上运行此脚本完成初始化
# ============================================

set -e

echo "=========================================="
echo "公考系统 - 服务器首次部署"
echo "=========================================="

# 配置
GITHUB_REPO="https://github.com/chaim709/xtj.git"
CODE_DIR="/root/gongkao"
DATA_DIR="/root/gongkao-data"
DOMAIN="shxtj.chaim.top"

# 1. 安装基础依赖
echo "[1/7] 安装系统依赖..."
apt update
apt install -y python3 python3-venv python3-pip git nginx certbot python3-certbot-nginx

# 2. 创建目录
echo "[2/7] 创建项目目录..."
mkdir -p $CODE_DIR
mkdir -p $DATA_DIR/{question-bank,parsed,uploads,images,database}

# 3. 克隆代码
echo "[3/7] 克隆代码仓库..."
if [ -d "$CODE_DIR/.git" ]; then
    echo "代码已存在，执行更新..."
    cd $CODE_DIR && git pull
else
    git clone $GITHUB_REPO $CODE_DIR
fi

# 4. 创建 Python 虚拟环境
echo "[4/7] 配置 Python 环境..."
cd $CODE_DIR/gongkao-system
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
pip install gunicorn  # 生产服务器

# 5. 创建环境变量文件
echo "[5/7] 创建配置文件..."
if [ ! -f "$CODE_DIR/.env" ]; then
    # 生成随机 SECRET_KEY
    SECRET=$(openssl rand -hex 32)
    cat > $CODE_DIR/.env << ENVFILE
# Flask 配置
FLASK_ENV=production
SECRET_KEY=$SECRET

# 数据目录
DATA_ROOT=$DATA_DIR
QUESTION_BANK_PATH=$DATA_DIR/question-bank
PARSED_DATA_PATH=$DATA_DIR/parsed
UPLOAD_PATH=$DATA_DIR/uploads
DATABASE_PATH=$DATA_DIR/database
ENVFILE
    echo "已创建 .env 文件"
fi

# 6. 创建 systemd 服务
echo "[6/7] 创建系统服务..."
cat > /etc/systemd/system/gongkao.service << SERVICE
[Unit]
Description=公考培训管理系统
After=network.target

[Service]
User=root
WorkingDirectory=$CODE_DIR/gongkao-system
Environment="PATH=$CODE_DIR/gongkao-system/venv/bin"
ExecStart=$CODE_DIR/gongkao-system/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable gongkao

# 7. 配置 Nginx 反向代理
echo "[7/7] 配置 Nginx..."
cat > /etc/nginx/sites-available/gongkao << NGINX
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }

    # 静态文件缓存
    location /static {
        alias $CODE_DIR/gongkao-system/app/static;
        expires 7d;
    }

    # 上传文件大小限制
    client_max_body_size 100M;
}
NGINX

ln -sf /etc/nginx/sites-available/gongkao /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default
nginx -t && systemctl reload nginx

echo ""
echo "=========================================="
echo "✅ 部署完成！"
echo "=========================================="
echo ""
echo "下一步操作："
echo "1. 启动服务: systemctl start gongkao"
echo "2. 上传题库数据（在本地电脑运行上传脚本）"
echo "3. 访问系统: http://$DOMAIN"
echo ""
echo "常用命令："
echo "  查看状态: systemctl status gongkao"
echo "  查看日志: journalctl -u gongkao -f"
echo "  重启服务: systemctl restart gongkao"
echo ""
