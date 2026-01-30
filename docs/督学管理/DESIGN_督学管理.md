# 督学管理模块设计文档

## 1. 功能概述

督学管理是一个一站式督学工作台，整合学员督学状态、学习计划管理、督学记录追踪和业绩统计四大功能模块。

## 2. 页面布局

```
┌────────────────────────────────────────────────────────────┐
│  督学管理                                    [+ 新建计划]   │
├────────────────────────────────────────────────────────────┤
│ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│ │ 待跟进   │ │ 逾期任务 │ │ 本周联系 │ │ 计划完成 │       │
│ │   12     │ │    3     │ │   26     │ │  78.5%   │       │
│ └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
├────────────────────────────────────────────────────────────┤
│ [学员督学] [学习计划] [督学记录] [业绩统计]                 │
├────────────────────────────────────────────────────────────┤
│  (各Tab内容区域)                                           │
└────────────────────────────────────────────────────────────┘
```

## 3. 功能模块设计

### 3.1 学员督学Tab

| 功能 | 说明 |
|------|------|
| 学员列表 | 卡片式展示所有学员，显示姓名、状态、最后联系时间、当前计划进度 |
| 快速筛选 | 按状态筛选（待跟进/已完成/逾期/全部） |
| 快速操作 | 每个学员卡片支持：记录日志、查看计划、分配督学 |
| 待跟进高亮 | 今日需跟进的学员用醒目颜色标记 |

### 3.2 学习计划Tab

| 功能 | 说明 |
|------|------|
| 计划模板库 | 预设常用计划模板（基础阶段30天、冲刺阶段15天等） |
| 批量创建 | 选择多个学员，一键应用模板创建计划 |
| 计划列表 | 显示所有进行中的计划，按完成率排序 |
| 任务管理 | 可直接在此页面添加/完成任务 |
| 智能推荐 | 基于学员学习状态，推荐调整计划建议 |

### 3.3 督学记录Tab

| 功能 | 说明 |
|------|------|
| 时间线视图 | 按时间展示所有督学记录 |
| 筛选功能 | 按学员、日期范围、心态状态筛选 |
| 批量导出 | 导出督学记录为Excel |
| 快速录入 | 页面内快速添加督学记录 |

### 3.4 业绩统计Tab

| 功能 | 说明 |
|------|------|
| 督学工作量 | 各督学老师的联系学员数、记录数 |
| 学员状态分布 | 饼图展示心态、学习状态分布 |
| 计划完成率 | 各阶段计划的平均完成率 |
| 趋势图 | 周/月维度的督学工作趋势 |

## 4. 数据模型

### 4.1 新增模型

#### PlanTemplate (计划模板)
```python
class PlanTemplate(db.Model):
    __tablename__ = 'plan_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)      # 模板名称
    phase = db.Column(db.String(20))                       # 阶段
    duration_days = db.Column(db.Integer)                  # 持续天数
    description = db.Column(db.Text)                       # 描述
    goals_template = db.Column(db.Text)                    # 目标模板(JSON)
    tasks_template = db.Column(db.Text)                    # 任务模板(JSON)
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
```

### 4.2 现有模型扩展

现有模型已足够支持大部分功能，无需大幅修改。

## 5. 路由设计

| 路由 | 方法 | 功能 |
|------|------|------|
| `/supervision/manage` | GET | 督学管理主页 |
| `/supervision/manage/students` | GET | 学员督学数据(AJAX) |
| `/supervision/manage/plans` | GET | 学习计划数据(AJAX) |
| `/supervision/manage/logs` | GET | 督学记录数据(AJAX) |
| `/supervision/manage/stats` | GET | 统计数据(AJAX) |
| `/supervision/templates` | GET/POST | 计划模板管理 |
| `/supervision/templates/<id>` | GET/PUT/DELETE | 模板CRUD |
| `/supervision/assign` | POST | 分配学员给督学 |
| `/supervision/batch-create-plan` | POST | 批量创建计划 |

## 6. 技术实现

### 6.1 前端
- 使用现有Bootstrap 5 + jQuery框架
- Tab切换使用Bootstrap Tabs组件
- 图表使用现有Chart.js库
- 响应式设计，支持移动端

### 6.2 后端
- Flask Blueprint扩展现有supervision_bp
- 新增supervision_service.py中的管理方法
- 复用现有认证和权限机制

## 7. 实施计划

1. **Phase 1**: 创建主页面框架和统计卡片
2. **Phase 2**: 实现学员督学Tab
3. **Phase 3**: 实现学习计划Tab（含模板功能）
4. **Phase 4**: 实现督学记录Tab
5. **Phase 5**: 实现业绩统计Tab
6. **Phase 6**: 测试和优化
