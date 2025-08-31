import re
import os
import logging
import uuid
from typing import Dict, Any, Optional
from datetime import datetime

from security import is_authorized_user, is_authorized_repo

logger = logging.getLogger(__name__)

class GitCodeEventHandler:
    """处理 GitCode webhook 事件"""
    
    def __init__(self):
        self.platform = 'gitcode'
        
        # GitCode 应用配置
        app_name = os.getenv('GITCODE_APP_NAME', 'bug-fix-agent')
        
        self.trigger_patterns = [
            # GitCode App @mention 模式
            rf'@{re.escape(app_name)}\s+fix',
            rf'@{re.escape(app_name)}\s+help',
            rf'@{re.escape(app_name)}\b',  # 简单的 @app-name 提及
            # 传统模式（向后兼容）
            r'@agent\s+fix',
            r'/agent\s+fix',
            r'@agent fix',
            r'/agent fix'
        ]
        
        logger.info(f"GitCode 事件处理器已初始化，应用名称: {app_name}")
    
    def should_process_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        判断是否应该处理这个事件
        """
        try:
            # 支持的事件类型
            valid_events = ['issues', 'issue_comment', 'Issue Hook', 'Note Hook']
            
            if event_type not in valid_events:
                logger.debug(f"不支持的事件类型: {event_type}")
                return False
            
            # 获取评论内容
            comment_body = self._get_comment_body(event_type, payload)
            if not comment_body:
                logger.debug("未找到评论内容")
                return False
            
            # 对于 issues 事件，只处理新建的 issue
            if event_type in ['issues', 'Issue Hook']:
                action = payload.get('action', '')
                if action not in ['open', 'opened']:
                    logger.debug(f"忽略 issue 操作: {action}")
                    return False
            
            # 对于 issue_comment 事件，只处理新建的评论
            elif event_type in ['issue_comment', 'Note Hook']:
                action = payload.get('action', '')
                if action not in ['create', 'created']:
                    logger.debug(f"忽略评论操作: {action}")
                    return False
                
                # 过滤掉 Agent 自己的评论，避免递归触发
                comment_author = self._get_comment_author(payload)
                app_name = os.getenv('GITCODE_APP_NAME', 'bug-fix-agent')
                    
                if comment_author == app_name or comment_author.endswith('[bot]'):
                    logger.info(f"跳过机器人用户的评论: {comment_author}")
                    return False
                
                # 过滤掉包含 Agent 状态报告的评论
                if ('Bug Fix Agent 已接单' in comment_body or 
                    '任务ID:' in comment_body or
                    '分支: `agent/' in comment_body or
                    '🤖 Agent 正在分析问题' in comment_body):
                    logger.info("跳过 Agent 状态评论以避免递归")
                    return False
            
            # 检查触发模式
            logger.debug(f"检查评论内容: {comment_body[:100]}...")
            for pattern in self.trigger_patterns:
                if re.search(pattern, comment_body, re.IGNORECASE):
                    logger.info(f"触发模式匹配: {pattern}")
                    return True
            
            logger.debug("没有匹配的触发模式")
            return False
            
        except Exception as e:
            logger.error(f"检查事件触发时发生错误: {e}")
            return False
    
    def _get_comment_body(self, event_type: str, payload: Dict[str, Any]) -> str:
        """从 payload 中提取评论内容"""
        try:
            if event_type in ['issues', 'Issue Hook']:
                # 新创建的 issue
                return payload.get('issue', {}).get('body', '') or payload.get('object_attributes', {}).get('description', '')
            elif event_type in ['issue_comment', 'Note Hook']:
                # Issue 评论
                return (payload.get('comment', {}).get('body', '') or 
                       payload.get('object_attributes', {}).get('note', ''))
            return ''
        except Exception as e:
            logger.error(f"提取评论内容时发生错误: {e}")
            return ''
    
    def _get_comment_author(self, payload: Dict[str, Any]) -> str:
        """获取评论作者"""
        try:
            # 尝试不同的字段
            author = (payload.get('comment', {}).get('user', {}).get('login', '') or
                     payload.get('comment', {}).get('user', {}).get('username', '') or
                     payload.get('user', {}).get('login', '') or
                     payload.get('user', {}).get('username', '') or
                     payload.get('object_attributes', {}).get('author', {}).get('username', ''))
            return author
        except Exception:
            return ''
    
    def create_job(self, event_type: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Create a job from the webhook payload
        """
        try:
            repository = payload.get('repository', {})
            issue = payload.get('issue', {})
            
            # Extract basic info
            owner = repository.get('owner', {}).get('login', '')
            repo_name = repository.get('name', '')
            issue_number = issue.get('number', 0)
            
            # Get actor (who triggered this)
            actor = ''
            if event_type == 'issues':
                actor = issue.get('user', {}).get('login', '')
            elif event_type == 'issue_comment':
                actor = payload.get('comment', {}).get('user', {}).get('login', '')
            
            # Validate required fields
            if not all([owner, repo_name, issue_number, actor]):
                logger.error(f"Missing required fields: owner={owner}, repo={repo_name}, issue_number={issue_number}, actor={actor}")
                return None
            
            # Check authorization
            allowed_users = os.getenv('ALLOWED_USERS', '')
            allowed_repos = os.getenv('ALLOWED_REPOS', '')
            
            if not is_authorized_user(actor, allowed_users):
                logger.warning(f"Unauthorized user: {actor}")
                return None
            
            if not is_authorized_repo(owner, repo_name, allowed_repos):
                logger.warning(f"Unauthorized repo: {owner}/{repo_name}")
                return None
            
            # Create job
            # Generate unique branch name with timestamp
            timestamp = datetime.utcnow().strftime('%m%d-%H%M%S')
            branch_name = f'agent/fix-{issue_number}-{timestamp}'
            
            job = {
                'job_id': str(uuid.uuid4()),
                'created_at': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'owner': owner,
                'repo': repo_name,
                'issue_number': issue_number,
                'issue_title': issue.get('title', ''),
                'issue_body': issue.get('body', ''),
                'actor': actor,
                'branch': branch_name,
                'default_branch': repository.get('default_branch', 'main'),
                'comment_id': payload.get('comment', {}).get('id') if event_type == 'issue_comment' else None,
                'platform': self.platform
            }
            
            # 设置克隆URL
            if self.platform == 'github':
                job['repo_clone_url'] = f"https://github.com/{owner}/{repo_name}.git"
            else:
                job['repo_clone_url'] = repository.get('clone_url', '')
            
            return job
            
        except Exception as e:
            logger.error(f"Error creating job: {e}")
            return None
    
    async def send_initial_response(self, job: Dict[str, Any]) -> bool:
        """
        Send immediate response to the issue
        """
        try:
            # Import appropriate API client based on platform
            import sys
            import os
            sys.path.append(os.path.dirname(os.path.dirname(__file__)))
            
            if self.platform == 'github':
                from github_api import GitHubAPI
                api = GitHubAPI()
                app_name = os.getenv('GITHUB_APP_NAME', 'agent')
            else:  # gitcode
                from gitcode_api import GitCodeAPI
                api = GitCodeAPI()
                app_name = os.getenv('GITCODE_APP_NAME', 'agent')
            
            response_message = f"""✅ **Bug Fix Agent 已接单**

📋 **任务信息:**
- 任务ID: `{job['job_id']}`
- 分支: `{job['branch']}`  
- 触发者: @{job['actor']}

🚀 Agent 正在分析问题，即将创建修复分支和 PR...

---
*我是 @{app_name}，一个自动化 Bug 修复助手*"""

            success = await api.comment_issue(
                job['owner'], 
                job['repo'], 
                job['issue_number'], 
                response_message
            )
            
            if success:
                logger.info(f"Initial response sent for job {job['job_id']}")
            else:
                logger.error(f"Failed to send initial response for job {job['job_id']}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending initial response: {e}")
            return False

# 为了兼容性，保持原有的类名
GitCodeEventHandler = GitPlatformEventHandler
