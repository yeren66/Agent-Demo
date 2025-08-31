# GitHub Agent 开发示例

一个智能的 GitHub Agent 示例项目，展示如何构建支持 @mention 触发的自动化代码修复机器人。

## ✨ 功能演示

用户在 Issue 中输入：
```
@your-agent-name 这个登录功能有 bug，请帮忙修复
```

Agent 自动响应：
- 🧠 AI 分析问题内容
- 📁 定位相关代码文件  
- 💡 生成修复方案
- 🛠️ 自动创建修复 PR
- 📊 实时反馈处理进度

## 🚀 快速开始

### 1. 配置环境

```bash
# 克隆项目
git clone https://github.com/your-username/Agent-Demo.git
cd Agent-Demo

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
cp .env.example .env
# 编辑 .env 文件，填入你的配置
```

### 2. 启动服务

```bash
# 启动本地开发服务器
python start_local.py

# 使用 ngrok 暴露到公网
./scripts/ngrok.sh
```

### 3. 完整教程

**📖 详细教程请参考：[TUTORIAL.md](./TUTORIAL.md)**

**⚡ 快速开始请参考：[QUICKSTART.md](./QUICKSTART.md)**

教程包含：
- GitHub App 创建与配置详解
- 环境变量完整说明
- Webhook 配置步骤
- 本地开发和调试技巧
- 生产环境部署指南
- 故障排除完整指南
## 📁 项目结构

```
Agent-Demo/
├── 📚 文档
│   ├── README.md              # 项目概述（当前文件）
│   ├── TUTORIAL.md            # 完整开发教程 ⭐
│   ├── API.md                 # API 接口文档
│   └── PROJECT_STRUCTURE.md   # 项目结构说明
├── ⚙️  配置
│   ├── .env.example           # 环境变量模板
│   ├── requirements.txt       # Python 依赖
│   └── start_local.py         # 本地启动脚本
├── 🌐 Gateway 服务
│   ├── app.py                 # FastAPI 主应用
│   ├── github_api.py          # GitHub API 封装
│   ├── security.py            # 安全验证
│   └── handlers/              # 事件处理器
├── 🤖 Worker 核心
│   ├── main.py                # 业务逻辑入口
│   ├── github_app_auth.py     # GitHub App 认证
│   ├── llm_client.py          # AI 客户端
│   ├── gitops.py              # Git 操作
│   └── stages/                # 处理阶段
│       ├── locate.py          # 问题定位
│       ├── propose.py         # 方案生成
│       ├── fix.py             # 代码修复
│       └── verify.py          # 验证测试
├── 🔧 辅助脚本
│   ├── setup.sh               # 环境设置
│   ├── ngrok.sh               # 隧道启动
│   └── test.sh                # 本地测试
└── 🐳 容器化
    └── docker/                # Docker 配置
```

## 🛠️ 技术栈

- **Web 框架**: FastAPI
- **GitHub 集成**: GitHub Apps API  
- **AI 能力**: OpenAI/Compatible LLM
- **Git 操作**: GitPython
- **容器化**: Docker + Docker Compose
- **开发工具**: Ngrok

## 📚 使用说明

### 触发方式

在 Issue 中使用以下任一方式触发 Agent：

```
@your-agent-name fix this bug
@your-agent-name 请帮忙修复这个问题
@your-agent-name analyze this issue
```

### 响应示例

Agent 会自动回复并开始处理：

```
👋 我是 AI 修复助手，已接收到您的修复请求！

🔍 **问题分析中...**
- 正在分析 Issue 内容
- 定位相关代码文件  
- 生成修复方案

完成后会创建 PR 供您审查。
```

## 🔧 开发扩展

这个项目可以作为基础，扩展更多功能：

- **多语言支持** - 支持更多编程语言的代码修复
- **更复杂的分析** - 集成代码质量检查工具
- **自动化测试** - 自动运行和创建测试用例
- **性能优化** - 代码性能分析和优化建议
- **安全扫描** - 自动检测和修复安全漏洞

## 📄 许可证

MIT License - 详见 [LICENSE](LICENSE) 文件

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

---

**💡 提示**: 完整的开发教程请查看 [TUTORIAL.md](./TUTORIAL.md)
