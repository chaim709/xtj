# 错题系统与督学系统合并指南

## 当前状态

### 错题系统 (cuoti-system)
- 端口：5005
- 数据库：cuoti_dev.db
- 主要功能：
  - 题目管理和导入
  - 习题册生成（品牌化PDF）
  - 学员扫码提交错题
  - 错题分析和统计
  - 个人错题本和学习报告

### 督学系统 (gongkao-system)
- 端口：5000
- 数据库：data/dev.db
- 主要功能：
  - 学员管理
  - 课程管理
  - 督学日志
  - 作业管理
  - 职位分析

## 已实现的互通

1. **学员数据同步**
   - 错题系统可以从督学系统同步学员
   - 同步API：`/api/sync_students`
   - 配置项：`DUXUE_DB_PATH`

## 合并方案

### 方案一：模块整合（推荐）

将错题系统作为督学系统的一个模块整合进去。

**步骤：**

1. **复制模型**
   ```
   cuoti-system/app/models/ → gongkao-system/app/models/
   - Question (重命名避免冲突)
   - Workbook
   - WorkbookItem
   - WorkbookPage
   - Mistake
   - Submission
   - Institution
   - WorkbookTemplate
   ```

2. **复制路由**
   ```
   cuoti-system/app/routes/admin.py → gongkao-system/app/routes/mistakes.py
   cuoti-system/app/routes/h5.py → gongkao-system/app/routes/h5.py
   ```

3. **复制工具**
   ```
   cuoti-system/app/utils/ → gongkao-system/app/utils/
   - generator.py
   - parser.py
   - analyzer.py
   - report_generator.py
   ```

4. **复制模板**
   ```
   cuoti-system/app/templates/ → gongkao-system/app/templates/mistakes/
   ```

5. **数据迁移**
   - 导出错题系统数据
   - 导入到督学系统数据库
   - 建立Student外键关联

6. **统一入口**
   - 在督学系统侧边栏添加"错题管理"菜单
   - 合并登录系统

### 方案二：微服务架构

保持两个系统独立运行，通过API互通。

**优点：**
- 系统解耦
- 独立部署
- 风险隔离

**实现：**
- 督学系统提供学员API
- 错题系统调用学员API
- 统一的前端门户

## 合并检查清单

- [ ] 备份两个系统的数据库
- [ ] 确认数据模型无冲突
- [ ] 测试数据迁移脚本
- [ ] 合并路由无冲突
- [ ] 静态资源整合
- [ ] 权限系统统一
- [ ] 测试所有功能
- [ ] 更新文档

## 数据库表对照

| 错题系统表 | 督学系统表 | 合并方案 |
|-----------|-----------|---------|
| students | students | 使用督学系统的students，建立外键 |
| questions | - | 新增 |
| workbooks | - | 新增 |
| workbook_items | - | 新增 |
| workbook_pages | - | 新增 |
| mistakes | - | 新增，关联students |
| submissions | - | 新增，关联students |
| institution | - | 新增或合并到settings |
| workbook_templates | - | 新增 |
| admins | users | 使用督学系统的users |

## 待办事项

1. 确定合并时间点
2. 执行数据备份
3. 准备迁移脚本
4. 进行测试环境合并
5. 验证所有功能
6. 生产环境合并
