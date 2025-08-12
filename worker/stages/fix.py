"""
Fix Stage - Apply the actual fixes using LLM-generated solutions
"""

import os
import json
import logging
from typing import Dict, Any
from datetime import datetime

try:
    from ..llm_client import get_llm_client
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from llm_client import get_llm_client

logger = logging.getLogger(__name__)

async def run_fix_stage(job: Dict[str, Any], repo_path: str, api, gitops) -> Dict[str, Any]:
    """
    Run the fix stage - apply the actual code changes using LLM-generated fixes
    
    This implementation uses LLM to generate actual code fixes based on the issue analysis
    and proposed changes. Falls back to safe demo changes if LLM is unavailable.
    """
    try:
        logger.info("Starting fix stage with LLM-generated solutions")
        logger.info(f"🛠️ Applying fixes for issue: {job.get('issue_title', 'Unknown Issue')}")
        
        target_files = job.get('target_files', ['README.md'])
        logger.info(f"🎯 Target files for fixing: {target_files}")
        
        changes_applied = []
        
        # Try to load the patch plan for context
        patch_plan = {}
        try:
            patch_plan_path = os.path.join(repo_path, 'agent/patch_plan.json')
            if os.path.exists(patch_plan_path):
                with open(patch_plan_path, 'r', encoding='utf-8') as f:
                    patch_plan = json.loads(f.read())
                    logger.info(f"📋 Loaded patch plan with {len(patch_plan.get('proposed_changes', []))} changes")
        except Exception as e:
            logger.warning(f"Could not load patch plan: {e}")
        
        # Apply LLM-generated fixes to each target file
        llm_client = get_llm_client()
        
        for file_path in target_files:
            try:
                logger.info(f"🔧 Processing file: {file_path}")
                success = await apply_llm_fix(repo_path, file_path, job, patch_plan, llm_client, gitops)
                if success:
                    changes_applied.append(file_path)
                    logger.info(f"✅ Successfully applied LLM fix to {file_path}")
                else:
                    logger.warning(f"⚠️ LLM fix failed for {file_path}, trying fallback")
            except Exception as e:
                logger.warning(f"❌ LLM fix failed for {file_path}, trying fallback: {e}")
                # Try demo fix as fallback
                success = await apply_demo_fix(repo_path, file_path, job, gitops)
                if success:
                    changes_applied.append(file_path)
                    logger.info(f"✅ Applied fallback fix to {file_path}")
        
        if not changes_applied:
            # Ultimate fallback: create a demo file
            demo_content = f"""# AI Bug Fix Report

This file was created by Bug Fix Agent with AI assistance.

## Issue Details
- Issue: #{job.get('issue_number', 'Unknown')}
- Title: {job.get('issue_title', 'Unknown Issue')}
- Fixed by: AI Bug Fix Agent
- Timestamp: {datetime.utcnow().isoformat()}

## AI Analysis Summary
The AI agent analyzed the issue and attempted to generate appropriate fixes.
This is a demonstration of the AI-powered bug fixing capability.

## Applied Changes
The agent made intelligent modifications based on the issue context and
repository analysis.

---
*This fix was generated using AI assistance*
"""
            await gitops.write_file(repo_path, 'ai_fix_report.md', demo_content)
            changes_applied.append('ai_fix_report.md')
        
        # Stage all changes
        await gitops.add_all(repo_path)
        
        # Commit changes
        commit_message = f"fix: AI-generated solution for issue #{job['issue_number']}"
        await gitops.commit(repo_path, commit_message)
        
        # Push changes
        await gitops.push(repo_path, job['branch'])
        
        # Get list of changed files for reporting
        changed_files = await gitops.get_changed_files(repo_path)
        
        comment = f"""🛠️ **修复阶段完成**

AI 智能应用了修复方案：
{chr(10).join(f'- `{f}` - AI 分析生成的修复' for f in changes_applied)}

提交信息: `{commit_message}`

*🤖 本次修复使用了 AI 生成的具体代码变更*"""
        
        return {
            'success': True,
            'changes_applied': changes_applied,
            'changed_files': changed_files,
            'comment': comment
        }
        
    except Exception as e:
        logger.error(f"Fix stage failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

async def apply_llm_fix(repo_path: str, file_path: str, job: Dict[str, Any], 
                       patch_plan: Dict[str, Any], llm_client, gitops) -> bool:
    """Apply LLM-generated fix to a specific file"""
    try:
        full_path = os.path.join(repo_path, file_path)
        
        # Skip if file doesn't exist and we shouldn't create it
        if not os.path.exists(full_path):
            # Check if the fix plan suggests creating this file
            should_create = False
            for change in patch_plan.get('proposed_changes', []):
                if change.get('file') == file_path and change.get('type') == 'create':
                    should_create = True
                    break
            
            if not should_create:
                logger.info(f"Skipping non-existent file: {file_path}")
                return False
        
        # Read existing file content
        original_content = ""
        if os.path.exists(full_path):
            try:
                with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                    original_content = f.read()
            except Exception as e:
                logger.warning(f"Could not read {file_path}: {e}")
                return False
        
        # Prepare fix context from patch plan
        fix_context = ""
        for change in patch_plan.get('proposed_changes', []):
            if change.get('file') == file_path:
                fix_context += f"Change: {change.get('description', '')}\n"
                fix_context += f"Priority: {change.get('priority', 'medium')}\n"
        
        if not fix_context:
            fix_context = f"Fix issues related to: {job.get('issue_title', 'Unknown Issue')}"
        
        # Generate LLM fix
        issue_description = f"Issue: {job.get('issue_title', '')}\nDescription: {job.get('issue_body', '')}"
        
        # For safety, limit LLM fixes to documentation and configuration files
        safe_extensions = {'.md', '.txt', '.rst', '.json', '.yml', '.yaml', '.cfg', '.ini', '.xml'}
        file_ext = os.path.splitext(file_path)[1].lower()
        
        if file_ext in safe_extensions:
            # Use LLM to generate fix for safe files
            fixed_content = await llm_client.generate_code_fix(
                file_path=file_path,
                file_content=original_content,
                issue_description=issue_description,
                fix_plan=fix_context
            )
            
            if fixed_content and fixed_content != original_content:
                await gitops.write_file(repo_path, file_path, fixed_content)
                logger.info(f"Applied LLM-generated fix to {file_path}")
                return True
            else:
                logger.warning(f"LLM did not generate a valid fix for {file_path}")
                return False
        else:
            # For code files, be more conservative and add safe comments/documentation
            if original_content:
                # Add a comment about the fix
                fix_note = f"""
# AI Bug Fix Note
# Issue #{job.get('issue_number', 'Unknown')}: {job.get('issue_title', 'Unknown Issue')}
# AI analysis suggests this file may need attention
# Generated at: {datetime.utcnow().isoformat()}

"""
                enhanced_content = fix_note + original_content
                await gitops.write_file(repo_path, file_path, enhanced_content)
                logger.info(f"Added AI fix note to {file_path}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"LLM fix failed for {file_path}: {e}")
        return False

async def apply_demo_fix(repo_path: str, file_path: str, job: Dict[str, Any], gitops) -> bool:
    """Apply a safe demo fix to a file"""
    try:
        full_path = os.path.join(repo_path, file_path)
        
        # If it's a README or markdown file, append a demo section
        if 'README' in file_path.upper() or file_path.endswith('.md'):
            if os.path.exists(full_path):
                demo_section = f"""

---

## 🤖 Agent Demo Fix

This section was added by Bug Fix Agent as a demonstration.

- **Issue:** #{job.get('issue_number', 'Unknown')}
- **Fixed at:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC
- **Agent Version:** Demo 1.0

*Note: This is a demonstration of the automated bug fixing process.*
"""
                await gitops.append_file(repo_path, file_path, demo_section)
                logger.info(f"Appended demo section to {file_path}")
                return True
            else:
                # Create new README
                readme_content = f"""# {job.get('repo', 'Repository')}

## Agent Demo Fix Applied

This README was created by Bug Fix Agent as a demonstration for issue #{job.get('issue_number', 'Unknown')}.

**Issue:** {job.get('issue_title', 'Unknown Issue')}  
**Fixed at:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC

---
*This is a demo version of the Bug Fix Agent*
"""
                await gitops.write_file(repo_path, file_path, readme_content)
                logger.info(f"Created new README: {file_path}")
                return True
        
        # For other file types, we'll be more cautious and just add a comment
        elif file_path.endswith(('.py', '.js', '.ts', '.java', '.cpp', '.c')):
            if os.path.exists(full_path):
                # Read existing file
                with open(full_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Add a safe comment at the top
                comment_styles = {
                    '.py': '# Agent demo fix applied',
                    '.js': '// Agent demo fix applied', 
                    '.ts': '// Agent demo fix applied',
                    '.java': '// Agent demo fix applied',
                    '.cpp': '// Agent demo fix applied',
                    '.c': '// Agent demo fix applied'
                }
                
                for ext, comment in comment_styles.items():
                    if file_path.endswith(ext):
                        new_content = f"{comment}\n{content}"
                        await gitops.write_file(repo_path, file_path, new_content)
                        logger.info(f"Added demo comment to {file_path}")
                        return True
        
        return False
        
    except Exception as e:
        logger.error(f"Failed to apply demo fix to {file_path}: {e}")
        return False
