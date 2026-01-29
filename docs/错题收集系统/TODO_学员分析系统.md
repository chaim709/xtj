# 学员分析系统 - 待办事项

> 更新日期：2026-01-29

## 1. 环境配置

### 1.1 Word转PDF功能（可选）

如需使用Word文件自动转PDF功能，需要安装以下任一软件：

| 方式 | 安装命令/说明 |
|------|---------------|
| Microsoft Word | macOS上安装Office套件 |
| LibreOffice | `brew install --cask libreoffice` |

**注意**：如果未安装，系统会提示用户手动转换Word为PDF后再上传。

### 1.2 中文字体

确保 `data/fonts/SourceHanSansSC-Regular.otf` 字体文件存在，否则PDF中的中文可能显示异常。

```bash
# 检查字体
ls -la cuoti-system/data/fonts/
```

## 2. 数据迁移

### 2.1 历史提交记录

现有的5条提交记录没有 `total_attempted` 数据（默认为0），正确率显示为"-"。

**解决方案**：
- 可以手动补充历史数据
- 或者等待新提交自动记录

```sql
-- 示例：为历史记录补充做题数（假设每页8题）
UPDATE submissions 
SET total_attempted = 8, 
    correct_count = 8 - mistake_count,
    accuracy_rate = ROUND((8.0 - mistake_count) / 8 * 100, 1)
WHERE total_attempted = 0 OR total_attempted IS NULL;
```

## 3. 功能优化建议

### 3.1 短期优化

| 优先级 | 功能 | 说明 |
|--------|------|------|
| 高 | 批量导入历史数据 | 支持Excel导入学员历史做题记录 |
| 中 | 学员排行榜 | 按正确率、刷题数排名 |
| 中 | 班级分组 | 支持按班级管理学员 |
| 低 | 微信通知 | 学习报告自动推送 |

### 3.2 长期规划

| 功能 | 说明 |
|------|------|
| 智能推荐 | 根据错题自动推荐练习题 |
| 错题重做 | 定期提醒学员重做错题 |
| 对比分析 | 与班级平均水平对比 |
| 学习计划 | 根据弱项生成学习计划 |

## 4. 运维注意

### 4.1 服务管理

```bash
# 启动服务
cd /Users/chaim/CodeBuddy/公考项目/cuoti-system
python3 run.py

# 后台运行
nohup python3 run.py > /tmp/cuoti.log 2>&1 &

# 停止服务
pkill -f "cuoti-system/run.py"
```

### 4.2 数据备份

```bash
# 备份数据库
cp cuoti-system/data/cuoti.db cuoti-system/data/cuoti_backup_$(date +%Y%m%d).db
```

### 4.3 日志位置

- 应用日志：`/tmp/cuoti.log`
- 生成的PDF：`cuoti-system/data/output/`
- 上传的文件：`cuoti-system/data/uploads/`

## 5. 已知问题

| 问题 | 状态 | 说明 |
|------|------|------|
| 雷达图需要>=3个板块 | 正常 | 板块少于3个时不显示雷达图 |
| Word转PDF需要安装软件 | 正常 | 提示用户手动转换 |
| 首次生成图表较慢 | 正常 | matplotlib首次运行需要构建字体缓存 |

## 6. 联系支持

如有问题，请检查：
1. 服务是否正常运行
2. 数据库是否有数据
3. 字体文件是否存在
4. 日志文件中的错误信息
