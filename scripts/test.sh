#!/bin/bash
# GitHub Agent - 本地测试脚本

echo "🧪 GitHub Agent - 本地测试"
echo "=========================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查服务是否运行
echo "🔍 检查服务状态..."
if curl -s http://localhost:8080/health > /dev/null; then
    echo -e "${GREEN}✅ Gateway 服务正在运行 (端口 8080)${NC}"
else
    echo -e "${RED}❌ Gateway 服务未运行${NC}"
    echo ""
    echo "启动方法："
    echo "  python start_local.py"
    echo "或"
    echo "  docker-compose -f docker/docker-compose.yml up -d"
    exit 1
fi

# 测试健康检查端点
echo ""
echo "🏥 测试健康检查端点..."
health_response=$(curl -s http://localhost:8080/health)
if [[ $health_response == *"healthy"* ]]; then
    echo -e "${GREEN}✅ 健康检查通过${NC}"
    echo "   响应: $health_response"
else
    echo -e "${YELLOW}⚠️  健康检查响应异常${NC}"
    echo "   响应: $health_response"
fi

# 测试配置检查
echo ""
echo "⚙️  测试配置状态..."
config_response=$(curl -s http://localhost:8080/config)
if [[ $config_response == *"github"* ]]; then
    echo -e "${GREEN}✅ 配置检查通过${NC}"
else
    echo -e "${YELLOW}⚠️  配置可能需要检查${NC}"
fi

# 测试 Webhook 端点（OPTIONS 请求）
echo ""
echo "� 测试 Webhook 端点..."
webhook_response=$(curl -s -X OPTIONS http://localhost:8080/api/webhook)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Webhook 端点可访问${NC}"
else
    echo -e "${RED}❌ Webhook 端点无法访问${NC}"
fi
# 检查环境变量配置
echo ""
echo "🔧 检查关键环境变量..."
if [ -f ".env" ]; then
    source .env 2>/dev/null || true
    
    required_vars=("GITHUB_TOKEN" "GITHUB_APP_ID" "GITHUB_APP_NAME" "LLM_API_KEY")
    all_configured=true
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var}" ]]; then
            echo -e "${RED}❌ $var 未配置${NC}"
            all_configured=false
        else
            echo -e "${GREEN}✅ $var 已配置${NC}"
        fi
    done
    
    if [ "$all_configured" = true ]; then
        echo -e "${GREEN}✅ 所有关键配置已设置${NC}"
    else
        echo -e "${YELLOW}⚠️  请检查 .env 文件中的配置${NC}"
    fi
else
    echo -e "${RED}❌ .env 文件不存在${NC}"
    echo "   运行 ./scripts/setup.sh 来创建"
fi

echo ""
echo "=========================="
echo -e "${BLUE}🎉 测试完成！${NC}"
echo "=========================="
echo ""
echo -e "${BLUE}📋 接下来的步骤：${NC}"
echo ""
echo "1. ${YELLOW}如果测试通过${NC}，启动 ngrok："
echo "   ./scripts/ngrok.sh"
echo ""
echo "2. ${YELLOW}配置 GitHub App Webhook${NC}："
echo "   使用 ngrok 提供的 HTTPS URL + /api/webhook"
echo ""
echo "3. ${YELLOW}测试功能${NC}："
echo "   在 Issue 中评论 @your-agent-name fix this"
echo ""
echo -e "${BLUE}📚 参考文档：${NC}"
echo "   - TUTORIAL.md 完整教程"
echo "   - API.md API 文档"
