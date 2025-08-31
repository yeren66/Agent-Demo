#!/bin/bash
# GitHub Agent 开发环境设置脚本

echo "🚀 GitHub Agent - 开发环境设置"
echo "=================================="
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查 Python 版本
echo "检查 Python 环境..."
python_version=$(python3 --version 2>/dev/null || python --version 2>/dev/null)
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Python 已安装: $python_version${NC}"
else
    echo -e "${RED}❌ 未找到 Python，请先安装 Python 3.8+${NC}"
    exit 1
fi

# 检查 pip
if command -v pip &> /dev/null || command -v pip3 &> /dev/null; then
    echo -e "${GREEN}✅ pip 已安装${NC}"
else
    echo -e "${RED}❌ 未找到 pip，请先安装 pip${NC}"
    exit 1
fi

# 检查 .env 文件
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 创建环境配置文件..."
    cp .env.example .env
    echo -e "${GREEN}✅ .env 文件已创建${NC}"
    echo -e "${YELLOW}⚠️  请编辑 .env 文件，填入你的 GitHub App 配置${NC}"
    echo ""
    echo "需要配置的关键参数："
    echo "  - GITHUB_TOKEN"
    echo "  - GITHUB_APP_ID"
    echo "  - GITHUB_APP_PRIVATE_KEY_PATH"
    echo "  - GITHUB_APP_CLIENT_ID"
    echo "  - GITHUB_APP_CLIENT_SECRET"
    echo "  - GITHUB_APP_NAME"
    echo "  - LLM_API_KEY"
    echo ""
else
    echo -e "${GREEN}✅ .env 文件已存在${NC}"
fi

# 创建虚拟环境（推荐）
if [ ! -d "venv" ]; then
    echo ""
    echo "📦 创建 Python 虚拟环境..."
    python3 -m venv venv 2>/dev/null || python -m venv venv
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ 虚拟环境创建成功${NC}"
    else
        echo -e "${YELLOW}⚠️  虚拟环境创建失败，将使用系统 Python${NC}"
    fi
fi

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo ""
    echo "🔄 激活虚拟环境..."
    source venv/bin/activate
    echo -e "${GREEN}✅ 虚拟环境已激活${NC}"
fi

# 安装依赖
echo ""
echo "� 安装 Python 依赖..."
pip install -r requirements.txt
if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 依赖安装完成${NC}"
else
    echo -e "${RED}❌ 依赖安装失败${NC}"
    exit 1
fi

# 检查 ngrok 安装
echo ""
echo "🌐 检查 ngrok 安装状态..."
if command -v ngrok &> /dev/null; then
    echo -e "${GREEN}✅ ngrok 已安装${NC}"
    echo "   可以使用 ./scripts/ngrok.sh 启动隧道"
else
    echo -e "${YELLOW}⚠️  ngrok 未安装${NC}"
    echo "   安装方法："
    echo "   - macOS: brew install ngrok"
    echo "   - Ubuntu: sudo snap install ngrok"
    echo "   - 或访问: https://ngrok.com/download"
fi

# 创建必要的目录
echo ""
echo "📁 创建项目目录..."
mkdir -p logs
mkdir -p temp
echo -e "${GREEN}✅ 项目目录创建完成${NC}"

# 设置脚本权限
echo ""
echo "� 设置脚本权限..."
chmod +x scripts/*.sh
echo -e "${GREEN}✅ 脚本权限设置完成${NC}"

# 完成提示
echo ""
echo "=================================="
echo -e "${GREEN}🎉 环境设置完成！${NC}"
echo "=================================="
echo ""
echo -e "${BLUE}📋 接下来的步骤：${NC}"
echo ""
echo "1. ${YELLOW}配置 GitHub App${NC}"
echo "   - 访问 GitHub Settings > Developer settings > GitHub Apps"
echo "   - 创建新的 GitHub App 并获取认证信息"
echo "   - 详细步骤请参考 TUTORIAL.md"
echo ""
echo "2. ${YELLOW}编辑 .env 文件${NC}"
echo "   - 填入 GitHub App 的认证信息"
echo "   - 配置 LLM API 密钥"
echo "   - 设置其他必要参数"
echo ""
echo "3. ${YELLOW}启动本地服务${NC}"
echo "   python start_local.py"
echo ""
echo "4. ${YELLOW}暴露到公网${NC}"
echo "   ./scripts/ngrok.sh"
echo ""
echo "5. ${YELLOW}配置 Webhook${NC}"
echo "   - 在 GitHub App 中设置 Webhook URL"
echo "   - 测试 Agent 功能"
echo ""
echo -e "${BLUE}� 文档参考：${NC}"
echo "   - TUTORIAL.md  - 完整开发教程"
echo "   - API.md       - API 接口文档"
echo "   - README.md    - 项目概述"
echo ""
echo -e "${GREEN}� 有用的命令：${NC}"
echo "   python start_local.py     # 启动本地服务"
echo "   ./scripts/ngrok.sh        # 启动 ngrok 隧道"
echo "   ./scripts/test.sh         # 运行测试"
echo ""
echo "如有问题，请参考 TUTORIAL.md 中的故障排除部分。"
