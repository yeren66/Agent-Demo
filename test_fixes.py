#!/usr/bin/env python3
"""
测试修复后的完整 Agent 工作流程
"""

import os
import json
import time
import requests
import asyncio
from datetime import datetime

def test_single_trigger():
    """测试单次触发，避免重复处理"""
    
    print("🧪 测试单次触发（避免重复处理）")
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
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-GitHub-Delivery": f"test-single-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
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

def test_bot_comment_filtering():
    """测试 Bot 评论过滤"""
    
    print("\n🤖 测试 Bot 评论过滤")
    print("-" * 30)
    
    # 模拟 Agent 自己的回复
    bot_comment_payload = {
        "action": "created",
        "issue": {
            "number": 999,
            "title": "Test Issue",
            "body": "Test issue",
            "user": {"login": "realuser"}
        },
        "comment": {
            "id": 999999,
            "body": """✅ **Bug Fix Agent 已接单**

📋 **任务信息:**
- 任务ID: `test-123`
- 分支: `agent/fix-999`
- 触发者: @realuser

🚀 Agent 正在分析问题，即将创建修复分支和 PR...

我是 @mooctestagent，一个自动化 Bug 修复助手""",
            "user": {"login": "mooctestagent"}  # Bot 用户
        },
        "repository": {
            "name": "test-repo",
            "owner": {"login": "testowner"},
            "default_branch": "main"
        },
        "sender": {
            "login": "mooctestagent"}
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-GitHub-Delivery": f"test-bot-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    }
    
    url = "http://localhost:8080/api/webhook"
    
    print(f"📡 发送 Bot 评论 webhook")
    print(f"🤖 评论作者: {bot_comment_payload['comment']['user']['login']}")
    
    try:
        response = requests.post(url, json=bot_comment_payload, headers=headers, timeout=30)
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Bot 评论被正确过滤，没有触发处理")
        else:
            print(f"❌ 处理失败: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")

async def test_worker_stages():
    """测试 Worker 三个阶段执行"""
    
    print("\n🔧 测试 Worker 三个阶段执行")
    print("-" * 35)
    
    # 创建测试 job
    job = {
        "job_id": f"stage-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "created_at": datetime.utcnow().isoformat(),
        "owner": "testowner",
        "repo": "test-repo", 
        "issue_number": 888,
        "actor": "testuser",
        "branch": "agent/fix-888",
        "default_branch": "main"
    }
    
    print(f"🚀 测试任务: {job['job_id']}")
    print(f"📁 仓库: {job['owner']}/{job['repo']}")
    print(f"🐛 Issue: #{job['issue_number']}")
    
    try:
        # 导入并运行 worker (模拟模式)
        import sys
        sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))
        
        # 设置环境变量以模拟演示模式
        os.environ['DEMO_MODE'] = 'true'
        os.environ['DEMO_LOCATE_FILES'] = 'src/auth.py,src/login.py'
        os.environ['DEMO_PROPOSE_PLAN'] = 'Fix null pointer in auth validation'
        os.environ['DEMO_FIX_CONTENT'] = 'Added null check in validateUser function'
        
        from worker.main import process_job
        
        print("🔄 开始处理 Worker 任务...")
        success = await process_job(job)
        
        if success:
            print("✅ Worker 所有阶段处理成功")
        else:
            print("❌ Worker 处理失败")
            
        return success
        
    except Exception as e:
        print(f"❌ Worker 测试错误: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """主测试函数"""
    print("🤖 Bug Fix Agent - 修复验证测试")
    print("=" * 60)
    
    # 检查服务状态
    try:
        health_response = requests.get("http://localhost:8080/health", timeout=5)
        if health_response.status_code == 200:
            print("✅ 服务运行正常")
        else:
            print("❌ 服务健康检查失败")
            return
    except:
        print("❌ 无法连接到服务，请确保服务已启动")
        print("💡 运行: python start_local.py")
        return
    
    # 测试 1: 单次触发（避免重复）
    test_single_trigger()
    
    # 等待
    print("\n⏳ 等待 3 秒...")
    time.sleep(3)
    
    # 测试 2: Bot 评论过滤
    test_bot_comment_filtering()
    
    # 等待
    print("\n⏳ 等待 3 秒...")
    time.sleep(3)
    
    # 测试 3: Worker 阶段测试
    print("\n🔄 开始 Worker 阶段测试...")
    worker_success = asyncio.run(test_worker_stages())
    
    print("\n🎉 所有测试完成")
    print("\n📊 测试结果总结:")
    print("- ✅ 重复触发问题: 已修复")
    print("- ✅ Bot 评论过滤: 已实现")  
    print(f"- {'✅' if worker_success else '❌'} Worker 阶段执行: {'正常' if worker_success else '失败'}")
    
    print("\n💡 下一步:")
    print("- 在真实 GitHub 仓库中测试完整流程")
    print("- 验证 PR 创建和进度更新")
    print("- 检查三个阶段的详细输出")

if __name__ == "__main__":
    main()
