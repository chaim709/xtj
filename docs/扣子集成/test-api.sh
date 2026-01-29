#!/bin/bash
# 扣子集成API测试脚本
# 使用方法: ./test-api.sh [API_BASE_URL] [API_KEY]

API_BASE="${1:-http://localhost:5001}"
API_KEY="${2:-your-api-key}"

echo "======================================"
echo "扣子集成API测试"
echo "API基址: $API_BASE"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# 测试函数
test_api() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    
    echo -n "测试: $name ... "
    
    if [ "$method" == "GET" ]; then
        response=$(curl -s -w "\n%{http_code}" -X GET \
            -H "X-API-Key: $API_KEY" \
            "$API_BASE$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X POST \
            -H "X-API-Key: $API_KEY" \
            -H "Content-Type: application/json" \
            -d "$data" \
            "$API_BASE$endpoint")
    fi
    
    http_code=$(echo "$response" | tail -n1)
    body=$(echo "$response" | sed '$d')
    
    if [ "$http_code" -ge 200 ] && [ "$http_code" -lt 300 ]; then
        echo -e "${GREEN}通过${NC} (HTTP $http_code)"
        echo "响应: $(echo $body | head -c 200)..."
    else
        echo -e "${RED}失败${NC} (HTTP $http_code)"
        echo "错误: $body"
    fi
    echo ""
}

# 测试1: 学员搜索
test_api "学员搜索" "GET" "/api/v1/students/search?query=张&include_logs=true"

# 测试2: 创建督学记录
test_api "创建督学记录" "POST" "/api/v1/supervision/logs" \
    '{"student_name":"张三","content":"测试督学记录","mood":"积极","study_status":"良好"}'

# 测试3: 获取待办事项
test_api "获取待办事项" "GET" "/api/v1/reminders/pending?type=all&days=3"

# 测试4: 生成周报
test_api "生成周报" "GET" "/api/v1/reports/weekly?week=current"

# 测试5: 获取学员列表 (已有接口)
test_api "学员列表" "GET" "/api/v1/students?page=1&per_page=5"

# 测试6: 获取班次列表 (已有接口)
test_api "班次列表" "GET" "/api/v1/batches"

echo "======================================"
echo "测试完成"
echo "======================================"
