# 公考项目部署指南

## 架构概述

本项目采用 **代码与数据分离** 的部署架构，优化机构内部使用场景：

```
服务器目录结构:
├── /var/www/gongkao/          # 代码目录 (从 GitHub 拉取)
│   ├── gongkao-system/        # 公考培训管理系统
│   ├── cuoti-system/          # 错题收集系统
│   ├── gongkao-zhishiku/      # 知识库系统
│   └── docs/                  # 开发文档
│
└── /data/gongkao/             # 数据目录 (本地存储)
    ├── question-bank/         # 原始题库 (PDF/Word/Excel)
    ├── parsed/                # 解析后的 JSON 数据
    ├── uploads/               # 用户上传文件
    ├── images/                # 题目图片
    └── database/              # SQLite 数据库
```

## 部署步骤

### 1. 服务器环境准备

```bash
# 安装基础依赖
sudo apt update
sudo apt install -y python3.11 python3.11-venv python3-pip git nginx

# 创建目录
sudo mkdir -p /var/www/gongkao
sudo mkdir -p /data/gongkao/{question-bank,parsed,uploads,images,database}
sudo chown -R $USER:$USER /var/www/gongkao /data/gongkao
```

### 2. 拉取代码

```bash
cd /var/www/gongkao
git clone https://github.com/YOUR_USERNAME/gongkao-project.git .
```

### 3. 配置环境

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置（设置数据目录路径等）
nano .env
```

### 4. 安装依赖

```bash
# 公考管理系统
cd /var/www/gongkao/gongkao-system
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 错题系统
cd /var/www/gongkao/cuoti-system
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 5. 上传数据文件

将题库文件通过 SCP/SFTP 上传到服务器：

```bash
# 从本地上传题库到服务器
scp -r ./公考培训机构管理系统/* user@server:/data/gongkao/question-bank/
scp -r ./cuoti-system/data/parsed/* user@server:/data/gongkao/parsed/
```

### 6. 初始化数据库

```bash
cd /var/www/gongkao/gongkao-system
source venv/bin/activate
python init_phase2_db.py
```

### 7. 启动服务

```bash
# 使用 gunicorn 启动
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

## 数据目录说明

| 目录 | 用途 | 备注 |
|------|------|------|
| `question-bank/` | 原始题库文件 | PDF、Word、Excel 格式 |
| `parsed/` | 解析后的结构化数据 | JSON 格式，供系统读取 |
| `uploads/` | 用户上传的文件 | 学员作业、错题截图等 |
| `images/` | 题目配图 | 图形推理等题目的图片 |
| `database/` | SQLite 数据库 | 生产环境可考虑使用 MySQL |

## 数据同步方案

### 方案一：手动同步（推荐小规模）

```bash
# 使用 rsync 同步题库
rsync -avz --progress ./题库文件/ user@server:/data/gongkao/question-bank/
```

### 方案二：自动同步脚本

创建 `sync-data.sh`：

```bash
#!/bin/bash
SERVER="user@your-server.com"
rsync -avz --progress ./公考培训机构管理系统/ $SERVER:/data/gongkao/question-bank/
rsync -avz --progress ./cuoti-system/data/parsed/ $SERVER:/data/gongkao/parsed/
echo "数据同步完成！"
```

## 环境变量配置

在 `.env` 文件中配置数据目录路径：

```env
# 数据目录配置
DATA_ROOT=/data/gongkao
QUESTION_BANK_PATH=/data/gongkao/question-bank
PARSED_DATA_PATH=/data/gongkao/parsed
UPLOAD_PATH=/data/gongkao/uploads
DATABASE_PATH=/data/gongkao/database

# Flask 配置
FLASK_ENV=production
SECRET_KEY=your-secret-key-here

# 数据库配置（生产环境推荐使用 MySQL）
# DATABASE_URL=mysql://user:password@localhost/gongkao
```

## 更新部署

```bash
cd /var/www/gongkao
git pull origin main
# 重启服务
sudo systemctl restart gongkao
```

## 备份策略

```bash
# 备份数据库
pg_dump gongkao > backup_$(date +%Y%m%d).sql

# 备份数据目录
tar -czvf gongkao_data_$(date +%Y%m%d).tar.gz /data/gongkao/
```
