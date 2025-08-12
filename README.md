# Bug Fix Agent - GitHub App

一个智能的 GitHub App，能够自动修复代码问题。用户在 Issue 中 @agent 即可触发自动分析、生成修复方案并提交 PR。

## 功能特性

- 🤖 **GitHub App 集成** - 真正的 @agent 提及支持
- 🚀 **自动响应** - 用户在 Issue 中 @your-app-name 即可触发
- 🧠 **AI 智能分析** - 使用 LLM 智能分析问题并定位相关文件
- 💡 **智能修复方案** - AI 生成具体的修复策略和方案
- 🛠️ **自动修复** - 创建修复分支和 PR，应用 AI 生成的修复
- 📊 **进度追踪** - PR 中实时显示处理进度
- ✅ **AI 驱动** - 真实的 LLM 驱动的 bug 分析和修复

## 快速开始

### 1. 创建 GitHub App

参考 `GITHUB_APP_SETUP.md` 创建你的 GitHub App 并获取必要的认证信息。

### 2. 配置环境变量

复制 `.env.example` 为 `.env` 并填入配置：

```bash
cp .env.example .env
```

编辑 `.env` 文件：

```bash
# GitHub 配置
PLATFORM=github
GITHUB_TOKEN=your_github_personal_access_token
WEBHOOK_SECRET=your_webhook_secret

# GitHub App 配置（推荐，用于 @mention）
GITHUB_APP_ID=your_app_id
GITHUB_APP_PRIVATE_KEY_PATH=./your-app-private-key.pem
GITHUB_APP_CLIENT_ID=your_client_id
GITHUB_APP_CLIENT_SECRET=your_client_secret
GITHUB_APP_NAME=your-app-name

# LLM 配置（AI 功能）
LLM_BASE_URL=https://api.geekai.pro/v1/chat/completions
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-3.5-turbo

# 可选：限制用户和仓库
ALLOWED_USERS=user1,user2
ALLOWED_REPOS=owner/repo1,owner/repo2
```

### 3. 安装依赖

```bash
pip install -r requirements.txt
```

### 4. 启动服务

```bash
# 开发模式
python start_local.py

# 或使用 Docker
docker-compose -f docker/docker-compose.yml up -d
```

### 5. 暴露本地服务（开发环境）

```bash
# 使用 ngrok
./scripts/ngrok.sh

# 或手动运行
ngrok http 8080
```

### 6. 配置 GitHub App Webhook

在 GitHub App 设置中配置 Webhook URL：
- **URL**: `https://your-ngrok-url.ngrok-free.app/api/webhook`  
- **Events**: Issues, Issue comments
- **Secret**: 填入你的 `WEBHOOK_SECRET`

### 7. 安装并测试

1. 将 GitHub App 安装到你的仓库
2. 在任意 Issue 中评论：`@your-app-name fix this bug`
3. Agent 将自动响应并开始处理

## 项目架构

```
Agent-Demo/
├── gateway/              # Webhook 网关服务
│   ├── app.py           # FastAPI 主应用
│   ├── github_api.py    # GitHub API 客户端
│   ├── handlers/        # 事件处理器
│   └── security.py      # 安全验证
├── worker/              # 核心执行器
│   ├── main.py          # 主执行逻辑
│   ├── gitops.py        # Git 操作封装
│   ├── github_app_auth.py # GitHub App 认证
│   └── stages/          # 处理阶段
│       ├── locate.py    # 定位问题
│       ├── propose.py   # 生成方案
│       ├── fix.py       # 应用修复
│       ├── verify.py    # 验证测试
│       └── deploy.py    # 部署演示
├── docker/              # 容器配置
└── scripts/             # 辅助脚本
```

## Agent 工作流程

1. **触发**: 用户在 Issue 中 `@your-app-name` 
2. **响应**: Agent 自动回复确认接单
3. **AI 分析**: 使用 LLM 智能分析问题并定位相关文件
4. **智能修复**: AI 生成具体修复方案并自动应用
5. **验证**: 运行测试和验证
6. **完成**: 创建 PR 并标记为可审查

## AI 驱动的特性

- **🧠 智能问题分析**: LLM 分析 issue 内容，理解问题本质
- **📁 精准文件定位**: AI 基于问题描述识别最相关的代码文件  
- **💡 生成修复方案**: 智能生成具体的修复策略和实施步骤
- **🛠️ 代码修复生成**: 为安全的文件类型生成实际的代码修复
- **📝 详细分析报告**: AI 生成包含根因分析和修复建议的报告

## 支持的触发方式

- `@your-app-name` - 基本提及
- `@your-app-name fix` - 明确修复请求
- `@your-app-name help` - 寻求帮助

## 开发与调试

### 本地运行

```bash
# 启动开发服务器
python start_local.py

# 查看日志
tail -f logs/gateway.log
```

### 测试 LLM 集成

```bash
# 测试 AI 功能
python test_llm_integration.py

# 运行配置测试
python test_github_app.py
```

### 手动测试 Webhook

```bash
curl -X POST http://localhost:8080/api/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issue_comment" \
  -H "X-GitHub-Delivery: test-123" \
  -d '{
    "action": "created",
    "issue": {
      "number": 1,
      "title": "Test Issue", 
      "body": "Test issue body",
      "user": {"login": "testuser"}
    },
    "comment": {
      "body": "@your-app-name fix this",
      "user": {"login": "testuser"}
    },
    "repository": {
      "name": "test-repo",
      "owner": {"login": "testowner"},
      "default_branch": "main"
    }
  }'
```

## 安全考虑

- ✅ Webhook 签名验证
- ✅ GitHub App 权限控制
- ✅ 用户权限检查
- ✅ 仓库白名单限制
- ✅ 安全的分支命名（`agent/*`）
- ✅ 演示模式下只进行安全修改

## 故障排除

### 无法 @mention Agent

1. **确认 GitHub App 已安装**到目标仓库
2. **检查 App 名称**是否与环境变量 `GITHUB_APP_NAME` 一致
3. **验证权限**：App 需要 Issues 和 Pull requests 的读写权限
4. **查看 Webhook 日志**确认事件是否到达

### Webhook 不响应

1. **检查 ngrok 状态**：`curl https://your-ngrok-url.ngrok-free.app/health`
2. **验证 Webhook 配置**：URL 和 Secret 是否正确
3. **查看服务日志**：`docker-compose logs -f gateway`

### API 权限错误

1. **检查 GitHub Token**权限：需要 repo 完整权限
2. **验证 GitHub App**安装和权限配置
3. **确认仓库访问**权限

## 部署到生产环境

### 使用 Docker

```bash
# 构建镜像
docker build -f docker/Dockerfile.gateway -t agent-gateway .
docker build -f docker/Dockerfile.worker -t agent-worker .

# 运行服务
docker-compose -f docker/docker-compose.yml up -d
```

### 环境变量

生产环境必需配置：

```bash
PLATFORM=github
GITHUB_TOKEN=your_production_token
GITHUB_APP_ID=your_app_id
GITHUB_APP_PRIVATE_KEY_PATH=/app/private-key.pem
WEBHOOK_SECRET=strong_random_secret
ALLOWED_REPOS=owner/repo1,owner/repo2  # 限制可用仓库
```

## 贡献指南

1. Fork 项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## License

MIT License - 详见 [LICENSE](LICENSE) 文件
