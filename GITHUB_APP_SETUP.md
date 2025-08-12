# GitHub App 设置指南

为了让用户能够在 GitHub Issue 中使用 `@your-app-name` 提及您的 Bug Fix Agent，您需要创建一个 GitHub App 并获取相应的认证信息。

## 为什么需要 GitHub App？

- ✅ **真正的 @mention 支持** - 用户可以直接 @your-app-name 触发
- ✅ **自动补全** - GitHub 会在输入时提示可用的 App
- ✅ **更好的权限控制** - 细粒度的权限管理  
- ✅ **专业体验** - 更像真正的 GitHub 机器人

## 第一步：创建 GitHub App

1. **访问 GitHub App 设置页面**
   - 登录 GitHub，访问 https://github.com/settings/apps
   - 点击 **"New GitHub App"**

2. **填写基本信息**
   ```
   GitHub App name: bug-fix-agent-[your-username]
   Description: Automated bug fixing agent that analyzes issues and creates fix PRs
   Homepage URL: https://github.com/[your-username]/Agent-Demo
   ```
   
   ⚠️ **重要**: App 名称必须全局唯一，建议加上你的用户名后缀

3. **配置 Webhook**
   ```
   Webhook URL: https://[your-ngrok-domain].ngrok-free.app/api/webhook
   Webhook secret: [创建一个强密码，记录下来]
   ```
   
   💡 如果你还没有 ngrok URL，可以先填写占位符，后续再更新

4. **设置权限** (Repository permissions)
   - **Issues**: Read & Write ✅
   - **Pull requests**: Read & Write ✅  
   - **Contents**: Read & Write ✅
   - **Metadata**: Read ✅

5. **订阅事件** (Subscribe to events)
   - [x] Issues
   - [x] Issue comments

6. **安装范围**
   - 选择 **"Any account"** (推荐) 或 "Only on this account"

7. **点击 "Create GitHub App"**

## 第二步：获取认证信息

创建成功后，你需要收集以下信息：

1. **App ID**: 在 App 页面顶部显示
2. **Client ID**: 在页面中部显示  
3. **Client Secret**: 点击 "Generate a new client secret"
4. **私钥**: 点击 "Generate a private key" 下载 `.pem` 文件

## 第三步：配置环境变量

将下载的私钥文件放到项目目录，然后编辑 `.env` 文件：

```bash
# GitHub 基本配置
PLATFORM=github
GITHUB_TOKEN=your_github_personal_access_token  # 备用认证
WEBHOOK_SECRET=your_webhook_secret_here

# GitHub App 配置
GITHUB_APP_ID=123456
GITHUB_APP_PRIVATE_KEY_PATH=./bug-fix-agent.pem
GITHUB_APP_CLIENT_ID=Iv1.abc123def456
GITHUB_APP_CLIENT_SECRET=your_client_secret_here
GITHUB_APP_NAME=bug-fix-agent-yourname

# 可选限制
ALLOWED_USERS=your-username,friend-username
ALLOWED_REPOS=your-username/repo1,your-username/repo2
```

⚠️ **安全提醒**: 
- 不要将 `.pem` 文件提交到版本控制
- 将 `*.pem` 添加到 `.gitignore`

## 第四步：安装 App 到仓库

1. **访问安装页面**
   - 在 App 设置页面，点击 **"Install App"**
   - 选择你的账户或组织

2. **选择仓库**
   - **推荐**: 选择 "Selected repositories" 并选择测试仓库
   - 或选择 "All repositories" (生产环境不推荐)

3. **完成安装**
   - 点击 "Install"
   - 记录安装后的 URL 中的 `installation_id`（可选）

## 第五步：测试配置

1. **运行测试脚本**
   ```bash
   python test_github_app.py
   ```

2. **启动服务**
   ```bash
   python start_local.py
   ```

3. **设置 ngrok 隧道**
   ```bash
   ./scripts/ngrok.sh
   # 或手动: ngrok http 8080
   ```

4. **更新 Webhook URL**
   - 复制 ngrok 提供的 HTTPS URL
   - 在 GitHub App 设置中更新 Webhook URL：
     `https://abc123.ngrok-free.app/api/webhook`

## 第六步：实际测试

1. **在已安装 App 的仓库中创建 Issue**

2. **尝试 @mention**
   - 开始输入 `@bug-fix-agent-yourname`
   - 应该看到自动补全提示 ✨

3. **发送测试评论**
   ```
   @bug-fix-agent-yourname fix this bug please
   ```

4. **检查响应**
   - Agent 应该在几秒内回复
   - 查看服务日志确认 webhook 接收成功

## 常见问题解答

### Q: 为什么输入 @agent 没有自动补全？

**A: 检查以下几点**
- ✅ GitHub App 已正确安装到仓库
- ✅ App 名称正确（区分大小写）
- ✅ App 有 Issues 权限
- ✅ 你在正确的仓库中尝试

### Q: Webhook 没有收到请求？

**A: 排查步骤**
1. 确认 ngrok 正在运行：`curl https://your-ngrok-url.ngrok-free.app/health`
2. 检查 Webhook URL 配置是否正确
3. 验证 Webhook secret 匹配
4. 查看 GitHub App 的 Advanced → Recent Deliveries

### Q: 认证失败错误？

**A: 验证配置**
- App ID 是否正确（纯数字）
- 私钥文件路径是否正确且文件存在
- 私钥文件格式正确（包含 BEGIN/END 标记）
- Client ID 和 Secret 是否匹配

### Q: Agent 响应了但没有创建 PR？

**A: 检查权限**
- GitHub Token 有足够权限（repo 完整权限）
- App 安装时授予了 Pull requests 写权限
- 目标仓库允许创建分支

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

---

## 完成！

🎉 **恭喜！你现在拥有了一个真正的 GitHub App Bug Fix Agent！**

用户现在可以：
- 在 Issue 中直接 `@your-app-name` 获得自动补全
- 触发智能 bug 修复流程
- 获得专业的 PR 和进度追踪

**下一步建议**：
1. 在多个测试仓库中试用
2. 根据实际需求调整触发条件
3. 扩展修复策略和分析能力
4. 考虑集成更多 AI 能力
