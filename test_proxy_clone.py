#!/usr/bin/env python3
"""
Test script to verify proxy and clone functionality
"""

import asyncio
import tempfile
import shutil
import os
import sys
sys.path.append('.')

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from worker.gitops import GitOps
from worker.git_platform_api import GitPlatformAPI

async def test_with_proxy():
    """Test clone with proxy settings"""
    
    print("🔧 Testing proxy configuration...")
    print(f"HTTP_PROXY: {os.getenv('HTTP_PROXY')}")
    print(f"HTTPS_PROXY: {os.getenv('HTTPS_PROXY')}")
    
    # Test GitHub API with proxy
    print("\n🔧 Testing GitHub API with proxy...")
    api = GitPlatformAPI()
    
    # Test getting repository info
    repo_info = api.get_repo('yeren66', 'skills-expand-your-team-with-copilot')
    if repo_info:
        print("✅ GitHub API request successful")
        print(f"Repository: {repo_info.get('full_name')}")
        print(f"Default branch: {repo_info.get('default_branch')}")
    else:
        print("❌ GitHub API request failed")
        return False
    
    # Test git clone with proxy
    print("\n🔧 Testing git clone with proxy...")
    gitops = GitOps()
    
    # Get token for authentication
    token = api.get_token('yeren66', 'skills-expand-your-team-with-copilot')
    if not token:
        print("❌ No authentication token available")
        return False
    
    print(f"✅ Got authentication token: {token[:10]}...")
    
    # Create temporary directory
    repo_path = tempfile.mkdtemp(prefix="test-proxy-clone-")
    
    try:
        # Prepare clone URL
        clone_url = f"https://x-access-token:{token}@github.com/yeren66/skills-expand-your-team-with-copilot.git"
        
        print(f"Cloning to: {repo_path}")
        
        # Test clone
        clone_success = await gitops.clone_repo(clone_url, repo_path)
        if clone_success:
            print("✅ Git clone successful")
            
            # Test branch creation
            print("\n🔧 Testing branch creation...")
            branch_success = await gitops.create_branch(repo_path, 'test-proxy-branch', 'main')
            if branch_success:
                print("✅ Branch creation successful")
                return True
            else:
                print("❌ Branch creation failed")
                return False
        else:
            print("❌ Git clone failed")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)

if __name__ == "__main__":
    print("🚀 Starting proxy and clone test...")
    result = asyncio.run(test_with_proxy())
    if result:
        print("\n✅ All tests passed! Proxy configuration is working.")
    else:
        print("\n❌ Tests failed!")
