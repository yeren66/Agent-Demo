# GitHub Agent API 文档

本文档描述了 GitHub Agent 的 API 接口和内部组件。

## API 端点

### 健康检查

```http
GET /health
```

**响应示例**：
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "service": "github-agent",
  "version": "1.0.0"
}
```

### Webhook 端点

```http
POST /api/webhook
```

**请求头**：
```
Content-Type: application/json
X-GitHub-Event: issue_comment | issues
X-GitHub-Delivery: unique-delivery-id
X-Hub-Signature-256: sha256=signature
```

**请求体**（Issue Comment 事件）：
```json
{
  "action": "created",
  "issue": {
    "number": 123,
    "title": "Bug in login function",
    "body": "详细的问题描述...",
    "user": {
      "login": "username"
    }
  },
  "comment": {
    "body": "@agent-name fix this issue",
    "user": {
      "login": "username"
    }
  },
  "repository": {
    "name": "repo-name",
    "owner": {
      "login": "owner-name"
    },
    "default_branch": "main",
    "clone_url": "https://github.com/owner/repo.git"
  }
}
```

**响应**：
```json
{
  "status": "accepted",
  "task_id": "task-uuid-123",
  "message": "Processing request..."
}
```

## 内部组件

### GitHub App 认证

**类**: `GitHubAppAuth`

**方法**：
```python
def get_installation_token(installation_id: int) -> str
    """获取安装令牌用于 API 调用"""

def get_installation_id(owner: str, repo: str) -> int
    """获取仓库的安装 ID"""
```

### LLM 客户端

**类**: `LLMClient`

**方法**：
```python
async def analyze_issue(issue_content: str) -> dict
    """分析 Issue 内容，提取问题要点"""

async def locate_files(issue_content: str, repo_structure: str) -> list
    """基于问题内容定位相关代码文件"""

async def generate_fix_plan(issue_content: str, file_content: str) -> dict
    """生成具体的修复计划"""

async def generate_code_fix(file_content: str, fix_plan: str) -> str
    """生成修复后的代码内容"""
```

### Git 操作

**类**: `GitOps`

**方法**：
```python
def clone_repository(repo_url: str, local_path: str) -> bool
    """克隆仓库到本地"""

def create_branch(branch_name: str) -> bool
    """创建新的修复分支"""

def apply_fixes(fixes: list) -> bool
    """应用代码修复"""

def commit_and_push(message: str) -> bool
    """提交并推送更改"""

def create_pull_request(title: str, body: str) -> str
    """创建 Pull Request"""
```

## 处理阶段

### 1. 定位阶段 (locate.py)

**输入**: Issue 内容，仓库信息
**输出**: 相关文件列表，问题分析

```python
async def locate_stage(issue_content, repo_info):
    """
    使用 AI 分析 Issue 并定位相关文件
    """
    # AI 分析问题
    analysis = await llm_client.analyze_issue(issue_content)
    
    # 定位相关文件
    files = await llm_client.locate_files(issue_content, repo_structure)
    
    return {
        "analysis": analysis,
        "relevant_files": files,
        "confidence": analysis.get("confidence", 0.8)
    }
```

### 2. 方案阶段 (propose.py)

**输入**: 问题分析，文件内容
**输出**: 详细修复方案

```python
async def propose_stage(analysis, file_contents):
    """
    基于分析结果生成修复方案
    """
    plan = await llm_client.generate_fix_plan(
        analysis["issue_content"],
        file_contents
    )
    
    return {
        "fix_plan": plan,
        "affected_files": plan.get("files", []),
        "estimated_effort": plan.get("effort", "medium")
    }
```

### 3. 修复阶段 (fix.py)

**输入**: 修复方案，文件内容  
**输出**: 修复后的代码

```python
async def fix_stage(fix_plan, file_contents):
    """
    应用修复方案到代码文件
    """
    fixes = []
    
    for file_path, content in file_contents.items():
        fixed_content = await llm_client.generate_code_fix(
            content, 
            fix_plan["details"]
        )
        
        fixes.append({
            "file": file_path,
            "original": content,
            "fixed": fixed_content
        })
    
    return fixes
```

### 4. 验证阶段 (verify.py)

**输入**: 修复后的代码
**输出**: 验证结果

```python
async def verify_stage(fixes):
    """
    验证修复的正确性
    """
    results = []
    
    for fix in fixes:
        # 语法检查
        syntax_ok = check_syntax(fix["fixed"])
        
        # 运行测试（如果有）
        test_ok = await run_tests(fix["file"])
        
        results.append({
            "file": fix["file"],
            "syntax_valid": syntax_ok,
            "tests_pass": test_ok
        })
    
    return results
```

## 错误处理

### 错误码

```python
class AgentErrorCode:
    # 认证错误
    AUTH_FAILED = "AUTH_001"
    INVALID_TOKEN = "AUTH_002"
    PERMISSION_DENIED = "AUTH_003"
    
    # Webhook 错误
    INVALID_SIGNATURE = "WEBHOOK_001"
    UNSUPPORTED_EVENT = "WEBHOOK_002"
    
    # 处理错误
    AI_ANALYSIS_FAILED = "PROCESS_001"
    FILE_NOT_FOUND = "PROCESS_002"
    GIT_OPERATION_FAILED = "PROCESS_003"
    
    # 外部服务错误
    GITHUB_API_ERROR = "EXTERNAL_001"
    LLM_API_ERROR = "EXTERNAL_002"
```

### 错误响应格式

```json
{
  "error": {
    "code": "AUTH_001",
    "message": "GitHub App authentication failed",
    "details": "Invalid private key or app ID",
    "timestamp": "2024-01-01T12:00:00Z"
  }
}
```

## 配置参数

### 环境变量完整列表

| 变量名 | 必需 | 默认值 | 描述 |
|--------|------|--------|------|
| `PLATFORM` | 是 | - | Git 平台类型（github） |
| `GITHUB_TOKEN` | 是 | - | GitHub Personal Access Token |
| `WEBHOOK_SECRET` | 是 | - | Webhook 签名密钥 |
| `GITHUB_APP_ID` | 是 | - | GitHub App ID |
| `GITHUB_APP_PRIVATE_KEY_PATH` | 是 | - | 私钥文件路径 |
| `GITHUB_APP_CLIENT_ID` | 是 | - | GitHub App Client ID |
| `GITHUB_APP_CLIENT_SECRET` | 是 | - | GitHub App Client Secret |
| `GITHUB_APP_NAME` | 是 | - | GitHub App 名称 |
| `LLM_BASE_URL` | 是 | - | LLM API 基础 URL |
| `LLM_API_KEY` | 是 | - | LLM API 密钥 |
| `LLM_MODEL` | 否 | gpt-3.5-turbo | 使用的 LLM 模型 |
| `ALLOWED_USERS` | 否 | - | 允许的用户列表 |
| `ALLOWED_REPOS` | 否 | - | 允许的仓库列表 |
| `DEBUG` | 否 | false | 调试模式 |
| `LOG_LEVEL` | 否 | INFO | 日志级别 |

### GitHub App 权限要求

| 权限类型 | 权限级别 | 用途 |
|----------|----------|------|
| Contents | Write | 读取和修改仓库文件 |
| Issues | Write | 读取 Issue 和添加评论 |
| Pull requests | Write | 创建和管理 PR |
| Metadata | Read | 读取仓库基本信息 |

### Webhook 事件订阅

| 事件类型 | 必需 | 用途 |
|----------|------|------|
| Issues | 是 | 监听 Issue 创建和更新 |
| Issue comments | 是 | 监听 Issue 评论（@mention） |
| Pull requests | 否 | 监听 PR 状态变化 |

这个 API 文档为开发者提供了完整的接口参考和技术实现细节。
