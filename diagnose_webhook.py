#!/usr/bin/env python3
"""
GitHub Webhook 诊断工具
帮助诊断为什么 webhook 没有被触发
"""

import os
import sys
import json
import hmac
import hashlib
import requests
from pathlib import Path

def load_env_file():
    """Load environment variables from .env file"""
    env_file = Path(__file__).parent / '.env'
    if env_file.exists():
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    if key not in os.environ:
                        os.environ[key] = value

def create_github_signature(payload_body, secret):
    """Create GitHub webhook signature"""
    if isinstance(payload_body, str):
        payload_body = payload_body.encode('utf-8')
    
    signature = hmac.new(
        secret.encode('utf-8'),
        payload_body,
        hashlib.sha256
    ).hexdigest()
    
    return f"sha256={signature}"

def test_webhook_with_signature():
    """Test webhook with proper GitHub signature"""
    print("🔧 测试 Webhook 端点 (带签名验证)")
    
    webhook_secret = os.getenv('WEBHOOK_SECRET', '123456')
    
    # 创建测试 payload
    test_payload = {
        "action": "created",
        "issue": {
            "number": 1,
            "title": "Test Issue",
            "body": "This is a test issue",
            "user": {"login": "testuser"}
        },
        "comment": {
            "body": "@mooctestagent fix this bug please",
            "user": {"login": "testuser"}
        },
        "repository": {
            "name": "test-repo",
            "owner": {"login": "testowner"},
            "default_branch": "main"
        }
    }
    
    payload_str = json.dumps(test_payload, separators=(',', ':'))
    signature = create_github_signature(payload_str, webhook_secret)
    
    headers = {
        'Content-Type': 'application/json',
        'X-GitHub-Event': 'issue_comment',
        'X-GitHub-Delivery': 'test-delivery-123',
        'X-Hub-Signature-256': signature
    }
    
    try:
        response = requests.post(
            'http://localhost:8080/api/webhook',
            data=payload_str,
            headers=headers,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'accepted':
                print("✅ 本地 Webhook 测试成功！")
                return True
            else:
                print(f"⚠️  Webhook 处理结果: {result}")
        else:
            print(f"❌ Webhook 测试失败: {response.status_code}")
            
    except Exception as e:
        print(f"❌ 请求失败: {e}")
    
    return False

def test_ngrok_endpoint():
    """Test ngrok endpoint"""
    print("\n🌐 测试 ngrok 端点")
    
    ngrok_url = "https://131afe4df86c.ngrok-free.app"
    
    # 测试健康检查
    try:
        response = requests.get(f"{ngrok_url}/health", timeout=5)
        if response.status_code == 200:
            print(f"✅ ngrok 健康检查正常: {response.json()}")
        else:
            print(f"❌ ngrok 健康检查失败: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ 无法访问 ngrok 端点: {e}")
        return False
    
    return True

def check_github_app_config():
    """Check GitHub App configuration"""
    print("\n📱 GitHub App 配置检查")
    
    app_id = os.getenv('GITHUB_APP_ID')
    app_name = os.getenv('GITHUB_APP_NAME')
    webhook_secret = os.getenv('WEBHOOK_SECRET')
    
    print(f"App ID: {app_id}")
    print(f"App 名称: {app_name}")
    print(f"Webhook Secret: {'已配置' if webhook_secret else '未配置'}")
    
    print("\n🔍 需要检查的设置:")
    print("1. GitHub App Webhook URL 是否正确:")
    print("   https://131afe4df86c.ngrok-free.app/api/webhook")
    print("\n2. 订阅的事件是否包含:")
    print("   ✅ Issues")
    print("   ✅ Issue comments") 
    print("\n3. Repository permissions:")
    print("   ✅ Issues: Read & write")
    print("   ✅ Pull requests: Read & write")
    print("   ✅ Contents: Read & write")
    print("\n4. App 是否已安装到测试仓库")

def simulate_github_webhook():
    """Simulate a real GitHub webhook"""
    print("\n🧪 模拟真实 GitHub Webhook")
    
    webhook_secret = os.getenv('WEBHOOK_SECRET', '123456')
    ngrok_url = "https://131afe4df86c.ngrok-free.app"
    
    # 更真实的 payload 结构
    payload = {
        "action": "created",
        "issue": {
            "number": 1,
            "title": "Test bug report",
            "body": "Found a bug that needs fixing",
            "user": {
                "login": "testuser",
                "id": 12345
            },
            "state": "open"
        },
        "comment": {
            "id": 67890,
            "body": "@mooctestagent fix this bug please",
            "user": {
                "login": "testuser", 
                "id": 12345
            }
        },
        "repository": {
            "id": 123456789,
            "name": "test-repo",
            "full_name": "testowner/test-repo",
            "owner": {
                "login": "testowner",
                "id": 11111
            },
            "default_branch": "main"
        },
        "installation": {
            "id": 98765
        }
    }
    
    payload_str = json.dumps(payload, separators=(',', ':'))
    signature = create_github_signature(payload_str, webhook_secret)
    
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'GitHub-Hookshot/abc123',
        'X-GitHub-Event': 'issue_comment',
        'X-GitHub-Delivery': f'12345678-1234-1234-1234-123456789012',
        'X-Hub-Signature-256': signature
    }
    
    try:
        print("发送请求到:", f"{ngrok_url}/api/webhook")
        response = requests.post(
            f"{ngrok_url}/api/webhook",
            data=payload_str,
            headers=headers,
            timeout=10
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            print("✅ 模拟 webhook 测试成功！")
        else:
            print("❌ 模拟 webhook 测试失败")
            
    except Exception as e:
        print(f"❌ 模拟测试失败: {e}")

def main():
    print("🔍 GitHub Webhook 诊断工具")
    print("="*50)
    
    # 加载环境变量
    load_env_file()
    
    # 运行诊断
    tests = [
        ("ngrok 端点测试", test_ngrok_endpoint),
        ("本地 Webhook 测试", test_webhook_with_signature),
        ("GitHub App 配置检查", lambda: (check_github_app_config(), True)[1]),
        ("模拟 GitHub Webhook", lambda: (simulate_github_webhook(), True)[1])
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            test_func()
        except Exception as e:
            print(f"❌ {test_name} 失败: {e}")
    
    print("\n" + "="*50)
    print("🔧 故障排除建议:")
    print("1. 确认 GitHub App Webhook URL 配置正确")
    print("2. 确认 Webhook Secret 匹配")
    print("3. 确认 App 已安装到测试仓库")
    print("4. 检查 GitHub App 事件订阅设置")
    print("5. 查看 GitHub App → Advanced → Recent Deliveries")

if __name__ == '__main__':
    main()
