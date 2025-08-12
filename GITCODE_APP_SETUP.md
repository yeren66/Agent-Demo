# GitCode App 设置指南

为了让用户能够在 GitCode Issue 中使用 `@your-app-name` 提及您的 Bug Fix Agent，您需要创建一个 GitCode 应用并获取相应的认证信息。

## 为什么需要 GitCode App？

- ✅ **真正的 @mention 支持** - 用户可以直接 @your-app-name 触发
- ✅ **更好的权限控制** - 细粒度的权限管理  
- ✅ **专业体验** - 更像真正的 GitCode 机器人

与传统的 Personal Access Token 相比，GitCode App 提供了更安全、更专业的集成方式。

## 第一步：创建 GitCode 应用

1. **访问 GitCode 应用设置页面**
   - 登录 GitCode，访问 设置 → 应用
   - 点击 **"新建应用"**

2. **填写基本信息**
   ```
   应用名称: bug-fix-agent-[your-username]
   描述: 自动化 Bug 修复助手，分析问题并创建修复 PR
   主页 URL: https://gitcode.com/[your-username]/Agent-Demo
   ```
   
   ⚠️ **重要**: 应用名称必须唯一，建议加上你的用户名后缀

3. **配置回调 URL**
   ```
   Authorization callback URL: https://[your-domain]/api/callback
   ```
   
   💡 如果你使用 ngrok，可以暂时填写占位符，后续再更新

4. **设置权限范围**
   - **api**: 访问 GitCode API
   - **read_repository**: 读取仓库内容
   - **write_repository**: 写入仓库内容（创建分支、提交）
   - **read_issue**: 读取 Issue
   - **write_issue**: 写入 Issue（评论）

5. **点击 "创建应用"**

## 第二步：获取认证信息

创建成功后，你需要收集以下信息：

1. **Application ID**: 在应用页面显示
2. **Application Secret**: 在应用页面显示（点击显示）

💡 **保存这些信息** - 你将在下一步中用到它们

## 第三步：获取 Private Token

除了 OAuth 应用，GitCode 还支持 Private Token，这通常更简单：

1. **访问 Token 设置页面**
   - 登录 GitCode，访问 设置 → 访问令牌
   - 点击 **"生成新令牌"**

2. **设置权限**
   ```
   令牌名称: bug-fix-agent-token
   过期时间: 根据需要选择
   
   权限范围:
   - api: 访问 GitCode API
   - read_repository: 读取仓库
   - write_repository: 写入仓库
   - read_issue: 读取 Issue
   - write_issue: 写入 Issue
   ```

3. **保存令牌**
   ⚠️ 令牌只会显示一次，请妥善保存

## 第四步：配置环境变量

将获取的认证信息添加到 `.env` 文件：

```bash
# 平台配置
PLATFORM=gitcode

# GitCode 基本配置
GITCODE_TOKEN=your_personal_access_token_here  # 备用认证
GITCODE_BASE=https://api.gitcode.com/api/v5
WEBHOOK_SECRET=your_webhook_secret_here

# GitCode App 配置（推荐）
GITCODE_APP_ID=your_app_id
GITCODE_APP_SECRET=your_app_secret
GITCODE_PRIVATE_TOKEN=your_private_token
GITCODE_APP_NAME=bug-fix-agent-yourname

# LLM 配置
LLM_BASE_URL=https://api.geekai.pro/v1/chat/completions
LLM_API_KEY=your_llm_api_key
LLM_MODEL=gpt-4o-mini

# 可选限制
ALLOWED_USERS=your-username,friend-username
ALLOWED_REPOS=your-username/repo1,your-username/repo2
```

⚠️ **安全提醒**: 
- 不要将认证信息提交到版本控制
- 确保 `.env` 已添加到 `.gitignore`

## 第五步：配置 Webhook

1. **启动本地服务**
   ```bash
   python start_local.py
   ```

2. **设置 ngrok 隧道**（开发环境）
   ```bash
   ngrok http 8080
   # 复制 https://abc123.ngrok-free.app 这个 URL
   ```

3. **配置仓库 Webhook**
   - 进入你的 GitCode 仓库
   - 设置 → Webhook
   - 添加 Webhook：
     ```
     URL: https://abc123.ngrok-free.app/api/webhook
     Secret Token: your_webhook_secret_here
     事件: Issues, Issue comments
     ```

## 第六步：测试配置

1. **运行测试脚本**
   ```bash
   python test_gitcode_config.py
   ```

2. **检查所有测试项**
   - ✅ GitCode 配置
   - ✅ API 连接
   - ✅ LLM 配置
   - ✅ 网络连通性

## 第七步：实际测试

1. **在 Issue 中测试**
   - 创建一个新 Issue 或在现有 Issue 中评论
   - 输入：`@your-app-name fix this bug`
   - 观察是否有自动回复

2. **检查日志**
   ```bash
   # 查看服务日志
   tail -f logs/gateway.log
   ```

3. **调试 Webhook**
   - 检查 ngrok 请求日志
   - 确认 Webhook 事件被正确接收

## 常见问题解答

### Q: 为什么输入 @agent 没有响应？

**A: 检查以下几点**
- ✅ Webhook 配置正确且 URL 可访问
- ✅ 应用名称正确（区分大小写）
- ✅ 令牌权限充足
- ✅ 在正确的仓库中尝试

### Q: Webhook 没有收到请求？

**A: 排查步骤**
1. 确认 ngrok 正在运行：`curl https://your-ngrok-url.ngrok-free.app/health`
2. 检查 Webhook URL 配置是否正确
3. 验证 Webhook secret 匹配
4. 查看 GitCode 仓库的 Webhook 日志

### Q: 认证失败错误？

**A: 验证配置**
- Application ID 和 Secret 是否正确
- Private Token 是否有效且权限充足
- API Base URL 是否正确

### Q: Agent 响应了但没有创建 PR？

**A: 检查权限**
- GitCode Token 有足够权限（仓库完整权限）
- 应用授权时包含了仓库写权限
- 目标仓库允许创建分支

### Q: 如何限制使用范围？

**A: 配置限制**
```bash
# 限制特定用户
ALLOWED_USERS=trusted-user1,trusted-user2

# 限制特定仓库
ALLOWED_REPOS=org/repo1,user/repo2
```

## 进阶配置

### 多仓库部署

```bash
# 限制特定仓库
ALLOWED_REPOS=org/repo1,org/repo2,user/repo3

# 限制特定用户  
ALLOWED_USERS=trusted-user1,trusted-user2
```

### 生产环境部署

1. **使用正式域名而非 ngrok**
2. **配置 HTTPS 证书**
3. **设置合适的资源限制**
4. **配置日志轮转**
5. **定期轮换 secrets**

### 自定义触发词

修改 `gateway/handlers/gitcode.py` 中的触发模式：

```python
self.trigger_patterns = [
    rf'@{re.escape(app_name)}\s+fix',
    rf'@{re.escape(app_name)}\s+help',  
    rf'@{re.escape(app_name)}\s+debug',  # 添加新的触发词
]
```

## 完成！

🎉 **恭喜！** 你的 GitCode Bug Fix Agent 现在已经配置完成，具备完整的 @agent 提及功能！

### 下一步

1. **测试功能**: 在 Issue 中使用 `@your-app-name fix` 测试
2. **监控日志**: 观察系统运行状态
3. **优化配置**: 根据使用情况调整权限和限制
4. **扩展功能**: 根据需要添加更多的修复策略

---

**📚 相关文档:**
- [GitCode API 文档](https://docs.gitcode.com/docs/apis/)
- [项目 README](README.md)
- [测试脚本](test_gitcode_config.py)

有任何问题请运行 `python test_gitcode_config.py` 进行诊断。
