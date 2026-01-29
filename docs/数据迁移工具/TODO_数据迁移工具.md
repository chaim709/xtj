# 待办事项：数据迁移工具

## 需要用户操作的事项

### 1. 安装依赖 ⚠️

```bash
# 题库系统
cd gongkao-tiku-system
pip install -r requirements.txt

# 督学系统
cd gongkao-system
pip install -r requirements.txt
```

### 2. 初始化数据库迁移 ⚠️

首次使用需要初始化迁移目录：

```bash
# 题库系统
cd gongkao-tiku-system
flask db init
flask db migrate -m "初始化迁移"
flask db upgrade

# 督学系统
cd gongkao-system
flask db init
flask db migrate -m "初始化迁移"
flask db upgrade
```

### 3. 测试导出功能

```bash
# 题库系统
cd gongkao-tiku-system
flask migrate status
flask migrate export --format json
ls -la backups/

# 督学系统
cd gongkao-system
flask migrate status
flask migrate export --format json
ls -la backups/
```

## 可选的后续开发

### 优先级高

1. **Web管理界面**
   - 在管理后台添加"数据备份"页面
   - 支持可视化操作导出/导入
   - 显示备份历史

### 优先级中

3. **定时自动备份**
   - 配置cron定时任务
   - 自动清理旧备份

4. **备份文件加密**
   - 敏感数据加密存储
   - 支持密码保护的备份

### 优先级低

5. **云存储支持**
   - 支持备份到云存储（OSS/S3）
   - 远程备份管理

## 文件附件备份

图片等上传文件不在数据库中，需要单独备份：

```bash
# 备份uploads目录
tar -czf uploads_backup.tar.gz uploads/
```

## 配置文件备份

```bash
# 备份配置
cp .env .env.backup
```
