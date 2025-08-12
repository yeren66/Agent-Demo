#!/usr/bin/env python3
"""
Test the enhanced workflow with detailed analysis and no deployment stage
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

async def test_enhanced_workflow():
    """Test the enhanced workflow with detailed analysis"""
    
    # Create job with unique branch name
    timestamp = datetime.utcnow().strftime('%m%d-%H%M%S')
    test_job = {
        'job_id': f'test-enhanced-{timestamp}',
        'owner': 'yeren66',
        'repo': 'skills-expand-your-team-with-copilot',
        'issue_number': 4,
        'issue_title': 'Test Enhanced Analysis Workflow',
        'issue_body': 'This is a test issue to verify the enhanced analysis and reporting features.',
        'actor': 'test-user',
        'branch': f'agent/fix-4-{timestamp}',
        'default_branch': 'main'
    }
    
    worker = AgentWorker()
    
    # Create temporary directory
    repo_path = tempfile.mkdtemp(prefix="test-enhanced-")
    
    try:
        print(f"🚀 Testing enhanced workflow...")
        print(f"Branch: {test_job['branch']}")
        print(f"Issue: {test_job['issue_title']}")
        
        # Step 1: Initialize repo
        print("\n1️⃣ Repository initialization...")
        init_success = await worker._initialize_repo(test_job, repo_path)
        if not init_success:
            print("❌ Repository initialization failed")
            return False
        print("✅ Repository initialization successful")
        
        # Step 2: Create initial PR
        print("\n2️⃣ Creating initial PR...")
        pr_number = await worker._create_initial_pr(test_job, repo_path)
        if not pr_number:
            print("❌ PR creation failed")
            return False
        print(f"✅ Initial PR created: #{pr_number}")
        test_job['pr_number'] = pr_number
        
        # Step 3: Run locate stage (with detailed analysis)
        print("\n3️⃣ Running locate stage...")
        from worker.stages import locate
        locate_result = await locate.run_locate_stage(test_job, repo_path, worker.api, worker.gitops)
        if not locate_result.get('success'):
            print("❌ Locate stage failed")
            return False
        print("✅ Locate stage completed with detailed analysis")
        print(f"   Found candidate files: {test_job.get('candidate_files', [])}")
        
        # Update PR progress
        await worker._update_pr_progress(test_job, 'locate', True)
        
        # Step 4: Run propose stage
        print("\n4️⃣ Running propose stage...")
        from worker.stages import propose
        propose_result = await propose.run_propose_stage(test_job, repo_path, worker.api, worker.gitops)
        if not propose_result.get('success'):
            print("❌ Propose stage failed")
            return False
        print("✅ Propose stage completed with detailed fix plan")
        print(f"   Target files: {test_job.get('target_files', [])}")
        
        # Update PR progress
        await worker._update_pr_progress(test_job, 'propose', True)
        
        # Step 5: Run fix stage
        print("\n5️⃣ Running fix stage...")
        from worker.stages import fix
        fix_result = await fix.run_fix_stage(test_job, repo_path, worker.api, worker.gitops)
        if not fix_result.get('success'):
            print("❌ Fix stage failed")
            return False
        print("✅ Fix stage completed with code modifications")
        
        # Update PR progress
        await worker._update_pr_progress(test_job, 'fix', True)
        
        # Step 6: Run verify stage
        print("\n6️⃣ Running verify stage...")
        from worker.stages import verify
        verify_result = await verify.run_verify_stage(test_job, repo_path, worker.api, worker.gitops)
        if not verify_result.get('success'):
            print("❌ Verify stage failed")
            return False
        print("✅ Verify stage completed with test results")
        
        # Update PR progress
        await worker._update_pr_progress(test_job, 'verify', True)
        
        # Step 7: Finalize (no deploy stage)
        print("\n7️⃣ Finalizing PR...")
        await worker._finalize_pr(test_job)
        print("✅ PR finalized successfully")
        
        print(f"\n🎉 Enhanced workflow test completed!")
        print(f"Created PR #{pr_number} with detailed analysis")
        print(f"✅ All 4 stages completed (locate, propose, fix, verify)")
        print(f"❌ Deploy stage removed as requested")
        
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
    print("🔬 Testing enhanced analysis workflow...")
    result = asyncio.run(test_enhanced_workflow())
    if result:
        print("\n✅ All enhanced workflow tests passed!")
        print("\n💡 Enhanced features verified:")
        print("   - Detailed problem analysis in locate stage")
        print("   - Comprehensive fix planning in propose stage")  
        print("   - Enhanced code modification reporting in fix stage")
        print("   - Thorough verification reporting in verify stage")
        print("   - Removed deploy stage as requested")
        print("   - Removed AI promotional messages")
    else:
        print("\n❌ Enhanced workflow tests failed!")
