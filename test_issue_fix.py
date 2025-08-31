#!/usr/bin/env python3
"""
Test the fixed Issue number handling
"""

import os
import sys

# Add project paths
sys.path.append(os.path.join(os.path.dirname(__file__), 'gateway'))

def test_issue_number_fix():
    """Test the issue number parsing fix"""
    print("🧪 测试Issue编号修复")
    print("=" * 40)
    
    # 模拟GitCode webhook payload
    test_payload = {
        'object_attributes': {
            'id': 3243389,      # 全局ID（用于显示）
            'iid': 2,           # 内部ID
            'number': 2,        # API编号（正确的）
            'title': 'npm start 失败：react-scripts 未找到'
        },
        'project': {
            'name': 'react-demo-front',
            'namespace': {
                'name': 'syeren'
            }
        },
        'user': {
            'username': 'testuser'
        },
        'action': 'assigned'
    }
    
    from handlers.gitcode_handler import GitCodeEventHandler
    
    handler = GitCodeEventHandler()
    job = handler.create_job('Issue Hook', test_payload)
    
    if job:
        print(f"✅ 任务创建成功:")
        print(f"   API Issue编号: {job['issue_number']}")
        print(f"   显示Issue编号: {job['display_issue_number']}")
        print(f"   仓库: {job['owner']}/{job['repo']}")
        print(f"   标题: {job['issue_title']}")
        print(f"   分支: {job['branch']}")
        
        # 验证编号是否正确
        if job['issue_number'] == 2:  # API调用应该使用number=2
            print("✅ API编号正确")
        else:
            print(f"❌ API编号错误，期望2，实际{job['issue_number']}")
            
        if job['display_issue_number'] == 3243389:  # 显示应该使用id=3243389
            print("✅ 显示编号正确")
        else:
            print(f"❌ 显示编号错误，期望3243389，实际{job['display_issue_number']}")
    else:
        print("❌ 任务创建失败")
    
    print("\n🎯 修复总结:")
    print("- GitCode API使用 'number' 字段作为Issue编号")
    print("- 显示时使用 'id' 字段的全局ID")
    print("- 这解释了为什么Issue #5不存在的错误")

if __name__ == '__main__':
    test_issue_number_fix()
