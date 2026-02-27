# 安徽事业单位智能选岗系统 - 项目对齐文档

**创建时间**: 2026-02-05  
**项目代号**: SHIYE-SYSTEM  
**执行模式**: 完全自主执行

---

## 一、项目特性规范

### 1.1 项目定位
- **项目名称**: 安徽事业单位智能选岗系统
- **英文名称**: Anhui Public Institution Position Selection System
- **简称**: 事业选岗系统 / SHIYE-SYSTEM
- **版本**: v1.0.0

### 1.2 核心目标
为安徽省事业单位考生提供智能化、数据驱动的岗位选择系统，通过AI算法和大数据分析，帮助考生：
1. **快速筛选**：3秒内找到最适合的岗位（vs 传统Excel需要几天）
2. **精准匹配**：基于15+维度的智能推荐算法
3. **概率预测**：提供科学的上岸概率评估
4. **决策支持**：多维度对比和可视化分析

### 1.3 数据基础
- **数据来源**: 2026年安徽省事业单位官方招聘公告
- **数据规模**: 3,443个岗位，4,221个招聘名额
- **覆盖范围**: 省直 + 16个地级市
- **数据准确率**: 98.90%（已验证）

---

## 二、需求理解

### 2.1 用户画像

**主要用户群体**:
1. **应届毕业生** (40%)
   - 年龄: 22-25岁
   - 需求: 求稳上岸、待遇适中
   - 痛点: 缺乏经验、信息过载

2. **往届生** (35%)
   - 年龄: 26-30岁
   - 需求: 快速上岸、追求发展
   - 痛点: 竞争压力、机会成本

3. **在职考生** (25%)
   - 年龄: 30-35岁
   - 需求: 跳槽改善、稳定编制
   - 痛点: 时间有限、选择纠结

**学历分布**:
- 博士: 0.5%（几乎无竞争）
- 研究生: 15%（竞争适中）
- 本科: 70%（竞争最激烈）
- 专科: 14.5%（岗位减少）

### 2.2 核心功能需求

#### 必须实现（MVP）:
1. ✅ **智能选岗向导**
   - 个人画像建立（学历、专业、分数、地域）
   - 多维度智能筛选
   - 三档推荐（冲刺/稳妥/保底）
   - 上岸概率计算

2. ✅ **岗位搜索引擎**
   - 关键词搜索
   - 多条件筛选
   - 高级筛选
   - 结果排序

3. ✅ **数据可视化**
   - 地市分布地图
   - 学历专业分布图
   - 竞争度热力图
   - 个人匹配度展示

4. ✅ **岗位详情页**
   - 完整岗位信息
   - 竞争态势分析
   - 历年数据对比
   - 专家建议

#### 应该实现（完整版）:
5. ✅ **竞争力测评**
   - 5维度评分系统
   - 个性化报告
   - 提升建议

6. ✅ **地区深度对比**
   - 16地市横向对比
   - 五维雷达图
   - 详细解析

7. ✅ **专业匹配助手**
   - AI专业识别
   - 专业大类映射
   - 报考指南

8. ✅ **岗位对比功能**
   - 最多5个岗位
   - 全维度对比
   - AI推荐

#### 可选实现（增值服务）:
9. ⭐ **AI智能问答**
10. ⭐ **备考助手**
11. ⭐ **社区交流**
12. ⭐ **VIP服务**

### 2.3 技术约束

**技术栈选择**:
- **后端**: Python 3.11 + Flask (保持技术栈统一)
- **前端**: HTML5 + Tailwind CSS + Alpine.js (轻量级)
- **数据库**: SQLite (开发) → PostgreSQL (生产)
- **可视化**: ECharts (丰富图表)
- **地图**: AMap/百度地图 API

**架构原则**:
1. **独立性**: 与现有公考系统完全分离
2. **可扩展**: 模块化设计，便于后期扩展
3. **高性能**: 3秒内完成智能推荐
4. **易维护**: 清晰的代码结构和文档

**开发约束**:
- 复用现有gongkao-system的基础框架
- 使用相同的UI设计风格（保持一致性）
- 数据库独立（避免冲突）
- 端口独立（5002）

---

## 三、边界确认

### 3.1 项目范围

**包含**:
✅ 2026年安徽省事业单位岗位数据
✅ 智能选岗核心功能
✅ 数据分析和可视化
✅ 基础用户系统
✅ 岗位收藏和对比
✅ 响应式Web界面

**不包含**:
❌ 其他省份数据
❌ 历年真题题库（备考类）
❌ 在线支付系统
❌ 移动端原生APP
❌ 社交功能（一期）
❌ 直播课程

### 3.2 时间边界

**开发周期**: 立即开始，持续执行
- MVP版本: 核心功能优先
- 完整版: 逐步迭代
- 测试优化: 持续进行

### 3.3 数据边界

**数据来源**:
- CSV文件: `/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/整合后总表_2026年安徽省事业单位岗位.csv`
- 分析报告: `/Users/chaim/CodeBuddy/公考项目/docs/2026年安徽省事业单位招聘超详细分析报告_完整版.md`

**数据处理**:
- 标准化字段名称
- 清洗无效数据
- 补充分析维度
- 建立关联关系

---

## 四、疑问澄清（已通过分析报告解决）

### 4.1 已明确的问题

1. **Q**: 推荐算法的权重如何分配？
   **A**: 基于报告数据分析：
   - 上岸概率 30%（最重要）
   - 待遇水平 25%
   - 发展空间 20%
   - 生活质量 15%
   - 综合评价 10%

2. **Q**: 竞争度如何计算？
   **A**: 基于历年报录比数据 + 岗位特征预测
   - 省直/沿江: 60-80:1（高竞争）
   - 一般地市: 30-50:1（中等）
   - 皖北/基层: 10-30:1（低竞争）

3. **Q**: 上岸概率模型如何设计？
   **A**: 多因子模型（详见报告第六章）
   - 基础概率（报录比）
   - 学历加成系数
   - 专业匹配系数
   - 分数段加成
   - 地域加成

4. **Q**: 地市待遇数据从何而来？
   **A**: 基于报告分析的薪资区间
   - 省直: 10-15万
   - 沿江城市: 9-12万
   - 皖北地区: 7-10万
   - 基层岗位: 6-9万

### 4.2 需要在开发中验证的问题

1. **性能优化**: 3秒内完成推荐是否可达成？
   - 策略: 数据库索引优化、算法优化、缓存机制

2. **用户体验**: 5步选岗流程是否流畅？
   - 策略: 原型测试、迭代优化

3. **数据准确性**: 预测模型是否可靠？
   - 策略: 基于历年数据训练、持续校准

---

## 五、技术方案

### 5.1 系统架构

```
┌─────────────────────────────────────────┐
│           用户浏览器（前端）              │
│  HTML + Tailwind CSS + Alpine.js        │
└──────────────┬──────────────────────────┘
               │ HTTP/JSON
┌──────────────┴──────────────────────────┐
│         Flask应用服务器（后端）          │
│  ┌────────────────────────────────────┐ │
│  │  路由层 (Blueprint)                 │ │
│  │  ├─ /positions (岗位相关)          │ │
│  │  ├─ /wizard (选岗向导)             │ │
│  │  ├─ /api (API接口)                 │ │
│  │  └─ /admin (管理后台)              │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  业务逻辑层 (Services)              │ │
│  │  ├─ PositionService (岗位服务)     │ │
│  │  ├─ RecommendService (推荐算法)    │ │
│  │  ├─ AnalysisService (数据分析)     │ │
│  │  └─ UserService (用户服务)         │ │
│  └────────────────────────────────────┘ │
│  ┌────────────────────────────────────┐ │
│  │  数据访问层 (Models)                │ │
│  │  ├─ Position (岗位模型)            │ │
│  │  ├─ User (用户模型)                │ │
│  │  ├─ UserProfile (用户画像)         │ │
│  │  └─ Favorite (收藏记录)            │ │
│  └────────────────────────────────────┘ │
└──────────────┬──────────────────────────┘
               │ SQL
┌──────────────┴──────────────────────────┐
│         SQLite数据库 (开发环境)          │
│  ├─ positions (岗位表)                  │
│  ├─ users (用户表)                      │
│  ├─ user_profiles (用户画像表)          │
│  ├─ favorites (收藏表)                  │
│  └─ recommendations (推荐记录表)        │
└─────────────────────────────────────────┘
```

### 5.2 核心算法设计

**智能推荐算法**:
```python
def calculate_recommendation_score(position, user_profile):
    """
    综合评分 = Σ(维度分数 × 权重)
    """
    score = 0
    
    # 1. 上岸概率 (30%)
    landing_prob = calculate_landing_probability(position, user_profile)
    score += landing_prob * 0.30
    
    # 2. 待遇水平 (25%)
    salary_score = normalize_salary(position.estimated_salary)
    score += salary_score * 0.25
    
    # 3. 发展空间 (20%)
    development_score = calculate_development(position)
    score += development_score * 0.20
    
    # 4. 生活质量 (15%)
    life_quality = calculate_life_quality(position.city)
    score += life_quality * 0.15
    
    # 5. 综合评价 (10%)
    overall_score = position.overall_rating or 75
    score += overall_score * 0.10
    
    return score
```

**上岸概率模型**:
```python
def calculate_landing_probability(position, user):
    """
    上岸概率 = 基础概率 × 学历系数 × 专业系数 × 分数系数 × 地域系数
    """
    # 基础概率（基于报录比）
    base_prob = 1 / position.estimated_competition_ratio
    
    # 学历系数
    edu_coef = {'博士': 3.0, '研究生': 1.8, '本科': 1.0, '专科': 0.7}
    
    # 专业匹配系数
    major_coef = {'精确': 1.5, '大类': 1.2, '相关': 1.0, '不限': 0.8}
    
    # 分数系数（相对历年最低分）
    score_coef = calculate_score_coefficient(user.score, position.min_score)
    
    # 地域系数
    local_coef = 1.3 if user.is_local else 1.0
    
    # 综合计算
    probability = base_prob * edu_coef[user.education] * \
                  major_coef[user.major_match] * score_coef * local_coef
    
    return min(probability * 100, 99)  # 限制在0-99%
```

### 5.3 数据库设计

**核心表结构**:
```sql
-- 岗位表
CREATE TABLE positions (
    id INTEGER PRIMARY KEY,
    year INTEGER NOT NULL,
    exam_type VARCHAR(20) DEFAULT '事业单位',
    city VARCHAR(50),
    affiliation VARCHAR(20),
    region_name VARCHAR(50),
    system_type VARCHAR(50),
    department_name VARCHAR(200),
    position_code VARCHAR(50),
    position_name VARCHAR(200),
    position_desc TEXT,
    exam_category VARCHAR(20),
    recruit_count INTEGER,
    education VARCHAR(50),
    major_requirement TEXT,
    other_requirements TEXT,
    -- 分析字段
    estimated_salary INTEGER,
    estimated_competition_ratio FLOAT,
    difficulty_level VARCHAR(20),
    recommendation_score FLOAT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 用户画像表
CREATE TABLE user_profiles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    education VARCHAR(20),
    major VARCHAR(100),
    graduation_status VARCHAR(20),
    estimated_score INTEGER,
    preferred_cities TEXT,
    special_status TEXT,
    political_status VARCHAR(20),
    competitiveness_score INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- 收藏表
CREATE TABLE favorites (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    position_id INTEGER,
    note TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, position_id)
);

-- 推荐记录表
CREATE TABLE recommendations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER,
    position_id INTEGER,
    score FLOAT,
    landing_probability FLOAT,
    recommendation_type VARCHAR(20),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

---

## 六、验收标准

### 6.1 功能验收

**核心功能**:
- [ ] 智能选岗向导：5步流程顺畅，3秒出结果
- [ ] 推荐准确率：至少70%的用户满意推荐结果
- [ ] 搜索性能：1秒内返回搜索结果
- [ ] 数据展示：图表清晰、数据准确

**用户体验**:
- [ ] 界面美观：现代化UI，响应式设计
- [ ] 操作流畅：无明显卡顿
- [ ] 信息清晰：重点突出，层次分明

### 6.2 技术验收

**性能指标**:
- [ ] 页面加载：首页<2秒
- [ ] API响应：<500ms
- [ ] 推荐计算：<3秒
- [ ] 并发支持：100用户

**代码质量**:
- [ ] 代码规范：符合PEP8
- [ ] 注释完整：关键函数有文档
- [ ] 模块化：高内聚低耦合
- [ ] 可维护：清晰的项目结构

### 6.3 数据验收

**数据准确性**:
- [ ] 导入成功率：100%
- [ ] 数据完整性：无缺失关键字段
- [ ] 计算准确性：随机抽查10个岗位验证

---

## 七、项目计划

### 7.1 开发顺序

**Phase 1: 基础设施**
1. 项目结构搭建
2. 数据库设计和创建
3. 数据导入和清洗

**Phase 2: 核心功能**
4. 岗位搜索引擎
5. 智能选岗向导
6. 推荐算法实现
7. 岗位详情页

**Phase 3: 增强功能**
8. 数据可视化
9. 竞争力测评
10. 地区对比
11. 专业匹配

**Phase 4: 优化完善**
12. 性能优化
13. UI/UX优化
14. 测试修复

### 7.2 技术决策记录

| 决策项 | 选择方案 | 原因 |
|--------|---------|------|
| 后端框架 | Flask | 轻量级、灵活、团队熟悉 |
| 前端框架 | Alpine.js | 轻量级、学习成本低、性能好 |
| 数据库 | SQLite → PostgreSQL | 开发快速、生产稳定 |
| 图表库 | ECharts | 功能强大、美观、中文友好 |
| 地图 | 高德地图 | 国内使用广泛、免费额度 |

---

## 八、风险评估

### 8.1 技术风险

**风险1**: 推荐算法准确性不足
- **影响**: 用户不信任推荐结果
- **应对**: 基于真实数据训练、持续优化、提供多样化推荐

**风险2**: 性能问题（3秒目标）
- **影响**: 用户体验差
- **应对**: 数据库索引、缓存机制、算法优化

**风险3**: 数据维护成本
- **影响**: 数据更新困难
- **应对**: 设计灵活的数据结构、提供管理后台

### 8.2 业务风险

**风险1**: 用户需求理解偏差
- **影响**: 功能不符合实际需求
- **应对**: 基于详细报告、迭代优化

**风险2**: 数据时效性
- **影响**: 2027年数据需要更新
- **应对**: 设计可扩展的数据导入机制

---

## 九、后续迭代方向

### V1.1 计划
- 历年数据对比功能
- 更多地市的详细分析
- 用户反馈系统

### V2.0 计划
- AI智能问答
- 社区交流功能
- 移动端适配

### V3.0 计划
- 备考资料整合
- 在线课程
- VIP增值服务

---

**文档状态**: ✅ 已完成对齐
**下一阶段**: 进入架构设计（ARCHITECT）
