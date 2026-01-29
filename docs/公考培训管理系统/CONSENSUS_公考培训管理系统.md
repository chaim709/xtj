# 共识文档 - 公考培训机构管理系统

## 文档信息
- **创建日期**：2026-01-27
- **文档版本**：v1.0
- **任务阶段**：Align完成 → 进入Architect

---

## 1. 需求描述（最终版）

### 1.1 项目目标
为泗洪校区公务员考试培训机构开发内部管理系统，实现：
- 学员信息数字化管理（替代Excel）
- 督学工作流程化（替代微信沟通+脑子记）
- 作业跟踪系统化（替代口头反馈）
- 薄弱项自动识别（替代人工判断）

### 1.2 第一期功能范围（MVP）

| 模块 | 功能 | 说明 |
|------|------|------|
| 用户认证 | 登录/注销/权限控制 | 使用Flask-Login成熟方案 |
| 学员管理 | 档案CRUD、搜索、筛选 | 导入现有26个学员 |
| 学情档案 | 薄弱项标签、基础水平 | 支持手动和自动标记 |
| 督学日志 | 记录沟通、心态评估 | 快速记录模板 |
| 作业管理 | 发布、手动录入完成情况 | 督学人员录入学员成绩 |
| 督学工作台 | 待跟进列表、今日概览 | 自动生成待办 |

### 1.3 第一期不包含
- ❌ 学员端（H5/小程序）- 微信手动收集
- ❌ 课程管理 - 继续用Excel管理
- ❌ 数据看板 - 第二期开发
- ❌ 自动通知 - 微信手动转发

---

## 2. 验收标准

### 2.1 功能验收标准

| 功能 | 验收标准 |
|------|---------|
| 用户登录 | 管理员/督学人员可登录，密码加密存储 |
| 学员管理 | 26个学员数据已导入，可增删改查 |
| 学员搜索 | 按姓名/电话/班次/报考类型搜索，响应<1秒 |
| 薄弱项标签 | 可手动添加/删除，支持红黄绿三色标记 |
| 督学日志 | 可快速记录沟通内容，支持常用短语 |
| 作业发布 | 可创建作业任务，指定学员 |
| 作业录入 | 督学人员可录入学员作业完成情况 |
| 工作台 | 显示待跟进学员列表，按优先级排序 |

### 2.2 技术验收标准

| 指标 | 标准 |
|------|------|
| 页面加载 | < 2秒 |
| API响应 | < 500ms |
| 数据完整性 | 26个学员+4个教师数据完整导入 |
| 代码质量 | 函数有注释，代码可读 |

---

## 3. 技术方案（最终版）

### 3.1 技术栈

| 层级 | 技术 | 版本 |
|------|------|------|
| 后端框架 | Python Flask | 2.3+ |
| ORM | SQLAlchemy | 3.0+ |
| 数据库 | SQLite（开发）| - |
| 用户认证 | Flask-Login + Werkzeug | 最新 |
| 密码加密 | Werkzeug.security | - |
| 前端UI | Bootstrap | 5.3+ |
| 前端JS | jQuery | 3.7+ |
| 图表 | Chart.js | 4.x |

### 3.2 项目结构

```
gongkao-system/
├── app/
│   ├── __init__.py          # Flask应用初始化
│   ├── models/               # 数据模型
│   │   ├── __init__.py
│   │   ├── user.py          # 用户模型
│   │   ├── student.py       # 学员模型
│   │   ├── supervision.py   # 督学记录模型
│   │   ├── homework.py      # 作业模型
│   │   └── tag.py           # 标签模型
│   ├── routes/               # 路由（视图）
│   │   ├── __init__.py
│   │   ├── auth.py          # 登录认证
│   │   ├── students.py      # 学员管理
│   │   ├── supervision.py   # 督学服务
│   │   ├── homework.py      # 作业管理
│   │   └── dashboard.py     # 工作台
│   ├── services/             # 业务逻辑
│   │   ├── __init__.py
│   │   ├── student_service.py
│   │   ├── tag_service.py
│   │   └── follow_up_service.py
│   ├── static/               # 静态文件
│   │   ├── css/
│   │   ├── js/
│   │   └── images/
│   └── templates/            # HTML模板
│       ├── base.html
│       ├── auth/
│       ├── students/
│       ├── supervision/
│       └── dashboard/
├── data/                     # 数据导入脚本和源文件
│   └── import_excel.py
├── config.py                 # 配置文件
├── requirements.txt          # 依赖
├── run.py                    # 启动文件
└── README.md
```

### 3.3 数据库设计（精简版-第一期）

**users（用户表）**
```sql
- id: INTEGER PRIMARY KEY
- username: VARCHAR(50) UNIQUE
- password_hash: VARCHAR(255)
- real_name: VARCHAR(50)
- role: VARCHAR(20)  -- admin/supervisor
- created_at: DATETIME
```

**students（学员表）**
```sql
- id: INTEGER PRIMARY KEY
- name: VARCHAR(50)
- phone: VARCHAR(20)
- wechat: VARCHAR(50)
- class_name: VARCHAR(50)      -- 班次：全程班/暑假班
- exam_type: VARCHAR(100)      -- 报考类型：国省考/事业编
- has_basic: BOOLEAN           -- 是否有基础
- is_agreement: BOOLEAN        -- 是否协议班
- enrollment_date: DATE        -- 入学日期
- supervisor_id: INTEGER FK    -- 督学负责人
- address: VARCHAR(200)        -- 家庭住址
- parent_phone: VARCHAR(20)    -- 家长联系方式
- id_number: VARCHAR(30)       -- 身份证号
- status: VARCHAR(20)          -- active/inactive
- created_at: DATETIME
- updated_at: DATETIME
```

**weakness_tags（薄弱项标签）**
```sql
- id: INTEGER PRIMARY KEY
- student_id: INTEGER FK
- module: VARCHAR(50)          -- 一级模块
- sub_module: VARCHAR(100)     -- 具体知识点
- level: VARCHAR(10)           -- red/yellow/green
- accuracy_rate: DECIMAL       -- 正确率
- practice_count: INTEGER      -- 练习次数
- created_at: DATETIME
- updated_at: DATETIME
```

**supervision_logs（督学记录）**
```sql
- id: INTEGER PRIMARY KEY
- student_id: INTEGER FK
- supervisor_id: INTEGER FK
- contact_type: VARCHAR(20)    -- phone/wechat/face
- contact_duration: INTEGER    -- 分钟
- content: TEXT                -- 沟通内容
- student_mood: VARCHAR(20)    -- 心态评估
- study_status: VARCHAR(20)    -- 学习状态
- next_follow_date: DATE       -- 下次跟进
- log_date: DATE
- created_at: DATETIME
```

**homework_tasks（作业任务）**
```sql
- id: INTEGER PRIMARY KEY
- task_name: VARCHAR(100)
- module: VARCHAR(50)          -- 模块
- sub_module: VARCHAR(100)     -- 子模块
- question_count: INTEGER      -- 题量
- deadline: DATETIME
- target_students: TEXT        -- JSON数组
- description: TEXT
- creator_id: INTEGER FK
- status: VARCHAR(20)          -- published/closed
- created_at: DATETIME
```

**homework_submissions（作业提交-督学录入）**
```sql
- id: INTEGER PRIMARY KEY
- task_id: INTEGER FK
- student_id: INTEGER FK
- completed_count: INTEGER     -- 完成题量
- correct_count: INTEGER       -- 正确数量
- accuracy_rate: DECIMAL       -- 正确率（自动计算）
- time_spent: INTEGER          -- 用时（分钟）
- feedback: TEXT               -- 备注
- recorder_id: INTEGER FK      -- 录入人（督学）
- created_at: DATETIME
```

**module_categories（知识点分类）**
```sql
- id: INTEGER PRIMARY KEY
- level1: VARCHAR(50)          -- 一级：常识判断/言语理解...
- level2: VARCHAR(100)         -- 二级：科技常识/法律常识...
- level3: VARCHAR(150)         -- 三级（可选）
```

---

## 4. 技术约束

### 4.1 开发约束
- 开发环境：Mac
- Python版本：3.9+
- 不使用React/Vue等前端框架
- 不使用Docker（保持简单）

### 4.2 集成约束
- 第一期不接入微信API
- 第一期不开发小程序
- 使用SQLite数据库（后续可迁移PostgreSQL）

### 4.3 安全约束
- 密码必须加密存储
- API密钥放入.env文件
- .env文件不提交Git

---

## 5. 任务边界

### 5.1 第一期边界
**DO（做）**：
- 完整的学员管理功能
- 督学日志记录
- 作业发布和手动录入
- 督学工作台
- 数据导入脚本（Excel → SQLite）

**DON'T（不做）**：
- 学员自主提交作业
- 课程排课管理
- 财务/缴费管理
- 数据分析看板
- 微信通知推送

### 5.2 数据导入范围
**导入**：
- 学员档案管理（26人）
- 教师管理（4人）
- 题型分类（作为知识点体系）
- 每日学员刷题汇总（作为历史数据参考）

**不导入**：
- 入帐系统明细（财务数据）
- 协议班管理（协议数据）
- 课表规划（第二期功能）

---

## 6. 风险与应对

| 风险 | 可能性 | 影响 | 应对 |
|------|-------|------|------|
| Excel数据格式不规范 | 高 | 中 | 数据导入前先清洗验证 |
| 学员数据字段缺失 | 中 | 低 | 允许部分字段为空 |
| 督学人员不适应 | 中 | 中 | 保持界面简洁，提供培训 |

---

## 7. 下一步

### 7.1 即将进入
**阶段2: Architect（架构阶段）**
- 设计系统架构图
- 设计模块依赖关系
- 定义接口契约
- 设计数据流向

### 7.2 后续阶段
- Atomize：拆分原子任务
- Approve：审批确认
- Automate：开发执行
- Assess：验收评估

---

*文档状态：共识达成 ✅*
