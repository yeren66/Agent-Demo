#!/usr/bin/env python3
"""
Test the branch conflict fix with unique branch names
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
from datetime import datetime

async def test_branch_conflict_fix():
    """Test the branch conflict fix"""
    
    # Create job with unique branch name
    timestamp = datetime.utcnow().strftime('%m%d-%H%M%S')
    test_job = {
        'job_id': f'test-branch-fix-{timestamp}',
        'owner': 'yeren66',
        'repo': 'skills-expand-your-team-with-copilot',
        'issue_number': 4,
        'issue_title': 'Test Branch Conflict Fix',
        'actor': 'test-user',
        'branch': f'agent/fix-4-{timestamp}',  # Unique branch name
        'default_branch': 'main'
    }
    
    worker = AgentWorker()
    
    # Create temporary directory
    repo_path = tempfile.mkdtemp(prefix="test-branch-fix-")
    
    try:
        print(f"🔧 Testing branch conflict fix...")
        print(f"Unique branch: {test_job['branch']}")
        
        # Step 1: Initialize repo
        print("\n1️⃣ Repository initialization...")
        init_success = await worker._initialize_repo(test_job, repo_path)
        if not init_success:
            print("❌ Repository initialization failed")
            return False
        print("✅ Repository initialization successful")
        
        # Step 2: Create PR
        print("\n2️⃣ Creating initial PR...")
        pr_number = await worker._create_initial_pr(test_job, repo_path)
        if not pr_number:
            print("❌ PR creation failed")
            return False
        print(f"✅ PR creation successful: #{pr_number}")
        
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
    print("🛠️  Testing branch conflict fix...")
    result = asyncio.run(test_branch_conflict_fix())
    if result:
        print("\n✅ Branch conflict fix successful!")
        print("Agent should now work without branch conflicts.")
    else:
        print("\n❌ Branch conflict fix failed!")
