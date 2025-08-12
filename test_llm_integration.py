#!/usr/bin/env python3
"""
Test LLM Integration for Bug Fix Agent
"""

import os
import sys
import asyncio
import logging

# Add worker directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'worker'))

from worker.llm_client import LLMClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_llm_integration():
    """Test the LLM client integration"""
    
    print("🤖 Testing LLM Integration for Bug Fix Agent")
    print("=" * 50)
    
    # Initialize LLM client
    llm_client = LLMClient()
    
    # Test 1: Bug analysis
    print("\n🔍 Test 1: Bug Analysis")
    print("-" * 30)
    
    test_issue_title = "Login button not working"
    test_issue_body = "When users click the login button, nothing happens. No error messages are shown."
    test_files = [
        "src/components/LoginForm.js",
        "src/auth/authentication.py", 
        "src/api/login.py",
        "README.md",
        "package.json",
        "src/utils/validation.js"
    ]
    
    try:
        analysis_result = await llm_client.analyze_bug(
            issue_title=test_issue_title,
            issue_body=test_issue_body,
            file_list=test_files
        )
        
        print(f"✅ Analysis successful!")
        print(f"📋 Analysis: {analysis_result.get('analysis', 'N/A')}")
        print(f"🎯 Technical areas: {analysis_result.get('technical_areas', [])}")
        print(f"📁 Candidate files: {analysis_result.get('candidate_files', [])}")
        print(f"💡 Reasoning: {analysis_result.get('reasoning', 'N/A')}")
        
    except Exception as e:
        print(f"❌ Bug analysis failed: {e}")
        return False
    
    # Test 2: Fix plan generation
    print("\n💡 Test 2: Fix Plan Generation")
    print("-" * 35)
    
    try:
        candidate_files = analysis_result.get('candidate_files', ['src/components/LoginForm.js'])[:2]
        
        fix_plan = await llm_client.generate_fix_plan(
            issue_title=test_issue_title,
            issue_body=test_issue_body,
            candidate_files=candidate_files
        )
        
        print(f"✅ Fix plan generated!")
        print(f"🔍 Root cause: {fix_plan.get('root_cause', 'N/A')}")
        print(f"🛠️ Fix strategy: {fix_plan.get('fix_strategy', 'N/A')}")
        print(f"📝 Changes: {len(fix_plan.get('changes', []))} proposed changes")
        
        for i, change in enumerate(fix_plan.get('changes', [])[:3], 1):  # Show first 3
            print(f"   {i}. {change.get('file', 'unknown')}: {change.get('description', 'no description')}")
        
        print(f"⚠️ Risks: {len(fix_plan.get('risks', []))} identified")
        print(f"🧪 Testing suggestions: {len(fix_plan.get('testing_suggestions', []))} provided")
        
    except Exception as e:
        print(f"❌ Fix plan generation failed: {e}")
        return False
    
    # Test 3: Code fix generation (simple example)
    print("\n🛠️ Test 3: Code Fix Generation")
    print("-" * 34)
    
    try:
        test_file_content = """# User Authentication Guide

## Login Process
Users should be able to login using the form on the homepage.

## Known Issues
- Login button appears inactive
- No feedback on click
"""
        
        fixed_content = await llm_client.generate_code_fix(
            file_path="README.md",
            file_content=test_file_content,
            issue_description=f"{test_issue_title}: {test_issue_body}",
            fix_plan=fix_plan.get('fix_strategy', '')
        )
        
        if fixed_content:
            print(f"✅ Code fix generated!")
            print(f"📝 Original length: {len(test_file_content)} characters")
            print(f"📝 Fixed length: {len(fixed_content)} characters")
            print(f"🔄 Content changed: {'Yes' if fixed_content != test_file_content else 'No'}")
            
            # Show a preview of changes
            if fixed_content != test_file_content:
                print("\n🔍 Preview of changes:")
                print("--- Original ---")
                print(test_file_content[-100:])  # Last 100 chars
                print("\n--- Fixed ---")  
                print(fixed_content[-100:])  # Last 100 chars
        else:
            print(f"⚠️ No fix content generated")
            
    except Exception as e:
        print(f"❌ Code fix generation failed: {e}")
        return False
    
    await llm_client.close()
    
    print("\n🎉 All tests passed! LLM integration is working.")
    return True

async def main():
    """Main test function"""
    success = await test_llm_integration()
    
    if success:
        print("\n✅ LLM Integration Test: PASSED")
        print("\n🚀 Your Bug Fix Agent is now ready with AI capabilities!")
        print("\n📋 Next steps:")
        print("1. Start the agent: python start_local.py")
        print("2. Test with a real issue: @your-app-name fix this bug")
        print("3. Observe AI-generated analysis and fixes")
    else:
        print("\n❌ LLM Integration Test: FAILED")
        print("\n🔧 Please check:")
        print("1. API key is correct")
        print("2. Network connection is available")
        print("3. API endpoint is accessible")

if __name__ == "__main__":
    asyncio.run(main())
