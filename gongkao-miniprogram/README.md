# 公考学员助手 - 微信小程序

公考培训机构学员服务小程序，聚焦督学互动和课程学习。

## 功能特性

### 第一期（已完成）
- ✅ 微信登录 + 手机号绑定
- ✅ 学员首页（今日课程、打卡、消息预览）
- ✅ 课表查询（今日/本周视图）
- ✅ 录播课列表（科目筛选、分页加载）
- ✅ 督学消息列表
- ✅ 我的页面（信息展示、退出登录）

### 第二期（规划中）
- 每日打卡日历
- 作业提交
- 订阅消息推送
- 扣子智能督学

## 技术栈

- 微信小程序原生开发
- Vant Weapp UI组件库
- Flask后端API

## 项目结构

```
gongkao-miniprogram/
├── app.js                 # 应用入口
├── app.json               # 全局配置
├── app.wxss               # 全局样式
├── project.config.json    # 项目配置
├── package.json           # npm依赖
│
├── pages/                 # 页面目录
│   ├── index/             # 首页
│   ├── schedule/          # 课表
│   ├── study/             # 学习（录播课）
│   ├── mine/              # 我的
│   ├── login/             # 登录
│   ├── bind-phone/        # 绑定手机号
│   ├── messages/          # 消息列表
│   └── webview/           # 内嵌网页
│
├── utils/                 # 工具函数
│   ├── request.js         # HTTP请求封装
│   ├── auth.js            # 认证相关
│   └── util.js            # 通用工具
│
├── styles/                # 公共样式
│   ├── variables.wxss     # 样式变量
│   └── common.wxss        # 通用样式
│
└── images/                # 静态资源
    └── tabbar/            # TabBar图标
```

## 开发指南

### 环境准备

1. 安装 [微信开发者工具](https://developers.weixin.qq.com/miniprogram/dev/devtools/download.html)
2. 注册微信小程序账号，获取AppID

### 本地开发

1. 用微信开发者工具打开项目
2. 在 `project.config.json` 中填入真实AppID
3. 安装npm依赖：
   ```bash
   npm install
   ```
4. 在开发者工具中点击 "工具" → "构建npm"
5. 配置后端地址（app.js中的baseUrl）

### 配置TabBar图标

在 `images/tabbar/` 目录放置8个PNG图标（81x81px）：
- home.png / home-active.png
- schedule.png / schedule-active.png
- study.png / study-active.png
- mine.png / mine-active.png

推荐从 [iconfont.cn](https://www.iconfont.cn/) 获取图标。

## 后端API

小程序依赖以下API接口（Flask后端）：

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/wx/login` | POST | 微信登录 |
| `/api/v1/wx/bind-phone` | POST | 绑定手机号 |
| `/api/v1/students/me` | GET | 获取当前学员信息 |
| `/api/v1/students/me/schedule` | GET | 获取课表 |
| `/api/v1/students/me/recordings` | GET | 获取录播课 |
| `/api/v1/students/me/messages` | GET | 获取督学消息 |
| `/api/v1/students/me/checkin` | POST | 每日打卡 |

后端地址: `https://shxtj.chaim.top/api/v1`

## 部署上线

1. 在微信公众平台完成小程序认证（300元/年）
2. 配置服务器域名白名单
3. 配置业务域名（视频外链）
4. 提交审核

## 版本历史

| 版本 | 日期 | 说明 |
|------|------|------|
| v1.0.0 | 2026-02-01 | 初始版本，基础功能 |

## 联系方式

如有问题，请联系开发者。
