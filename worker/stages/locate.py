"""
Locate Stage - Find problematic files using LLM analysis
"""

import os
import logging
from typing import Dict, Any, List

try:
    from ..templates import render_analysis
    from ..llm_client import get_llm_client
except ImportError:
    import sys
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from templates import render_analysis
    from llm_client import get_llm_client

logger = logging.getLogger(__name__)

async def run_locate_stage(job: Dict[str, Any], repo_path: str, api, gitops) -> Dict[str, Any]:
    """
    Run the locate stage - identify files that might contain the bug using LLM analysis
    
    This implementation uses LLM to intelligently analyze the issue and suggest candidate files.
    Falls back to simple heuristics if LLM is unavailable.
    """
    try:
        logger.info("Starting locate stage with LLM analysis")
        
        # Check for demo override first
        demo_files = os.getenv('DEMO_LOCATE_FILES')
        if demo_files:
            candidate_files = [f.strip() for f in demo_files.split(',')]
            logger.info(f"Using demo override files: {candidate_files}")
            
            # Generate simple analysis for demo files
            analysis_content = render_analysis(
                issue_title=job.get('issue_title', 'Unknown Issue'),
                issue_body=job.get('issue_body', ''),
                candidate_files=candidate_files
            )
        else:
            logger.info(f"🧠 Starting LLM-powered analysis for issue: {job.get('issue_title', 'Unknown Issue')}")
            
            # Get repository file list for LLM analysis
            file_list = get_repository_files(repo_path)
            logger.info(f"Found {len(file_list)} files in repository")
            
            # Use LLM to analyze the bug and suggest files
            llm_client = get_llm_client()
            
            try:
                logger.info("🤖 Calling LLM for bug analysis...")
                bug_analysis = await llm_client.analyze_bug(
                    issue_title=job.get('issue_title', 'Unknown Issue'),
                    issue_body=job.get('issue_body', ''),
                    file_list=file_list
                )
                
                candidate_files = bug_analysis.get('candidate_files', [])
                logger.info(f"🎯 LLM suggested {len(candidate_files)} candidate files: {candidate_files}")
                
                # Generate enhanced analysis report
                analysis_content = render_analysis_with_llm(
                    issue_title=job.get('issue_title', 'Unknown Issue'),
                    issue_body=job.get('issue_body', ''),
                    candidate_files=candidate_files,
                    llm_analysis=bug_analysis
                )
                
                logger.info(f"✅ LLM analysis completed successfully")
                
            except Exception as e:
                logger.warning(f"❌ LLM analysis failed, using heuristics: {e}")
                # Fall back to heuristics
                candidate_files = find_candidate_files(job, repo_path)
                
                analysis_content = render_analysis(
                    issue_title=job.get('issue_title', 'Unknown Issue'),
                    issue_body=job.get('issue_body', ''),
                    candidate_files=candidate_files
                )
        
        # Write analysis file
        await gitops.write_file(repo_path, 'agent/analysis.md', analysis_content)
        await gitops.add_file(repo_path, 'agent/analysis.md')
        await gitops.commit(repo_path, 'chore(agent): add problem analysis')
        await gitops.push(repo_path, job['branch'])
        
        # Store results in job
        job['candidate_files'] = candidate_files
        
        comment = f"""🔍 **定位阶段完成**

通过智能分析找到 {len(candidate_files)} 个候选文件：
{chr(10).join(f'- `{f}`' for f in candidate_files)}

详细分析见: `agent/analysis.md`

*🤖 本次使用了 AI 辅助分析定位问题文件*"""
        
        return {
            'success': True,
            'candidate_files': candidate_files,
            'comment': comment
        }
        
    except Exception as e:
        logger.error(f"Locate stage failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }

def find_candidate_files(job: Dict[str, Any], repo_path: str) -> List[str]:
    """Find candidate files using simple heuristics"""
    
    candidates = []
    
    # Look for common source directories
    common_paths = ['src/', 'lib/', 'app/', '']
    common_extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.go', '.rs', '.php']
    
    for base_path in common_paths:
        full_path = os.path.join(repo_path, base_path)
        if os.path.exists(full_path):
            # Find source files
            for root, dirs, files in os.walk(full_path):
                # Skip hidden directories and common ignore patterns
                dirs[:] = [d for d in dirs if not d.startswith('.') and d not in ['node_modules', '__pycache__', 'target', 'build']]
                
                for file in files[:5]:  # Limit to first 5 files per directory
                    if any(file.endswith(ext) for ext in common_extensions):
                        rel_path = os.path.relpath(os.path.join(root, file), repo_path)
                        candidates.append(rel_path)
                        
                        if len(candidates) >= 3:  # Max 3 candidates for demo
                            break
                
                if len(candidates) >= 3:
                    break
            
            if len(candidates) >= 3:
                break
    
    # Fallback: look for README and common config files
    if not candidates:
        fallback_files = ['README.md', 'README.rst', 'README.txt', 'package.json', 'setup.py', 'Makefile']
        for file in fallback_files:
            file_path = os.path.join(repo_path, file)
            if os.path.exists(file_path):
                candidates.append(file)
                if len(candidates) >= 2:
                    break
    
    # Final fallback
    if not candidates:
        candidates = ['README.md', 'src/main.py', 'app.py']
    
    return candidates

def get_repository_files(repo_path: str) -> List[str]:
    """Get list of all relevant files in the repository for LLM analysis"""
    
    files = []
    ignore_dirs = {'.git', '__pycache__', 'node_modules', '.pytest_cache', 'build', 'dist', 'target'}
    ignore_exts = {'.pyc', '.pyo', '.log', '.tmp', '.cache', '.DS_Store'}
    
    try:
        for root, dirs, filenames in os.walk(repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.startswith('.')]
            
            for filename in filenames:
                # Skip ignored files
                if any(filename.endswith(ext) for ext in ignore_exts):
                    continue
                if filename.startswith('.'):
                    continue
                    
                rel_path = os.path.relpath(os.path.join(root, filename), repo_path)
                files.append(rel_path)
                
                # Limit total files to avoid token limits
                if len(files) >= 200:
                    break
            
            if len(files) >= 200:
                break
                
    except Exception as e:
        logger.warning(f"Error scanning repository: {e}")
    
    return files

def render_analysis_with_llm(issue_title: str, issue_body: str, candidate_files: List[str], 
                           llm_analysis: Dict[str, Any]) -> str:
    """Render analysis.md with LLM insights"""
    
    analysis_summary = llm_analysis.get('analysis', 'LLM analysis completed')
    technical_areas = llm_analysis.get('technical_areas', [])
    reasoning = llm_analysis.get('reasoning', 'Files selected based on LLM analysis')
    
    content = f"""# Bug Analysis Report

## Issue Information
- **Title:** {issue_title}
- **Description:** {issue_body}

## AI Analysis Summary
{analysis_summary}

## Technical Areas Identified
{chr(10).join(f'- {area}' for area in technical_areas)}

## Candidate Files
{chr(10).join(f'- `{file}`' for file in candidate_files)}

## Selection Reasoning
{reasoning}

## Analysis Method
🤖 **AI-Powered Analysis** - This analysis was generated using advanced language models to understand the issue context and suggest relevant files.

---
*Generated by Bug Fix Agent - AI Analysis*
"""
    
    return content
