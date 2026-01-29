# 项目总结报告：数据迁移工具

## 1. 项目概述

本项目为公考培训系统实现了完整的数据迁移解决方案，**同时支持题库系统和督学系统**，提供数据导出、导入和版本升级管理功能。

### 支持的系统

| 系统 | 目录 | 说明 |
|------|------|------|
| **题库系统** | `gongkao-tiku-system/` | 题目、练习、错题本等 |
| **督学系统** | `gongkao-system/` | 学员、教师、课程、督学日志等 |

## 2. 实现功能

### 2.1 数据导出

| 功能 | 描述 | 命令示例 |
|------|------|----------|
| 完整导出 | 导出所有数据 | `flask migrate export` |
| JSON格式 | 程序化格式 | `--format json` |
| Excel格式 | 人工可读 | `--format excel` |
| 增量导出 | 指定时间后的数据 | `--since 2026-01-01` |
| 模块化导出 | 只导出指定模块 | `-m questions,users` |

### 2.2 数据导入

| 功能 | 描述 | 命令示例 |
|------|------|----------|
| 文件验证 | 检查格式和版本 | 自动执行 |
| 冲突处理 | skip/overwrite/error | `--conflict skip` |
| 预览模式 | 不实际导入 | `--dry-run` |
| 事务管理 | 失败自动回滚 | 自动执行 |
| ID映射 | 自动处理外键 | 自动执行 |

### 2.3 数据库迁移

| 功能 | 描述 | 命令示例 |
|------|------|----------|
| 初始化 | 创建迁移目录 | `flask db init` |
| 生成迁移 | 生成迁移脚本 | `flask db migrate` |
| 应用迁移 | 升级数据库 | `flask db upgrade` |
| 回滚迁移 | 降级数据库 | `flask db downgrade` |

## 3. 文件结构

### 题库系统

```
gongkao-tiku-system/
├── app/
│   ├── __init__.py              # 添加了migrate初始化
│   └── migrate/                 # 迁移工具模块
│       ├── __init__.py
│       ├── commands.py          # CLI命令
│       ├── exporter.py          # 导出服务
│       ├── importer.py          # 导入服务
│       ├── version.py           # 版本管理
│       ├── utils.py             # 工具函数
│       └── formatters/
│           ├── __init__.py
│           ├── json_formatter.py
│           └── excel_formatter.py
├── backups/                     # 备份文件目录
└── requirements.txt             # 添加了Flask-Migrate
```

### 督学系统

```
gongkao-system/
├── app/
│   ├── __init__.py              # 添加了migrate初始化
│   └── migrate/                 # 迁移工具模块（结构同上）
│       ├── __init__.py
│       ├── commands.py
│       ├── exporter.py
│       ├── importer.py
│       ├── version.py
│       ├── utils.py
│       └── formatters/
│           ├── __init__.py
│           ├── json_formatter.py
│           └── excel_formatter.py
├── backups/                     # 备份文件目录
└── requirements.txt             # 添加了Flask-Migrate
```

## 4. 使用指南

### 4.1 安装依赖

```bash
# 题库系统
cd gongkao-tiku-system
pip install -r requirements.txt

# 督学系统
cd gongkao-system
pip install -r requirements.txt
```

### 4.2 初始化数据库迁移（首次使用）

```bash
flask db init
flask db migrate -m "初始化"
flask db upgrade
```

### 4.3 日常备份

```bash
# 完整备份
flask migrate export --format json -o backups/daily_backup.json

# 增量备份（只备份今天的变更）
flask migrate export --since $(date -v-1d +%Y-%m-%dT00:00:00)
```

### 4.4 版本升级流程

1. **备份数据**
   ```bash
   flask migrate export -o backup_before_upgrade.json
   ```

2. **升级代码**（拉取新版本代码）

3. **升级数据库**
   ```bash
   flask db upgrade
   ```

4. **验证数据**
   ```bash
   flask migrate status
   ```

### 4.5 数据迁移（换服务器/换系统）

1. **在旧系统导出**
   ```bash
   flask migrate export --format json -o full_backup.json
   ```

2. **在新系统导入**
   ```bash
   # 先初始化数据库
   flask db init
   flask db upgrade
   
   # 导入数据
   flask migrate import full_backup.json
   ```

## 5. 支持的数据模块

### 题库系统（14个模块）

| 模块 | 中文名 | 说明 |
|------|--------|------|
| users | 用户 | 账号信息 |
| categories | 分类 | 三级题目分类 |
| question_books | 题本 | 题目集合 |
| questions | 题目 | 核心题目数据 |
| practice_tasks | 练习任务 | 督学布置的任务 |
| student_submissions | 学员提交 | 扫码提交记录 |
| practices | 练习记录 | 在线练习 |
| practice_details | 答题详情 | 每题作答记录 |
| mistakes | 错题本 | 学员错题 |
| weaknesses | 薄弱项 | 知识点掌握情况 |
| knowledge_points | 知识点 | 知识库 |
| question_knowledge | 题目知识点 | 关联关系 |
| exam_papers | 试卷 | 套卷 |
| study_materials | 学习资料 | 讲义等 |

### 督学系统（22个模块）

| 模块 | 中文名 | 说明 |
|------|--------|------|
| users | 用户 | 管理员账号 |
| teachers | 教师 | 教师信息 |
| subjects | 科目 | 科目设置 |
| projects | 项目 | 项目管理 |
| packages | 套餐 | 套餐设置 |
| class_types | 班型 | 班型配置 |
| class_batches | 班次 | 班次管理 |
| schedules | 课表 | 课程安排 |
| schedule_change_logs | 调课记录 | 调课历史 |
| course_recordings | 课程录播 | 录播信息 |
| weakness_tags | 薄弱标签 | 学员薄弱项标签 |
| module_categories | 题型分类 | 题型分类配置 |
| students | 学员 | 学员信息 |
| student_batches | 学员班次 | 学员-班次关联 |
| supervision_logs | 督学日志 | 督学记录 |
| homework_tasks | 作业任务 | 布置的作业 |
| homework_submissions | 作业提交 | 学员提交 |
| attendances | 考勤记录 | 出勤情况 |
| study_plans | 学习计划 | 个性化计划 |
| plan_goals | 计划目标 | 计划目标设定 |
| plan_tasks | 计划任务 | 计划任务项 |
| plan_progresses | 计划进度 | 进度记录 |

## 6. 注意事项

1. **密码安全**：导出时自动排除用户密码字段，导入后需要用户重置密码
2. **文件附件**：图片等附件文件需要单独备份uploads目录
3. **配置文件**：.env配置文件需要单独备份

## 7. 后续扩展

### 7.1 已规划功能

- Web管理界面（在管理后台添加备份管理页面）
- 定时自动备份
- 备份文件加密
- 云存储支持

### 7.2 版本迁移扩展

当数据结构发生变化时，需要在 `version.py` 中添加迁移函数：

```python
# 示例：从1.0升级到1.1
def migrate_1_0_to_1_1(data):
    # 添加新字段的默认值
    for question in data['data'].get('questions', []):
        question['new_field'] = 'default_value'
    return data
```
