import os
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GitCodeAuth:
    """GitCode 机器人 PAT 认证管理器
    
    使用机器人账号的 Personal Access Token (PAT) 进行认证
    这是 GitCode 平台推荐的机器人应用认证方式
    """
    
    def __init__(self):
        # 机器人 PAT 配置
        self.pat_token = os.getenv('GITCODE_PAT')
        self.bot_username = os.getenv('GITCODE_BOT_USERNAME', 'bug-fix-agent-bot')
        
        # API URLs
        self.api_base = 'https://api.gitcode.com/api/v5'
        
        self._validate_config()
    
    def _validate_config(self):
        """验证配置"""
        if self.pat_token:
            logger.info(f"GitCode PAT 配置已加载，机器人用户: {self.bot_username}")
            logger.info(f"PAT Token: {self.pat_token[:8]}...{self.pat_token[-4:] if len(self.pat_token) > 12 else '****'}")
        else:
            logger.error("未找到 GitCode PAT 配置 - 请设置 GITCODE_PAT 环境变量")
    
    def is_auth_available(self) -> bool:
        """检查认证是否可用"""
        return bool(self.pat_token)
    
    def get_setup_info(self) -> Dict[str, Any]:
        """获取 GitCode 机器人设置信息"""
        return {
            "认证方式": "机器人 Personal Access Token (PAT)",
            "所需账号": {
                "机器人账号": {
                    "用途": "执行自动化操作（评论、创建分支、PR等）",
                    "权限要求": [
                        "仓库读取权限",
                        "仓库写入权限（创建分支、推送代码）",
                        "Issue 读写权限",
                        "Pull Request 读写权限"
                    ],
                    "配置": f"用户名: {self.bot_username}，需要加入目标仓库"
                },
                "项目所属账号": {
                    "用途": "仓库所有者，设置 Webhook",
                    "配置": "在仓库设置中配置 Webhook 指向 Agent 服务"
                }
            },
            "PAT_配置": {
                "获取方式": "GitCode 用户设置 → 访问令牌 → 新建个人访问令牌",
                "权限范围": ["api", "read_user", "read_repository", "write_repository"],
                "环境变量": "GITCODE_PAT",
                "当前状态": "已配置" if self.is_auth_available() else "未配置"
            },
            "Webhook_配置": {
                "URL": "https://your-domain.com/api/webhook",
                "事件类型": ["Issues events", "Issue comments"],
                "Secret": "配置在 WEBHOOK_SECRET 环境变量中"
            }
        }
    
    def get_auth_headers(self) -> Dict[str, str]:
        """获取用于 API 请求的认证头部"""
        headers = {
            'User-Agent': f'GitCode-Bug-Fix-Agent/{self.bot_username}',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        if self.pat_token:
            headers['Authorization'] = f'Bearer {self.pat_token}'
        else:
            logger.warning("没有可用的 PAT Token 用于认证")
        
        return headers
    
    def test_authentication(self) -> bool:
        """测试 PAT 认证是否有效"""
        if not self.is_auth_available():
            logger.error("PAT Token 未配置")
            return False
        
        try:
            headers = self.get_auth_headers()
            
            response = requests.get(
                f'{self.api_base}/user',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('username', user_data.get('login', 'unknown'))
                user_id = user_data.get('id', 'unknown')
                logger.info(f"GitCode PAT 认证测试成功，机器人用户: {username} (ID: {user_id})")
                
                # 验证这是否是预期的机器人账号
                if username != self.bot_username:
                    logger.warning(f"当前认证用户 ({username}) 与配置的机器人用户名 ({self.bot_username}) 不匹配")
                
                return True
            elif response.status_code == 401:
                logger.error("GitCode PAT 认证失败: Token 无效或已过期")
                return False
            else:
                logger.error(f"GitCode PAT 认证测试失败: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"GitCode PAT 认证测试时发生错误: {e}")
            return False
    
    def get_user_info(self) -> Optional[Dict[str, Any]]:
        """获取当前认证用户信息"""
        if not self.is_auth_available():
            return None
        
        try:
            headers = self.get_auth_headers()
            response = requests.get(
                f'{self.api_base}/user',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"获取用户信息失败: {response.status_code}")
                return None
                
        except Exception as e:
            logger.error(f"获取用户信息时发生错误: {e}")
            return None
    
    def test_repository_access(self, owner: str, repo: str) -> Dict[str, Any]:
        """测试对指定仓库的访问权限"""
        if not self.is_auth_available():
            return {"success": False, "error": "PAT Token 未配置"}
        
        try:
            headers = self.get_auth_headers()
            
            # 测试仓库基本信息读取
            repo_response = requests.get(
                f'{self.api_base}/repos/{owner}/{repo}',
                headers=headers,
                timeout=30
            )
            
            results = {
                "repository_access": repo_response.status_code == 200,
                "permissions": {}
            }
            
            if repo_response.status_code == 200:
                repo_data = repo_response.json()
                permissions = repo_data.get('permissions', {})
                results["permissions"] = permissions
                results["repository_info"] = {
                    "name": repo_data.get('name'),
                    "full_name": repo_data.get('full_name'),
                    "private": repo_data.get('private', False),
                    "default_branch": repo_data.get('default_branch')
                }
                
                # 检查关键权限
                required_permissions = ['pull', 'push', 'admin']
                missing_permissions = []
                for perm in required_permissions:
                    if not permissions.get(perm, False):
                        missing_permissions.append(perm)
                
                results["success"] = len(missing_permissions) == 0
                if missing_permissions:
                    results["error"] = f"缺少权限: {', '.join(missing_permissions)}"
                else:
                    results["message"] = "机器人对仓库具有足够权限"
            else:
                results["success"] = False
                results["error"] = f"无法访问仓库: HTTP {repo_response.status_code}"
            
            return results
            
        except Exception as e:
            return {"success": False, "error": f"测试仓库访问时发生错误: {e}"}
