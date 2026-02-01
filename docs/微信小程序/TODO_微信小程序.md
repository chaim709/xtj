# 公考学员服务微信小程序 - 待办事项

> 创建日期: 2026-02-01

---

## 一、上线前必须完成

### 1.1 小程序配置 ⚠️

| 事项 | 操作 | 负责人 |
|-----|------|-------|
| **注册小程序** | 访问 https://mp.weixin.qq.com 注册小程序账号 | 用户 |
| **完成认证** | 企业/个体户认证，300元/年 | 用户 |
| **获取AppID** | 登录后台 → 开发 → 开发设置 → AppID | 用户 |
| **配置AppID** | 修改 `project.config.json` 中的 `appid` 字段 | 用户 |

### 1.2 服务器配置 ⚠️

| 事项 | 操作 | 负责人 |
|-----|------|-------|
| **配置服务器域名** | 小程序后台 → 开发 → 开发设置 → 服务器域名 | 用户 |
| **request合法域名** | 添加 `https://shxtj.chaim.top` | 用户 |
| **业务域名** | 添加视频平台域名（腾讯视频等） | 用户 |

### 1.3 后端配置 ⚠️

| 事项 | 操作 | 说明 |
|-----|------|------|
| **配置微信密钥** | 在服务器 `.env` 文件添加：| |
| | `WX_APPID=你的小程序AppID` | |
| | `WX_SECRET=你的小程序密钥` | |
| **执行数据库迁移** | 在服务器执行 `python add_miniprogram_tables.py` | |
| **安装依赖** | `pip install PyJWT requests pycryptodome` | |
| **重启服务** | `systemctl restart gongkao` | |

### 1.4 TabBar图标 ⚠️

| 事项 | 操作 | 说明 |
|-----|------|------|
| **下载图标** | 从 iconfont.cn 下载8个图标 | 81x81px PNG |
| **放置图标** | 放到 `images/tabbar/` 目录 | 见README |
| **图标列表** | home.png, home-active.png, schedule.png... | 共8个 |

---

## 二、构建和测试

### 2.1 本地开发测试

```bash
# 1. 打开微信开发者工具
# 2. 导入项目：gongkao-miniprogram 目录
# 3. 填入AppID（或使用测试号）

# 4. 安装npm依赖
npm install

# 5. 构建npm（开发者工具 → 工具 → 构建npm）

# 6. 编译运行
```

### 2.2 真机调试

1. 开发者工具 → 预览 → 扫码
2. 测试登录流程
3. 测试各页面功能

---

## 三、第二期功能（规划中）

### 3.1 功能列表

| 功能 | 说明 | 优先级 |
|-----|------|-------|
| 打卡日历 | 可视化打卡记录 | P1 |
| 作业提交 | 完成作业打勾 | P1 |
| 订阅消息 | 上课/作业提醒推送 | P1 |
| 扣子智能督学 | 嵌入扣子对话 | P1 |
| 学习反馈 | 主动提交状态 | P2 |
| 学习报告 | 周报/月报 | P2 |
| 错题复习 | 复习中心 | P2 |

### 3.2 订阅消息模板

需要在小程序后台申请以下模板：

| 模板类型 | 用途 | 触发场景 |
|---------|------|---------|
| 上课提醒 | 课程开始前30分钟 | 定时任务 |
| 作业提醒 | 作业截止前1天 | 定时任务 |
| 督学关怀 | 老师主动发送 | 后台操作 |

---

## 四、运维事项

### 4.1 日常运维

| 事项 | 频率 | 说明 |
|-----|------|------|
| 查看小程序数据 | 每日 | 小程序后台数据分析 |
| 监控后端日志 | 每日 | `journalctl -u gongkao -f` |
| 备份数据库 | 每周 | 见DEPLOYMENT.md |

### 4.2 更新流程

```bash
# 小程序更新
1. 本地修改代码
2. 开发者工具 → 上传
3. 小程序后台 → 版本管理 → 提交审核

# 后端更新
1. git push origin main
2. ssh racknerd "cd /var/www/gongkao-system && git pull"
3. ssh racknerd "systemctl restart gongkao"
```

---

## 五、配置清单汇总

### 需要用户提供/操作

| 序号 | 事项 | 获取方式 |
|-----|------|---------|
| 1 | 小程序AppID | 微信公众平台注册后获取 |
| 2 | 小程序AppSecret | 微信公众平台 → 开发设置 |
| 3 | 完成企业认证 | 微信公众平台 → 认证 |
| 4 | 配置服务器域名 | 微信公众平台 → 开发设置 |
| 5 | 下载TabBar图标 | iconfont.cn |
| 6 | （可选）扣子Bot ID | 扣子平台创建Bot后获取 |

### 需要在服务器配置

```bash
# 1. 编辑.env文件
ssh racknerd
cd /var/www/gongkao-system/gongkao-system
nano .env

# 添加以下内容：
WX_APPID=wx1234567890abcdef
WX_SECRET=abcdef1234567890abcdef1234567890

# 2. 执行迁移
source venv/bin/activate
python add_miniprogram_tables.py

# 3. 安装依赖
pip install PyJWT requests pycryptodome

# 4. 重启服务
sudo systemctl restart gongkao
```

---

## 六、联系支持

如需帮助，请联系：
- 技术问题：查看项目README和文档
- 微信配置：参考微信官方文档
- 认证问题：咨询微信客服

---

> **状态**: 待用户操作
> **下一步**: 完成上述配置后即可上线
