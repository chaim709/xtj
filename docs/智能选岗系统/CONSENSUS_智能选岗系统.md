# CONSENSUS - 智能选岗系统

## 阶段1完成: Align → Consensus

**创建日期**: 2026-01-28  
**状态**: 需求已确认，进入架构设计

---

## 一、需求描述

### 1.1 系统定位

智能选岗系统是公考培训管理系统的核心功能模块，旨在通过AI技术帮助学员快速、精准地筛选和推荐适合自己的公务员岗位。

### 1.2 核心价值

| 价值点 | 描述 |
|--------|------|
| **效率提升** | 从人工一对一筛选 → 系统自动匹配，效率提升100倍 |
| **精准匹配** | 基于学员条件精确筛选，避免遗漏或错选 |
| **智能推荐** | 结合竞争数据和学员偏好，推荐最优岗位 |
| **数据驱动** | 基于历年数据分析，提供科学决策依据 |

### 1.3 目标用户

- **主要用户**：培训机构老师（为学员进行选岗服务）
- **次要用户**：学员本人（查看推荐岗位和报告）

---

## 二、功能需求（已确认）

### 2.1 核心功能清单

```
智能选岗系统
├── 1. 数据管理
│   ├── 1.1 岗位数据导入（Excel）
│   ├── 1.2 专业目录管理（PDF解析）
│   ├── 1.3 历史数据管理（报名人数、进面分）
│   └── 1.4 数据更新与同步
│
├── 2. 学员信息扩展
│   ├── 2.1 新增选岗必需字段
│   ├── 2.2 专业智能匹配
│   └── 2.3 条件完整性校验
│
├── 3. 岗位筛选引擎
│   ├── 3.1 硬性条件匹配（学历、专业、政治面貌等）
│   ├── 3.2 软性条件筛选（地域、单位类型等）
│   └── 3.3 自动排除不符合岗位
│
├── 4. 智能推荐系统
│   ├── 4.1 竞争难度评估
│   ├── 4.2 岗位推荐排序
│   └── 4.3 冲刺/稳妥/保底分级
│
├── 5. 对话式交互（扣子Bot）
│   ├── 5.1 自然语言查询
│   ├── 5.2 多轮对话支持
│   └── 5.3 个性化推荐
│
├── 6. 选岗报告生成
│   ├── 6.1 学员条件分析
│   ├── 6.2 推荐岗位列表
│   ├── 6.3 竞争分析图表
│   └── 6.4 PDF导出
│
└── 7. 系统集成
    ├── 7.1 学员管理集成
    ├── 7.2 学员详情页岗位展示
    └── 7.3 权限控制
```

### 2.2 功能优先级

| 优先级 | 功能 | 说明 |
|--------|------|------|
| P0 | 岗位数据导入 | 基础数据，必须先完成 |
| P0 | 专业目录解析 | 专业匹配的基础 |
| P0 | 学员字段扩展 | 筛选的前提条件 |
| P0 | 岗位筛选引擎 | 核心功能 |
| P1 | 智能推荐系统 | 增值功能 |
| P1 | 选岗报告生成 | 输出交付物 |
| P2 | 对话式交互 | 体验优化 |

---

## 三、技术方案（已确认）

### 3.1 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        前端展示层                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ 学员详情页   │ │ 岗位列表页  │ │ 报告预览页  │               │
│  │ (岗位推荐)   │ │ (筛选查询)  │ │ (PDF导出)   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
├─────────────────────────────────────────────────────────────────┤
│                        业务逻辑层                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ 筛选服务     │ │ 推荐服务    │ │ 报告服务    │               │
│  │ PositionSvc │ │ RecommendSvc│ │ ReportSvc   │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
│  ┌─────────────┐ ┌─────────────┐                               │
│  │ 专业匹配服务 │ │ 数据导入服务│                               │
│  │ MajorSvc    │ │ ImportSvc   │                               │
│  └─────────────┘ └─────────────┘                               │
├─────────────────────────────────────────────────────────────────┤
│                        数据访问层                                │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐               │
│  │ 岗位表      │ │ 专业目录表  │ │ 学员表(扩展)│               │
│  │ positions   │ │ majors      │ │ students    │               │
│  └─────────────┘ └─────────────┘ └─────────────┘               │
├─────────────────────────────────────────────────────────────────┤
│                        外部集成                                  │
│  ┌─────────────────────────────────────────────┐               │
│  │              扣子Bot API                     │               │
│  │         (对话式选岗交互)                     │               │
│  └─────────────────────────────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 技术栈

| 层级 | 技术选型 | 说明 |
|------|----------|------|
| 后端框架 | Flask | 与现有系统一致 |
| 数据库 | SQLite | 与现有系统一致 |
| PDF生成 | ReportLab / WeasyPrint | Python PDF库 |
| Excel解析 | pandas + openpyxl | 数据导入 |
| PDF解析 | PyMuPDF / pdfplumber | 专业目录解析 |
| 对话集成 | 扣子Bot API | 现有集成复用 |

### 3.3 数据模型

#### 3.3.1 岗位表 (positions)

```python
class Position(db.Model):
    """岗位模型"""
    __tablename__ = 'positions'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 年份和考试类型
    year = db.Column(db.Integer, nullable=False, index=True)  # 2024, 2025
    exam_type = db.Column(db.String(20), nullable=False)      # 省考/国考
    
    # 地区信息
    region_code = db.Column(db.String(20))        # 地区代码
    region_name = db.Column(db.String(50))        # 地区名称（江苏省、南京市等）
    city = db.Column(db.String(50), index=True)   # 所属城市
    
    # 单位信息
    department_code = db.Column(db.String(20))    # 单位代码
    department_name = db.Column(db.String(100))   # 单位名称
    
    # 职位信息
    position_code = db.Column(db.String(20))      # 职位代码
    position_name = db.Column(db.String(100))     # 职位名称
    position_desc = db.Column(db.Text)            # 职位简介
    
    # 招录条件
    exam_category = db.Column(db.String(10))      # 考试类别 A/B/C
    education = db.Column(db.String(50))          # 学历要求
    major_requirement = db.Column(db.Text)        # 专业要求（原始文本）
    other_requirements = db.Column(db.Text)       # 其他条件
    
    # 招录信息
    recruit_count = db.Column(db.Integer, default=1)  # 招考人数
    open_ratio = db.Column(db.Integer, default=3)     # 开考比例
    
    # 竞争数据（可为空，报名后更新）
    apply_count = db.Column(db.Integer)           # 报名人数
    competition_ratio = db.Column(db.Float)       # 竞争比
    min_entry_score = db.Column(db.Float)         # 最低进面分
    max_entry_score = db.Column(db.Float)         # 最高进面分
    max_xingce_score = db.Column(db.Float)        # 最高行测分
    max_shenlun_score = db.Column(db.Float)       # 最高申论分
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
```

#### 3.3.2 专业目录表 (major_categories)

```python
class MajorCategory(db.Model):
    """专业大类"""
    __tablename__ = 'major_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    code = db.Column(db.Integer, unique=True)     # 序号 1-50
    name = db.Column(db.String(50), nullable=False)  # 大类名称
    year = db.Column(db.Integer, default=2026)    # 适用年份

class Major(db.Model):
    """具体专业"""
    __tablename__ = 'majors'
    
    id = db.Column(db.Integer, primary_key=True)
    category_id = db.Column(db.Integer, db.ForeignKey('major_categories.id'))
    name = db.Column(db.String(100), nullable=False, index=True)  # 专业名称
    education_level = db.Column(db.String(20))    # 学历层次：研究生/本科/专科
    
    category = db.relationship('MajorCategory', backref='majors')
```

#### 3.3.3 学员表扩展字段

```python
# 在 Student 模型中新增字段
major = db.Column(db.String(100), comment='专业')
major_category_id = db.Column(db.Integer, db.ForeignKey('major_categories.id'), comment='专业大类ID')
political_status = db.Column(db.String(20), comment='政治面貌')  # 党员/预备党员/团员/群众
work_years = db.Column(db.Integer, default=0, comment='基层工作年限')
hukou_province = db.Column(db.String(50), comment='户籍省份')
hukou_city = db.Column(db.String(50), comment='户籍城市')
gender = db.Column(db.String(10), comment='性别')  # 男/女
birth_date = db.Column(db.Date, comment='出生日期')
```

---

## 四、验收标准

### 4.1 功能验收

| 编号 | 验收项 | 验收标准 |
|------|--------|----------|
| F01 | 岗位数据导入 | 能正确导入2024/2025年岗位Excel，数据完整无丢失 |
| F02 | 专业目录解析 | 能解析PDF专业目录，建立大类-专业映射关系 |
| F03 | 学员字段扩展 | 学员表单能录入新增的7个字段 |
| F04 | 专业智能匹配 | 输入专业名称能自动匹配所属大类 |
| F05 | 岗位筛选 | 根据学员条件筛选符合的岗位，结果准确 |
| F06 | 智能推荐 | 推荐岗位按竞争难度分级，排序合理 |
| F07 | 选岗报告 | 生成的PDF报告内容全面、排版美观 |
| F08 | 对话交互 | 扣子Bot能理解自然语言查询并返回结果 |

### 4.2 性能验收

| 指标 | 标准 |
|------|------|
| 岗位筛选响应时间 | < 2秒 |
| 报告生成时间 | < 10秒 |
| 数据导入（6000+岗位） | < 30秒 |

### 4.3 质量验收

- 代码符合现有项目规范
- 新增功能有单元测试覆盖
- 文档与代码保持同步

---

## 五、技术约束

1. **数据库兼容**：必须使用SQLite，与现有系统一致
2. **框架一致**：必须使用Flask框架
3. **权限复用**：复用现有用户权限体系
4. **UI风格**：与现有系统UI风格保持一致

---

## 六、边界限制

### 在范围内
- 岗位数据管理（导入、查询、更新）
- 专业目录映射
- 学员条件匹配筛选
- 智能推荐排序
- 选岗报告PDF生成
- 扣子Bot对话集成

### 不在范围内
- 官方报名系统对接
- 实时爬取官方数据
- 考试成绩管理
- 面试辅导功能
- 多省份支持（当前仅支持江苏省考和国考）

---

## 七、下一步行动

1. ✅ 需求对齐完成
2. ⏳ 进入架构设计阶段（DESIGN文档）
3. ⏳ 任务拆分（TASK文档）
4. ⏳ 审批确认（APPROVE）
5. ⏳ 开发实施（AUTOMATE）

---

**文档状态**: 已确认  
**下次更新**: 架构设计完成后
