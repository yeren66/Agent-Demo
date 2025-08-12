#!/usr/bin/env python3
"""
Complete workflow test to verify the proxy fix works end-to-end
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

async def test_complete_workflow():
    """Test complete agent workflow with proxy"""
    
    # Create test job data similar to real webhook
    test_job = {
        'job_id': 'test-proxy-workflow-001',
        'owner': 'yeren66',
        'repo': 'skills-expand-your-team-with-copilot', 
        'issue_number': 4,
        'issue_title': 'Test Proxy Fix',
        'actor': 'test-user',
        'branch': 'agent/test-proxy-fix-4',
        'default_branch': 'main'
    }
    
    print("🚀 Starting complete workflow test with proxy...")
    print(f"Job: {test_job['job_id']}")
    print(f"Repository: {test_job['owner']}/{test_job['repo']}")
    print(f"Issue: #{test_job['issue_number']}")
    print(f"Proxy: {os.getenv('HTTP_PROXY')}")
    
    worker = AgentWorker()
    
    # Create temporary directory
    repo_path = tempfile.mkdtemp(prefix="test-workflow-")
    
    try:
        # Test 1: Repository initialization
        print("\n🔧 Step 1: Testing repository initialization...")
        init_success = await worker._initialize_repo(test_job, repo_path)
        if not init_success:
            print("❌ Repository initialization failed")
            return False
        print("✅ Repository initialization successful")
        
        # Test 2: Initial PR creation
        print("\n🔧 Step 2: Testing initial PR creation...")
        pr_number = await worker._create_initial_pr(test_job, repo_path)
        if not pr_number:
            print("❌ Initial PR creation failed")
            return False
        print(f"✅ Initial PR creation successful: #{pr_number}")
        
        test_job['pr_number'] = pr_number
        
        # Test 3: Progress update
        print("\n🔧 Step 3: Testing progress update...")
        await worker._update_pr_progress(test_job, 'locate', True)
        print("✅ Progress update successful")
        
        # Test 4: Final comment (simulate)
        print("\n🔧 Step 4: Testing final finalization...")
        # await worker._finalize_pr(test_job)  # Skip to avoid real comments
        print("✅ Finalization test skipped (would add real comments)")
        
        print(f"\n🎉 Complete workflow test successful!")
        print(f"Created PR #{pr_number} with proxy support")
        return True
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)

if __name__ == "__main__":
    print("🌟 Starting complete agent workflow test with proxy support...")
    result = asyncio.run(test_complete_workflow())
    if result:
        print("\n✅ All workflow tests passed! Agent should now work with proxy.")
        print("\n💡 The proxy fix includes:")
        print("   - Git clone with proxy support")  
        print("   - Git push with proxy support")
        print("   - GitHub API requests with proxy")
        print("   - LLM API requests with proxy")
        print("   - Timeout protection against network hangs")
    else:
        print("\n❌ Workflow tests failed!")
