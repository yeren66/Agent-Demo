# GitHub Agent 开发完整教程

本教程将带你从零开始构建一个完整的 GitHub Agent，实现在 Issue 中通过 @mention 触发自动化代码修复功能。

## 目录

1. [项目概述](#项目概述)
2. [前置准备](#前置准备)
3. [GitHub App 创建与配置](#github-app-创建与配置)
4. [本地开发环境搭建](#本地开发环境搭建)
5. [核心代码架构解析](#核心代码架构解析)
6. [配置文件详解](#配置文件详解)
7. [本地服务运行](#本地服务运行)
8. [Ngrok 公网映射](#ngrok-公网映射)
9. [Webhook 配置与测试](#webhook-配置与测试)
10. [功能测试与验证](#功能测试与验证)
11. [生产环境部署](#生产环境部署)
12. [故障排除指南](#故障排除指南)

## 项目概述

### 功能特性

这个 GitHub Agent 具备以下核心功能：

- **🤖 GitHub App 集成** - 支持真正的 @mention 触发
- **🚀 自动响应** - 用户在 Issue 中 @agent 即可触发
- **🧠 AI 智能分析** - 使用 LLM 分析问题并定位相关文件
- **💡 智能修复方案** - AI 生成具体的修复策略
- **🛠️ 自动修复** - 创建修复分支和 PR，应用修复
- **📊 进度追踪** - PR 中实时显示处理进度
- **✅ AI 驱动** - 完全基于 LLM 的智能分析和修复

### 工作流程

```mermaid
graph TD
    A[用户在Issue中@agent] --> B[GitHub Webhook触发]
    B --> C[Agent接收并验证请求]
    C --> D[AI分析问题内容]
    D --> E[定位相关代码文件]
    E --> F[生成修复方案]
    F --> G[创建修复分支]
    G --> H[应用代码修复]
    H --> I[创建Pull Request]
    I --> J[用户审查并合并]
```

## 前置准备

### 环境要求

- Python 3.8+
- Git
- GitHub 账号（需要管理员权限以创建 GitHub App）
- 网络环境（能够访问 GitHub API 和 LLM 服务）

### 必需工具

```bash
# 安装 Python 依赖管理工具
pip install --upgrade pip

# 安装 ngrok（用于本地开发）
# macOS
brew install ngrok

# Ubuntu/Debian
sudo apt update && sudo apt install snapd
sudo snap install ngrok

# Windows
# 下载并安装：https://ngrok.com/download
```

## GitHub App 创建与配置

### 步骤 1：创建 GitHub App

1. **访问 GitHub Settings**
   - 进入 GitHub → Settings → Developer settings → GitHub Apps
   - 点击 "New GitHub App"

2. **基本信息配置**
   ```
   GitHub App name: your-agent-name
   Description: AI-powered code fixing agent
   Homepage URL: https://github.com/your-username/your-repo
   ```

3. **Webhook 配置（临时）**
   ```
   Webhook URL: https://example.com/webhook（稍后更新）
   Webhook secret: 生成一个强密码，记录下来
   ```

4. **权限配置**

   **Repository permissions（仓库权限）**：
   ```
   Contents: Write          （读写仓库内容）
   Issues: Write            （管理 Issues）
   Pull requests: Write     （创建和管理 PR）
   Metadata: Read           （读取仓库元数据）
   ```

   **Account permissions（账户权限）**：
   ```
   Email addresses: Read    （可选，用于用户识别）
   ```

5. **Subscribe to events（订阅事件）**
   ```
   ☑️ Issues
   ☑️ Issue comments
   ☑️ Pull requests
   ```

6. **Where can this GitHub App be installed?**
   - 选择 "Only on this account"（推荐用于学习）
   - 或 "Any account"（如果要公开发布）

### 步骤 2：获取认证信息

创建完成后，记录以下信息：

```bash
# 在 GitHub App 页面获取
App ID: 123456
Client ID: Iv1.a1b2c3d4e5f6g7h8
Client Secret: 点击 "Generate a new client secret"

# 生成私钥
点击 "Generate a private key" → 下载 .pem 文件
```

### 步骤 3：安装 GitHub App

1. 在 GitHub App 设置页面，点击 "Install App"
2. 选择要安装的账户和仓库
3. 确认权限并完成安装

## 本地开发环境搭建

### 步骤 1：克隆项目

```bash
git clone https://github.com/your-username/Agent-Demo.git
cd Agent-Demo
```

### 步骤 2：创建虚拟环境

```bash
# 创建虚拟环境
python -m venv venv

# 激活虚拟环境
# macOS/Linux
source venv/bin/activate

# Windows
venv\Scripts\activate
```

### 步骤 3：安装依赖

```bash
pip install -r requirements.txt
```

### 步骤 4：配置环境变量

复制示例配置文件：

```bash
cp .env.example .env
```

## 配置文件详解

编辑 `.env` 文件，以下是详细的配置说明：

### GitHub 配置

```bash
# 基础平台配置
PLATFORM=github

# GitHub Personal Access Token
# 需要 repo 完整权限，用于 API 调用
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Webhook 签名验证密钥
# 必须与 GitHub App 中设置的 Webhook Secret 一致
WEBHOOK_SECRET=your_strong_secret_here
```

### GitHub App 配置（核心）

```bash
# GitHub App ID（在 App 设置页面获取）
GITHUB_APP_ID=123456

# 私钥文件路径（下载的 .pem 文件）
GITHUB_APP_PRIVATE_KEY_PATH=./your-app-private-key.pem

# Client ID（在 App 设置页面获取）
GITHUB_APP_CLIENT_ID=Iv1.a1b2c3d4e5f6g7h8

# Client Secret（需要生成）
GITHUB_APP_CLIENT_SECRET=your_generated_client_secret

# App 名称（用于 @mention）
GITHUB_APP_NAME=your-agent-name
```

### LLM 配置

```bash
# LLM API 基础 URL
LLM_BASE_URL=https://api.openai.com/v1/chat/completions

# API 密钥
LLM_API_KEY=sk-your_api_key_here

# 使用的模型
LLM_MODEL=gpt-3.5-turbo
```

### 可选安全配置

```bash
# 限制允许的用户（用逗号分隔）
ALLOWED_USERS=user1,user2,user3

# 限制允许的仓库（用逗号分隔）
ALLOWED_REPOS=owner/repo1,owner/repo2

# 调试模式
DEBUG=true
LOG_LEVEL=INFO
```

### 私钥文件处理

将下载的私钥文件放置到项目根目录：

```bash
# 确保私钥文件在正确位置
ls -la your-app-private-key.pem

# 设置正确的权限（Linux/macOS）
chmod 600 your-app-private-key.pem
```

## 核心代码架构解析

### 项目结构

```
Agent-Demo/
├── gateway/              # Web 服务网关
│   ├── app.py           # FastAPI 主应用
│   ├── github_api.py    # GitHub API 封装
│   ├── security.py      # 安全验证中间件
│   ├── task_queue.py    # 任务队列管理
│   └── handlers/        # 事件处理器
│       ├── __init__.py
│       └── gitcode.py   # GitHub 事件处理
├── worker/              # 核心业务逻辑
│   ├── main.py          # 主执行入口
│   ├── github_app_auth.py # GitHub App 认证
│   ├── git_platform_api.py # Git 平台 API
│   ├── gitops.py        # Git 操作封装
│   ├── llm_client.py    # LLM 客户端
│   ├── templates.py     # 消息模板
│   └── stages/          # 处理阶段
│       ├── locate.py    # 问题定位
│       ├── propose.py   # 方案生成
│       ├── fix.py       # 代码修复
│       ├── verify.py    # 验证测试
│       └── deploy.py    # 部署提交
├── scripts/             # 辅助脚本
│   ├── ngrok.sh         # Ngrok 启动脚本
│   ├── setup.sh         # 环境设置脚本
│   └── test.sh          # 测试脚本
├── docker/              # 容器化配置
│   ├── docker-compose.yml
│   ├── Dockerfile.gateway
│   └── Dockerfile.worker
└── start_local.py       # 本地开发启动脚本
```

### 关键组件说明

#### 1. Gateway（网关服务）

**app.py** - 主要的 FastAPI 应用：
```python
# 处理 GitHub Webhook 请求
@app.post("/api/webhook")
async def handle_webhook(request: Request)

# 健康检查端点
@app.get("/health") 
async def health_check()
```

**security.py** - 安全验证：
```python
# Webhook 签名验证
def verify_github_signature(payload, signature, secret)

# 用户权限检查
def check_user_permission(user, allowed_users)
```

#### 2. Worker（核心执行器）

**main.py** - 业务流程编排：
```python
# 主要的任务执行函数
async def process_issue_comment(payload)

# 各个处理阶段
- locate_stage()    # AI 分析和文件定位
- propose_stage()   # 生成修复方案  
- fix_stage()       # 应用代码修复
- verify_stage()    # 测试验证
- deploy_stage()    # 创建 PR
```

**llm_client.py** - LLM 集成：
```python
# 与 LLM 服务交互
async def chat_completion(messages, model)

# 专门的分析函数
async def analyze_issue(issue_content)
async def locate_files(issue_content, repo_structure)
async def generate_fix_plan(issue_content, file_content)
```

## 本地服务运行

### 启动服务

使用项目提供的启动脚本：

```bash
python start_local.py
```

这个脚本会：
1. 加载 `.env` 环境变量
2. 验证配置完整性
3. 启动 FastAPI 服务（端口 8080）
4. 启用自动重载（开发模式）

### 服务验证

**健康检查**：
```bash
curl http://localhost:8080/health
```

预期响应：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "github-agent"
}
```

**配置检查**：
```bash
curl http://localhost:8080/config
```

## Ngrok 公网映射

### 为什么需要 Ngrok

GitHub Webhook 需要一个公网可访问的 URL，在本地开发时，我们使用 Ngrok 将本地服务映射到公网。

### 安装和配置 Ngrok

1. **注册账号**：访问 [ngrok.com](https://ngrok.com) 注册免费账号

2. **获取 Authtoken**：
   ```bash
   ngrok config add-authtoken YOUR_AUTHTOKEN
   ```

3. **启动映射**：
   ```bash
   # 使用项目脚本
   ./scripts/ngrok.sh
   
   # 或手动启动
   ngrok http 8080
   ```

### 使用项目的 Ngrok 脚本

查看 `scripts/ngrok.sh` 的内容：

```bash
#!/bin/bash
echo "🚀 启动 Ngrok 隧道..."
echo "📍 本地服务: http://localhost:8080"
echo "🔗 Webhook 路径: /api/webhook"
echo ""

# 启动 ngrok
ngrok http 8080 --log=stdout
```

启动后会看到类似输出：
```
Session Status    online
Account           your-email@example.com
Version           3.1.0
Region            United States (us)
Latency           45.123ms
Web Interface     http://127.0.0.1:4040
Forwarding        https://abc123.ngrok-free.app -> http://localhost:8080
```

记录下 Forwarding 地址，这就是你的公网 Webhook URL。

## Webhook 配置与测试

### 更新 GitHub App Webhook

1. **返回 GitHub App 设置**
   - GitHub → Settings → Developer settings → GitHub Apps → 你的 App

2. **更新 Webhook URL**
   ```
   Webhook URL: https://abc123.ngrok-free.app/api/webhook
   ```

3. **测试连接**
   - 点击 "Redeliver" 测试已有的 webhook 事件
   - 或在安装了 App 的仓库中创建一个测试 Issue

### 手动测试 Webhook

你可以使用 curl 模拟 GitHub Webhook：

```bash
curl -X POST http://localhost:8080/api/webhook \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: issue_comment" \
  -H "X-GitHub-Delivery: test-12345" \
  -H "X-Hub-Signature-256: sha256=YOUR_SIGNATURE" \
  -d '{
    "action": "created",
    "issue": {
      "number": 1,
      "title": "Test Bug Report",
      "body": "There is a bug in the login function",
      "user": {"login": "testuser"},
      "repository": {
        "name": "test-repo",
        "owner": {"login": "testowner"}
      }
    },
    "comment": {
      "body": "@your-agent-name please fix this issue",
      "user": {"login": "testuser"}
    },
    "repository": {
      "name": "test-repo",
      "owner": {"login": "testowner"},
      "default_branch": "main",
      "clone_url": "https://github.com/testowner/test-repo.git"
    }
  }'
```

### 查看日志

监控服务日志来调试问题：

```bash
# 查看实时日志
tail -f logs/app.log

# 或者如果使用 Docker
docker-compose logs -f gateway worker
```

## 功能测试与验证

### 端到端测试流程

1. **创建测试 Issue**
   - 在已安装 App 的仓库中创建一个 Issue
   - 描述一个代码问题，例如："登录函数出现空指针异常"

2. **触发 Agent**
   - 在 Issue 中评论：`@your-agent-name fix this bug`
   - 观察 Agent 是否自动回复

3. **检查处理过程**
   - Agent 应该回复确认信息
   - 检查是否创建了新的修复分支
   - 查看 PR 是否正确创建

### 预期的 Agent 响应

**第一次回复**（确认接单）：
```
👋 我是 AI 修复助手，已接收到您的修复请求！

🔍 **问题分析中...**
- 正在分析 Issue 内容
- 定位相关代码文件
- 生成修复方案

我会在此 Issue 中实时更新处理进度，完成后会创建 PR 供您审查。
```

**处理过程中的更新**：
```
🧠 **AI 分析完成**
- 识别问题类型：空指针异常
- 定位文件：`src/auth.py`, `src/login.py`
- 问题根因：未对用户输入进行空值检查

💡 **修复方案生成**
- 添加输入验证函数
- 增强错误处理逻辑  
- 更新相关测试用例

🛠️ **开始修复...**
```

**完成后的总结**：
```
✅ **修复完成**

📋 **修复总结**
- 创建分支：`agent/fix-null-pointer-issue-123`
- 修改文件：2 个
- 新增代码：15 行
- PR 链接：#456

🔍 **修复内容**
1. 在 `validateUser()` 函数中添加了空值检查
2. 改进了错误处理和用户提示
3. 添加了相应的单元测试

请审查 PR 并测试修复效果！
```

### 验证修复质量

1. **检查创建的 PR**
   - 代码改动是否合理
   - 是否有清晰的提交信息
   - 修复是否针对问题本身

2. **代码质量检查**
   - 语法是否正确
   - 逻辑是否合理
   - 是否遵循项目代码规范

3. **测试修复分支**
   ```bash
   git checkout agent/fix-null-pointer-issue-123
   # 运行项目测试
   python -m pytest
   # 手动测试修复的功能
   ```

### 域名和 HTTPS

#### 1. 获取域名

注册一个域名或使用子域名，例如：
- `agent.yourcompany.com`
- `github-bot.yourcompany.com`

#### 2. 配置 HTTPS

**使用 Let's Encrypt（免费）**：
```bash
# 安装 certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d agent.yourcompany.com

# 自动续期
sudo crontab -e
# 添加：0 12 * * * /usr/bin/certbot renew --quiet
```

**使用云平台证书**：
- AWS: Certificate Manager
- GCP: Google-managed SSL certificates  
- Azure: App Service certificates

#### 3. 更新 GitHub App Webhook

将 Webhook URL 更新为生产域名：
```
https://agent.yourcompany.com/api/webhook
```

### 监控和日志

#### 1. 应用监控

**健康检查端点**：
```bash
# 设置监控检查
curl -f https://agent.yourcompany.com/health || exit 1
```

**关键指标监控**：
- 响应时间
- 错误率
- 活跃连接数
- 内存和 CPU 使用率

#### 2. 日志管理

**集中式日志收集**：
```yaml
# docker-compose.yml 中添加日志配置
version: '3.8'
services:
  gateway:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: "fluentd:24224"
        tag: "gateway"
  
  worker:
    logging:
      driver: "fluentd"
      options:
        fluentd-address: "fluentd:24224"
        tag: "worker"
```

### 扩展和优化

#### 1. 水平扩展

```yaml
# docker-compose.yml
version: '3.8'
services:
  gateway:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
        max_attempts: 3

  worker:
    deploy:
      replicas: 5  # 根据负载调整
```

#### 2. 缓存优化

**Redis 缓存配置**：
```python
# 在代码中添加缓存
import redis

# 缓存仓库结构和分析结果
cache = redis.Redis(host='redis', port=6379, db=0)

def cache_repo_analysis(repo_key, analysis):
    cache.setex(f"analysis:{repo_key}", 3600, analysis)  # 1小时缓存
```

#### 3. 速率限制

```python
# 添加到 FastAPI 中间件
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)

@app.post("/api/webhook")
@limiter.limit("10/minute")  # 每分钟最多 10 个请求
async def handle_webhook(request: Request):
    # Webhook 处理逻辑
    pass
```

## 故障排除指南

### 常见问题及解决方案

#### 1. Agent 无法响应 @mention

**症状**：在 Issue 中 @agent 但没有回复

**排查步骤**：

1. **检查 GitHub App 安装**：
   ```bash
   # 验证 App 是否安装到仓库
   curl -H "Authorization: Bearer YOUR_TOKEN" \
        "https://api.github.com/repos/OWNER/REPO/installation"
   ```

2. **验证 App 名称**：
   ```bash
   # 检查环境变量
   echo $GITHUB_APP_NAME
   
   # 在 Issue 中使用确切的名称
   @your-exact-app-name fix this
   ```

3. **检查权限设置**：
   - Issues: Write
   - Pull requests: Write  
   - Contents: Write
   - Metadata: Read

4. **查看 Webhook 日志**：
   ```bash
   # 在 GitHub App 设置中查看 "Recent Deliveries"
   # 或查看服务日志
   docker-compose logs -f gateway
   ```

#### 2. Webhook 签名验证失败

**症状**：收到 Webhook 但签名验证失败

**解决方案**：

1. **检查 Secret 配置**：
   ```bash
   # 确保 .env 中的 WEBHOOK_SECRET 与 GitHub App 设置一致
   echo $WEBHOOK_SECRET
   ```

2. **验证签名算法**：
   ```python
   # 确保使用 SHA-256
   signature = "sha256=" + hmac.new(
       webhook_secret.encode(),
       payload,
       hashlib.sha256
   ).hexdigest()
   ```

3. **调试签名过程**：
   ```python
   # 在 security.py 中添加调试日志
   print(f"Expected: {expected_signature}")
   print(f"Received: {received_signature}")
   print(f"Payload length: {len(payload)}")
   ```

#### 3. LLM API 调用失败

**症状**：Agent 无法进行 AI 分析

**排查步骤**：

1. **测试 API 连接**：
   ```bash
   curl -X POST "$LLM_BASE_URL" \
     -H "Authorization: Bearer $LLM_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{
       "model": "gpt-3.5-turbo",
       "messages": [{"role": "user", "content": "Hello"}],
       "max_tokens": 100
     }'
   ```

2. **检查 API 配额**：
   - 确认 API Key 有效
   - 检查账户余额
   - 验证速率限制

3. **调整重试逻辑**：
   ```python
   # 在 llm_client.py 中增加重试
   import tenacity
   
   @tenacity.retry(
       wait=tenacity.wait_exponential(multiplier=1, min=4, max=10),
       stop=tenacity.stop_after_attempt(3)
   )
   async def chat_completion(messages):
       # API 调用逻辑
   ```

#### 4. GitHub API 权限错误

**症状**：无法创建分支或 PR

**解决方案**：

1. **检查 Token 权限**：
   ```bash
   # 测试 Token 权限
   curl -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/user"
   
   # 检查仓库权限  
   curl -H "Authorization: token $GITHUB_TOKEN" \
        "https://api.github.com/repos/OWNER/REPO"
   ```

2. **验证 GitHub App 权限**：
   ```python
   # 测试 App Token 生成
   from worker.github_app_auth import GitHubAppAuth
   
   auth = GitHubAppAuth()
   token = auth.get_installation_token(installation_id)
   print(f"App Token: {token[:10]}...")
   ```

3. **检查分支保护**：
   - 确认目标仓库没有严格的分支保护规则
   - 验证 Agent 有权限创建新分支

#### 5. 服务无法启动

**症状**：运行 `python start_local.py` 失败

**排查步骤**：

1. **检查依赖安装**：
   ```bash
   pip list | grep fastapi
   pip list | grep uvicorn
   
   # 重新安装依赖
   pip install -r requirements.txt
   ```

2. **验证端口占用**：
   ```bash
   # 检查端口 8080 是否被占用
   lsof -i :8080
   netstat -tlnp | grep 8080
   
   # 使用其他端口
   uvicorn gateway.app:app --port 8081
   ```

3. **检查文件权限**：
   ```bash
   # 确保私钥文件权限正确
   chmod 600 your-app-private-key.pem
   
   # 检查目录权限
   ls -la gateway/
   ls -la worker/
   ```

### 日志分析技巧

#### 重要日志关键词

搜索这些关键词来快速定位问题：

```bash
# 错误相关
grep -i "error\|exception\|failed" logs/app.log

# 认证相关  
grep -i "auth\|token\|signature" logs/app.log

# GitHub API 相关
grep -i "github\|api\|webhook" logs/app.log

# LLM 相关
grep -i "llm\|openai\|chat" logs/app.log
```

#### 开启调试模式

在 `.env` 中设置：

```bash
DEBUG=true
LOG_LEVEL=DEBUG
```

这会输出更详细的调试信息，包括：
- HTTP 请求/响应详情
- API 调用参数
- 内部处理步骤
- 错误堆栈信息

### 性能优化建议

#### 1. 响应时间优化

- 使用异步处理避免阻塞
- 实现请求去重避免重复处理
- 缓存常用的分析结果

#### 2. 资源使用优化

```python
# 设置合理的超时
import asyncio

async def with_timeout(coro, timeout=30):
    return await asyncio.wait_for(coro, timeout=timeout)

# 限制并发处理数量
semaphore = asyncio.Semaphore(5)  # 最多同时处理5个请求
```

#### 3. 错误恢复策略

```python
# 实现优雅的错误恢复
async def safe_process(payload):
    try:
        return await process_issue_comment(payload)
    except Exception as e:
        # 记录错误但不影响其他请求
        logger.error(f"Processing failed: {e}")
        # 可以实现重试队列
        await retry_queue.put(payload)
```
