# Cloudflare Tunnel 配置指南

使用 Cloudflare Tunnel 将本地学生管理系统暴露到公网，供扣子智能体调用。

## 优势对比

| 特性 | ngrok (免费版) | Cloudflare Tunnel |
|------|---------------|-------------------|
| 地址固定 | 每次重启变化 | 固定子域名 |
| 费用 | 免费有限制 | 免费 |
| 速度 | 较慢 | 快（国内节点） |
| 安全 | 基础 | WAF + DDoS 防护 |
| 自定义域名 | 需付费 | 免费 |

## 前置条件

- 域名 `chaim.top` 已托管到 Cloudflare
- Cloudflare 账号已登录

---

## 一、安装 cloudflared

### macOS

```bash
brew install cloudflared
```

### 验证安装

```bash
cloudflared --version
```

---

## 二、登录 Cloudflare

```bash
cloudflared tunnel login
```

这会打开浏览器，选择域名 `chaim.top` 进行授权。

授权成功后，凭证会保存在 `~/.cloudflared/cert.pem`

---

## 三、创建 Tunnel

```bash
# 创建名为 gongkao-api 的 tunnel
cloudflared tunnel create gongkao-api
```

成功后会显示 Tunnel ID，记下来：

```
Created tunnel gongkao-api with id xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

---

## 四、配置 DNS 记录

```bash
# 将子域名 gongkao-api.chaim.top 指向 tunnel
cloudflared tunnel route dns gongkao-api gongkao-api.chaim.top
```

这会在 Cloudflare DNS 中自动创建一条 CNAME 记录。

---

## 五、创建配置文件

创建 `~/.cloudflared/config.yml`：

```yaml
# Cloudflare Tunnel 配置
tunnel: gongkao-api
credentials-file: /Users/chaim/.cloudflared/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx.json

ingress:
  # 学生管理系统 API
  - hostname: gongkao-api.chaim.top
    service: http://localhost:5001
    originRequest:
      noTLSVerify: true
  
  # 可选：题库系统 API
  # - hostname: tiku-api.chaim.top
  #   service: http://localhost:5002
  
  # 默认规则（必须）
  - service: http_status:404
```

**注意**: 将 `credentials-file` 中的 ID 替换为你的实际 Tunnel ID。

---

## 六、启动 Tunnel

### 前台运行（测试）

```bash
cloudflared tunnel run gongkao-api
```

### 后台运行（推荐）

```bash
# 使用 tmux
tmux new -s cloudflared
cloudflared tunnel run gongkao-api
# Ctrl+B, D 退出但保持运行

# 或者安装为服务
sudo cloudflared service install
sudo cloudflared service start
```

---

## 七、验证连接

```bash
# 测试 API 是否可访问
curl https://gongkao-api.chaim.top/api/v1/students \
  -H "X-API-Key: gongkao-api-key-2026-dev-only"
```

预期返回学员列表 JSON。

---

## 八、更新扣子插件配置

在扣子平台的插件配置中，将 API 地址更新为：

```
https://gongkao-api.chaim.top
```

### 各接口完整 URL

| 接口 | URL |
|------|-----|
| 查询学员 | `https://gongkao-api.chaim.top/api/v1/students/search` |
| 创建督学记录 | `https://gongkao-api.chaim.top/api/v1/supervision/logs` |
| 推送作业 | `https://gongkao-api.chaim.top/api/v1/homework/batch-push` |
| 获取待办 | `https://gongkao-api.chaim.top/api/v1/reminders/pending` |
| 生成周报 | `https://gongkao-api.chaim.top/api/v1/reports/weekly` |

---

## 九、安全加固（可选）

### 9.1 Cloudflare Access（零信任访问）

可以在 Cloudflare Zero Trust 中配置访问策略，限制只有特定来源可以访问 API。

### 9.2 IP 白名单

在 Cloudflare WAF 中配置规则，只允许扣子服务器 IP 访问。

### 9.3 更换 API Key

生产环境务必使用强密码：

```bash
# 生成随机 API Key
openssl rand -hex 32
```

更新 `.env` 中的 `API_KEY`，同时更新扣子插件配置。

---

## 十、常用命令

```bash
# 查看所有 tunnel
cloudflared tunnel list

# 查看 tunnel 状态
cloudflared tunnel info gongkao-api

# 删除 tunnel
cloudflared tunnel delete gongkao-api

# 查看日志
cloudflared tunnel run gongkao-api --loglevel debug
```

---

## 十一、故障排查

### Tunnel 无法连接

```bash
# 检查 Flask 是否运行
curl http://localhost:5001/api/v1/students -H "X-API-Key: your-key"

# 检查 tunnel 状态
cloudflared tunnel info gongkao-api
```

### DNS 解析失败

```bash
# 检查 DNS 记录
dig gongkao-api.chaim.top

# 在 Cloudflare 控制台确认 CNAME 记录存在
```

### API 返回 502

- 确认 Flask 应用正在运行
- 检查 config.yml 中的端口是否正确

---

## 十二、开机自启（macOS）

创建 LaunchAgent：

```bash
# 创建 plist 文件
cat > ~/Library/LaunchAgents/com.cloudflare.tunnel.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.cloudflare.tunnel</string>
    <key>ProgramArguments</key>
    <array>
        <string>/opt/homebrew/bin/cloudflared</string>
        <string>tunnel</string>
        <string>run</string>
        <string>gongkao-api</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>/tmp/cloudflared.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/cloudflared.err</string>
</dict>
</plist>
EOF

# 加载服务
launchctl load ~/Library/LaunchAgents/com.cloudflare.tunnel.plist

# 启动服务
launchctl start com.cloudflare.tunnel
```

---

## 最终架构

```
督学老师(手机扣子App) 
    ↓ 语音输入
扣子智能体 
    ↓ HTTPS 请求
gongkao-api.chaim.top (Cloudflare CDN)
    ↓ Cloudflare Tunnel
本地 Mac (cloudflared)
    ↓ localhost:5001
Flask 学生管理系统
    ↓ SQLAlchemy
SQLite 数据库
```

---

更新日期: 2026-01-28
