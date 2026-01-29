# 扣子智能督学集成指南

本文档指导如何将公考培训管理系统与扣子(Coze)智能体集成，实现语音督学功能。

## 一、系统架构

```
督学老师(手机扣子App) 
    ↓ 语音输入
扣子智能体 
    ↓ 调用自定义插件
ngrok内网穿透 
    ↓ 转发请求
本地学生管理系统API 
    ↓ 处理数据
SQLite数据库
```

## 二、前置准备

### 2.1 确保系统正常运行

```bash
cd /Users/chaim/CodeBuddy/公考项目/gongkao-system
source venv/bin/activate
flask run --port=5001
```

### 2.2 配置 API Key

在 `.env` 文件中确保设置了 API_KEY：

```
API_KEY=your-secure-api-key-here
```

## 三、配置公网访问

### 方案A: Cloudflare Tunnel（推荐）

由于您的域名 `chaim.top` 托管在 Cloudflare，推荐使用 Cloudflare Tunnel：

- 地址固定：`https://gongkao.chaim.top`
- 免费无限制
- 自带 CDN 加速和安全防护

详细配置请参考：[cloudflare-tunnel-setup.md](./cloudflare-tunnel-setup.md)

**快速配置：**

```bash
# 1. 安装
brew install cloudflared

# 2. 登录
cloudflared tunnel login

# 3. 创建 tunnel
cloudflared tunnel create gongkao

# 4. 配置 DNS
cloudflared tunnel route dns gongkao gongkao.chaim.top

# 5. 创建配置文件 ~/.cloudflared/config.yml
# 6. 启动
cloudflared tunnel run gongkao
```

### 方案B: ngrok（备选）

如果不想配置 Cloudflare Tunnel，可以使用 ngrok：

```bash
# 安装
brew install ngrok

# 启动穿透 (Flask 运行在 5001 端口)
ngrok http 5001
```

**注意**: ngrok 免费版每次重启地址会变化，需要更新扣子插件配置。

## 四、API 接口说明

### 4.1 学员智能搜索

```
GET /api/v1/students/search
Header: X-API-Key: your-api-key

Query Params:
- query: 搜索关键词（姓名/手机号）
- include_logs: 是否包含督学记录 (true/false)
- include_homework: 是否包含作业情况 (true/false)
- limit: 返回数量限制 (默认5)

示例:
GET /api/v1/students/search?query=张三&include_logs=true
```

### 4.2 创建督学记录

```
POST /api/v1/supervision/logs
Header: X-API-Key: your-api-key
Content-Type: application/json

Body:
{
    "student_name": "张三",           // 学员姓名（智能匹配）
    "content": "今天状态不错，学习进度正常", 
    "mood": "积极",                   // 积极/平稳/焦虑/低落
    "study_status": "良好",           // 优秀/良好/一般/较差
    "contact_type": "语音录入",
    "next_action": "继续保持"
}
```

### 4.3 批量推送作业

```
POST /api/v1/homework/batch-push
Header: X-API-Key: your-api-key
Content-Type: application/json

Body:
{
    "homework_id": 1,
    "batch_name": "A班"               // 或 batch_id: 1
}
```

### 4.4 获取待办事项

```
GET /api/v1/reminders/pending
Header: X-API-Key: your-api-key

Query Params:
- type: follow_up / homework / all
- days: 超期天数阈值 (默认3)
- limit: 返回数量 (默认10)
```

### 4.5 生成周报

```
GET /api/v1/reports/weekly
Header: X-API-Key: your-api-key

Query Params:
- week: current / last
```

## 五、扣子配置步骤

### 5.1 创建自定义插件

1. 登录扣子平台：https://www.coze.cn
2. 进入「插件」→「创建插件」
3. 选择「API 插件」
4. 配置如下：

#### 插件1: 查询学员

- 名称: `查询学员`
- 描述: `根据姓名查询学员信息`
- 请求方式: GET
- URL: `https://gongkao.chaim.top/api/v1/students/search`
- 参数:
  - query (必填): 学员姓名或手机号
  - include_logs (可选): 是否包含督学记录
- Headers:
  - X-API-Key: `gongkao-api-key-2026-dev-only`

#### 插件2: 创建督学记录

- 名称: `创建督学记录`
- 描述: `为学员创建督学记录`
- 请求方式: POST
- URL: `https://gongkao.chaim.top/api/v1/supervision/logs`
- Body (JSON):
```json
{
    "student_name": "{{student_name}}",
    "content": "{{content}}",
    "mood": "{{mood}}",
    "study_status": "{{study_status}}"
}
```
- Headers:
  - X-API-Key: `gongkao-api-key-2026-dev-only`
  - Content-Type: application/json

#### 插件3: 推送作业

- 名称: `推送作业`
- 描述: `将作业推送给班次学员`
- 请求方式: POST
- URL: `https://gongkao.chaim.top/api/v1/homework/batch-push`

#### 插件4: 获取待办

- 名称: `获取待办事项`
- 描述: `查看待跟进学员和未完成作业`
- 请求方式: GET
- URL: `https://gongkao.chaim.top/api/v1/reminders/pending`

#### 插件5: 生成周报

- 名称: `生成周报`
- 描述: `生成本周工作报告`
- 请求方式: GET
- URL: `https://gongkao.chaim.top/api/v1/reports/weekly`

### 5.2 创建智能体

1. 进入「智能体」→「创建智能体」
2. 名称: `督学小助手`
3. 人设提示词:

```
你是泗洪教育的智能督学助理，帮助督学老师高效管理学员。

你的能力：
1. 语音记录督学内容 - 老师说话后，提取学员姓名和督学内容，调用API创建记录
2. 查询学员信息 - 根据姓名查询学员的详细信息和历史记录
3. 推送作业 - 将作业推送给指定班次的学员
4. 查看待办 - 查看需要跟进的学员和未完成的作业
5. 生成周报 - 生成本周工作总结

交互规则：
- 语音输入时，智能提取关键信息
- 创建督学记录时，确认学员姓名后再保存
- 查询结果简洁明了，突出重点信息
- 使用友好的语气回复

情绪识别关键词：
- 积极：开心、高兴、有信心、状态好、进步
- 平稳：正常、还行、一般
- 焦虑：紧张、压力大、担心
- 低落：没状态、不想学、放弃
```

4. 添加技能：勾选刚才创建的5个插件
5. 发布智能体

### 5.3 创建工作流 (可选)

对于复杂场景，可以创建工作流：

**语音督学工作流**:
1. 触发器: 用户语音输入
2. 节点1: 语音转文字 (扣子内置)
3. 节点2: LLM提取信息 (提取学员姓名、督学内容、情绪等)
4. 节点3: 调用查询学员API (确认学员存在)
5. 节点4: 调用创建督学记录API
6. 节点5: 返回确认消息

## 六、使用示例

### 6.1 语音记录督学

督学老师说: "记录一下张三今天的情况，学习状态不错，正在复习行测，心态比较积极"

扣子解析后调用API:
```json
{
    "student_name": "张三",
    "content": "学习状态不错，正在复习行测",
    "mood": "积极",
    "study_status": "良好"
}
```

返回: "已为学员张三创建督学记录"

### 6.2 查询学员

督学老师说: "张三最近怎么样"

扣子返回:
```
学员: 张三
班次: 公务员冲刺班A
状态: 在读
最近督学记录:
- 01-27: 学习状态不错，正在复习行测（积极）
- 01-25: 完成了言语理解练习（平稳）
```

### 6.3 查看待办

督学老师说: "今天有什么需要处理的"

扣子返回:
```
待处理事项：
1. 待跟进学员(3人): 李四(5天未联系)、王五(4天)...
2. 待完成作业: 行测模拟卷(完成率60%)
3. 重点关注: 2人需特别关注
```

## 七、注意事项

1. **ngrok 地址会变化**: 免费版 ngrok 每次重启地址会变，需要更新扣子插件配置
2. **安全性**: 
   - 不要泄露 API Key
   - 建议设置 ngrok 的 basic auth
3. **性能**: 
   - 本地网络稳定性影响响应速度
   - 考虑后续部署到云服务器

## 八、故障排查

### ngrok 无法连接
```bash
# 检查 Flask 是否运行
curl http://localhost:5001/api/v1/students

# 检查 ngrok 状态
curl https://your-ngrok-url/api/v1/students -H "X-API-Key: your-key"
```

### API 返回 401
- 检查 X-API-Key 是否正确
- 检查 .env 中的 API_KEY 配置

### 学员匹配失败
- 确认学员姓名在系统中存在
- 检查是否有同名学员需要确认

---

更新日期: 2026-01-28
