#!/usr/bin/env python3
"""
Test to reproduce the exact PR creation failure with real job format
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
from worker.templates import render_progress_panel

async def test_real_job_format():
    """Test with exact job format that agent receives"""
    
    # This is the exact format the agent receives from webhook
    test_job = {
        'job_id': 'a7c829be-eed9-4bc5-a333-8c676916303a',
        'owner': 'yeren66',
        'repo': 'skills-expand-your-team-with-copilot',
        'issue_number': 4,
        'actor': 'yeren66',
        'branch': 'agent/fix-4',
        'default_branch': 'main',
        'created_at': '2025-08-12T10:30:00Z'
        # Note: issue_title might be missing!
    }
    
    worker = AgentWorker()
    
    # Create temporary directory
    repo_path = tempfile.mkdtemp(prefix="test-real-job-")
    
    try:
        print(f"🔧 Testing with real job format...")
        print(f"Job data: {test_job}")
        
        # Test template rendering first
        print("\n1️⃣ Testing template rendering...")
        try:
            pr_body = render_progress_panel(
                issue_number=test_job['issue_number'],
                actor=test_job['actor'],
                job_id=test_job['job_id'],
                initialized=True,
                locate=False, propose=False, fix=False, 
                verify=False, deploy=False, ready=False
            )
            print("✅ Template rendering successful")
            print(f"PR body length: {len(pr_body)} characters")
        except Exception as e:
            print(f"❌ Template rendering failed: {e}")
            return False
        
        # Test repo initialization
        print("\n2️⃣ Testing repository initialization...")
        init_success = await worker._initialize_repo(test_job, repo_path)
        if not init_success:
            print("❌ Repository initialization failed")
            return False
        print("✅ Repository initialization successful")
        
        # Test the exact PR creation process
        print("\n3️⃣ Testing _create_initial_pr with exact same data...")
        
        # Check if issue_title is missing and add it
        if 'issue_title' not in test_job:
            print("⚠️  issue_title missing, adding default...")
            test_job['issue_title'] = 'Issue'
        
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
    print("🧪 Testing with real job format...")
    result = asyncio.run(test_real_job_format())
    if result:
        print("\n✅ Real job format test successful!")
    else:
        print("\n❌ Real job format test failed!")
