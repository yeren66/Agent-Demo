#!/usr/bin/env python3
"""
Debug script to check PR creation issue
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
from worker.git_platform_api import GitPlatformAPI

async def debug_pr_creation():
    """Debug the PR creation process step by step"""
    
    # Create test job data
    test_job = {
        'job_id': 'debug-pr-creation-001',
        'owner': 'yeren66',
        'repo': 'skills-expand-your-team-with-copilot',
        'issue_number': 4,
        'issue_title': 'Debug PR Creation',
        'actor': 'debug-user',
        'branch': 'agent/debug-pr-4',
        'default_branch': 'main'
    }
    
    worker = AgentWorker()
    api = GitPlatformAPI()
    
    # Create temporary directory
    repo_path = tempfile.mkdtemp(prefix="debug-pr-")
    
    try:
        print(f"🔧 Debugging PR creation for job: {test_job['job_id']}")
        
        # Step 1: Initialize repo
        print("\n1️⃣ Repository initialization...")
        init_success = await worker._initialize_repo(test_job, repo_path)
        if not init_success:
            print("❌ Repository initialization failed")
            return False
        print("✅ Repository initialization successful")
        
        # Step 2: Check if we can manually create a minimal commit and push
        print("\n2️⃣ Creating test file and commit...")
        
        # Create test file
        test_file = os.path.join(repo_path, 'debug.txt')
        with open(test_file, 'w') as f:
            f.write(f"Debug test for {test_job['job_id']}")
        
        # Add and commit
        add_success = await worker.gitops.add_file(repo_path, 'debug.txt')
        if not add_success:
            print("❌ Failed to add file")
            return False
        print("✅ File added")
        
        commit_success = await worker.gitops.commit(repo_path, "debug: test commit")
        if not commit_success:
            print("❌ Failed to commit")
            return False
        print("✅ Commit successful")
        
        # Step 3: Push branch
        print("\n3️⃣ Pushing branch...")
        push_success = await worker.gitops.push(repo_path, test_job['branch'])
        if not push_success:
            print("❌ Push failed")
            return False
        print("✅ Push successful")
        
        # Step 4: Check branch exists on remote
        print("\n4️⃣ Verifying branch exists on remote...")
        # We can't directly check this via API easily, but let's try creating PR
        
        # Step 5: Try to create PR
        print("\n5️⃣ Creating PR...")
        
        # Check if there's any existing PR for this branch first
        # This might give us more info
        
        pr_data = {
            'title': f"🧪 Debug PR for #{test_job['issue_number']}",
            'body': 'This is a debug PR to test the creation process.',
            'head': test_job['branch'],
            'base': test_job['default_branch'],
            'draft': True
        }
        
        print(f"PR data: {pr_data}")
        
        pr_result = api.create_pr(**pr_data, owner=test_job['owner'], repo=test_job['repo'])
        
        if pr_result:
            print(f"✅ PR creation successful: #{pr_result.get('number', 'unknown')}")
            return True
        else:
            print("❌ PR creation failed")
            
            # Let's try to get more detailed error info
            print("\n🔍 Getting repository info...")
            repo_info = api.get_repo(test_job['owner'], test_job['repo'])
            if repo_info:
                print(f"Default branch: {repo_info.get('default_branch')}")
                print(f"Private: {repo_info.get('private')}")
            
            return False
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # Cleanup
        if os.path.exists(repo_path):
            shutil.rmtree(repo_path, ignore_errors=True)

if __name__ == "__main__":
    print("🐛 Starting PR creation debug...")
    result = asyncio.run(debug_pr_creation())
    if result:
        print("\n✅ Debug completed successfully!")
    else:
        print("\n❌ Debug found issues!")
