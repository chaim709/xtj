# 学员正确率统计与分析报告系统设计

> 设计日期：2026-01-29

## 1. 需求概述

### 1.1 功能目标

1. **正确率计算**：学生提交错题时输入"做了多少题"，系统自动计算各板块正确率
2. **学习分析报告**：生成PDF格式的完整学习分析报告，包含多维度统计

### 1.2 设计决策

| 决策点 | 选择 |
|--------|------|
| 做题确认方式 | 学生提交时手动输入做了多少题 |
| 统计粒度 | 全部（题册→板块→知识点逐级汇总） |
| 板块判断方式 | 按扫码范围自动识别 |
| 展示形式 | PDF报告 |
| 报告内容 | 完整版（7个模块） |
| 时间范围 | 可选（7天/30天/全部） |

---

## 2. 数据模型设计

### 2.1 修改 Submission 模型

```python
class Submission(db.Model):
    """提交记录"""
    __tablename__ = 'submissions'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    workbook_id = db.Column(db.Integer, db.ForeignKey('workbooks.id'), nullable=False)
    page_num = db.Column(db.Integer)
    
    # 原有字段
    mistake_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.now)
    
    # 新增字段
    total_attempted = db.Column(db.Integer, default=0)  # 本次做了多少题
    correct_count = db.Column(db.Integer, default=0)    # 正确数（自动计算）
    accuracy_rate = db.Column(db.Float)                 # 正确率（自动计算）
    
    # 关联的板块信息（从二维码解析）
    category = db.Column(db.String(64))      # 一级分类
    subcategory = db.Column(db.String(64))   # 二级分类（板块）
```

### 2.2 新增 StudentStats 模型

```python
class StudentStats(db.Model):
    """学员统计汇总（缓存表）"""
    __tablename__ = 'student_stats'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    
    # 统计维度
    dimension = db.Column(db.String(32))      # 'total'/'category'/'subcategory'/'knowledge_point'
    dimension_value = db.Column(db.String(128))  # 具体值
    
    # 统计数据
    total_attempted = db.Column(db.Integer, default=0)
    total_correct = db.Column(db.Integer, default=0)
    total_mistakes = db.Column(db.Integer, default=0)
    accuracy_rate = db.Column(db.Float)
    
    # 时间范围
    period = db.Column(db.String(16))  # 'all'/'7d'/'30d'
    updated_at = db.Column(db.DateTime, default=datetime.now)
    
    # 索引
    __table_args__ = (
        db.Index('idx_student_dimension', 'student_id', 'dimension', 'period'),
    )
```

---

## 3. H5提交流程设计

### 3.1 二维码类型识别

| 二维码格式 | 类型 | 解析内容 |
|------------|------|----------|
| `WB{id}P{page}` | 标准模式 | 题册ID + 页码 |
| `CAT{id}_{idx}` | 分类模式 | 题册ID + 分类索引 |
| `WB{id}` | 单二维码 | 题册ID |

### 3.2 提交表单

```
┌─────────────────────────────────────┐
│  📘 言语理解专项一                    │
│  📂 片段阅读（第1-40题）              │
├─────────────────────────────────────┤
│  本板块做了多少题：[    40    ] 题   │
├─────────────────────────────────────┤
│  请勾选错题题号：                     │
│  ☐1  ☐2  ☑3  ☐4  ☐5  ☐6  ☐7  ☑8   │
│  ...                                 │
├─────────────────────────────────────┤
│  📊 本次正确率：37/40 = 92.5%        │
│                                      │
│         [ 提交 ]                     │
└─────────────────────────────────────┘
```

### 3.3 提交逻辑

```python
# 计算正确数和正确率
correct_count = total_attempted - len(mistake_orders)
accuracy_rate = correct_count / total_attempted * 100 if total_attempted > 0 else 0

# 保存提交记录
submission = Submission(
    student_id=student.id,
    workbook_id=workbook.id,
    total_attempted=total_attempted,
    mistake_count=len(mistake_orders),
    correct_count=correct_count,
    accuracy_rate=accuracy_rate,
    category=category,
    subcategory=subcategory
)
```

---

## 4. PDF学习分析报告设计

### 4.1 报告结构（4页）

#### 第1页：封面+总览
- 机构Logo + 报告标题
- 学员姓名 + 统计周期
- 四大核心指标卡片：总刷题数、正确率、学习天数、错题数

#### 第2页：板块分析
- 雷达图：各板块正确率可视化
- 板块明细表：板块名、刷题数、正确率
- 弱项提示：自动识别正确率最低的2-3个板块

#### 第3页：知识点热力图
- 按知识点细分的表格
- 颜色状态：🟢优秀(>85%) 🟡良好(70-85%) 🔴需加强(<70%)

#### 第4页：趋势+高频错题
- 正确率变化趋势折线图
- 高频错题TOP5列表

### 4.2 图表技术方案

| 图表类型 | 技术 |
|----------|------|
| 雷达图 | matplotlib → PNG → PDF |
| 折线图 | matplotlib → PNG → PDF |
| 热力图 | ReportLab Table + 颜色 |
| 统计卡片 | ReportLab Table + 样式 |

---

## 5. 实现计划

### 5.1 任务分解

| 阶段 | 任务 | 文件 |
|------|------|------|
| 阶段1 | 数据模型改造 | `models/__init__.py` |
| 阶段2 | H5提交流程改造 | `routes/h5.py`, `templates/h5/submit.html` |
| 阶段3 | 统计服务 | `utils/stats.py` (新建) |
| 阶段4 | PDF报告生成 | `utils/report_generator.py` (新建) |
| 阶段5 | 管理后台入口 | `routes/admin.py`, `templates/admin/student_view.html` |

### 5.2 依赖关系

```
阶段1 (模型) 
    ↓
阶段2 (H5提交) ──→ 阶段3 (统计服务)
                        ↓
                  阶段4 (PDF报告)
                        ↓
                  阶段5 (后台入口)
```

### 5.3 文件清单

| 类型 | 文件 |
|------|------|
| 修改 | `app/models/__init__.py` |
| 修改 | `app/routes/h5.py` |
| 修改 | `app/templates/h5/submit.html` |
| 新建 | `app/utils/stats.py` |
| 新建 | `app/utils/report_generator.py` |
| 修改 | `app/routes/admin.py` |
| 修改 | `app/templates/admin/student_view.html` |

---

## 6. 验收标准

1. ✅ 学生扫码后可输入"做了多少题"
2. ✅ 提交后自动计算并显示正确率
3. ✅ 支持按题册/板块/知识点多维度统计
4. ✅ 管理后台可选择时间范围生成PDF报告
5. ✅ PDF报告包含全部7个内容模块
6. ✅ 雷达图、折线图正确渲染
