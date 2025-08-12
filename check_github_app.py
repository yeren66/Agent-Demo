#!/usr/bin/env python3
"""
GitHub App 状态检查工具
检查 GitHub App 的实际配置和安装状态
"""

import os
import sys
import json
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

def check_github_app_webhook():
    """检查 GitHub App webhook 配置"""
    print("📱 GitHub App Webhook 检查")
    print("-" * 40)
    
    app_id = os.getenv('GITHUB_APP_ID')
    if not app_id:
        print("❌ 未配置 GITHUB_APP_ID")
        return
    
    print(f"App ID: {app_id}")
    print(f"Expected Webhook URL: https://131afe4df86c.ngrok-free.app/api/webhook")
    print()
    print("请手动检查以下设置:")
    print(f"1. 访问: https://github.com/settings/apps/{app_id}/advanced")
    print("2. 查看 'Recent Deliveries' 部分")
    print("3. 确认是否有失败的 webhook 请求")
    print()
    print("如果看到失败的请求，点击查看详情，检查:")
    print("   - Response status")
    print("   - Response body") 
    print("   - Request headers")

def check_app_installation():
    """检查 App 安装状态"""
    print("\n🏠 GitHub App 安装检查")
    print("-" * 40)
    
    app_name = os.getenv('GITHUB_APP_NAME', 'mooctestagent')
    
    print(f"App 名称: {app_name}")
    print()
    print("请确认以下几点:")
    print("1. 访问你想测试的仓库")
    print("2. 在 Issue 中尝试输入 @mooc") 
    print("3. 检查是否出现 @mooctestagent 的自动补全")
    print("4. 如果没有自动补全，说明 App 可能没有安装到该仓库")
    print()
    print("安装步骤:")
    print(f"1. 访问: https://github.com/apps/{app_name}")
    print("2. 点击 'Install'")
    print("3. 选择要安装的仓库")
    print("4. 点击 'Install' 确认")

def test_webhook_delivery():
    """测试 webhook 传递"""
    print("\n🚀 Webhook 传递测试")
    print("-" * 40)
    
    ngrok_url = "https://131afe4df86c.ngrok-free.app"
    
    print("手动测试步骤:")
    print("1. 在已安装 App 的仓库中创建一个 Issue")
    print("2. 在 Issue 中评论: @mooctestagent fix this bug")
    print("3. 立即检查以下内容:")
    print()
    print("   a) 服务器日志 (查看终端输出)")
    print("   b) GitHub App Advanced → Recent Deliveries")
    print(f"   c) ngrok 状态: {ngrok_url}/health")
    print()
    print("预期结果:")
    print("✅ GitHub 发送 webhook 到你的 ngrok URL")
    print("✅ Agent 服务接收请求并处理")
    print("✅ Agent 在 Issue 中回复确认消息")

def print_troubleshooting_guide():
    """打印故障排除指南"""
    print("\n🔧 常见问题排除")
    print("=" * 50)
    
    print("\n问题 1: @mention 没有自动补全")
    print("解决方案:")
    print("- 确认 GitHub App 已安装到目标仓库")
    print("- 检查 App 权限设置 (Issues: Read & write)")
    print("- 尝试重新安装 App")
    
    print("\n问题 2: 有自动补全但 webhook 没有触发")
    print("解决方案:")
    print("- 检查 GitHub App Webhook URL 配置")
    print("- 确认 ngrok 隧道正在运行")
    print("- 查看 GitHub App Advanced → Recent Deliveries")
    print("- 检查 Webhook Secret 是否匹配")
    
    print("\n问题 3: Webhook 到达但处理失败")
    print("解决方案:")  
    print("- 检查服务器日志错误信息")
    print("- 确认 GitHub Token 权限充足")
    print("- 检查目标仓库是否存在且可访问")
    
    print("\n问题 4: Agent 回复失败")
    print("解决方案:")
    print("- 确认 GitHub Token 有 repo 完整权限")
    print("- 检查 API rate limit 状态") 
    print("- 确认仓库允许 App 创建评论")

def main():
    print("🔍 GitHub App 状态检查工具")
    print("=" * 50)
    
    load_env_file()
    
    check_github_app_webhook()
    check_app_installation()
    test_webhook_delivery()
    print_troubleshooting_guide()
    
    print("\n💡 下一步:")
    print("1. 按照上述指南检查每个配置项")
    print("2. 在真实仓库中测试 @mooctestagent") 
    print("3. 查看终端日志和 GitHub App 日志")
    print("4. 如果仍有问题，请提供具体的错误信息")

if __name__ == '__main__':
    main()
