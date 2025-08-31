#!/usr/bin/env python3
"""
Test script to debug GitCode Issue API issues
"""

import os
import sys
import requests
import logging

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_gitcode_issue_api():
    """Test GitCode Issue API to identify the problem"""
    
    print("🔍 GitCode Issue API 调试测试")
    print("=" * 50)
    
    # 从.env文件读取配置
    env_file = '.env'
    gitcode_pat = None
    gitcode_bot_username = 'yeren66'
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('GITCODE_PAT='):
                    gitcode_pat = line.split('=', 1)[1]
                elif line.startswith('GITCODE_BOT_USERNAME='):
                    gitcode_bot_username = line.split('=', 1)[1]
    
    if not gitcode_pat:
        print("❌ GITCODE_PAT 未在.env文件中找到")
        return False
    
    print(f"✅ GitCode PAT: {'*' * 20}{gitcode_pat[-4:] if len(gitcode_pat) > 4 else 'Set'}")
    print(f"✅ Bot Username: {gitcode_bot_username}")
    
    # 测试配置 - 根据实际错误日志调整
    test_owner = 'syeren'  # 从错误日志中获取
    test_repo = 'react-demo-front'  # 从错误日志中获取
    
    base_url = 'https://api.gitcode.com/api/v5'
    headers = {
        'Authorization': f'Bearer {gitcode_pat}',
        'Content-Type': 'application/json',
        'User-Agent': 'Bug-Fix-Agent/1.0'
    }
    
    print(f"\n🎯 测试目标: {test_owner}/{test_repo}")
    
    # 1. 测试获取仓库信息
    print("\n1. 测试仓库访问权限...")
    repo_url = f"{base_url}/repos/{test_owner}/{test_repo}"
    
    try:
        response = requests.get(repo_url, headers=headers, timeout=10)
        print(f"仓库API响应: {response.status_code}")
        
        if response.status_code == 200:
            repo_data = response.json()
            print(f"✅ 仓库访问成功: {repo_data.get('name', 'Unknown')}")
            print(f"   默认分支: {repo_data.get('default_branch', 'Unknown')}")
            print(f"   权限: {repo_data.get('permissions', 'Unknown')}")
        else:
            print(f"❌ 仓库访问失败: {response.text}")
            
    except Exception as e:
        print(f"❌ 仓库API调用失败: {e}")
    
    # 2. 测试获取Issues列表
    print("\n2. 测试Issues列表...")
    issues_url = f"{base_url}/repos/{test_owner}/{test_repo}/issues"
    
    try:
        response = requests.get(issues_url, headers=headers, timeout=10)
        print(f"Issues列表API响应: {response.status_code}")
        
        if response.status_code == 200:
            issues = response.json()
            print(f"✅ 获取到 {len(issues)} 个Issues")
            
            # 显示前几个Issue的信息
            for i, issue in enumerate(issues[:3]):
                issue_id = issue.get('id')
                issue_iid = issue.get('iid') 
                issue_number = issue.get('number')
                issue_title = issue.get('title', 'No Title')[:50]
                
                print(f"   Issue #{i+1}:")
                print(f"     ID: {issue_id}")
                print(f"     IID: {issue_iid}")
                print(f"     Number: {issue_number}")
                print(f"     Title: {issue_title}")
                
                # 测试这个Issue的评论API
                test_issue_number = issue_iid or issue_number or issue_id
                if test_issue_number:
                    print(f"     测试评论API (使用编号 {test_issue_number})...")
                    comment_url = f"{base_url}/repos/{test_owner}/{test_repo}/issues/{test_issue_number}/comments"
                    
                    try:
                        # 先获取现有评论
                        get_response = requests.get(comment_url, headers=headers, timeout=5)
                        print(f"       获取评论: {get_response.status_code}")
                        
                        if get_response.status_code == 200:
                            comments = get_response.json()
                            print(f"       ✅ 该Issue有 {len(comments)} 个评论")
                            
                            # 测试发送评论 (只在测试模式下)
                            test_comment = {
                                "body": "🧪 GitCode Bug Fix Agent API连通性测试 (请忽略此消息)"
                            }
                            
                            print(f"       准备发送测试评论...")
                            post_response = requests.post(comment_url, headers=headers, 
                                                        json=test_comment, timeout=5)
                            print(f"       发送评论: {post_response.status_code}")
                            
                            if post_response.status_code in [200, 201]:
                                print(f"       ✅ 评论发送成功!")
                            else:
                                print(f"       ❌ 评论发送失败: {post_response.text}")
                            
                        else:
                            print(f"       ❌ 获取评论失败: {get_response.text}")
                            
                    except Exception as e:
                        print(f"       ❌ 评论API测试失败: {e}")
                
                print()  # 空行分隔
                
        else:
            print(f"❌ Issues列表获取失败: {response.text}")
            
    except Exception as e:
        print(f"❌ Issues API调用失败: {e}")
    
    # 3. 根据错误日志测试特定Issue
    print("\n3. 测试特定Issue (根据错误日志)...")
    
    # 从错误日志看，系统尝试访问 issues/5/comments 但实际应该是其他编号
    test_issue_numbers = [5, 3243389]  # 尝试不同的编号
    
    for issue_num in test_issue_numbers:
        print(f"\n   测试Issue #{issue_num}:")
        comment_url = f"{base_url}/repos/{test_owner}/{test_repo}/issues/{issue_num}/comments"
        
        try:
            response = requests.get(comment_url, headers=headers, timeout=5)
            print(f"     响应状态: {response.status_code}")
            
            if response.status_code == 200:
                comments = response.json()
                print(f"     ✅ Issue #{issue_num} 存在，有 {len(comments)} 个评论")
                
                # 获取Issue详情
                issue_url = f"{base_url}/repos/{test_owner}/{test_repo}/issues/{issue_num}"
                issue_response = requests.get(issue_url, headers=headers, timeout=5)
                if issue_response.status_code == 200:
                    issue_data = issue_response.json()
                    print(f"     Issue标题: {issue_data.get('title', 'Unknown')}")
                    print(f"     Issue ID: {issue_data.get('id')}")
                    print(f"     Issue IID: {issue_data.get('iid')}")
                    
            elif response.status_code == 404:
                print(f"     ⚠️ Issue #{issue_num} 不存在或无权限访问")
            else:
                print(f"     ❌ Issue #{issue_num} 访问失败: {response.text}")
                
        except Exception as e:
            print(f"     ❌ Issue #{issue_num} API调用失败: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 调试建议:")
    print("1. 确认Issue编号映射 (id vs iid vs number)")
    print("2. 检查API访问权限和认证")
    print("3. 验证仓库和Issue的实际存在性")
    print("4. 检查GitCode API的具体要求和限制")

if __name__ == '__main__':
    test_gitcode_issue_api()
