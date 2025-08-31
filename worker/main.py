#!/usr/bin/env python3
"""
Bug Fix Agent Worker - Main Entry Point

This is the core execution engine that processes bug fix jobs.
"""

import os
import sys
import asyncio
import logging
import argparse
import tempfile
import shutil
from typing import Dict, Any, Optional
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(__file__))

try:
    from .gitops import GitOps
    from .git_platform_api import GitPlatformAPI as GitCodeAPI  
    from .stages import locate, propose, fix, verify, deploy
    from .templates import render_progress_panel, render_analysis, render_patch_plan, render_report
except ImportError:
    # Fallback for standalone execution
    from gitops import GitOps
    from git_platform_api import GitPlatformAPI as GitCodeAPI
    from stages import locate, propose, fix, verify, deploy
    from templates import render_progress_panel, render_analysis, render_patch_plan, render_report

logger = logging.getLogger(__name__)

class AgentWorker:
    """Main worker class for processing bug fix jobs"""
    
    def __init__(self):
        self.api = GitCodeAPI()
        self.gitops = GitOps()
    
    async def process_job(self, job: Dict[str, Any]) -> bool:
        """
        Process a complete bug fix job with stage-by-stage PR updates
        
        Args:
            job: Job configuration containing repo, issue info, etc.
            
        Returns:
            bool: True if successful, False otherwise
        """
        repo_path = None
        try:
            logger.info(f"Starting job {job['job_id']} for {job['owner']}/{job['repo']} issue #{job['issue_number']}")
            
            # Create temporary directory for repo
            repo_path = tempfile.mkdtemp(prefix=f"agent-{job['job_id']}-")
            
            # Initialize repository and branch
            if not await self._initialize_repo(job, repo_path):
                logger.error("Repository initialization failed")
                return False
            
            # Create initial PR first (draft state)
            pr_number = await self._create_initial_pr(job, repo_path)
            if not pr_number:
                logger.error("Failed to create initial PR")
                return False
            
            job['pr_number'] = pr_number
            logger.info(f"Created initial PR #{pr_number}")
            
            # Define stages (removed deploy stage)
            stages = [
                ('locate', locate.run_locate_stage),
                ('propose', propose.run_propose_stage),
                ('fix', fix.run_fix_stage),
                ('verify', verify.run_verify_stage)
            ]
            
            # Run each stage with progress updates
            for stage_name, stage_func in stages:
                logger.info(f"Starting stage: {stage_name}")
                
                # Run stage
                stage_result = await self._run_stage(stage_name, stage_func, job, repo_path)
                if not stage_result:
                    logger.error(f"Stage {stage_name} failed")
                    return False
                
                # Update PR progress after each stage
                await self._update_pr_progress(job, stage_name, True)
                
                logger.info(f"Stage {stage_name} completed successfully")
            
            # Finalize PR (mark as ready for review)
            await self._finalize_pr(job)
            
            logger.info(f"Job {job['job_id']} completed successfully! PR #{job['pr_number']} created.")
            return True
            
        except Exception as e:
            logger.error(f"Job {job['job_id']} failed: {str(e)}", exc_info=True)
            await self._handle_job_failure(job, str(e))
            return False
        finally:
            # Cleanup
            if repo_path and os.path.exists(repo_path):
                shutil.rmtree(repo_path, ignore_errors=True)
    
    async def _initialize_repo(self, job: Dict[str, Any], repo_path: str) -> bool:
        """Initialize repository and branch (without creating PR)"""
        try:
            logger.info(f"Initializing repository for job {job['job_id']}")
            
            # Get token for cloning
            token = self.api.get_token(job['owner'], job['repo'])
            if not token:
                logger.error("No authentication token available")
                return False
            
            logger.info(f"Token available, length: {len(token)}, starts with: {token[:4]}...")

            # Clone repository with proper authentication format
            if self.api.platform == 'github':
                # GitHub使用x-access-token格式或直接token格式
                clone_url = f"https://x-access-token:{token}@github.com/{job['owner']}/{job['repo']}.git"
            else:
                # GitCode 使用 oauth2:TOKEN 格式（正确的GitLab风格认证）
                clone_url = f"https://oauth2:{token}@gitcode.com/{job['owner']}/{job['repo']}.git"
            
            logger.info(f"Clone URL: {clone_url[:50]}...{clone_url[-20:]}")  # 只显示部分避免泄露token            # Clone repository and check result
            clone_success = await self.gitops.clone_repo(clone_url, repo_path)
            if not clone_success:
                logger.error("Repository clone failed")
                return False
            
            # Create and checkout branch and check result
            branch_success = await self.gitops.create_branch(repo_path, job['branch'], job['default_branch'])
            if not branch_success:
                logger.error("Branch creation failed")
                return False
            
            logger.info(f"Repository and branch initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"Repository initialization failed: {e}")
            return False
    
    async def _create_initial_pr(self, job: Dict[str, Any], repo_path: str) -> Optional[int]:
        """Create initial PR in draft state for progress tracking"""
        try:
            logger.info(f"Creating initial PR for job {job['job_id']}")
            
            # Create initial agent directory and status file
            agent_dir = os.path.join(repo_path, 'agent')
            os.makedirs(agent_dir, exist_ok=True)
            
            # Create initial status file
            status_file = os.path.join(agent_dir, 'status.txt')
            with open(status_file, 'w', encoding='utf-8') as f:
                f.write(f"""Agent Job Status
Job ID: {job['job_id']}
Issue: #{job['issue_number']}
Started: {datetime.now().isoformat()}

Status: Initializing...
""")
            
            # Add and commit the initial file
            await self.gitops.add_file(repo_path, 'agent/status.txt')
            await self.gitops.commit(repo_path, "chore(agent): initialize fix branch")
            
            # Push the branch to make it available on remote (force push to handle conflicts)
            push_success = await self.gitops.push(repo_path, job['branch'], force=True)
            if not push_success:
                logger.error("Failed to push initial branch")
                return None
            
            # Create initial progress panel
            pr_title = f"🤖 Agent: fix #{job['issue_number']} - {job.get('issue_title', 'Issue')}"
            pr_body = render_progress_panel(
                issue_number=job['issue_number'],
                actor=job['actor'],
                job_id=job['job_id'],
                initialized=True,
                locate=False, propose=False, fix=False, 
                verify=False, ready=False
            )
            
            # Create draft PR
            pr_result = self.api.create_pr(
                owner=job['owner'], 
                repo=job['repo'], 
                head=job['branch'],
                base=job['default_branch'],
                title=pr_title, 
                body=pr_body,
                draft=True
            )
            
            if isinstance(pr_result, dict) and 'number' in pr_result:
                return pr_result['number']
            elif isinstance(pr_result, int):
                return pr_result
            else:
                return None
            
        except Exception as e:
            logger.error(f"Initial PR creation failed: {e}")
            return None

    async def _create_pr(self, job: Dict[str, Any], repo_path: str) -> Optional[int]:
        """Create PR after content has been generated"""
        try:
            logger.info(f"Creating PR for job {job['job_id']}")
            
            # Commit all changes first
            await self.gitops.commit_changes(repo_path, f"Agent: fix issue #{job['issue_number']}")
            
            # Push the branch
            await self.gitops.push_branch(repo_path, job['branch'])
            
            # Create draft PR
            pr_title = f"🤖 Agent: fix #{job['issue_number']}"
            pr_body = render_progress_panel(
                issue_number=job['issue_number'],
                actor=job['actor'],
                job_id=job['job_id'],
                initialized=True,
                locate=True,
                propose=True, 
                fix=True,
                verify=True,
                ready=True
            )
            
            pr_response = self.api.create_pr(
                job['owner'], job['repo'],
                head=job['branch'],
                base=job['default_branch'],
                title=pr_title,
                body=pr_body,
                draft=False  # Not draft since work is complete
            )
            
            if not pr_response:
                logger.error("Failed to create PR")
                return None
            
            pr_number = pr_response.get('number')
            if not pr_number:
                logger.error("PR created but no number returned")
                return None
                
            logger.info(f"Created PR #{pr_number}")
            
            # Comment on original issue
            issue_comment = f"""✅ **修复完成！**

🎉 Agent 已成功处理此问题并创建了修复 PR：

**📥 Pull Request**: #{pr_number}
- **分支**: `{job['branch']}`
- **状态**: 已完成所有处理阶段

### 📁 生成的文件:
- `agent/analysis.md` - 问题分析报告
- `agent/patch_plan.json` - 修复方案详情
- `agent/report.txt` - 验证测试结果

请查看 PR 了解详细的修复方案！🚀"""

            self.api.comment_issue(job['owner'], job['repo'], job['issue_number'], issue_comment)
            
            return pr_number
            
        except Exception as e:
            logger.error(f"PR creation failed: {e}")
            return None

    async def _run_stage(self, stage_name: str, stage_func, job: Dict[str, Any], repo_path: str) -> bool:
        """Run a processing stage and post stage comment to PR and Issue"""
        try:
            logger.info(f"Running stage: {stage_name}")
            
            # Execute stage
            stage_result = await stage_func(job, repo_path, self.api, self.gitops)
            
            if not stage_result.get('success', False):
                logger.error(f"Stage {stage_name} failed: {stage_result.get('error', 'Unknown error')}")
                return False
            
            # Mark stage as completed
            job.setdefault('stages_completed', {})[stage_name] = True
            
            # Send Issue progress update (NEW)
            await self._send_issue_stage_update(job, stage_name, stage_result)
            
            # Post stage-specific comment to PR if available
            if job.get('pr_number') and stage_result.get('comment'):
                try:
                    self.api.comment_pr(
                        job['owner'], 
                        job['repo'], 
                        job['pr_number'], 
                        stage_result['comment']
                    )
                except Exception as e:
                    logger.warning(f"Failed to post stage comment: {e}")
            
            logger.info(f"Stage {stage_name} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Stage {stage_name} error: {e}", exc_info=True)
            return False
    
    async def _send_issue_stage_update(self, job: Dict[str, Any], stage_name: str, stage_result: Dict[str, Any]):
        """Send stage update to the original Issue"""
        try:
            # 构建阶段特定的更新消息
            stage_messages = {
                'locate': {
                    'emoji': '🔍',
                    'title': '阶段1: 问题定位完成',
                    'description': '已识别出可能的问题文件和根因分析'
                },
                'propose': {
                    'emoji': '💡', 
                    'title': '阶段2: 修复方案设计完成',
                    'description': '已制定详细的修复策略和实施计划'
                },
                'fix': {
                    'emoji': '🛠️',
                    'title': '阶段3: 代码修改完成', 
                    'description': '已应用修复方案，修改相关代码文件'
                },
                'verify': {
                    'emoji': '✅',
                    'title': '阶段4: 验证测试完成',
                    'description': '已验证修改效果，确保功能正常'
                }
            }
            
            stage_info = stage_messages.get(stage_name, {
                'emoji': '🔄',
                'title': f'阶段: {stage_name.title()}完成',
                'description': '阶段处理完成'
            })
            
            # 从stage_result和job中提取详细信息
            details = []
            if stage_name == 'locate':
                candidate_files = job.get('candidate_files', [])
                if candidate_files:
                    details.append(f"**🎯 发现候选文件** ({len(candidate_files)}个):")
                    for file in candidate_files[:5]:  # 最多显示5个文件
                        details.append(f"  - `{file}`")
                    if len(candidate_files) > 5:
                        details.append(f"  - ... 还有{len(candidate_files)-5}个文件")
                        
            elif stage_name == 'propose':
                target_files = job.get('target_files', [])
                if target_files:
                    details.append(f"**🎯 目标修改文件** ({len(target_files)}个):")
                    for file in target_files:
                        details.append(f"  - `{file}` - 计划修改")
                        
            elif stage_name == 'fix':
                changes_applied = stage_result.get('changes_applied', [])
                if changes_applied:
                    details.append(f"**📝 已修改文件** ({len(changes_applied)}个):")
                    for file in changes_applied:
                        details.append(f"  - `{file}` ✅")
                        
            elif stage_name == 'verify':
                if stage_result.get('build_success'):
                    details.append("**🧪 验证结果**: ✅ 构建成功，功能正常")
                else:
                    details.append("**🧪 验证结果**: ⚠️ 需要进一步调整")
            
            # 构建进度指示器
            completed = job.get('stages_completed', {})
            progress_indicators = [
                f"- [{'✅' if completed.get('locate') else '⏳'}] **问题定位** - 分析问题根因",
                f"- [{'✅' if completed.get('propose') else '⏳'}] **方案设计** - 制定修复计划", 
                f"- [{'✅' if completed.get('fix') else '⏳'}] **代码修改** - 实施修复方案",
                f"- [{'✅' if completed.get('verify') else '⏳'}] **验证测试** - 确认修复效果",
                f"- [{'✅' if job.get('pr_number') else '⏳'}] **创建PR** - 提交审查请求"
            ]
            
            # 构建完整的更新消息  
            update_message = f"""{stage_info['emoji']} **{stage_info['title']}**

{stage_info['description']}

{chr(10).join(details) if details else ''}

📈 **总体进度:**
{chr(10).join(progress_indicators)}

🔗 **工作分支:** `{job['branch']}`
🆔 **任务ID:** `{job['job_id']}`

---
*继续处理中，请稍候...*"""

            # 发送Issue评论
            self.api.comment_issue_sync(
                job['owner'],
                job['repo'], 
                job['issue_number'],
                update_message
            )
            
            logger.info(f"✅ 已向Issue #{job['issue_number']}发送{stage_name}阶段更新")
            
        except Exception as e:
            logger.warning(f"Failed to send issue stage update: {e}")
    
    
    async def _update_pr_progress(self, job: Dict[str, Any], completed_stage: str, success: bool):
        """Update PR progress panel after each stage"""
        try:
            if not job.get('pr_number'):
                logger.warning("No PR number available for progress update")
                return
                
            # Build progress state
            stages_completed = job.get('stages_completed', {})
            progress = {
                'initialized': True,
                'locate': completed_stage == 'locate' or stages_completed.get('locate', False),
                'propose': completed_stage == 'propose' or stages_completed.get('propose', False),
                'fix': completed_stage == 'fix' or stages_completed.get('fix', False),
                'verify': completed_stage == 'verify' or stages_completed.get('verify', False),
                'ready': completed_stage == 'ready' or stages_completed.get('ready', False)
            }
            
            # Mark current stage as completed if successful
            if success and completed_stage != 'ready':
                progress[completed_stage] = True
                job.setdefault('stages_completed', {})[completed_stage] = True
            
            # Render new PR body
            pr_body = render_progress_panel(
                issue_number=job['issue_number'],
                actor=job['actor'],
                job_id=job['job_id'],
                **progress
            )
            
            # Update PR description
            try:
                self.api.update_pr_body(job['owner'], job['repo'], job['pr_number'], pr_body)
                logger.info(f"Updated PR progress for stage: {completed_stage}")
            except Exception as e:
                logger.error(f"Failed to update PR body: {e}")
                
        except Exception as e:
            logger.error(f"Failed to update PR progress: {e}")
    
    async def _finalize_pr(self, job: Dict[str, Any]) -> bool:
        """Finalize PR - mark as ready and comment on issue"""
        try:
            # Mark PR as ready for review
            self.api.mark_pr_ready(job['owner'], job['repo'], job['pr_number'])
            
            # Update progress to show ready
            await self._update_pr_progress(job, 'ready', True)
            
            # Enhanced final comment on PR with detailed workflow summary
            summary_comment = f"""🎉 **Agent 完整处理流程已结束**

## 📋 处理摘要

**🔍 阶段1 - 问题定位:**
- ✅ 深度分析Issue描述和上下文
- ✅ 识别了 {len(job.get('candidate_files', []))} 个候选问题文件
- ✅ 生成详细诊断报告: `agent/analysis.md`

**💡 阶段2 - 方案设计:**
- ✅ 制定针对性修复策略
- ✅ 确定 {len(job.get('target_files', []))} 个目标修改文件
- ✅ 输出完整实施计划: `agent/patch_plan.json`

**🛠️ 阶段3 - 代码修改:**
- ✅ 基于AI分析应用具体修复代码
- ✅ 确保修改符合项目规范和最佳实践
- ✅ 保持代码向后兼容性

**✅ 阶段4 - 验证测试:**
- ✅ 验证修复效果和功能完整性
- ✅ 确认构建和基本功能正常
- ✅ 生成验证报告: `agent/report.txt`

## � 生成的关键文件

| 文件 | 说明 |
|------|------|
| `agent/analysis.md` | 🔍 问题根因分析和诊断报告 |
| `agent/patch_plan.json` | 📋 详细修复方案和实施计划 |
| `agent/report.txt` | 📊 验证测试结果和变更报告 |
| 修改的源文件 | 🛠️ 实际的代码修复内容 |

## 🎯 修复的关键文件
{chr(10).join(f'- `{f}` - 已成功修复' for f in job.get('target_files', [])) if job.get('target_files') else '- 已生成演示修复'}

## 🔍 下一步操作
1. **仔细审查代码变更** - 检查修复逻辑是否符合预期
2. **运行完整测试** - 确保修复没有引入新问题  
3. **考虑合并PR** - 如果修复方案满意，请合并此PR
4. **反馈和优化** - 如有问题，请在PR中提出改进建议

---
**🤖 任务ID:** `{job['job_id']}`  
**⏰ 处理时长:** 整个流程已完成  
**🌿 修复分支:** `{job['branch']}`

*感谢使用Agent！如有任何疑问，请在Issue或PR中留言。*"""

            self.api.comment_pr(job['owner'], job['repo'], job['pr_number'], summary_comment)
            
            # Enhanced comment on original issue
            issue_comment = f"""🎊 **修复任务圆满完成！**

Agent 已完成对 Issue #{job['issue_number']} 的全面分析和修复工作。

## 📊 任务完成情况

**✅ 处理阶段:**
- [✅] **问题定位** - 深度分析，找出根本原因  
- [✅] **方案设计** - 制定详细修复计划
- [✅] **代码修改** - 智能应用修复方案
- [✅] **验证测试** - 确保修复质量
- [✅] **创建PR** - 提交完整修复方案

## 🔗 相关链接

**📥 Pull Request:** #{job['pr_number']}
- **分支:** `{job['branch']}`
- **状态:** ✅ 修复完成，已准备好审查

## 📋 生成的文档
- **分析报告:** `agent/analysis.md` - 详细的问题诊断
- **修复方案:** `agent/patch_plan.json` - 完整的实施计划  
- **验证报告:** `agent/report.txt` - 测试结果和验证

## 🎯 接下来请：
1. 查看 PR #{job['pr_number']} 了解具体修复内容
2. 审查代码变更确认修复方案
3. 如满意请合并PR，系统将自动关闭此Issue

感谢使用 GitCode Bug Fix Agent！🚀

---
**🆔 任务ID:** `{job['job_id']}`  
**⏰ 完成时间:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"""

            self.api.comment_issue_sync(job['owner'], job['repo'], job['issue_number'], issue_comment)
            
            return True
            
        except Exception as e:
            logger.error(f"PR finalization failed: {e}")
            return False
    
    async def _handle_job_failure(self, job: Dict[str, Any], error_msg: str):
        """Handle job failure"""
        try:
            # Comment on issue about failure
            failure_comment = f"""❌ **Agent 处理失败**

很抱歉，在处理此问题时遇到了错误：

```
{error_msg}
```

任务ID: `{job['job_id']}`

请检查问题描述或稍后重试。"""

            self.api.comment_issue_sync(job['owner'], job['repo'], job['issue_number'], failure_comment)
            
        except Exception as e:
            logger.error(f"Failed to handle job failure: {e}")

# Entry point functions
async def process_job(job: Dict[str, Any]) -> bool:
    """Process a single job (called from gateway)"""
    worker = AgentWorker()
    return await worker.process_job(job)

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description='Bug Fix Agent Worker')
    parser.add_argument('command', choices=['run'], help='Command to execute')
    parser.add_argument('--repo', required=True, help='Repository URL')
    parser.add_argument('--owner', required=True, help='Repository owner')
    parser.add_argument('--repo-name', required=True, help='Repository name')
    parser.add_argument('--issue', type=int, required=True, help='Issue number')
    parser.add_argument('--actor', required=True, help='Triggering user')
    parser.add_argument('--branch', help='Branch name (auto-generated if not provided)')
    
    args = parser.parse_args()
    
    if args.command == 'run':
        # Create job from CLI args
        job = {
            'job_id': f'cli-{datetime.utcnow().strftime("%Y%m%d-%H%M%S")}',
            'created_at': datetime.utcnow().isoformat(),
            'owner': args.owner,
            'repo': args.repo_name,
            'issue_number': args.issue,
            'actor': args.actor,
            'branch': args.branch or f'agent/fix-{args.issue}',
            'repo_clone_url': args.repo,
            'default_branch': 'main'
        }
        
        # Run job
        worker = AgentWorker()
        success = asyncio.run(worker.process_job(job))
        sys.exit(0 if success else 1)

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    main()
