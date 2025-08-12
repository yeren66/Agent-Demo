#!/usr/bin/env python3
"""
Test script to verify PR creation fix
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

from worker.main import AgentWorker

async def test_pr_creation():
    """Test PR creation with proper branch setup"""
    
    # Create test job data
    test_job = {
        'job_id': 'test-pr-fix-001',
        'owner': 'yeren66',
        'repo': 'skills-expand-your-team-with-copilot',
        'issue_number': 4,
        'issue_title': 'Test Issue',
        'actor': 'test-user',
        'branch': 'agent/test-pr-fix-4',
        'default_branch': 'main'
    }
    
    worker = AgentWorker()
    
    # Create temporary directory
    repo_path = tempfile.mkdtemp(prefix="test-pr-fix-")
    
    try:
        print(f"Testing PR creation with job: {test_job['job_id']}")
        
        # Test repository initialization
        print("🔧 Testing repository initialization...")
        init_success = await worker._initialize_repo(test_job, repo_path)
        if not init_success:
            print("❌ Repository initialization failed")
            return False
        print("✅ Repository initialization successful")
        
        # Test PR creation
        print("🔧 Testing PR creation...")
        pr_number = await worker._create_initial_pr(test_job, repo_path)
        if not pr_number:
            print("❌ PR creation failed")
            return False
        print(f"✅ PR creation successful: #{pr_number}")
        
        # Test progress update
        print("🔧 Testing progress update...")
        await worker._update_pr_progress(test_job, 'locate', True)
        print("✅ Progress update successful")
        
        return True
        
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
    print("🚀 Starting PR creation fix test...")
    result = asyncio.run(test_pr_creation())
    if result:
        print("✅ All tests passed!")
    else:
        print("❌ Tests failed!")
