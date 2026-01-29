# 第三阶段待办事项

## 系统启动检查

### 1. 启动前准备

- [ ] 确认 `.env` 文件中 `API_KEY` 已配置
- [ ] 确认服务器端口未被占用
- [ ] 确认数据库文件存在

### 2. 启动系统

```bash
cd /Users/chaim/CodeBuddy/公考项目/gongkao-system
python run.py
```

如遇端口占用，可指定其他端口：
```bash
python -c "from app import create_app; app = create_app(); app.run(port=5002, debug=True)"
```

### 3. 访问验证

| 页面 | URL | 说明 |
|-----|-----|------|
| 登录页 | http://localhost:5001/auth/login | 需要先登录 |
| 工作台 | http://localhost:5001/dashboard/ | 查看提醒功能 |
| 课程日历 | http://localhost:5001/calendar/ | 新增页面 |
| 数据分析 | http://localhost:5001/analytics/ | 新增页面 |
| 学员详情 | http://localhost:5001/students/{id} | 查看增强数据 |

## 功能测试清单

### 课程日历

- [ ] 月视图显示正确
- [ ] 周视图显示正确
- [ ] 班次筛选功能
- [ ] 老师筛选功能
- [ ] 科目筛选功能
- [ ] 点击日期弹出详情
- [ ] 跳转班次详情页

### 数据分析

- [ ] 统计卡片数据正确
- [ ] 学员增长趋势图
- [ ] 学员状态分布图
- [ ] 薄弱知识点分布
- [ ] 督学工作量排行
- [ ] 班次课程进度
- [ ] 考勤统计图表
- [ ] 时间范围切换

### 开放API

测试命令：
```bash
# 测试认证
curl -s http://localhost:5001/api/v1/students \
  -H "X-API-Key: gongkao-api-key-2026-dev-only"

# 测试学员详情
curl -s http://localhost:5001/api/v1/students/27 \
  -H "X-API-Key: gongkao-api-key-2026-dev-only"

# 测试班次列表
curl -s http://localhost:5001/api/v1/batches \
  -H "X-API-Key: gongkao-api-key-2026-dev-only"
```

### 工作台提醒

- [ ] 待处理事项卡片显示
- [ ] 超期未跟进学员列表
- [ ] 跟进按钮功能

### 学员详情增强

- [ ] 督学汇总卡片
- [ ] 课程进度卡片
- [ ] 考勤统计卡片
- [ ] 心态分布显示

## 配置说明

### .env 配置项

```env
# Flask配置
FLASK_ENV=development
FLASK_DEBUG=1

# 安全密钥
SECRET_KEY=your-secret-key

# API密钥（生产环境请更换！）
API_KEY=gongkao-api-key-2026-dev-only
```

### config.py 新增配置

| 配置项 | 默认值 | 说明 |
|-------|-------|------|
| API_KEY | 环境变量或默认值 | API认证密钥 |
| API_KEY_HEADER | X-API-Key | API Key请求头名称 |
| FOLLOW_UP_REMINDER_DAYS | 7 | 跟进提醒天数 |
| ANALYTICS_DEFAULT_DAYS | 30 | 分析默认天数 |

## 后续优化建议

### 短期（下次迭代）

1. 日历支持更多筛选条件
2. 分析看板支持自定义时间范围
3. API支持更多查询参数

### 中期

1. 数据导出功能（Excel/PDF）
2. API文档（Swagger）
3. 系统通知功能

### 长期

1. 移动端适配
2. 微信小程序集成
3. 题库系统对接

## 已知问题

暂无

## 联系支持

如有问题，请检查：
1. 服务器日志输出
2. 浏览器控制台错误
3. 网络请求状态

---

**第三阶段开发完成！** 🎉
