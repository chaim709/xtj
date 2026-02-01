# 公考学员助手 - 微信小程序

[![版本](https://img.shields.io/badge/版本-v2.0.0-blue)](https://github.com/chaim709/xtj)
[![状态](https://img.shields.io/badge/状态-开发完成-success)](https://github.com/chaim709/xtj)

公考培训机构学员服务小程序，聚焦**督学互动**和**课程学习**。

---

## 🌟 核心功能

### 第一期（基础功能）✅
- ✅ 微信登录 + 手机号绑定
- ✅ 学员首页（课程、打卡、消息）
- ✅ 课表查询（今日/本周）
- ✅ 录播课学习
- ✅ 督学消息
- ✅ 个人中心

### 第二期（增强功能）✅
- ✅ 打卡日历（可视化记录）
- ✅ 作业管理（提交/完成）
- ✅ 订阅消息（推送提醒）
- ✅ 扣子智能督学（AI对话）

---

## 📁 项目结构

```
gongkao-miniprogram/
├── README.md              # 本文档
├── 完整功能测试指南.md    # 测试指南
│
├── app.js                 # 应用入口
├── app.json               # 全局配置
├── app.wxss               # 全局样式
├── package.json           # npm依赖
├── project.config.json    # 项目配置
│
├── pages/                 # 页面（11个）
│   ├── index/             # 首页 ⭐
│   ├── login/             # 登录
│   ├── bind-phone/        # 绑定手机号
│   ├── schedule/          # 课表 ⭐
│   ├── study/             # 学习（录播课）⭐
│   ├── mine/              # 我的 ⭐
│   ├── messages/          # 督学消息
│   ├── checkin/           # 打卡日历 🆕
│   ├── homework/          # 作业管理 🆕
│   ├── coze/              # 智能督学 🆕
│   └── webview/           # 视频播放
│
├── utils/                 # 工具函数
│   ├── request.js         # 请求封装
│   ├── auth.js            # 认证管理
│   └── util.js            # 工具函数
│
├── styles/                # 公共样式
│   ├── variables.wxss     # 样式变量
│   └── common.wxss        # 通用样式
│
└── images/                # 静态资源
    └── tabbar/            # TabBar图标
```

---

## 🚀 快速开始

### 1. 安装微信开发者工具

下载地址：https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html

### 2. 导入项目

```
1. 打开微信开发者工具
2. 点击「导入项目」
3. 选择项目目录: gongkao-miniprogram
4. AppID: 选择「测试号」（或填入正式AppID）
5. 点击「导入」
```

### 3. 构建npm包

```bash
# 在项目根目录
npm install

# 然后在微信开发者工具中：
工具 → 构建npm
```

### 4. 配置开发环境

在开发者工具 → 详情 → 本地设置：
- ✅ 不校验合法域名
- ✅ 使用 npm 模块
- ✅ ES6 转 ES5
- ✅ 增强编译

### 5. 开始测试

点击「编译」按钮，小程序启动成功！

---

## 🎨 功能导航

### 底部TabBar

```
┌─────┬─────┬─────┬─────┐
│ 首页 │ 课表 │ 学习 │ 我的 │
└─────┴─────┴─────┴─────┘
```

### 首页功能入口

```
首页
├── 用户卡片
│   └── 今日打卡按钮
├── 今日课程
│   └── 点击查看全部 → 课表Tab
├── 待办任务
│   ├── 完成今日作业 → 作业列表
│   └── 智能督学 → AI对话
└── 督学消息
    └── 查看全部 → 消息列表
```

### 我的页面菜单

```
我的
├── 打卡日历 🆕
├── 学习记录
├── 我的作业 🆕
├── 督学消息
├── 消息提醒设置 🆕
├── 常见问题
├── 联系客服
└── 设置
```

---

## 🔧 技术栈

| 层级 | 技术 | 说明 |
|-----|------|------|
| 小程序框架 | 原生微信小程序 | 官方支持 |
| UI组件库 | Vant Weapp 1.11.3 | 美观易用 |
| 后端服务 | Flask | 复用现有 |
| 数据库 | SQLite | 轻量高效 |
| 认证方式 | JWT Token | 安全标准 |
| 后端地址 | https://shxtj.chaim.top | 线上环境 |

---

## 📡 API接口清单

### 认证接口
- `POST /api/v1/wx/login` - 微信登录
- `POST /api/v1/wx/bind-phone` - 绑定手机号

### 学员接口
- `GET /api/v1/students/me` - 获取学员信息
- `GET /api/v1/students/me/schedule` - 获取课表
- `GET /api/v1/students/me/recordings` - 获取录播课
- `GET /api/v1/students/me/messages` - 获取督学消息
- `POST /api/v1/students/me/checkin` - 每日打卡
- `GET /api/v1/students/me/checkin-history` - 打卡记录 🆕
- `GET /api/v1/students/me/checkin-stats` - 打卡统计 🆕
- `GET /api/v1/students/me/homework` - 获取作业列表
- `POST /api/v1/students/me/homework/<id>/complete` - 完成作业 🆕
- `GET /api/v1/students/me/homework/<id>` - 作业详情 🆕

### 订阅消息接口 🆕
- `POST /api/v1/wx/send-subscribe` - 发送订阅消息
- `GET /api/v1/wx/subscribe-templates` - 获取模板

### 扣子接口 🆕
- `POST /api/v1/coze/chat` - AI对话

---

## 🎯 开发指南

### 本地调试

1. **修改代码**：在 Cursor 或其他编辑器中修改
2. **保存文件**：微信开发者工具自动刷新
3. **查看效果**：模拟器实时预览
4. **调试问题**：打开调试器 → Console/Network

### 真机测试

```
1. 点击「预览」按钮
2. 用微信扫码
3. 在手机上测试
```

### 代码提交

```bash
git add .
git commit -m "描述修改内容"
git push origin main
```

### 部署到服务器

```bash
# 自动部署（代码已在服务器）
ssh racknerd "cd /var/www/gongkao-system && git pull && systemctl restart gongkao"
```

---

## 📚 文档导航

| 文档 | 路径 | 说明 |
|-----|------|------|
| 完整测试指南 | `完整功能测试指南.md` | 逐步测试所有功能 |
| 开发者工具指南 | `docs/微信小程序/微信开发者工具使用指南.md` | 工具使用教程 |
| 订阅消息指南 | `docs/微信小程序/订阅消息配置指南.md` | 订阅消息配置 |
| 架构设计 | `docs/微信小程序/DESIGN_微信小程序.md` | 技术架构 |
| 待办事项 | `docs/微信小程序/TODO_微信小程序.md` | 上线前配置 |

---

## 🔐 环境配置

### 小程序端
在 `project.config.json` 中配置真实AppID（上线前）

### 服务器端
在 `.env` 文件中配置：
```bash
# 微信小程序
WX_APPID=你的小程序AppID
WX_SECRET=你的小程序密钥

# 扣子智能体（可选）
COZE_BOT_ID=你的Bot ID
COZE_TOKEN=你的扣子Token
```

---

## 📊 版本历史

| 版本 | 日期 | 说明 |
|-----|------|------|
| v2.0.0 | 2026-02-01 | 第二期功能完成（打卡日历、作业、订阅、扣子） |
| v1.0.0 | 2026-02-01 | 第一期基础功能完成 |

---

## 🎓 学员使用说明

详见小程序内的帮助中心（计划中）或联系机构老师。

---

## 📞 技术支持

- 项目文档：`docs/微信小程序/`
- 后端仓库：https://github.com/chaim709/xtj
- 问题反馈：查看Console错误信息

---

## 📜 开源协议

本项目为教育培训机构内部使用项目。

---

**开发完成！可以开始完整测试和上线准备。** 🎉
