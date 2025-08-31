# 接口规范（API 说明）

本文件定义了“Bug Fix Agent”服务的对外 HTTP 接口与对内插桩接口契约，适用于集成与运维人员。文档不依赖源码引用，独立描述端点、请求/响应、鉴权、错误码、作业对象结构、阶段接口及调试开关。

更新时间：2025-08-22

## 1. 术语与范围

- 平台：指代码托管平台（GitHub 或 GitCode）。
- 触发事件：指平台 Webhook 推送的 issues/issue_comment 等事件。
- 作业（Job）：由触发事件解析后生成的处理任务，贯穿分析、方案、修复、验证等阶段。
- 阶段（Stage）：处理作业的分步流程，包含 locate、propose、fix、verify。

## 2. 服务基址与版本

- 本地开发基址（默认）：http://localhost:8080
- 生产环境基址：由部署者提供（负载均衡或网关域名）。
- 版本：1.0.0（接口稳定；如有破坏性变更，将提升主版本并在响应中反映）。

## 3. 鉴权与安全

3.1 Webhook 签名校验
- 支持平台：GitHub、GitCode。
- 必填请求头：
  - GitHub：
    - X-GitHub-Event：事件类型（如 issue_comment、issues）。
    - X-Hub-Signature-256：HMAC-SHA256 签名，格式 sha256=十六进制签名。
    - X-GitHub-Delivery：事件唯一 ID（用于幂等与重复投递识别）。
  - GitCode：
    - X-GitCode-Event（或同义头部，见 4.2）：事件类型（如 Note Hook、Issue Hook）。
    - 签名头：支持多候选头部之一（例如 X-GitCode-Token、X-GitCode-Signature、X-GitCode-Sign、X-Signature、X-GitCode-Webhook-Signature）。
- 签名计算：HMAC-SHA256(原始请求体, WEBHOOK_SECRET)。
- 验证失败：返回 401 Unauthorized。

3.2 访问控制
- 可选白名单：
  - ALLOWED_USERS（逗号分隔用户名）。
  - ALLOWED_REPOS（逗号分隔仓库全名 owner/repo）。
- 非白名单请求：返回 403 Forbidden 或忽略处理（见 4.4）。

3.3 调试模式
- TEST_MODE=true 时跳过签名校验，仅用于本地开发与联调。

## 4. 对外 HTTP 接口

4.1 健康检查
- 方法与路径：GET /health（等价 GET /）。
- 请求体：无。
- 成功响应：200 OK。
- 响应示例：
```
{
  "status": "healthy",
  "service": "agent-gateway"
}
```

4.2 Webhook 接收
- 方法与路径：
  - POST /api/webhook（通用端点，依据平台自动识别）。
  - POST /api/github/webhook（GitHub 兼容别名）。
  - POST /api/gitcode/webhook（GitCode 兼容别名）。
- 头部要求：
  - 平台识别：通过环境变量 PLATFORM=github|gitcode 与事件头（X-GitHub-Event 或 X-GitCode-Event 等）综合判定。
  - 签名头：见第 3 节。
  - Content-Type: application/json。
- 请求体：平台原生事件 JSON。典型事件：
  - GitHub：issue_comment（action=created）、issues（action=opened/assigned）。
  - GitCode：Note Hook（评论）、Issue Hook（新建/分配）。
- 触发条件（满足其一即受理）：
  - 评论触发：评论正文包含对应用名的 @ 提及（如 “@app-name fix” 或 “@app-name help”）。
  - 分配触发：将 Issue 分配给机器人账号（由配置的机器人用户名识别）。
  - Issue 创建触发：新建 Issue 时包含明确的触发短语（按需启用）。
- 过滤规则：
  - 忽略由机器人自身产生的评论（避免循环触发）；
  - 忽略非触发 action 的事件；
  - 可选：基于白名单的用户/仓库过滤。
- 成功响应：
  - 202/200 OK，JSON：{ "status": "accepted", "job_id": "..." }。
  - 对非触发事件：200 OK，JSON：{ "status": "ignored", "reason": "..." }。
- 失败响应：
  - 400 Bad Request（JSON 解析错误或缺失字段）。
  - 401 Unauthorized（签名校验失败）。
  - 403 Forbidden（白名单拒绝）。
  - 500 Internal Server Error（内部错误）。

GitHub 请求示例：
```
POST /api/webhook
Content-Type: application/json
X-GitHub-Event: issue_comment
X-GitHub-Delivery: 8e3c...
X-Hub-Signature-256: sha256=<签名>

{
  "action": "created",
  "issue": {"number": 42, "title": "Bug", "body": "details"},
  "comment": {"body": "@app-name fix", "user": {"login": "alice"}},
  "repository": {"owner": {"login": "acme"}, "name": "demo", "default_branch": "main"},
  "sender": {"login": "alice"}
}
```

GitCode 请求示例（评论事件）：
```
POST /api/webhook
Content-Type: application/json
X-GitCode-Event: Note Hook
X-GitCode-Signature: <签名>

{
  "action": "created",
  "object_attributes": {"note": "@app-name fix"},
  "project": {"namespace": {"name": "acme"}, "name": "demo", "default_branch": "master"},
  "user": {"username": "alice"}
}
```

响应示例（受理）：
```
{
  "status": "accepted",
  "job_id": "a2c1d3f0-..."
}
```

4.3 服务状态
- 方法与路径：GET /api/status。
- 功能：返回服务运行状态、版本。
- 成功响应：200 OK。
- 响应示例：
```
{
  "service": "agent-gateway",
  "status": "running",
  "version": "1.0.0"
}
```

4.4 幂等与重复投递
- Webhook 端点按“至多一次”语义处理单次请求；如平台发生重放，系统将再次判定是否满足触发条件：
  - 若判定为非触发，则返回 ignored；
  - 若重复触发但作业分支/PR 已存在，系统会尽量避免重复变更（分支名携带时间戳降低冲突风险）。

## 5. 作业（Job）对象契约

- 生成时机：Webhook 请求通过安全校验且满足触发条件时。
- 结构定义（示例）：
```
{
  "job_id": "uuid",
  "created_at": "ISO-8601 时间",
  "event_type": "issues|issue_comment|Issue Hook|Note Hook",
  "platform": "github|gitcode",
  "owner": "仓库所属空间",
  "repo": "仓库名",
  "issue_number": 42,                  
  "display_issue_number": 3243389,     
  "issue_title": "问题标题",
  "actor": "触发人",
  "branch": "agent/fix-42-0822-103000",
  "default_branch": "main|master",
  "triggered_by_assignment": false,
  "webhook_payload": { ... 原始事件 JSON ... }
}
```
- 字段说明：
  - issue_number：用于平台 API 调用的编号（GitHub 通常与显示一致；GitCode 可能为 iid/number）。
  - display_issue_number：仅用于消息展示，避免平台差异导致混淆。
  - branch：为每个作业生成独立的工作分支，包含时间戳避免冲突。

## 6. 阶段（Stage）接口契约（插桩）

各阶段以统一签名运行：
- 输入：
  - job：作业对象（见第 5 节）。
  - repo_path：本地工作副本路径（字符串）。
  - platform_api：平台 API 抽象（见第 7 节）。
  - gitops：Git 操作抽象（见第 8 节）。
- 输出（通用）：
```
{
  "success": true|false,
  "comment": "用于发布到 Issue/PR 的阶段性说明（可选）",
  "...stage_specific_fields": "阶段特有数据"
}
```

6.1 定位阶段 locate
- 目标：识别潜在问题文件并生成分析报告。
- 主要输出字段：
  - candidate_files：["相对路径"...]；
  - stage_data：{ analysis_method, confidence_level, files_analyzed }。
- 成功示例：
```
{
  "success": true,
  "candidate_files": ["src/app.py", "README.md"],
  "comment": "第1阶段：问题定位分析完成...",
  "stage_data": {"analysis_method": "LLM", "confidence_level": "high", "files_analyzed": 120}
}
```

6.2 方案阶段 propose
- 目标：基于定位结果生成修复方案与目标文件清单。
- 主要输出字段：
  - target_files：["相对路径"...]；
  - stage_data：{ fix_strategy, changes_count, risk_level }。
- 成功示例：
```
{
  "success": true,
  "target_files": ["README.md"],
  "comment": "第2阶段：修复方案设计完成...",
  "stage_data": {"fix_strategy": "demo_safe_patch", "changes_count": 1, "risk_level": "low"}
}
```

6.3 修复阶段 fix
- 目标：对目标文件应用修复并提交到工作分支。
- 主要输出字段：
  - changes_applied：["文件路径"...]；
  - changed_files：[ {"status": "A|M|D", "file": "路径"} ... ]。
- 成功示例：
```
{
  "success": true,
  "changes_applied": ["README.md"],
  "changed_files": [{"status": "M", "file": "README.md"}],
  "comment": "第3阶段：代码修改实施完成..."
}
```

6.4 验证阶段 verify
- 目标：模拟/执行构建与测试，生成验证报告。
- 主要输出字段：
  - build_success：true|false；
  - test_results：{ passed, failed, skipped, coverage, total }。
- 成功示例：
```
{
  "success": true,
  "build_success": true,
  "test_results": {"passed": 40, "failed": 0, "skipped": 3, "coverage": "78%", "total": 43},
  "comment": "第4阶段：验证测试完成..."
}
```

## 7. 平台 API 抽象（插桩）

用于访问平台资源（Issue、PR、仓库等）。所有方法在失败时返回 None/False，不抛出异常，调用方需自处理。

- 获取 Issue：get_issue(owner, repo, number) -> 对象 | None。
- Issue 评论：comment_issue(owner, repo, number, body) -> 布尔。
- 创建 PR：create_pr(owner, repo, head, base, title, body, draft) -> { number, ... } | None。
- 更新 PR 描述：update_pr_body(owner, repo, number, body) -> 布尔。
- 标记 PR 可审查：mark_pr_ready(owner, repo, number) -> 布尔。
- PR 评论：comment_pr(owner, repo, number, body) -> 布尔。
- 获取仓库：get_repo(owner, repo) -> 对象 | None。
- 获取默认分支：get_default_branch(owner, repo) -> 字符串（默认 main）。
- 创建分支引用：create_branch(owner, repo, branch, sha) -> 对象 | None。
- 创建/更新文件（平台 API 方式）：create_or_update_file(owner, repo, path, content, message, branch, sha?) -> 对象 | None。
- 获取文件内容：get_file_content(owner, repo, path, ref) -> 字符串 | None。
- 获取当前可用令牌：get_token(owner?, repo?) -> 字符串 | None。

注意：
- draft 字段对不同平台支持情况不同；
- 认证优先级：平台应用安装令牌 > 个人访问令牌；
- 失败时返回 None，调用方应记录错误并决定是否重试。

## 8. GitOps 抽象（插桩）

用于本地仓库操作。所有方法在失败时返回 False/空集合，避免抛出异常。

- clone_repo(clone_url, destination) -> 布尔。超时：约 120 秒。
- create_branch(repo_path, branch_name, base_branch) -> 布尔。
- add_file(repo_path, file_path) -> 布尔。
- add_all(repo_path) -> 布尔。
- commit(repo_path, message) -> 布尔（空变更视作成功）。
- push(repo_path, branch_name, force?) -> 布尔（采用安全的 --force-with-lease）。
- push_branch(repo_path, branch_name) -> 布尔。
- commit_changes(repo_path, message) -> 布尔（add_all+commit）。
- get_changed_files(repo_path) -> [ { status: "A|M|D", file: "..." } ]。
- write_file(repo_path, file_path, content) -> 布尔（自动建目录）。
- append_file(repo_path, file_path, content) -> 布尔。
- file_exists(repo_path, file_path) -> 布尔。
- list_files(repo_path, pattern="*") -> [相对路径]（忽略常见缓存与构建目录）。

注意：
- 将清理 HTTP(S)_PROXY 以降低认证冲突概率；
- 分支创建前会尝试检出 base 分支并清理同名本地分支；
- push 前会尽力确保远程 origin URL 使用含认证信息的形式。

## 9. LLM 客户端抽象（插桩）

- chat_completion(messages, model?, max_tokens?) -> 字符串 | None。
- analyze_bug(issue_title, issue_body, file_list) -> { analysis, technical_areas[], candidate_files[], reasoning }。
- generate_fix_plan(issue_title, issue_body, candidate_files, file_contents?) -> { root_cause, fix_strategy, changes[], risks[], testing_suggestions[] }。
- generate_code_fix(file_path, file_content, issue_description, fix_plan) -> 字符串（完整文件内容）| None。
- close()：释放 HTTP 资源。

环境变量：
- LLM_BASE_URL（OpenAI 兼容接口 /v1/chat/completions）。
- LLM_API_KEY。
- LLM_MODEL（默认如 gpt-4o-mini）。
- 可选代理：HTTP_PROXY/HTTPS_PROXY。

返回解析：
- 当模型输出包含代码围栏时，优先提取 JSON 围栏内容；解析失败回退为启发式结果。

## 10. 阶段产出与对外可见物

- 分支：agent/fix-<issue>-<时间戳>。
- PR：标题含 issue 编号与简要说明；正文为进度面板与摘要。
- 文档与报告（示例）：
  - agent/analysis.md（问题分析报告）。
  - agent/patch_plan.json（修复方案与目标文件）。
  - agent/report.txt（验证结果）。

注意：具体文件名与结构可按需调整，但建议保持一致性以便审查与追踪。

## 11. 错误码与故障处理

- 400 Bad Request：请求体不是合法 JSON、缺少必要字段、事件类型不受支持。
- 401 Unauthorized：Webhook 签名校验失败。
- 403 Forbidden：触发人或仓库不在白名单。
- 500 Internal Server Error：服务内部错误（记录堆栈）。

作业失败处理：
- 将在原 Issue 留言告知失败原因（包含作业 ID），供人工排查。

重试建议：
- Webhook：可安全重放，同一事件如不满足触发条件将被忽略；
- 平台 API：推荐应用侧做指数退避重试，避免速率限制。

## 12. 环境变量（关键项）

- 平台选择：PLATFORM=github|gitcode。
- Webhook 安全：WEBHOOK_SECRET，TEST_MODE。
- 认证：
  - GitHub：GITHUB_TOKEN 或 App 相关（ID、私钥路径等）。
  - GitCode：GITCODE_TOKEN/GITCODE_PAT，机器人用户名（GITCODE_BOT_USERNAME）。
- LLM：LLM_BASE_URL、LLM_API_KEY、LLM_MODEL、HTTP_PROXY/HTTPS_PROXY。
- 访问控制：ALLOWED_USERS、ALLOWED_REPOS。
- 日志级别：LOG_LEVEL（INFO/DEBUG 等）。

## 13. 合规与安全注意事项

- 严格保护访问令牌与私钥，避免出现在日志与 PR 内容中。
- PR 与评论中不应泄露敏感配置与环境变量值。
- 如需在受限网络环境中使用代理，请遵循组织安全策略。

## 14. 典型集成流程摘要

1) 配置环境变量（平台、签名、令牌、白名单）。
2) 暴露 /api/webhook 给平台 Webhook；确保签名一致。
3) 在 Issue 中 @ 应用名并附触发词，或将 Issue 分配给机器人。
4) 接收响应：服务返回 accepted 与 job_id；平台 Issue 收到受理评论。
5) 后台阶段推进：定位→方案→修复→验证；Issue/PR 获取进度更新与结果。
6) 审查 PR 并合并，关闭 Issue。

## 15. 兼容性与限制

- 不同平台对 Issue 编号字段命名存在差异（id/iid/number），系统已做统一映射；
- PR 草稿（draft）支持度按平台有差异；
- 演示/安全模式下对代码文件的直接修改较为保守，优先文档与配置类文件。

---

本文件为该服务的权威接口说明。若后续有扩展（如新增阶段、部署阶段、更多事件类型），应在保持向后兼容的前提下补充对应契约与示例。
