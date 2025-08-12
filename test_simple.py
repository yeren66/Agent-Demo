#!/usr/bin/env python3
"""
测试修复后的完整 Agent 工作流程（不需要签名验证）
"""

import os
import json
import time
import requests
import asyncio
from datetime import datetime

def test_single_trigger_no_signature():
    """测试单次触发，绕过签名验证"""
    
    print("🧪 测试单次触发（绕过签名验证）")
    print("=" * 50)
    
    # 创建一个正常的用户触发请求
    webhook_payload = {
        "action": "created",
        "issue": {
            "number": 999,
            "title": "Test Bug that needs fixing",
            "body": "There is a critical bug in the authentication module that causes login failures.",
            "user": {"login": "realuser"}
        },
        "comment": {
            "id": 888888,
            "body": "@mooctestagent fix this critical authentication bug",
            "user": {"login": "realuser"}  # 真实用户触发
        },
        "repository": {
            "name": "test-repo",
            "owner": {"login": "testowner"},
            "default_branch": "main"
        },
        "sender": {
            "login": "realuser"
        }
    }
    
    # 不使用 GitHub headers，直接 POST
    headers = {
        "Content-Type": "application/json"
    }
    
    url = "http://localhost:8080/api/webhook"
    
    print(f"📡 发送 webhook 到: {url}")
    print(f"🎯 触发语句: {webhook_payload['comment']['body']}")
    print(f"👤 触发用户: {webhook_payload['comment']['user']['login']}")
    
    try:
        response = requests.post(url, json=webhook_payload, headers=headers, timeout=30)
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook 处理成功")
            print("⏳ 等待 10 秒观察是否有重复触发...")
            time.sleep(10)
            print("✅ 如果没有看到重复的日志，说明重复触发问题已解决")
        else:
            print(f"❌ Webhook 处理失败: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")

def test_service_health():
    """测试服务健康状态"""
    print("🩺 检查服务健康状态")
    print("-" * 30)
    
    try:
        response = requests.get("http://localhost:8080/health", timeout=5)
        print(f"Health endpoint 状态: {response.status_code}")
        if response.status_code == 200:
            print("✅ 服务运行正常")
            return True
        else:
            print("❌ 服务健康检查失败")
            return False
    except Exception as e:
        print(f"❌ 无法连接到服务: {e}")
        return False

def main():
    """主测试函数"""
    print("🤖 Bug Fix Agent - 简化修复验证测试")
    print("=" * 60)
    
    # 检查服务状态
    if not test_service_health():
        print("💡 请确保服务已启动: python start_local.py")
        return
    
    print("\n")
    
    # 测试单次触发（绕过签名验证）
    test_single_trigger_no_signature()
    
    print("\n🎉 测试完成")
    print("\n💡 查看服务日志:")
    print("- 检查是否只有一次处理日志")
    print("- 确认没有重复的 'Bug Fix Agent 已接单' 消息")
    print("- 观察 Worker 是否正常启动处理阶段")

if __name__ == "__main__":
    main()
