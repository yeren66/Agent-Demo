#!/usr/bin/env python3
"""
Test authentication and clone functionality
"""

import asyncio
import tempfile
import shutil
import os
import sys
sys.path.append('.')

from dotenv import load_dotenv
load_dotenv()

from worker.git_platform_api import GitPlatformAPI
from worker.gitops import GitOps

async def test_auth_and_clone():
    """Test authentication and cloning"""
    
    # Test authentication
    print("🔧 Testing GitHub authentication...")
    api = GitPlatformAPI()
    
    print(f"Platform: {api.platform}")
    print(f"Base URL: {api.base_url}")
    print(f"GitHub App available: {api._github_app_auth.is_app_available() if api._github_app_auth else 'No'}")
    
    # Test getting token
    owner, repo = 'yeren66', 'skills-expand-your-team-with-copilot'
    token = api.get_token(owner, repo)
    
    if not token:
        print("❌ No authentication token available")
        return False
    
    print(f"✅ Token available: {token[:10]}...")
    
    # Test repository access
    print(f"🔧 Testing repository access for {owner}/{repo}...")
    repo_info = api.get_repo(owner, repo)
    if not repo_info:
        print("❌ Repository access failed")
        return False
    
    print(f"✅ Repository access successful: {repo_info.get('full_name')}")
    print(f"  Default branch: {repo_info.get('default_branch')}")
    print(f"  Private: {repo_info.get('private')}")
    
    # Test clone
    print("🔧 Testing repository clone...")
    gitops = GitOps()
    
    # Create temp directory
    temp_dir = tempfile.mkdtemp(prefix="test-clone-")
    
    try:
        # Format clone URL
        clone_url = f"https://x-access-token:{token}@github.com/{owner}/{repo}.git"
        
        clone_success = await gitops.clone_repo(clone_url, temp_dir)
        if not clone_success:
            print("❌ Repository clone failed")
            return False
        
        print("✅ Repository clone successful")
        
        # Test branch creation
        print("🔧 Testing branch creation...")
        branch_name = "test-auth-branch"
        branch_success = await gitops.create_branch(temp_dir, branch_name, "main")
        
        if not branch_success:
            print("❌ Branch creation failed")
            return False
        
        print("✅ Branch creation successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False
    
    finally:
        # Cleanup
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir, ignore_errors=True)

if __name__ == "__main__":
    print("🚀 Starting authentication and clone test...")
    result = asyncio.run(test_auth_and_clone())
    if result:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed!")
