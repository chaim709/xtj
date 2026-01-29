# 系统合并对齐文档

> 创建日期：2026-01-29

## 一、两个系统概览

### 1. 公考培训机构管理系统 (gongkao-system)

| 维度 | 说明 |
|------|------|
| **定位** | 机构内部管理系统（B端） |
| **用户** | 机构管理员、督学老师 |
| **技术栈** | Flask + SQLAlchemy + SQLite |
| **端口** | 5000 |

**核心模块：**
- 学员管理（Student）：完整的学员档案、报考信息、学习画像
- 督学服务（SupervisionLog）：督学日志、跟进记录
- 作业管理（Homework）：作业布置、提交跟踪
- 课程管理（Course）：科目、项目、套餐、班次、排期
- 老师管理（Teacher）：老师信息、课时统计
- 职位分析（Position）：公务员职位库、智能选岗
- 学习计划（StudyPlan）：个性化学习计划
- 日历视图（Calendar）：课程日历
- 数据分析（Analytics）：综合分析

**数据模型（18个）：**
```
User, Student, WeaknessTag, ModuleCategory, SupervisionLog
HomeworkTask, HomeworkSubmission
Teacher, Subject, Project, Package, ClassType, ClassBatch
Schedule, ScheduleChangeLog, StudentBatch, Attendance, CourseRecording
StudyPlan, PlanGoal, PlanTask, PlanProgress
Position, StudentPosition, MajorCategory, Major
```

---

### 2. 错题收集系统 (cuoti-system)

| 维度 | 说明 |
|------|------|
| **定位** | 学员学习辅助系统（C端+B端） |
| **用户** | 学员（H5扫码）、机构管理员 |
| **技术栈** | Flask + SQLAlchemy + SQLite |
| **端口** | 5005 |

**核心模块：**
- 题库管理（Question）：题目CRUD、分类管理
- 题册管理（Workbook）：题册创建、PDF生成
- 错题收集（Mistake）：H5扫码、错题记录
- 学员分析（StudentStats）：正确率统计、分析报告
- 智能推荐（Recommendation）：基于薄弱点推荐
- 复习提醒（MistakeReview）：艾宾浩斯记忆曲线
- 学习计划（StudyPlan）：基于错题的学习计划
- 排行榜（Leaderboard）：学员排名
- 班级管理（StudentClass）：学员分班

**数据模型（12个）：**
```
Admin, Institution, WorkbookTemplate
Question, Workbook, WorkbookItem, WorkbookPage
Student, StudentClass, Submission, Mistake, MistakeReview, StudentStats
```

---

## 二、功能重叠分析

| 功能领域 | gongkao-system | cuoti-system | 说明 |
|----------|----------------|--------------|------|
| **学员基础信息** | ✅ 完整（报考、学历、画像） | ✅ 简单（姓名、手机） | gongkao更完整 |
| **学员分班** | ❌ 无 | ✅ StudentClass | 需合并 |
| **督学日志** | ✅ SupervisionLog | ❌ 无 | gongkao有 |
| **作业管理** | ✅ Homework系列 | ❌ 无 | gongkao有 |
| **课程管理** | ✅ 完整 | ❌ 无 | gongkao有 |
| **题库管理** | ❌ 无 | ✅ Question | cuoti有 |
| **题册/PDF** | ❌ 无 | ✅ 完整 | cuoti有 |
| **错题收集** | ❌ 无 | ✅ H5扫码 | cuoti有 |
| **学习分析** | ⚪ 简单 | ✅ 完整 | cuoti更完整 |
| **智能推荐** | ❌ 无 | ✅ 有 | cuoti有 |
| **复习提醒** | ❌ 无 | ✅ 艾宾浩斯 | cuoti有 |
| **职位分析** | ✅ 完整 | ❌ 无 | gongkao有 |
| **登录系统** | ✅ User模型 | ✅ Admin模型 | 需统一 |

---

## 三、需要确认的合并细节

### 1. 合并方向

**方案A：cuoti-system → gongkao-system**
- 将错题收集系统的功能作为模块并入公考管理系统
- 优点：gongkao-system架构更完整，学员模型更丰富
- 缺点：需要大量代码迁移

**方案B：gongkao-system → cuoti-system**  
- 将公考管理系统的功能并入错题收集系统
- 优点：cuoti-system刚刚开发完成，代码更新
- 缺点：需要扩展学员模型

**方案C：创建新系统，整合两者**
- 从零创建统一架构，整合两个系统的功能
- 优点：架构最清晰
- 缺点：工作量最大

### 2. 学员模型合并

gongkao-system的Student有更多字段：
- 报考信息：exam_type, target_position, exam_date
- 学习画像：has_basic, base_level, learning_style
- 选岗信息：major, political_status, work_years, hukou
- 督学关联：supervisor_id
- 课程关联：package_id

cuoti-system的Student较简单，但有：
- 班级关联：class_id → StudentClass
- 错题关联：mistakes, submissions, reviews

**需确认：如何合并学员模型？**

### 3. 用户/管理员模型

| 系统 | 模型 | 角色 |
|------|------|------|
| gongkao | User | 管理员、督学老师 |
| cuoti | Admin | 管理员（单一角色） |

**需确认：是否保留多角色设计？**

### 4. 数据库合并

两个系统都使用SQLite：
- gongkao-system: 有数据
- cuoti-system: cuoti_dev.db（有题库和测试数据）

**需确认：如何处理现有数据？**

### 5. 路由命名空间

| 功能 | gongkao路由 | cuoti路由 | 建议 |
|------|-------------|-----------|------|
| 学员管理 | /students | /admin/students | 统一为/students |
| 课程管理 | /courses | 无 | 保留/courses |
| 题库管理 | 无 | /admin/questions | 改为/questions |
| 题册管理 | 无 | /admin/workbooks | 改为/workbooks |
| H5端 | 无 | /h5/* | 保留/h5 |
| 督学 | /supervision | 无 | 保留/supervision |

### 6. UI风格统一

两个系统都使用Bootstrap，但风格略有不同：
- gongkao-system：较传统的管理后台风格
- cuoti-system：更现代的卡片式风格

**需确认：以哪个为基准？**

### 7. 合并后的系统名称

**建议选项：**
- A. 公考培训机构管理系统
- B. 公考学习管理系统
- C. 新途径公考管理平台
- D. 其他（请指定）

---

## 四、推荐合并方案

基于分析，我推荐 **方案A：将cuoti-system功能并入gongkao-system**

**理由：**
1. gongkao-system的学员模型更完整，符合业务需求
2. gongkao-system有完整的用户权限设计
3. gongkao-system的课程、督学等模块与错题收集有业务关联
4. 统一后便于数据打通（如：学员做题情况与督学记录关联）

**具体步骤：**
1. 在gongkao-system中创建新的blueprint: `questions`, `workbooks`, `h5`
2. 迁移题库相关模型：Question, Workbook系列
3. 扩展Student模型：添加错题相关关联
4. 迁移工具类：generator.py, recommendation.py等
5. 迁移模板文件
6. 合并配置和依赖

---

## 五、请确认以下问题

1. **合并方向**：是否同意方案A（cuoti→gongkao）？
2. **系统名称**：合并后的系统叫什么？
3. **数据保留**：
   - 是否保留gongkao-system现有学员数据？
   - 是否保留cuoti-system的题库数据？
4. **UI风格**：以哪个系统为基准？
5. **端口**：合并后使用哪个端口？（建议5000）
6. **其他要求**：有没有其他特殊需求？

---

请回复确认或修改上述方案，确认后我将开始执行合并。
