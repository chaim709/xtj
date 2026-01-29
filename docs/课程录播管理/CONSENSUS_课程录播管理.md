# 共识文档 - 课程录播管理功能

## 文档信息
- **创建日期**：2026-01-28
- **文档版本**：v1.0

---

## 1. 需求确认 ✅

| 项目 | 确认内容 |
|------|---------|
| 录播关联 | 关联到课表（Schedule），支持上午/下午/晚间时段 |
| 字段内容 | 链接、标题、日期、科目、老师、时长、备注、时段 |
| 展示位置 | 班次详情"录播"标签页 + 学员详情页 + 独立录播管理菜单 |

## 2. 技术方案

### 2.1 数据模型设计

新建 `CourseRecording` 模型：

```python
class CourseRecording(db.Model):
    __tablename__ = 'course_recordings'
    
    id                  # 主键
    schedule_id         # 关联课表（可选，方便直接录入）
    batch_id            # 关联班次（必填）
    recording_date      # 录播日期
    period              # 时段：morning/afternoon/evening
    title               # 录播标题
    recording_url       # 录播链接
    subject_id          # 科目
    teacher_id          # 授课老师
    duration_minutes    # 时长（分钟）
    remark              # 备注
    created_at          # 创建时间
    created_by          # 创建人
```

### 2.2 路由设计

| 接口 | 方法 | URL | 功能 |
|------|------|-----|------|
| 录播列表 | GET | /courses/recordings | 全部录播列表 |
| 添加录播 | GET/POST | /courses/recordings/create | 新增录播 |
| 编辑录播 | GET/POST | /courses/recordings/<id>/edit | 编辑录播 |
| 删除录播 | POST | /courses/recordings/<id>/delete | 删除录播 |
| 班次录播 | GET | /courses/batches/<id>/recordings | 班次下的录播 |

### 2.3 页面设计

1. **录播管理列表页** - `templates/courses/recordings/list.html`
2. **录播表单页** - `templates/courses/recordings/form.html`
3. **班次详情页新增标签** - 修改 `templates/courses/batches/detail.html`
4. **学员详情页新增区块** - 修改 `templates/students/detail.html`

## 3. 验收标准

- [x] CourseRecording 模型创建成功
- [x] 录播增删改查功能正常
- [x] 班次详情页显示录播标签
- [x] 学员详情页显示所属班次录播
- [x] 录播管理独立入口可用
