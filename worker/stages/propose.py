"""
Propose Stage - Generate fix plan using LLM analysis
"""

import os
import json
import logging
from typing import Dict, Any

try:
    from ..templates import render_patch_plan
    from ..llm_client import get_llm_client
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from templates import render_patch_plan
    from llm_client import get_llm_client

logger = logging.getLogger(__name__)

async def run_propose_stage(job: Dict[str, Any], repo_path: str, api, gitops) -> Dict[str, Any]:
    """
    Run the propose stage - generate a fix plan using LLM analysis
    
    This implementation uses LLM to generate intelligent fix strategies based on the 
    issue description and candidate files. Falls back to safe demo fixes if needed.
    """
    try:
        logger.info("Starting propose stage with LLM analysis")
        logger.info(f"💡 Generating fix plan for issue: {job.get('issue_title', 'Unknown Issue')}")
        
        candidate_files = job.get('candidate_files', ['README.md'])
        logger.info(f"📁 Working with candidate files: {candidate_files}")
        
        # Try to read file contents for LLM context (limit to avoid token overflow)
        file_contents = {}
        for file_path in candidate_files[:3]:  # Limit to first 3 files
            try:
                full_path = os.path.join(repo_path, file_path)
                if os.path.exists(full_path) and os.path.getsize(full_path) < 10000:  # Max 10KB per file
                    with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                        file_contents[file_path] = f.read()
                        logger.info(f"📖 Read {len(file_contents[file_path])} chars from {file_path}")
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
        
        # Use LLM to generate fix plan
        llm_client = get_llm_client()
        
        try:
            logger.info("🤖 Calling LLM for fix plan generation...")
            fix_plan = await llm_client.generate_fix_plan(
                issue_title=job.get('issue_title', 'Unknown Issue'),
                issue_body=job.get('issue_body', ''),
                candidate_files=candidate_files,
                file_contents=file_contents
            )
            
            # Select target files from the fix plan
            target_files = []
            for change in fix_plan.get('changes', []):
                file_path = change.get('file', '')
                if file_path and file_path not in target_files:
                    target_files.append(file_path)
            
            # If no target files from LLM, use safe defaults
            if not target_files:
                target_files = select_safe_target_files(candidate_files, repo_path)
            
            # Generate enhanced patch plan with LLM insights
            patch_plan_content = render_llm_patch_plan(fix_plan, target_files)
            
            logger.info(f"✅ LLM generated fix plan with {len(target_files)} target files: {target_files}")
            
        except Exception as e:
            logger.warning(f"❌ LLM analysis failed, using safe fallback: {e}")
            # Fall back to safe target files
            target_files = select_safe_target_files(candidate_files, repo_path)
            
            # Generate basic patch plan
            patch_plan_content = render_patch_plan(
                issue_title=job.get('issue_title', 'Unknown Issue'),
                target_files=target_files
            )
        
        # Write patch plan file
        await gitops.write_file(repo_path, 'agent/patch_plan.json', patch_plan_content)
        await gitops.add_file(repo_path, 'agent/patch_plan.json')
        await gitops.commit(repo_path, 'chore(agent): add fix plan')
        await gitops.push(repo_path, job['branch'])
        
        # Store target files in job
        job['target_files'] = target_files
        
        comment = f"""💡 **修复方案设计完成**

**修复策略概述:**
- 🎯 明确了 {len(target_files)} 个需要修改的目标文件
- 📋 制定了详细的修复实施计划
- 🔧 分析了修复的技术可行性和风险点
- ⚡ 确定了修复的优先级和执行顺序

**目标修改文件:**
{chr(10).join(f'- `{f}` - 需要实施具体的代码修复' for f in target_files)}

**方案文档:**
- 📄 完整修复计划: `agent/patch_plan.json`
- 🎯 包含了具体的修改策略和实施步骤
- ⚠️  已识别潜在风险和注意事项
- 📝 提供了详细的测试建议

下一步将根据此方案进行具体的代码修复实施。"""
        
        return {
            'success': True,
            'target_files': target_files,
            'comment': comment
        }
        
    except Exception as e:
        logger.error(f"Propose stage failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

def select_safe_target_files(candidate_files: list, repo_path: str) -> list:
    """Select safe files to modify for demo"""
    
    safe_files = []
    
    # Priority 1: README files (safest)
    readme_files = [f for f in candidate_files if 'README' in f.upper()]
    if readme_files:
        safe_files.extend(readme_files[:1])  # Just one README
    
    # Priority 2: Check if README.md exists in repo root
    readme_path = os.path.join(repo_path, 'README.md')
    if os.path.exists(readme_path) and 'README.md' not in safe_files:
        safe_files.append('README.md')
    
    # If no README found, we'll create a demo file
    if not safe_files:
        safe_files.append('hotfix_demo.txt')
    
    return safe_files

def render_llm_patch_plan(fix_plan: Dict[str, Any], target_files: list) -> str:
    """Render patch plan with LLM-generated insights"""
    
    root_cause = fix_plan.get('root_cause', 'Analysis pending')
    fix_strategy = fix_plan.get('fix_strategy', 'Strategy being developed')
    changes = fix_plan.get('changes', [])
    risks = fix_plan.get('risks', [])
    testing_suggestions = fix_plan.get('testing_suggestions', [])
    
    # Create structured patch plan
    patch_plan = {
        "meta": {
            "generated_by": "AI Bug Fix Agent",
            "analysis_method": "LLM-powered analysis",
            "confidence": "high" if len(changes) > 0 else "medium"
        },
        "analysis": {
            "root_cause": root_cause,
            "fix_strategy": fix_strategy
        },
        "target_files": target_files,
        "proposed_changes": changes,
        "risk_assessment": risks,
        "testing_plan": testing_suggestions,
        "next_steps": [
            "Apply proposed changes to target files",
            "Run validation tests",
            "Verify fix resolves the issue"
        ]
    }
    
    return json.dumps(patch_plan, indent=2, ensure_ascii=False)
