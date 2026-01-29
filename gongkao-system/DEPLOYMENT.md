# 公考培训管理系统 - 部署文档

> **警告**: 部署前必须阅读并严格按照此文档执行，违反流程可能导致数据丢失！

## 服务器信息

| 项目 | 内容 |
|------|------|
| 服务器 | RackNerd VPS |
| SSH别名 | racknerd |
| 项目路径 | `/var/www/gongkao-system/gongkao-system` |
| 域名 | https://shxtj.chaim.top |
| 服务名 | gongkao.service |
| GitHub仓库 | https://github.com/chaim709/xtj.git |

## 目录结构

```
/var/www/gongkao-system/          # Git仓库根目录
├── gongkao-system/               # Flask应用目录
│   ├── app/                      # 应用代码
│   ├── data/                     # 【重要】数据库目录，禁止删除！
│   │   └── dev.db                # SQLite数据库文件
│   ├── venv/                     # Python虚拟环境
│   ├── run.py                    # 启动文件
│   └── ...
└── ...
```

---

## 常规更新流程（代码更新）

### 步骤1: 本地提交代码

```bash
cd /Users/chaim/CodeBuddy/公考项目/gongkao-system
git add .
git commit -m "更新说明"
git push origin main
```

### 步骤2: 服务器拉取更新

```bash
ssh racknerd "cd /var/www/gongkao-system && git pull origin main"
```

### 步骤3: 重启服务

```bash
ssh racknerd "systemctl restart gongkao"
```

### 步骤4: 验证服务状态

```bash
ssh racknerd "systemctl status gongkao --no-pager"
```

---

## 数据库迁移流程

> 当有新的数据库表或字段变更时执行

### 步骤1: 先备份数据库

```bash
ssh racknerd "cp /var/www/gongkao-system/gongkao-system/data/dev.db /var/www/gongkao-system/gongkao-system/data/dev.db.backup.$(date +%Y%m%d_%H%M%S)"
```

### 步骤2: 运行迁移脚本

```bash
ssh racknerd "cd /var/www/gongkao-system/gongkao-system && source venv/bin/activate && python3 迁移脚本名.py"
```

### 步骤3: 重启服务

```bash
ssh racknerd "systemctl restart gongkao"
```

---

## 依赖更新流程

> 当 requirements.txt 有变更时执行

```bash
ssh racknerd "cd /var/www/gongkao-system/gongkao-system && source venv/bin/activate && pip install -r requirements.txt"
ssh racknerd "systemctl restart gongkao"
```

---

## 数据库备份与恢复

### 备份数据库到本地

```bash
scp racknerd:/var/www/gongkao-system/gongkao-system/data/dev.db ./data/dev.db.server_backup
```

### 上传本地数据库到服务器

```bash
# 先备份服务器数据库
ssh racknerd "cp /var/www/gongkao-system/gongkao-system/data/dev.db /var/www/gongkao-system/gongkao-system/data/dev.db.backup.$(date +%Y%m%d_%H%M%S)"

# 上传本地数据库
scp /Users/chaim/CodeBuddy/公考项目/gongkao-system/data/dev.db racknerd:/var/www/gongkao-system/gongkao-system/data/dev.db

# 重启服务
ssh racknerd "systemctl restart gongkao"
```

---

## 完整重新部署（仅首次或灾难恢复）

> ⚠️ **警告**: 此流程会清空所有数据，仅在首次部署或确认要重置时使用！

### 步骤1: 备份现有数据（如果存在）

```bash
ssh racknerd "cp -r /var/www/gongkao-system/gongkao-system/data /root/gongkao-data-backup-$(date +%Y%m%d_%H%M%S)" 2>/dev/null || echo "无现有数据"
```

### 步骤2: 克隆仓库

```bash
ssh racknerd "cd /var/www && rm -rf gongkao-system && git clone https://github.com/chaim709/xtj.git gongkao-system"
```

### 步骤3: 配置虚拟环境

```bash
ssh racknerd "cd /var/www/gongkao-system/gongkao-system && python3 -m venv venv && source venv/bin/activate && pip install -r requirements.txt && pip install gunicorn"
```

### 步骤4: 配置环境变量

```bash
ssh racknerd "cp /var/www/gongkao-system/.env.example /var/www/gongkao-system/gongkao-system/.env"
# 然后编辑 .env 文件配置生产环境参数
```

### 步骤5: 恢复数据库（从备份或本地）

```bash
# 创建data目录
ssh racknerd "mkdir -p /var/www/gongkao-system/gongkao-system/data"

# 选项A: 从备份恢复
ssh racknerd "cp /root/gongkao-data-backup-xxx/dev.db /var/www/gongkao-system/gongkao-system/data/"

# 选项B: 从本地上传
scp /Users/chaim/CodeBuddy/公考项目/gongkao-system/data/dev.db racknerd:/var/www/gongkao-system/gongkao-system/data/
```

### 步骤6: 运行数据库迁移（如需要）

```bash
ssh racknerd "cd /var/www/gongkao-system/gongkao-system && source venv/bin/activate && python3 add_plan_templates_table.py"
```

### 步骤7: 启动服务

```bash
ssh racknerd "systemctl daemon-reload && systemctl restart gongkao && systemctl status gongkao"
```

---

## 常用运维命令

### 查看服务状态

```bash
ssh racknerd "systemctl status gongkao"
```

### 查看日志

```bash
ssh racknerd "journalctl -u gongkao -f"
```

### 重启服务

```bash
ssh racknerd "systemctl restart gongkao"
```

### 停止服务

```bash
ssh racknerd "systemctl stop gongkao"
```

### 查看数据库大小

```bash
ssh racknerd "ls -lh /var/www/gongkao-system/gongkao-system/data/"
```

---

## 禁止操作清单

1. **禁止** 直接删除 `/var/www/gongkao-system` 目录而不备份数据库
2. **禁止** 使用 `rm -rf` 删除项目目录
3. **禁止** 在未备份的情况下执行任何可能影响数据的操作
4. **禁止** 直接覆盖 `data/dev.db` 文件而不先备份

---

## 更新日志

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v1.0.1 | 2026-01-29 | 新增督学管理模块、计划模板、帮助中心 |
| v1.0.0 | 初始版本 | 基础功能 |
