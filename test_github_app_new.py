#!/usr/bin/env python3
"""
GitHub App Bug Fix Agent - 集成测试脚本
测试 GitHub App 和 Webhook 配置是否正确
"""

import os
import sys
import requests
import json
import re

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_health_check():
    """测试基础健康检查"""
    print("=== 健康检查 ===")
    try:
        response = requests.get('http://localhost:8080/health', timeout=5)
        if response.status_code == 200:
            print("✅ 服务运行正常")
            return True
        else:
            print(f"❌ 服务异常: HTTP {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ 无法连接到服务 (确保服务已启动: python start_local.py)")
        return False
    except Exception as e:
        print(f"❌ 健康检查失败: {e}")
        return False

def test_github_config():
    """测试 GitHub 配置"""
    print("\n=== GitHub 配置检查 ===")
    
    # 基本配置
    platform = os.getenv('PLATFORM', 'github')
    github_token = os.getenv('GITHUB_TOKEN')
    webhook_secret = os.getenv('WEBHOOK_SECRET')
    
    print(f"📍 平台: {platform}")
    print(f"✅ GitHub Token: {'已配置' if github_token else '❌ 未配置'}")
    print(f"✅ Webhook Secret: {'已配置' if webhook_secret else '❌ 未配置'}")
    
    # GitHub App 配置
    print("\n--- GitHub App 配置 (用于 @mention) ---")
    github_app_config = {
        'GITHUB_APP_ID': os.getenv('GITHUB_APP_ID'),
        'GITHUB_APP_PRIVATE_KEY_PATH': os.getenv('GITHUB_APP_PRIVATE_KEY_PATH'),
        'GITHUB_APP_CLIENT_ID': os.getenv('GITHUB_APP_CLIENT_ID'),
        'GITHUB_APP_CLIENT_SECRET': os.getenv('GITHUB_APP_CLIENT_SECRET'),
        'GITHUB_APP_NAME': os.getenv('GITHUB_APP_NAME')
    }
    
    github_app_configured = 0
    for key, value in github_app_config.items():
        if value:
            print(f"✅ {key}: 已配置")
            github_app_configured += 1
        else:
            print(f"⚠️  {key}: 未配置")
    
    # 私钥文件检查
    private_key_path = github_app_config.get('GITHUB_APP_PRIVATE_KEY_PATH')
    if private_key_path and os.path.exists(private_key_path):
        print(f"✅ 私钥文件: 存在 ({private_key_path})")
    elif private_key_path:
        print(f"❌ 私钥文件: 不存在 ({private_key_path})")
    
    # 配置建议
    if github_app_configured >= 4:
        print("🎉 GitHub App 配置完整 - 支持 @mention 功能")
        return True
    elif github_token:
        print("⚠️  使用 Personal Access Token - @mention 功能受限")
        print("💡 建议：按照 GITHUB_APP_SETUP.md 创建 GitHub App")
        return True
    else:
        print("❌ 需要配置 GitHub 认证信息")
        return False

def test_webhook_endpoint():
    """测试 Webhook 端点"""
    print("\n=== Webhook 端点测试 ===")
    
    test_payload = {
        "action": "created",
        "issue": {
            "number": 1,
            "title": "Test Issue",
            "body": "This is a test issue",
            "user": {"login": "testuser"}
        },
        "comment": {
            "body": "@bug-fix-agent fix this issue please",
            "user": {"login": "testuser"}
        },
        "repository": {
            "name": "test-repo",
            "owner": {"login": "testowner"},
            "default_branch": "main"
        }
    }
    
    try:
        # 测试 issue_comment 事件
        headers = {
            'Content-Type': 'application/json',
            'X-GitHub-Event': 'issue_comment',
            'X-GitHub-Delivery': 'test-delivery-123'
        }
        
        response = requests.post(
            'http://localhost:8080/api/webhook',
            json=test_payload,
            headers=headers,
            timeout=10
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'accepted':
                print("✅ Webhook 处理成功 - Agent 将开始处理")
                return True
            elif result.get('status') == 'ignored':
                print("⚠️  Webhook 被忽略 - 可能是触发条件不匹配")
                print(f"   原因: {result.get('reason', 'Unknown')}")
                return False
            else:
                print(f"⚠️  Webhook 响应异常: {result}")
                return False
        else:
            print(f"❌ Webhook 调用失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Webhook 测试失败: {e}")
        return False

def test_trigger_patterns():
    """测试触发模式识别"""
    print("\n=== 触发模式测试 ===")
    
    app_name = os.getenv('GITHUB_APP_NAME', 'bug-fix-agent')
    
    test_cases = [
        f"@{app_name} fix this bug",
        f"@{app_name} help me",
        f"@{app_name}",
        "@agent fix",  # 传统模式
        "Please fix this",  # 不应触发
    ]
    
    # 导入触发检测逻辑
    trigger_patterns = [
        rf'@{re.escape(app_name)}\s+fix',
        rf'@{re.escape(app_name)}\s+help', 
        rf'@{re.escape(app_name)}\b',
        r'@agent\s+fix',
        r'@agent fix'
    ]
    
    results = []
    for test_text in test_cases:
        matched = False
        for pattern in trigger_patterns:
            if re.search(pattern, test_text, re.IGNORECASE):
                matched = True
                break
        
        status = "✅" if matched else "❌"
        expected = test_text.startswith('@') and (app_name in test_text or 'agent' in test_text)
        correct = matched == expected
        
        print(f"{status} \"{test_text}\" - {'触发' if matched else '忽略'}")
        results.append(correct)
    
    success_rate = sum(results) / len(results)
    if success_rate >= 0.8:
        print(f"✅ 触发模式识别正常 ({success_rate:.1%})")
        return True
    else:
        print(f"⚠️  触发模式可能有问题 ({success_rate:.1%})")
        return False

def print_next_steps():
    """打印后续步骤建议"""
    print("\n" + "="*50)
    print("🚀 后续步骤:")
    print()
    
    github_token = os.getenv('GITHUB_TOKEN')
    github_app_id = os.getenv('GITHUB_APP_ID')
    
    if not github_token and not github_app_id:
        print("1. 配置 GitHub 认证:")
        print("   - 方式A: 设置 GITHUB_TOKEN (Personal Access Token)")
        print("   - 方式B: 配置 GitHub App (推荐，支持 @mention)")
        print()
    
    print("2. 启动服务:")
    print("   python start_local.py")
    print()
    
    print("3. 暴露 Webhook 端点:")
    print("   ./scripts/ngrok.sh")
    print("   # 或: ngrok http 8080")
    print()
    
    print("4. 配置 Webhook:")
    if github_app_id:
        print("   - 在 GitHub App 设置中配置 Webhook URL")
    else:
        print("   - 在仓库设置中添加 Webhook")
    print("   - URL: https://your-ngrok-url.ngrok-free.app/api/webhook")
    print("   - Events: Issues, Issue comments")
    print()
    
    print("5. 测试使用:")
    app_name = os.getenv('GITHUB_APP_NAME', 'your-app-name')
    print(f"   在 Issue 中评论: @{app_name} fix this bug")
    print()

def main():
    """主函数"""
    print("🤖 Bug Fix Agent - GitHub App 配置测试")
    print("="*50)
    
    tests = [
        test_health_check,
        test_github_config, 
        test_webhook_endpoint,
        test_trigger_patterns
    ]
    
    results = []
    for test_func in tests:
        try:
            result = test_func()
            results.append(result)
        except Exception as e:
            print(f"❌ 测试异常: {e}")
            results.append(False)
    
    # 总结
    passed = sum(results)
    total = len(results)
    success_rate = passed / total
    
    print("\n" + "="*50)
    print(f"📊 测试结果: {passed}/{total} 通过 ({success_rate:.0%})")
    
    if success_rate >= 0.75:
        print("🎉 配置基本正确，Agent 可以工作！")
        
        if os.getenv('GITHUB_APP_ID'):
            app_name = os.getenv('GITHUB_APP_NAME', 'your-app-name')
            print(f"✨ 支持 @{app_name} 提及功能")
        else:
            print("💡 建议配置 GitHub App 以支持 @mention")
    else:
        print("⚠️  存在配置问题，请检查上述失败项")
    
    print_next_steps()

if __name__ == '__main__':
    main()
