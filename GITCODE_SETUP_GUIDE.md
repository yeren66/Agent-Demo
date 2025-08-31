# GitCode 机器人设置指南

## 架构说明

GitCode 不同于 GitHub，没有"可安装应用"机制，因此我们采用 **仓库级 Webhook + 机器人 PAT** 的组合方式：

1. **机器人账号**: 专门用于自动化操作的 GitCode 账号
2. **仓库级 Webhook**: 在目标仓库设置 Webhook 来接收事件
3. **PAT 认证**: 使用机器人账号的 Personal Access Token 进行 API 认证

## 1. 准备机器人账号

### 创建/准备机器人账号
1. 注册一个专门的 GitCode 账号作为机器人 (如: `bug-fix-agent-bot`)
2. 将此机器人账号加入到目标仓库
3. 赋予机器人足够的权限:
   - ✅ **读取权限**: 访问仓库内容、Issue
   - ✅ **写入权限**: 创建分支、推送代码  
   - ✅ **Issue 管理**: 评论、添加标签、指派
   - ✅ **PR 管理**: 创建、更新 Pull Request

### 生成 Personal Access Token (PAT)
1. 使用机器人账号登录 GitCode
2. 访问: 用户设置 → 访问令牌 → 新建个人访问令牌
3. 设置权限范围:
   - ✅ `api`: 完整 API 访问权限
   - ✅ `read_user`: 读取用户信息
   - ✅ `read_repository`: 读取仓库
   - ✅ `write_repository`: 写入仓库
4. 复制生成的 Token（类似: `abc123...xyz789`）

## 2. 配置项目仓库

### 将机器人加入仓库
1. 在目标仓库设置中
2. 找到 "成员管理" 或 "协作者"
3. 添加机器人账号为协作者
4. 赋予 **Developer** 或 **Maintainer** 权限

### 设置仓库 Webhook  
1. 在目标仓库设置中找到 "Webhook"
2. 添加新的 Webhook:

**Webhook URL**:
```
https://your-domain.com/api/webhook
```
(本地测试使用 ngrok: `https://abc123.ngrok.io/api/webhook`)

**事件类型**:
- ✅ **Issues events** (Issue 创建、更新)
- ✅ **Note Hook** (评论事件)
- ✅ **Issue Hook** (Issue 事件)

**Secret Token**:
```
123456
```

## 3. 更新配置文件

将机器人信息填入 `.env` 文件:

```env
# GitCode 机器人 PAT 认证配置
GITCODE_PAT=你的机器人PAT这里
GITCODE_BOT_USERNAME=你的机器人用户名

# Webhook 配置  
WEBHOOK_SECRET=123456
```

## 4. 本地开发配置

### 使用 ngrok 暴露本地服务
```bash
# 安装 ngrok (如果还没有)
brew install ngrok

# 暴露本地端口
ngrok http 8080
```

然后将 ngrok 提供的 HTTPS URL 用于 Webhook URL:
```
https://abc123.ngrok.io/api/webhook
```

## 8. 使用说明

### 触发 Agent
在任何 Issue 或评论中提及：
```
@bug-fix-agent fix
```
或简单的：
```
@bug-fix-agent
```

### Agent 响应
Agent 会：
1. 立即回复确认消息
2. 分析问题描述
3. 创建修复分支
4. 生成修复代码
5. 创建 Pull Request

## 9. 注意事项

- GitCode OAuth 应用使用 `client_id`/`client_secret` 模式 (不是 GitHub 的 app_id)
- 确保回调 URL 与配置完全匹配
- Webhook secret 用于验证请求来源的安全性
- 本地开发时建议使用 ngrok 等工具暴露服务

## 10. 故障排除

### 常见问题
1. **授权失败**: 检查 client_id 和 redirect_uri 是否正确
2. **Webhook 不触发**: 检查 URL 可访问性和事件类型配置
3. **权限不足**: 确保申请了足够的 API 权限范围

### 调试方法
- 查看 Agent 日志输出
- 检查 GitCode Webhook 日志
- 使用 ngrok 查看请求详情
