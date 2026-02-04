# 待办事项 - 安徽省事业单位岗位整合

## 紧急待办（需要立即处理）

### 1. 处理2个失败的文件 ⚠️

**问题描述**  
以下2个文件在导入时失败（没有有效数据）：

1. `2026年度歙县事业单位统一公开招聘岗位汇总表.xls`
2. `2026年池州市市直事业单位公开招聘工作人员岗位计划表.xls`

**影响**  
预计缺失20-30个岗位数据。

**解决方案**  
1. 手动打开这两个文件，分析格式特点
2. 调整ExcelParser的表头识别逻辑
3. 重新运行导入脚本，仅处理这2个文件
4. 或者：人工整理这2个文件的数据，手动添加到数据库

**操作指引**
```bash
# 查看详细错误日志
cat /Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts/shiye_import_errors.txt

# 单独测试一个文件
cd /Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts
python3 -c "
from excel_parser import ExcelParser
parser = ExcelParser()
df, result = parser.parse_excel('/Users/chaim/CodeBuddy/公考项目/安徽省事业单位/黄山市岗位表/2026年度歙县事业单位统一公开招聘岗位汇总表.xls')
print(f'解析结果: {result}')
if result.success:
    print(df.head())
"
```

---

### 2. 修正考试类别异常数据 ⚠️

**问题描述**  
有14个岗位的考试类别显示为"11"，未正确识别为标准分类。

**影响**  
影响考试类别统计的准确性。

**解决方案**
1. 查询这14条记录，查看原始Excel数据
2. 确定"11"代表的实际类别
3. 更新`data_normalizer.py`中的标准化规则
4. 重新运行导入脚本或手动更新数据库

**操作指引**
```sql
-- 查询异常考试类别的岗位
SELECT id, city, department_name, position_name, exam_category
FROM positions
WHERE year = 2026 AND exam_type = '事业单位' AND exam_category = '11';

-- 更新（确定正确类别后）
UPDATE positions
SET exam_category = '综合管理类(A类)'  -- 替换为正确类别
WHERE year = 2026 AND exam_type = '事业单位' AND exam_category = '11';
```

---

## 重要待办（建议1周内完成）

### 3. 补充缺失的区县信息 📍

**问题描述**  
部分岗位的`region_name`字段为空，缺少具体的区县信息。

**操作指引**
```sql
-- 查询缺失区县信息的岗位
SELECT city, COUNT(*) as count
FROM positions
WHERE year = 2026 AND exam_type = '事业单位' AND region_name IS NULL
GROUP BY city;

-- 从department_name中提取区县信息（如适用）
UPDATE positions
SET region_name = SUBSTRING_INDEX(department_name, '区', 1) || '区'
WHERE year = 2026 AND exam_type = '事业单位' 
  AND region_name IS NULL 
  AND department_name LIKE '%区%';
```

---

### 4. 验证专业要求字段的完整性 📝

**问题描述**  
部分岗位的`major_requirement`字段可能为空。

**操作指引**
```sql
-- 统计专业要求缺失情况
SELECT 
    CASE WHEN major_requirement IS NULL THEN '缺失' ELSE '完整' END as status,
    COUNT(*) as count
FROM positions
WHERE year = 2026 AND exam_type = '事业单位'
GROUP BY status;

-- 查看专业要求缺失的岗位（前10条）
SELECT id, city, department_name, position_name, education
FROM positions
WHERE year = 2026 AND exam_type = '事业单位' AND major_requirement IS NULL
LIMIT 10;
```

---

## 优化建议（可选）

### 5. 添加Web管理界面 🌐

**功能需求**
- 在线上传Excel文件
- 实时显示导入进度
- 可视化导入结果和统计
- 支持导入记录查询

**技术方案**
- 在`app/routes/admin.py`中添加事业单位导入路由
- 使用Flask-SocketIO实现实时进度推送
- 复用现有的导入脚本逻辑

---

### 6. 增强字段映射配置 ⚙️

**优化点**
- 添加更多列名变体（基于未来新数据源）
- 支持正则表达式匹配
- 添加字段转换函数配置

**配置文件路径**
```
/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts/shiye_field_mapping.json
```

---

### 7. 数据质量监控 📊

**建议功能**
- 定期检查数据完整性
- 监控必填字段的填充率
- 自动生成数据质量报告

**实现方式**
创建定时任务脚本：
```python
# scripts/data_quality_check.py
# 定期检查Position表中事业单位数据的质量
```

---

## 长期规划（3个月内）

### 8. 报名数据跟踪 📈

**功能需求**
- 抓取官方网站的报名数据
- 自动更新`apply_count`和`competition_ratio`字段
- 提供竞争趋势分析

**技术方案**
- 使用爬虫定期抓取数据
- 更新Position模型的竞争数据字段
- 添加历史记录表跟踪变化

---

### 9. 历年数据对比 📅

**功能需求**
- 支持多年度岗位数据对比
- 分析岗位变化趋势
- 预测未来招聘趋势

**数据需求**
- 收集2025、2024年的岗位数据
- 建立年度数据对比模型

---

### 10. 智能推荐优化 🤖

**优化点**
- 针对事业单位特点调整匹配算法
- 考虑专业对口度、地域偏好等因素
- 提供个性化备考建议

---

## 运维相关

### 11. 定期数据备份 💾

**建议**  
在每次重新导入数据前，备份Position表。

**操作指引**
```bash
# 导出备份
mysqldump -u用户名 -p密码 数据库名 positions > backup_positions_$(date +%Y%m%d).sql

# 或使用SQLite（如果是SQLite数据库）
cp instance/gongkao.db instance/gongkao_backup_$(date +%Y%m%d).db
```

---

### 12. 日志文件管理 📁

**建议**  
定期清理或归档旧的导入日志。

**操作指引**
```bash
# 归档30天前的日志
find /Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts -name "*.txt" -mtime +30 -exec mv {} archive/ \;
```

---

## 联系支持

如果在处理上述待办事项时遇到问题，可以：

1. **查看项目文档**  
   `/Users/chaim/CodeBuddy/公考项目/docs/安徽事业单位岗位整合/`

2. **查看导入日志**  
   `/Users/chaim/CodeBuddy/公考项目/gongkao-system/scripts/shiye_import_log.txt`

3. **查看代码注释**  
   所有模块都有详细的docstring和注释

4. **重新运行导入**  
   ```bash
   cd /Users/chaim/CodeBuddy/公考项目/gongkao-system
   python3 scripts/import_shiye_positions.py
   ```

---

**文档更新时间**：2026-02-04  
**优先级说明**：⚠️ 紧急 | 📍 重要 | 📝 建议 | 🌐 增强功能
