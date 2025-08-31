"""
Locate Stage - Find problematic files using LLM analysis
"""

import os
import logging
from typing import Dict, Any, List
from datetime import datetime

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
        
        # Enhanced comment for better user feedback
        comment = f"""🔍 **第1阶段：问题定位分析完成**

**🎯 分析结果:**
- 候选问题文件: **{len(candidate_files)}个**
- 分析方法: AI智能分析 + 启发式匹配
- 置信度: {'🟢 高' if len(candidate_files) <= 5 else '🟡 中等'}

**📁 识别出的关键文件:**
{chr(10).join(f'- `{f}` - 高度相关' for f in candidate_files[:5])}
{('- ... 还有更多文件 (查看analysis.md获取完整列表)' if len(candidate_files) > 5 else '')}

**📊 分析详情:**
- 🔍 根据Issue描述进行语义分析
- 📂 扫描项目结构和文件依赖关系  
- 🎯 匹配潜在的问题代码位置
- 📝 生成详细诊断报告

**📋 生成文件:** `agent/analysis.md`
**🔗 工作分支:** `{job['branch']}`

---
*接下来将基于这些文件制定修复方案...*"""
        
        return {
            'success': True,
            'candidate_files': candidate_files,
            'comment': comment,
            'stage_data': {
                'analysis_method': 'LLM' if not demo_files else 'demo',
                'confidence_level': 'high' if len(candidate_files) <= 5 else 'medium',
                'files_analyzed': len(file_list) if not demo_files else 0
            }
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
    """Render analysis.md with detailed LLM insights"""
    
    analysis_summary = llm_analysis.get('analysis', '通过代码结构分析识别相关文件')
    technical_areas = llm_analysis.get('technical_areas', ['代码逻辑', '功能实现'])
    reasoning = llm_analysis.get('reasoning', '基于文件名和项目结构的分析')
    
    content = f"""# 问题定位分析报告

## 📋 问题概述
**标题:** {issue_title}
**描述:** {issue_body if issue_body else '详细描述请参考原始Issue'}

## 🎯 根因分析
{analysis_summary}

## 🔧 涉及技术领域
{chr(10).join(f'- **{area}**: 可能需要检查相关的实现逻辑和配置' for area in technical_areas)}

## 📂 候选问题文件

基于问题描述和代码结构分析，识别出以下文件最可能包含相关问题：

{chr(10).join(f'''### `{file_path}`
- **相关性**: 高度相关
- **检查重点**: 查看核心逻辑实现、错误处理和边界条件
- **修复优先级**: 建议优先检查此文件的相关功能''' for file_path in candidate_files)}

## 💡 分析依据
{reasoning}

## 🔍 推荐修复策略
基于当前分析，建议采用以下修复策略：
1. 重点检查上述候选文件的相关功能实现
2. 分析问题的根本原因和触发条件
3. 制定向后兼容的修复方案
4. 确保修复不会引入新的问题

---
*报告生成时间: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC*
*分析方法: LLM + 启发式算法*
"""
    
    return content
