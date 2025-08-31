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
    
    def _check_assignment_trigger(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        检查是否通过分配 Issue 来触发 Agent
        """
        try:
            bot_username = os.getenv('GITCODE_BOT_USERNAME', 'yeren66')
            
            # 调试：记录完整的 payload 结构
            logger.info(f"检查分配触发 - 事件类型: {event_type}")
            logger.info(f"检查分配触发 - action: {payload.get('action', 'MISSING')}")
            logger.info(f"检查分配触发 - 可用字段: {list(payload.keys())}")
            
            # 检查是否为 Issue 分配事件
            if event_type in ['issues', 'Issue Hook']:
                action = payload.get('action', '')
                
                # GitCode 可能使用不同的 action 值，添加更多可能性
                possible_assign_actions = ['assigned', 'assign', 'assignee_changed', 'update', 'edited']
                
                logger.info(f"检查分配触发 - 当前 action: '{action}'")
                
                # 如果 action 为空或者是更新类事件，检查是否有分配信息
                if action in possible_assign_actions or not action:
                    # 检查分配的用户是否是机器人
                    assignee = None
                    
                    # 方式1: 检查顶级 assignees 字段 (GitCode 真实 webhook)
                    if 'assignees' in payload and payload['assignees']:
                        assignees = payload['assignees']
                        logger.info(f"发现 assignees 字段: {assignees}")
                        if isinstance(assignees, list) and len(assignees) > 0:
                            first_assignee = assignees[0]
                            if isinstance(first_assignee, dict):
                                assignee = first_assignee.get('username', first_assignee.get('login', first_assignee.get('name', '')))
                            elif isinstance(first_assignee, str):
                                assignee = first_assignee
                            logger.info(f"从 payload.assignees 获取: {assignee}")
                    
                    # 方式2: 检查 object_attributes 中的分配信息 (GitCode 特定)
                    elif 'object_attributes' in payload:
                        obj_attrs = payload['object_attributes']
                        logger.info(f"检查 object_attributes: {list(obj_attrs.keys()) if isinstance(obj_attrs, dict) else obj_attrs}")
                        
                        # 检查 object_attributes.assignee
                        if 'assignee' in obj_attrs and obj_attrs['assignee']:
                            assignee_data = obj_attrs['assignee']
                            if isinstance(assignee_data, dict):
                                assignee = assignee_data.get('username', assignee_data.get('login', assignee_data.get('name', '')))
                            elif isinstance(assignee_data, str):
                                assignee = assignee_data
                            logger.info(f"从 object_attributes.assignee 获取: {assignee}")
                        
                        # 检查 object_attributes.assignees
                        elif 'assignees' in obj_attrs and obj_attrs['assignees']:
                            assignees = obj_attrs['assignees']
                            if isinstance(assignees, list) and len(assignees) > 0:
                                first_assignee = assignees[0]
                                if isinstance(first_assignee, dict):
                                    assignee = first_assignee.get('username', first_assignee.get('login', first_assignee.get('name', '')))
                                elif isinstance(first_assignee, str):
                                    assignee = first_assignee
                            logger.info(f"从 object_attributes.assignees 获取: {assignee}")
                    
                    # 方式3: 检查 issue 对象中的分配信息 (测试格式兼容)
                    elif 'issue' in payload:
                        issue = payload['issue']
                        if 'assignee' in issue and issue['assignee']:
                            assignee_data = issue['assignee']
                            if isinstance(assignee_data, dict):
                                assignee = assignee_data.get('username', assignee_data.get('login', assignee_data.get('name', '')))
                            elif isinstance(assignee_data, str):
                                assignee = assignee_data
                            logger.info(f"从 issue.assignee 获取: {assignee}")
                        elif 'assignees' in issue and issue['assignees']:
                            # 多个分配者的情况
                            assignees = issue['assignees']
                            if isinstance(assignees, list) and len(assignees) > 0:
                                first_assignee = assignees[0]
                                if isinstance(first_assignee, dict):
                                    assignee = first_assignee.get('username', first_assignee.get('login', first_assignee.get('name', '')))
                                elif isinstance(first_assignee, str):
                                    assignee = first_assignee
                            logger.info(f"从 issue.assignees 获取: {assignee}")
                    
                    # 方式4: 检查顶级 assignee 字段
                    elif 'assignee' in payload:
                        assignee_data = payload['assignee']
                        if isinstance(assignee_data, dict):
                            assignee = assignee_data.get('username', assignee_data.get('login', assignee_data.get('name', '')))
                        elif isinstance(assignee_data, str):
                            assignee = assignee_data
                        logger.info(f"从 payload.assignee 获取: {assignee}")
                    
                    logger.info(f"最终确定的分配用户: {assignee}, 机器人用户: {bot_username}")
                    
                    if assignee == bot_username:
                        logger.info(f"检测到 Issue 分配给机器人: {assignee}")
                        return True
                    elif assignee:
                        logger.debug(f"Issue 分配给其他用户: {assignee}")
                    else:
                        logger.debug("未找到分配信息")
                else:
                    logger.debug(f"不是分配类操作: {action}")
            
            return False
            
        except Exception as e:
            logger.error(f"检查分配触发时发生错误: {e}")
            return False
    
    def should_process_event(self, event_type: str, payload: Dict[str, Any]) -> bool:
        """
        判断是否应该处理这个事件
        支持三种触发方式：
        1. 评论触发 (@bug-fix-agent fix)
        2. Issue 分配触发 (assign issue to bot)
        3. Issue 创建时直接触发
        """
        try:
            logger.info(f"检查是否处理事件: {event_type}")
            
            # 支持的事件类型
            valid_events = ['issues', 'issue_comment', 'Issue Hook', 'Note Hook']
            
            if event_type not in valid_events:
                logger.info(f"不支持的事件类型: {event_type}")
                return False
            
            # 检查分配触发 - 新增功能
            logger.info("检查分配触发...")
            triggered_by_assignment = self._check_assignment_trigger(event_type, payload)
            logger.info(f"分配触发结果: {triggered_by_assignment}")
            if triggered_by_assignment:
                logger.info("通过 Issue 分配触发 Agent")
                return True
            
            # 原有的评论触发逻辑
            comment_body = self._get_comment_body(event_type, payload)
            if not comment_body:
                logger.debug("未找到评论内容")
                return False
            
            # 对于 issues 事件，检查创建或分配操作
            if event_type in ['issues', 'Issue Hook']:
                action = payload.get('action', '')
                # 如果已经通过分配触发检查，就不需要再检查 action
                # 否则只处理新建的 issue
                if not triggered_by_assignment and action not in ['open', 'opened', '']:
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
                bot_username = os.getenv('GITCODE_BOT_USERNAME', 'bug-fix-agent-bot')
                    
                if comment_author in [app_name, bot_username] or comment_author.endswith('[bot]'):
                    logger.info(f"跳过机器人用户的评论: {comment_author}")
                    return False
                
                # 过滤掉包含 Agent 状态报告的评论
                if ('Bug Fix Agent 已接单' in comment_body or 
                    '任务ID:' in comment_body or
                    '分支: `agent/' in comment_body or
                    '🤖 Agent 正在分析问题' in comment_body):
                    logger.info("跳过 Agent 状态评论以避免递归")
                    return False
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
        从 webhook payload 创建任务
        支持评论触发和分配触发
        """
        try:
            # 检测触发方式
            triggered_by_assignment = self._check_assignment_trigger(event_type, payload)
            
            # GitCode webhook payload 可能有不同的结构
            repository = payload.get('repository', {}) or payload.get('project', {})
            issue = payload.get('issue', {}) or payload.get('object_attributes', {})
            
            # 提取基本信息 - 支持不同的 GitCode webhook 格式
            owner = ''
            if 'project' in payload:
                # 真实的 GitCode webhook 格式
                project = payload['project']
                logger.info(f"调试 project 字段类型: {type(project)}, 值: {project}")
                
                if isinstance(project, dict):
                    namespace = project.get('namespace', {})
                    if isinstance(namespace, dict):
                        owner = namespace.get('name', '') or namespace.get('path', '')
                    elif isinstance(namespace, str):
                        owner = namespace
                    else:
                        logger.warning(f"Unexpected namespace type: {type(namespace)}")
                elif isinstance(project, str):
                    # 如果 project 是字符串，可能是项目名
                    parts = project.split('/')
                    if len(parts) >= 2:
                        owner = parts[0]
                else:
                    logger.warning(f"Unexpected project type: {type(project)}")
            elif 'repository' in payload:
                # 测试格式
                repository = payload['repository']
                if isinstance(repository, dict):
                    repo_owner = repository.get('owner', {})
                    if isinstance(repo_owner, dict):
                        owner = repo_owner.get('login', '') or repo_owner.get('username', '')
                    elif isinstance(repo_owner, str):
                        owner = repo_owner
            
            # 仓库名称
            repo_name = ''
            if 'project' in payload:
                project = payload['project']
                if isinstance(project, dict):
                    repo_name = project.get('name', '') or project.get('path', '')
                elif isinstance(project, str):
                    # 如果 project 是字符串，提取仓库名
                    parts = project.split('/')
                    if len(parts) >= 2:
                        repo_name = parts[1]
                    else:
                        repo_name = project
            elif 'repository' in payload:
                repository = payload['repository']
                if isinstance(repository, dict):
                    repo_name = repository.get('name', '') or repository.get('path', '')
            
            # Issue 编号 - GitCode特殊处理
            issue_number = 0
            display_issue_number = 0  # 用于显示的编号
            
            if 'object_attributes' in payload:
                obj_attrs = payload['object_attributes']
                if isinstance(obj_attrs, dict):
                    # GitCode的编号优先级：number > iid > id
                    issue_number = (obj_attrs.get('number', 0) or 
                                   obj_attrs.get('iid', 0) or 
                                   obj_attrs.get('id', 0))
                    display_issue_number = obj_attrs.get('id', 0) or issue_number  # 显示时使用全局ID
                    
                    logger.info(f"GitCode Issue解析: id={obj_attrs.get('id', 0)}, iid={obj_attrs.get('iid', 0)}, number={obj_attrs.get('number', 0)}")
                    logger.info(f"使用API编号: {issue_number}, 显示编号: {display_issue_number}")
                    
            elif 'issue' in payload:
                issue_obj = payload['issue']
                if isinstance(issue_obj, dict):
                    # 对于GitHub格式或测试格式
                    issue_number = issue_obj.get('number', 0) or issue_obj.get('iid', 0)
                    display_issue_number = issue_number  # 对于非GitCode平台，两者相同
            
            logger.info(f"解析结果: owner={owner}, repo={repo_name}, api_issue_number={issue_number}, display_issue_number={display_issue_number}")
            
            # 获取触发者
            actor = ''
            logger.debug(f"调试 payload 结构: user={payload.get('user')}, sender={payload.get('sender')}")
            
            if triggered_by_assignment:
                # 对于分配触发，使用执行分配操作的用户
                actor = (payload.get('user', {}).get('username', '') or
                        payload.get('user', {}).get('login', '') or
                        payload.get('sender', {}).get('username', '') or
                        payload.get('sender', {}).get('login', ''))
            elif event_type in ['issues', 'Issue Hook']:
                actor = (issue.get('user', {}).get('login', '') or 
                        issue.get('user', {}).get('username', '') or
                        issue.get('author', {}).get('username', ''))
            elif event_type in ['issue_comment', 'Note Hook']:
                actor = self._get_comment_author(payload)
            
            # 如果还没有找到 actor，使用备用方法
            if not actor:
                actor = (payload.get('user', {}).get('username', '') or
                        payload.get('user', {}).get('login', '') or
                        'unknown')
                
            logger.debug(f"最终确定的触发者: {actor}")
            
            # 验证必要字段
            if not all([owner, repo_name, issue_number, actor]):
                logger.error(f"缺少必要字段: owner={owner}, repo={repo_name}, issue_number={issue_number}, display_issue_number={display_issue_number}, actor={actor}")
                return None
            
            # 检查授权
            allowed_users = os.getenv('ALLOWED_USERS', '')
            allowed_repos = os.getenv('ALLOWED_REPOS', '')
            
            if not is_authorized_user(actor, allowed_users):
                logger.warning(f"未授权的用户: {actor}")
                return None
            
            if not is_authorized_repo(owner, repo_name, allowed_repos):
                logger.warning(f"未授权的仓库: {owner}/{repo_name}")
                return None
            
            # 创建任务
            timestamp = datetime.utcnow().strftime('%m%d-%H%M%S')
            branch_name = f'agent/fix-{issue_number}-{timestamp}'
            
            # 获取仓库默认分支（GitCode 通常是 master）
            default_branch = repository.get('default_branch', 'master')
            
            job = {
                'job_id': str(uuid.uuid4()),
                'created_at': datetime.utcnow().isoformat(),
                'event_type': event_type,
                'platform': self.platform,
                'owner': owner,
                'repo': repo_name,
                'issue_number': issue_number,  # 用于API调用的编号
                'display_issue_number': display_issue_number,  # 用于显示的编号
                'issue_title': issue.get('title', f'Issue #{display_issue_number}'),
                'actor': actor,
                'branch': branch_name,
                'default_branch': default_branch,
                'triggered_by_assignment': triggered_by_assignment,  # 新增字段
                'webhook_payload': payload  # 保存原始 payload 用于调试
            }
            
            logger.info(f"创建任务: {job['job_id']} for {owner}/{repo_name}#{display_issue_number} (API: #{issue_number})")
            return job
            
        except Exception as e:
            logger.error(f"创建任务时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    async def send_initial_response(self, job: Dict[str, Any]) -> bool:
        """
        发送初始响应到 Issue
        """
        try:
            # 简单的导入方式
            import sys
            import os
            
            # 添加gateway目录到路径
            gateway_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if gateway_dir not in sys.path:
                sys.path.insert(0, gateway_dir)
            
            from gitcode_api import GitCodeAPI
            
            api = GitCodeAPI()
            app_name = os.getenv('GITCODE_APP_NAME', 'bug-fix-agent')
            
            # 检测触发方式
            trigger_method = "评论触发"
            if job.get('triggered_by_assignment'):
                trigger_method = "Issue分配触发"
            elif job.get('event_type') in ['issues', 'Issue Hook']:
                trigger_method = "Issue创建触发"
            
            # 创建详细的接收确认消息
            response_message = f"""🤖 **GitCode Bug Fix Agent 已接收任务**

📋 **任务信息:**
- 🆔 任务ID: `{job['job_id']}`
- 🌿 工作分支: `{job['branch']}`  
- 🎯 触发方式: {trigger_method}
- 👤 触发者: @{job['actor']}
- 🏷️ Issue: #{job.get('display_issue_number', job['issue_number'])} - {job.get('issue_title', 'N/A')}

🚀 **处理流程预览:**
- [🔄] **第1阶段**: 代码分析与问题定位
- [⏳] **第2阶段**: 修复方案设计  
- [⏳] **第3阶段**: 代码修改实施
- [⏳] **第4阶段**: 验证测试
- [⏳] **第5阶段**: 创建Pull Request

⏰ **预计处理时间:** 2-5分钟

💡 **接下来会发生什么:**
1. 我将创建工作分支并开始深入分析您的问题
2. 每完成一个阶段，我都会在此Issue中更新进度
3. 最后会创建包含完整修复方案的PR，供您审查

---
*我是 @{app_name}，GitCode平台的AI代码修复助手。请稍等，我正在分析您的问题...*"""

            success = await api.comment_issue(
                job['owner'], 
                job['repo'], 
                job['issue_number'], 
                response_message
            )
            
            if success:
                logger.info(f"✅ 已为任务 {job['job_id']} 发送Issue接收确认")
            else:
                logger.error(f"❌ 为任务 {job['job_id']} 发送Issue接收确认失败")
            
            return success
            
        except Exception as e:
            logger.error(f"发送初始响应时发生错误: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    async def send_stage_update(self, job: Dict[str, Any], stage: str, stage_result: Dict[str, Any]) -> bool:
        """
        向Issue发送阶段性进度更新
        """
        try:
            import sys
            import os
            
            # 添加gateway目录到路径
            gateway_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            if gateway_dir not in sys.path:
                sys.path.insert(0, gateway_dir)
            
            from gitcode_api import GitCodeAPI
            
            api = GitCodeAPI()
            
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
            
            stage_info = stage_messages.get(stage, {
                'emoji': '🔄',
                'title': f'阶段: {stage.title()}完成',
                'description': '阶段处理完成'
            })
            
            # 从stage_result中提取详细信息
            details = []
            if stage == 'locate':
                candidate_files = job.get('candidate_files', [])
                if candidate_files:
                    details.append(f"**发现候选文件** ({len(candidate_files)}个):")
                    for file in candidate_files[:5]:  # 最多显示5个文件
                        details.append(f"  - `{file}`")
                    if len(candidate_files) > 5:
                        details.append(f"  - ... 还有{len(candidate_files)-5}个文件")
                        
            elif stage == 'propose':
                target_files = job.get('target_files', [])
                if target_files:
                    details.append(f"**目标修改文件** ({len(target_files)}个):")
                    for file in target_files:
                        details.append(f"  - `{file}` - 计划修改")
                        
            elif stage == 'fix':
                changes_applied = stage_result.get('changes_applied', [])
                if changes_applied:
                    details.append(f"**已修改文件** ({len(changes_applied)}个):")
                    for file in changes_applied:
                        details.append(f"  - `{file}` ✅ 修改完成")
                        
            elif stage == 'verify':
                if stage_result.get('build_success'):
                    details.append("**验证结果**: ✅ 构建成功，功能正常")
                else:
                    details.append("**验证结果**: ⚠️ 需要进一步调整")
            
            # 构建完整的更新消息
            update_message = f"""{stage_info['emoji']} **{stage_info['title']}**

{stage_info['description']}

{chr(10).join(details) if details else ''}

📋 **当前进度:**
- [✅] 第1阶段: 问题定位 {'✅' if job.get('stages_completed', {}).get('locate') else '⏳'}
- [{'✅' if job.get('stages_completed', {}).get('propose') else '⏳'}] 第2阶段: 修复方案 {'✅' if job.get('stages_completed', {}).get('propose') else '⏳'}
- [{'✅' if job.get('stages_completed', {}).get('fix') else '⏳'}] 第3阶段: 代码修改 {'✅' if job.get('stages_completed', {}).get('fix') else '⏳'}
- [{'✅' if job.get('stages_completed', {}).get('verify') else '⏳'}] 第4阶段: 验证测试 {'✅' if job.get('stages_completed', {}).get('verify') else '⏳'}
- [⏳] 第5阶段: 创建PR

🔗 **工作分支:** `{job['branch']}`
🆔 **任务ID:** `{job['job_id']}`

---
*Agent正在继续处理，请稍等...*"""

            success = await api.comment_issue(
                job['owner'],
                job['repo'], 
                job['issue_number'],
                update_message
            )
            
            if success:
                logger.info(f"✅ 已为任务 {job['job_id']} 发送{stage}阶段更新")
            else:
                logger.error(f"❌ 为任务 {job['job_id']} 发送{stage}阶段更新失败")
                
            return success
            
        except Exception as e:
            logger.error(f"发送阶段更新时发生错误: {e}")
            return False
