#!/bin/bash
# GitHub Agent - Ngrok 隧道启动脚本

echo "🌐 GitHub Agent - Ngrok 隧道启动"
echo "================================="
echo ""

# 检查 ngrok 是否已安装
if ! command -v ngrok &> /dev/null; then
    echo "❌ ngrok 未安装，请先安装："
    echo ""
    echo "macOS:"
    echo "  brew install ngrok"
    echo ""
    echo "Ubuntu/Debian:"
    echo "  sudo apt update && sudo apt install snapd"
    echo "  sudo snap install ngrok"
    echo ""
    echo "手动安装:"
    echo "  https://ngrok.com/download"
    echo ""
    exit 1
fi

# 检查端口 8080 是否有服务
if lsof -i :8080 > /dev/null 2>&1; then
    echo "✅ 检测到端口 8080 上有服务运行"
else
    echo "⚠️  端口 8080 上没有检测到服务"
    echo ""
    echo "请先启动 GitHub Agent 服务："
    echo "  python start_local.py"
    echo ""
    echo "或使用 Docker："
    echo "  docker-compose -f docker/docker-compose.yml up -d"
    echo ""
    echo "继续启动 ngrok..."
fi

echo ""
echo "🚀 启动 ngrok 隧道 (端口 8080)..."
echo ""
echo "📋 启动后请执行以下步骤："
echo ""
echo "1. 📋 复制 Forwarding 地址"
echo "   示例: https://abc123.ngrok-free.app"
echo ""
echo "2. 🔧 配置 GitHub App Webhook"
echo "   - 访问: GitHub Settings > Developer settings > GitHub Apps > 你的App"
echo "   - 更新 Webhook URL: https://your-url.ngrok-free.app/api/webhook"
echo "   - 选择事件: Issues, Issue comments"
echo "   - 设置 Secret: 使用 .env 中的 WEBHOOK_SECRET"
echo ""
echo "3. ✅ 测试功能"
echo "   - 在 Issue 中评论: @你的agent名称 fix this bug"
echo "   - 查看 Agent 是否自动回复"
echo ""
echo "================================="
echo ""
# 启动 ngrok 隧道
echo "🛑 按 Ctrl+C 停止 ngrok"
echo ""
ngrok http 8080 --log=stdout
