#!/usr/bin/env python3
"""
测试完整的AI驱动Bug Fix流程
"""

import sys
import os
import asyncio
import json
import logging
from datetime import datetime

# Add worker directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

async def test_ai_workflow():
    """测试完整的AI工作流"""
    
    print("🤖 Testing Complete AI-Driven Bug Fix Workflow")
    print("=" * 55)
    
    # 模拟一个真实的job
    test_job = {
        'job_id': f'test-ai-{datetime.now().strftime("%Y%m%d-%H%M%S")}',
        'created_at': datetime.utcnow().isoformat(),
        'owner': 'testowner',
        'repo': 'test-repo',
        'issue_number': 123,
        'issue_title': '用户登录功能异常，点击登录按钮无反应',
        'issue_body': '''用户在登录页面输入正确的用户名和密码后，点击登录按钮没有任何响应。

**复现步骤：**
1. 打开登录页面 /login
2. 输入用户名：test@example.com
3. 输入密码：password123
4. 点击"登录"按钮
5. 页面没有跳转，也没有错误提示

**预期结果：**
- 成功登录后跳转到dashboard页面
- 或显示相关错误信息

**环境信息：**
- 浏览器: Chrome 120.0
- 操作系统: macOS Sonoma
- 网络状况: 正常''',
        'actor': 'testuser',
        'branch': 'agent/fix-123',
        'default_branch': 'main',
        'platform': 'github',
        'repo_clone_url': 'https://github.com/testowner/test-repo.git'
    }
    
    print(f"📋 Test Job Info:")
    print(f"   Job ID: {test_job['job_id']}")
    print(f"   Issue: #{test_job['issue_number']} - {test_job['issue_title']}")
    print(f"   Repo: {test_job['owner']}/{test_job['repo']}")
    print()
    
    # 测试各个阶段
    from worker.stages import locate, propose, fix
    from worker.llm_client import get_llm_client
    import tempfile
    import os
    
    # 创建临时目录模拟仓库
    with tempfile.TemporaryDirectory() as temp_dir:
        print(f"📁 Created temp repo: {temp_dir}")
        
        # 创建模拟仓库结构
        os.makedirs(os.path.join(temp_dir, 'src', 'components'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'src', 'auth'), exist_ok=True)
        os.makedirs(os.path.join(temp_dir, 'src', 'api'), exist_ok=True)
        
        # 创建一些示例文件
        files_to_create = {
            'src/components/LoginForm.js': '''
import React, { useState } from 'react';

export default function LoginForm() {
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    
    const handleLogin = () => {
        // TODO: Implement login logic
        console.log('Login clicked');
    };
    
    return (
        <form>
            <input 
                type="email" 
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Email"
            />
            <input 
                type="password" 
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Password"
            />
            <button type="button" onClick={handleLogin}>
                Login
            </button>
        </form>
    );
}
            ''',
            'src/auth/authentication.py': '''
def authenticate_user(email, password):
    """Authenticate user with email and password"""
    # TODO: Implement actual authentication
    if not email or not password:
        return False
    
    # Mock authentication
    return True

def get_user_session(user_id):
    """Get user session data"""
    return {
        'user_id': user_id,
        'authenticated': True
    }
            ''',
            'src/api/login.py': '''
from flask import request, jsonify
from ..auth.authentication import authenticate_user

def login_endpoint():
    """Handle login API endpoint"""
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')
    
    if authenticate_user(email, password):
        return jsonify({'success': True, 'redirect': '/dashboard'})
    else:
        return jsonify({'success': False, 'error': 'Invalid credentials'})
            ''',
            'README.md': '''
# Test Application

A test application for demonstrating the bug fix agent.

## Login Feature

The login feature allows users to authenticate.
            '''
        }
        
        for file_path, content in files_to_create.items():
            full_path = os.path.join(temp_dir, file_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content.strip())
        
        print(f"✅ Created {len(files_to_create)} test files")
        print()
        
        # 模拟gitops和api
        class MockGitOps:
            async def write_file(self, repo_path, file_path, content):
                full_path = os.path.join(repo_path, file_path)
                os.makedirs(os.path.dirname(full_path), exist_ok=True)
                with open(full_path, 'w', encoding='utf-8') as f:
                    f.write(content)
            
            async def add_file(self, repo_path, file_path):
                pass  # Mock
            
            async def add_all(self, repo_path):
                pass  # Mock
            
            async def commit(self, repo_path, message):
                pass  # Mock
            
            async def push(self, repo_path, branch):
                pass  # Mock
            
            async def get_changed_files(self, repo_path):
                return []  # Mock
        
        class MockAPI:
            def comment_pr(self, owner, repo, pr_number, comment):
                print(f"📝 PR Comment: {comment[:100]}...")
                return True
        
        mock_gitops = MockGitOps()
        mock_api = MockAPI()
        
        # 测试 Stage 1: Locate
        print("🔍 Stage 1: AI-Powered Problem Location")
        print("-" * 40)
        
        try:
            locate_result = await locate.run_locate_stage(test_job, temp_dir, mock_api, mock_gitops)
            
            if locate_result['success']:
                print(f"✅ Locate stage completed successfully")
                print(f"📁 Candidate files: {locate_result['candidate_files']}")
                print(f"💬 Comment: {locate_result['comment'][:100]}...")
                
                # 检查生成的分析文件
                analysis_path = os.path.join(temp_dir, 'agent', 'analysis.md')
                if os.path.exists(analysis_path):
                    with open(analysis_path, 'r', encoding='utf-8') as f:
                        analysis_content = f.read()
                    print(f"📋 Generated analysis ({len(analysis_content)} chars)")
                
            else:
                print(f"❌ Locate stage failed: {locate_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Locate stage exception: {e}")
            return False
        
        print()
        
        # 测试 Stage 2: Propose
        print("💡 Stage 2: AI-Generated Fix Plan")
        print("-" * 35)
        
        try:
            propose_result = await propose.run_propose_stage(test_job, temp_dir, mock_api, mock_gitops)
            
            if propose_result['success']:
                print(f"✅ Propose stage completed successfully")
                print(f"🎯 Target files: {propose_result['target_files']}")
                print(f"💬 Comment: {propose_result['comment'][:100]}...")
                
                # 检查生成的补丁计划
                plan_path = os.path.join(temp_dir, 'agent', 'patch_plan.json')
                if os.path.exists(plan_path):
                    with open(plan_path, 'r', encoding='utf-8') as f:
                        plan_content = json.loads(f.read())
                    print(f"📋 Generated patch plan with {len(plan_content.get('proposed_changes', []))} changes")
                
            else:
                print(f"❌ Propose stage failed: {propose_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Propose stage exception: {e}")
            return False
        
        print()
        
        # 测试 Stage 3: Fix
        print("🛠️ Stage 3: AI-Assisted Code Fix")
        print("-" * 32)
        
        try:
            fix_result = await fix.run_fix_stage(test_job, temp_dir, mock_api, mock_gitops)
            
            if fix_result['success']:
                print(f"✅ Fix stage completed successfully")
                print(f"🔧 Changes applied: {fix_result['changes_applied']}")
                print(f"💬 Comment: {fix_result['comment'][:100]}...")
                
            else:
                print(f"❌ Fix stage failed: {fix_result.get('error')}")
                return False
                
        except Exception as e:
            print(f"❌ Fix stage exception: {e}")
            return False
        
        print()
        print("🎉 All AI stages completed successfully!")
        print()
        print("📊 Generated files:")
        agent_dir = os.path.join(temp_dir, 'agent')
        if os.path.exists(agent_dir):
            for file in os.listdir(agent_dir):
                file_path = os.path.join(agent_dir, file)
                if os.path.isfile(file_path):
                    size = os.path.getsize(file_path)
                    print(f"   - {file} ({size} bytes)")
        
        return True

def main():
    """主函数"""
    success = asyncio.run(test_ai_workflow())
    
    if success:
        print("\n✅ AI Workflow Test: PASSED")
        print("\n🚀 Your Bug Fix Agent AI features are working correctly!")
        print("\n📋 What was tested:")
        print("1. ✅ LLM-powered issue analysis")
        print("2. ✅ Intelligent file location")
        print("3. ✅ AI-generated fix plans")
        print("4. ✅ Automated code modifications")
        print("5. ✅ Stage-by-stage progress tracking")
    else:
        print("\n❌ AI Workflow Test: FAILED")
        print("\n🔧 Please check the logs above for specific errors")

if __name__ == "__main__":
    main()
