# 🚀 快速入门指南

> 5 分钟搭建你的第一个 GitHub Agent

## 📋 准备工作

- GitHub 账号（需要创建 GitHub App 的权限）
- Python 3.8+
- Git
- 一个支持的 LLM API（OpenAI, Anthropic 等）

## ⚡ 5 步快速启动

### 1️⃣ 环境设置

```bash
# 克隆项目
git clone https://github.com/your-username/Agent-Demo.git
cd Agent-Demo

# 运行设置脚本
./scripts/setup.sh
```

### 2️⃣ 创建 GitHub App

访问 [GitHub Developer Settings](https://github.com/settings/apps) → "New GitHub App"

**重要配置**：
```
App name: my-code-agent
Webhook URL: https://example.com（临时，稍后更新）
Webhook secret: 生成一个强密码
```

**权限设置**：
- Contents: Write
- Issues: Write  
- Pull requests: Write
- Metadata: Read

**订阅事件**：
- Issues ✅
- Issue comments ✅

### 3️⃣ 配置环境变量

编辑 `.env` 文件，填入关键信息：

```bash
# 必填项
GITHUB_TOKEN=ghp_your_token_here
GITHUB_APP_ID=123456
GITHUB_APP_NAME=my-code-agent
GITHUB_APP_PRIVATE_KEY_PATH=./private-key.pem
LLM_API_KEY=sk-your_api_key_here
WEBHOOK_SECRET=your_strong_secret
```

> 💡 详细配置说明请参考 [TUTORIAL.md](./TUTORIAL.md)

### 4️⃣ 启动服务

```bash
# 启动本地服务
python start_local.py

# 新终端窗口 - 启动 ngrok
./scripts/ngrok.sh
```

复制 ngrok 显示的 HTTPS URL，例如：`https://abc123.ngrok-free.app`

### 5️⃣ 更新 Webhook

回到 GitHub App 设置页面，更新 Webhook URL：
```
https://abc123.ngrok-free.app/api/webhook
```

## 🎯 测试功能

### 1. 安装 App

在 GitHub App 页面点击 "Install App"，选择测试仓库。

### 2. 创建测试 Issue

在仓库中创建一个 Issue，描述一个代码问题。

### 3. 触发 Agent

在 Issue 中评论：
```
@my-code-agent 请帮忙修复这个 bug
```

### 4. 观察响应

Agent 应该：
- ✅ 自动回复确认信息
- ✅ 分析问题并定位文件
- ✅ 生成修复方案
- ✅ 创建修复 PR

## 🚨 常见问题

### Agent 没有回复？

1. **检查 App 安装**：确认 App 已安装到测试仓库
2. **验证名称**：确保 `@` 后的名称与 `GITHUB_APP_NAME` 一致
3. **查看日志**：检查服务是否正常运行

### Webhook 调用失败？

1. **测试服务**：访问 `http://localhost:8080/health`
2. **检查 ngrok**：确认隧道正常工作
3. **验证配置**：在 GitHub App 中测试 Webhook 连接

### LLM 调用错误？

1. **检查 API Key**：确认密钥有效且有余额
2. **测试连接**：直接调用 LLM API 测试
3. **查看限流**：检查是否触发 API 速率限制

## 📚 深入学习

完成快速入门后，建议阅读：

- **[TUTORIAL.md](./TUTORIAL.md)** - 完整的开发教程，包含详细的配置说明和故障排除
- **[API.md](./API.md)** - API 接口和内部组件文档  
- **[PROJECT_STRUCTURE.md](./PROJECT_STRUCTURE.md)** - 项目结构和文件说明

## 🎉 恭喜！

你已经成功搭建了一个基础的 GitHub Agent。现在可以：

- 🔧 根据需求定制 AI 提示词
- 🚀 添加更多自动化功能
- 🌟 部署到生产环境
- 📈 监控和优化性能

有问题随时查看文档或提交 Issue！
