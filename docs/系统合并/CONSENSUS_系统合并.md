# 系统合并共识文档

> 确认日期：2026-01-29

## 一、确认的合并方案

| 决策项 | 确认内容 |
|--------|----------|
| 合并方向 | cuoti-system → gongkao-system |
| 系统名称 | 公考培训机构管理系统 |
| 数据保留 | 保留两个系统的数据 |
| UI风格 | 以gongkao为基准 |
| 运行端口 | 5000 |

---

## 二、合并范围

### 从cuoti-system迁移的功能模块

1. **题库管理** (Question)
   - 题目CRUD
   - 分类管理（category, subcategory, knowledge_point）
   - 题目解析、难度

2. **题册管理** (Workbook)
   - 题册创建、编辑
   - PDF生成（普通模式、增强模式）
   - 二维码生成（单个、分页、分类）
   - 模板管理

3. **错题收集** (H5端)
   - 扫码提交错题
   - 做题数输入
   - 正确率实时计算

4. **学员分析**
   - 学员统计 (StudentStats)
   - 学习报告PDF生成
   - 排行榜

5. **智能学习**
   - 智能推荐 (Recommendation)
   - 艾宾浩斯复习 (MistakeReview)
   - 学习计划生成

6. **数据导入**
   - Excel批量导入

### gongkao-system保留的功能模块

- 学员管理（完整学员档案）
- 督学服务
- 课程管理（科目、项目、套餐、班次）
- 老师管理
- 作业管理
- 职位分析（智能选岗）
- 日历视图
- 数据分析

---

## 三、数据模型合并计划

### 1. 需要迁移的模型

| cuoti模型 | 迁移方式 | 说明 |
|-----------|----------|------|
| Question | 新建 | 完整迁移 |
| Workbook | 新建 | 完整迁移 |
| WorkbookItem | 新建 | 完整迁移 |
| WorkbookPage | 新建 | 完整迁移 |
| WorkbookTemplate | 新建 | 完整迁移 |
| Institution | 合并到现有 | gongkao可能已有类似配置 |
| Submission | 新建 | 完整迁移 |
| Mistake | 新建 | 完整迁移 |
| MistakeReview | 新建 | 完整迁移 |
| StudentStats | 新建 | 完整迁移 |
| StudentClass | 合并到Student | 作为班级字段 |

### 2. Student模型合并

gongkao的Student模型已经很完整，需要添加：
- 错题相关关联：submissions, mistakes, reviews, stats
- 题册相关关联：与Workbook的关联

### 3. 用户模型

- 保留gongkao的User模型（支持多角色）
- 移除cuoti的Admin模型

---

## 四、路由规划

| 功能 | 新路由 | 原路由 |
|------|--------|--------|
| 题库管理 | /questions/* | cuoti: /admin/questions |
| 题册管理 | /workbooks/* | cuoti: /admin/workbooks |
| H5学员端 | /h5/* | cuoti: /h5/* |
| 学员分析 | /analytics/* | 整合cuoti功能 |
| 排行榜 | /leaderboard | 新增 |
| 数据导入 | /import/* | 新增 |

---

## 五、技术实施计划

### 阶段1：模型迁移
- 将cuoti的数据模型迁移到gongkao
- 创建数据库迁移脚本
- 测试模型关联

### 阶段2：工具类迁移
- 迁移generator.py（PDF生成）
- 迁移recommendation.py（智能推荐）
- 迁移reminder.py（复习提醒）
- 迁移stats.py（统计服务）
- 迁移report_generator.py（报告生成）
- 迁移study_plan.py（学习计划）
- 迁移data_import.py（数据导入）

### 阶段3：路由迁移
- 创建questions blueprint
- 创建workbooks blueprint
- 创建h5 blueprint
- 整合到现有analytics

### 阶段4：模板迁移
- 迁移题库管理模板
- 迁移题册管理模板
- 迁移H5端模板
- 适配gongkao的base.html风格

### 阶段5：数据迁移
- 导出cuoti题库数据
- 导入到合并后的系统
- 验证数据完整性

### 阶段6：测试验收
- 功能测试
- 数据验证
- 性能测试

---

## 六、验收标准

1. ✅ 所有gongkao原有功能正常工作
2. ✅ 题库管理功能可用
3. ✅ 题册PDF生成正常（三种模式）
4. ✅ H5扫码提交错题正常
5. ✅ 学员分析报告生成正常
6. ✅ 智能推荐功能可用
7. ✅ 艾宾浩斯复习提醒可用
8. ✅ 排行榜功能可用
9. ✅ 数据导入功能可用
10. ✅ 原有题库数据保留
