#!/usr/bin/env python3
"""
演示 AI 驱动的 Bug Fix Agent 功能
"""

import requests
import json
import time
from datetime import datetime

def test_ai_webhook():
    """测试AI功能的webhook响应"""
    
    print("🤖 AI Bug Fix Agent 功能演示")
    print("=" * 50)
    
    # 模拟一个真实的bug报告
    payload = {
        "action": "created",
        "issue": {
            "number": 42,
            "title": "用户登录页面报错，点击登录按钮没有反应",
            "body": """用户反馈在登录页面输入用户名和密码后，点击登录按钮没有任何反应。

**复现步骤:**
1. 打开登录页面 `/login`
2. 输入有效的用户名和密码
3. 点击 "登录" 按钮
4. 页面没有任何反应，也没有错误提示

**预期行为:**
用户应该成功登录并跳转到主页面，或者显示相应的错误信息

**环境信息:**
- 浏览器: Chrome 120
- 操作系统: macOS
- 项目版本: v2.3.1""",
            "user": {"login": "testuser"}
        },
        "comment": {
            "id": 123456,
            "body": "@mooctestagent 这个登录问题很紧急，能帮忙修复一下吗？",
            "user": {"login": "testuser"}
        },
        "repository": {
            "name": "web-app",
            "owner": {"login": "company"},
            "default_branch": "main",
            "full_name": "company/web-app"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-GitHub-Delivery": f"ai-demo-{int(time.time())}"
    }
    
    print("📤 发送智能bug分析请求...")
    print(f"🐛 Issue: #{payload['issue']['number']} - {payload['issue']['title']}")
    print(f"💬 Comment: {payload['comment']['body']}")
    print()
    
    try:
        response = requests.post(
            "http://localhost:8080/api/webhook",
            headers=headers,
            json=payload,
            timeout=10
        )
        
        if response.status_code == 200:
            print("✅ Webhook 请求成功发送!")
            print(f"📨 Response: {response.text}")
            
            print("\n🧠 AI Agent 开始工作...")
            print("预期处理流程:")
            print("1. 🔍 AI 分析问题：理解登录功能bug的根本原因")
            print("2. 📁 智能文件定位：找到可能包含登录逻辑的文件")
            print("3. 💡 生成修复方案：AI 生成具体的修复策略")
            print("4. 🛠️ 应用修复：对安全文件进行智能修复")
            print("5. 🔄 创建 PR：包含AI分析报告和修复内容")
            
            print("\n📝 生成的文件将包括:")
            print("- agent/analysis.md - AI问题分析报告")
            print("- agent/patch_plan.json - AI修复方案详情") 
            print("- 修复后的目标文件 - AI生成的代码修复")
            
        else:
            print(f"❌ Webhook 请求失败: {response.status_code}")
            print(f"📨 Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求错误: {e}")
        print("\n💡 确保服务正在运行:")
        print("python start_local.py")

def show_ai_features():
    """展示AI功能特性"""
    
    print("\n🚀 AI 功能特性展示")
    print("=" * 30)
    
    features = [
        {
            "icon": "🧠",
            "title": "智能问题分析", 
            "desc": "使用LLM深度理解issue描述，识别问题本质和技术领域"
        },
        {
            "icon": "📁", 
            "title": "精准文件定位",
            "desc": "AI基于问题上下文智能匹配最相关的代码文件"
        },
        {
            "icon": "💡",
            "title": "生成修复方案", 
            "desc": "AI分析根因并生成具体的修复策略和实施步骤"
        },
        {
            "icon": "🛠️",
            "title": "代码修复生成",
            "desc": "为文档和配置文件生成实际的修复内容"
        },
        {
            "icon": "📊",
            "title": "详细分析报告",
            "desc": "包含技术领域、风险评估、测试建议的完整报告"
        }
    ]
    
    for feature in features:
        print(f"{feature['icon']} **{feature['title']}**")
        print(f"   {feature['desc']}")
        print()

def main():
    """主函数"""
    
    print(f"🕐 演示时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 显示AI功能特性
    show_ai_features()
    
    # 测试AI webhook
    test_ai_webhook()
    
    print("\n🎯 下一步测试:")
    print("1. 在真实GitHub仓库中创建issue")
    print("2. 添加评论: @mooctestagent 请帮我修复这个bug")
    print("3. 观察AI分析过程和生成的PR")
    print("4. 查看agent/目录下的AI生成文件")
    
    print("\n✨ 恭喜！你的Bug Fix Agent现在具备了真正的AI能力！")

if __name__ == "__main__":
    main()
