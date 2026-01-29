#!/bin/bash
# 公考培训系统 - 一键启动脚本
# 启动 Flask 应用和 ngrok 隧道

echo "=========================================="
echo "  公考培训系统 - 服务启动脚本"
echo "=========================================="

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 项目目录
PROJECT_DIR="/Users/chaim/CodeBuddy/公考项目/gongkao-system"

# 停止已有进程
echo -e "${YELLOW}正在停止已有进程...${NC}"
pkill -f "flask run" 2>/dev/null
pkill -f "ngrok http" 2>/dev/null
sleep 2

# 启动 Flask
echo -e "${YELLOW}启动 Flask 应用...${NC}"
cd "$PROJECT_DIR"
source venv/bin/activate
nohup flask run --port=5001 > /tmp/flask-gongkao.log 2>&1 &
FLASK_PID=$!
sleep 3

# 检查 Flask 是否启动成功
if curl -s -o /dev/null -w "%{http_code}" http://localhost:5001/ | grep -q "200\|404"; then
    echo -e "${GREEN}✓ Flask 启动成功 (PID: $FLASK_PID)${NC}"
else
    echo "✗ Flask 启动失败，请检查日志: /tmp/flask-gongkao.log"
    exit 1
fi

# 启动 ngrok
echo -e "${YELLOW}启动 ngrok 隧道...${NC}"
ngrok http 5001 --region ap --log=stdout > /tmp/ngrok-gongkao.log 2>&1 &
NGROK_PID=$!
sleep 5

# 获取 ngrok 公网地址
NGROK_URL=$(curl -s http://127.0.0.1:4040/api/tunnels 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    if data.get('tunnels'):
        for t in data['tunnels']:
            if t['public_url'].startswith('https'):
                print(t['public_url'])
                break
except:
    pass
" 2>/dev/null)

if [ -n "$NGROK_URL" ]; then
    echo -e "${GREEN}✓ ngrok 启动成功 (PID: $NGROK_PID)${NC}"
    echo ""
    echo "=========================================="
    echo -e "${GREEN}服务启动完成！${NC}"
    echo "=========================================="
    echo ""
    echo "公网地址: $NGROK_URL"
    echo ""
    echo "API 测试:"
    echo "  curl '$NGROK_URL/api/v1/students' -H 'X-API-Key: gongkao-api-key-2026-dev-only' -H 'ngrok-skip-browser-warning: true'"
    echo ""
    echo "日志文件:"
    echo "  Flask: /tmp/flask-gongkao.log"
    echo "  ngrok: /tmp/ngrok-gongkao.log"
    echo ""
    echo -e "${YELLOW}重要：如果 ngrok 地址变化，需要更新扣子插件的 URL${NC}"
    echo ""
    
    # 保存当前地址到文件
    echo "$NGROK_URL" > /tmp/ngrok-current-url.txt
    echo "当前地址已保存到: /tmp/ngrok-current-url.txt"
else
    echo "✗ ngrok 启动失败，请检查日志: /tmp/ngrok-gongkao.log"
    echo "  可能是 authtoken 未配置或网络问题"
fi

echo ""
echo "停止服务: pkill -f 'flask run' && pkill -f 'ngrok http'"
