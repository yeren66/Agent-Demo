#!/usr/bin/env python3
"""
测试完整的 Agent 工作流程
"""

import os
import json
import asyncio
import requests
from datetime import datetime

def test_webhook_flow():
    """测试完整的 webhook 处理流程"""
    
    print("🧪 测试 Agent 完整工作流程")
    print("=" * 50)
    
    # 模拟 webhook 请求
    webhook_payload = {
        "action": "created",
        "issue": {
            "number": 1,
            "title": "Test Bug Report",
            "body": "There is a bug in the code that needs fixing.",
            "user": {"login": "testuser"}
        },
        "comment": {
            "id": 123456,
            "body": "@mooctestagent fix this bug please",
            "user": {"login": "testuser"}
        },
        "repository": {
            "name": "test-repo",
            "owner": {"login": "testowner"},
            "default_branch": "main"
        },
        "sender": {
            "login": "testuser"
        }
    }
    
    headers = {
        "Content-Type": "application/json",
        "X-GitHub-Event": "issue_comment",
        "X-GitHub-Delivery": f"test-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
    }
    
    url = "http://localhost:8080/api/webhook"
    
    print(f"📡 发送 webhook 到: {url}")
    print(f"🎯 触发语句: {webhook_payload['comment']['body']}")
    
    try:
        response = requests.post(url, json=webhook_payload, headers=headers, timeout=30)
        
        print(f"📊 响应状态: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ Webhook 处理成功")
            response_data = response.json() if response.content else {}
            if response_data:
                print(f"📋 响应数据: {json.dumps(response_data, indent=2)}")
        else:
            print(f"❌ Webhook 处理失败: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ 请求失败: {e}")

def test_direct_worker():
    """直接测试 Worker 处理"""
    print("\n🔧 直接测试 Worker 处理")
    print("-" * 30)
    
    # 创建测试 job
    job = {
        "job_id": f"direct-test-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
        "created_at": datetime.utcnow().isoformat(),
        "owner": "testowner",
        "repo": "test-repo", 
        "issue_number": 1,
        "actor": "testuser",
        "branch": "agent/fix-1",
        "repo_clone_url": "https://github.com/testowner/test-repo.git",
        "default_branch": "main"
    }
    
    async def run_worker():
        try:
            # 导入并运行 worker
            import sys
            sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))
            
            from worker.main import process_job
            
            print(f"🚀 处理任务: {job['job_id']}")
            success = await process_job(job)
            
            if success:
                print("✅ Worker 处理成功")
            else:
                print("❌ Worker 处理失败")
                
            return success
            
        except Exception as e:
            print(f"❌ Worker 错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    # 运行异步测试
    success = asyncio.run(run_worker())
    return success

def main():
    """主测试函数"""
    print("🤖 Bug Fix Agent - 工作流程测试")
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
        return
    
    # 测试 1: Webhook 流程
    test_webhook_flow()
    
    # 等待一会儿
    print("\n⏳ 等待 5 秒后进行直接测试...")
    import time
    time.sleep(5)
    
    # 测试 2: 直接 Worker 测试
    test_direct_worker()
    
    print("\n🎉 测试完成")
    print("\n💡 提示:")
    print("- 检查控制台日志查看详细执行过程")
    print("- 在真实仓库中测试完整的 @mention 流程")
    print("- 验证 GitHub App 安装和权限配置")

if __name__ == "__main__":
    main()
