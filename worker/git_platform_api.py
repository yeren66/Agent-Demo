import os
import requests
import logging
from typing import Dict, Any, Optional, List
import json
import base64

logger = logging.getLogger(__name__)

class GitPlatformAPI:
    """通用Git平台API适配器，支持GitHub和GitCode"""
    
    def __init__(self):
        self.platform = os.getenv('PLATFORM', 'github').lower()
        
        if self.platform == 'github':
            self.base_url = os.getenv('GITHUB_BASE', 'https://api.github.com')
        else:  # gitcode
            self.base_url = os.getenv('GITCODE_BASE', 'https://api.gitcode.com/api/v5')
        
        # GitHub App认证支持
        self._github_app_auth = None
        if self.platform == 'github':
            try:
                from .github_app_auth import GitHubAppAuth
                self._github_app_auth = GitHubAppAuth()
                if self._github_app_auth.is_app_available():
                    logger.info("GitHub App authentication initialized")
                else:
                    logger.info("GitHub App not configured, using Personal Access Token")
            except ImportError:
                logger.warning("GitHub App authentication module not available")
        
        # GitCode App认证支持
        self._gitcode_app_auth = None
        if self.platform == 'gitcode':
            try:
                from .gitcode_app_auth import GitCodeAppAuth
                self._gitcode_app_auth = GitCodeAppAuth()
                if self._gitcode_app_auth.is_app_available():
                    logger.info("GitCode App authentication initialized")
                else:
                    logger.info("GitCode App not configured, using Personal Access Token")
            except ImportError:
                logger.warning("GitCode App authentication module not available")
        
        self.fallback_token = self._get_fallback_token()
        if not self.fallback_token and not self._has_app_auth():
            token_var = "GITHUB_TOKEN" if self.platform == 'github' else "GITCODE_TOKEN/GITCODE_PAT"
            logger.warning(f"{token_var} not found - some operations may fail without App authentication")
        
        logger.info(f"Initialized {self.platform} API client")
    
    def _has_app_auth(self) -> bool:
        """检查是否有可用的App认证"""
        if self.platform == 'github':
            return bool(self._github_app_auth and self._github_app_auth.is_app_available())
        else:  # gitcode
            return bool(self._gitcode_app_auth and self._gitcode_app_auth.is_app_available())
    
    def _get_fallback_token(self) -> Optional[str]:
        """获取回退令牌（Personal Access Token）"""
        if self.platform == 'github':
            return os.getenv('GITHUB_TOKEN')
        else:  # gitcode
            # 支持两种环境变量名：GITCODE_TOKEN 和 GITCODE_PAT
            return os.getenv('GITCODE_TOKEN') or os.getenv('GITCODE_PAT')
    
    def _get_auth_headers(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, str]:
        """获取认证头部"""
        headers = {
            'Content-Type': 'application/json',
            'User-Agent': 'Bug-Fix-Agent/1.0'
        }
        
        if self.platform == 'github':
            # GitHub需要Accept header
            headers['Accept'] = 'application/vnd.github.v3+json'
            
            # 优先使用GitHub App认证
            if self._github_app_auth and self._github_app_auth.is_app_available() and owner and repo:
                try:
                    installation_id = self._github_app_auth.get_installation_id(owner, repo)
                    if installation_id:
                        token = self._github_app_auth.get_installation_token(installation_id)
                        if token:
                            headers['Authorization'] = f'token {token}'
                            return headers
                        logger.warning("Failed to get GitHub App installation token")
                    else:
                        logger.warning(f"No GitHub App installation found for {owner}/{repo}")
                except Exception as e:
                    logger.error(f"GitHub App authentication failed: {e}")
            
            # 回退到个人访问令牌
            if self.fallback_token:
                headers['Authorization'] = f'token {self.fallback_token}'
            else:
                raise ValueError("No GitHub authentication method available")
        else:  # gitcode
            # 优先使用GitCode App认证
            if self._gitcode_app_auth and self._gitcode_app_auth.is_app_available():
                try:
                    app_headers = self._gitcode_app_auth.get_auth_headers(owner, repo)
                    headers.update(app_headers)
                    return headers
                except Exception as e:
                    logger.error(f"GitCode App authentication failed: {e}")
            
            # 回退到个人访问令牌
            if self.fallback_token:
                # GitCode 支持多种认证方式，使用 Authorization Bearer
                headers['Authorization'] = f'Bearer {self.fallback_token}'
            else:
                raise ValueError("GITCODE_TOKEN is required")
        
        return headers
    
    def get_token(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Optional[str]:
        """获取当前可用的访问令牌"""
        logger.info(f"获取令牌 - 平台: {self.platform}, 回退令牌: {'已设置' if self.fallback_token else '未设置'}")
        
        if self.platform == 'github':
            # 优先使用GitHub App认证
            if self._github_app_auth and self._github_app_auth.is_app_available() and owner and repo:
                try:
                    installation_id = self._github_app_auth.get_installation_id(owner, repo)
                    if installation_id:
                        token = self._github_app_auth.get_installation_token(installation_id)
                        if token:
                            return token
                except Exception as e:
                    logger.error(f"Failed to get GitHub App token: {e}")
            
            # 回退到个人访问令牌
            return self.fallback_token
        else:  # gitcode
            # 优先使用GitCode App认证
            if self._gitcode_app_auth and self._gitcode_app_auth.is_app_available():
                try:
                    token = self._gitcode_app_auth.get_access_token(owner or '', repo or '')
                    if token:
                        return token
                except Exception as e:
                    logger.error(f"Failed to get GitCode App token: {e}")
            
            # 回退到个人访问令牌
            logger.info(f"返回回退令牌: {'已设置' if self.fallback_token else '未设置'}")
            return self.fallback_token
    
    def _request(self, method: str, endpoint: str, owner: Optional[str] = None, repo: Optional[str] = None, **kwargs) -> Optional[Dict]:
        """Make API request"""
        try:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            headers = self._get_auth_headers(owner, repo)
            
            logger.info(f"API请求: {method} {url}")
            logger.debug(f"请求头: {headers}")
            if 'json' in kwargs:
                logger.debug(f"请求体: {kwargs['json']}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                **kwargs
            )
            
            logger.info(f"API响应: {method} {endpoint} - Status: {response.status_code}")
            
            if response.status_code == 404:
                logger.warning(f"资源未找到: {endpoint}")
                return None
                
            if not response.ok:
                logger.error(f"API request failed: {method} {endpoint} - {response.status_code} {response.reason}")
                logger.error(f"Response body: {response.text}")
                
                # 对于GitCode，可能需要特殊处理某些错误
                if self.platform == 'gitcode' and response.status_code == 400:
                    try:
                        error_data = response.json()
                        if error_data.get('error_code') == 404:
                            logger.error(f"GitCode Issue不存在或无权限访问: {owner}/{repo} #{endpoint.split('/')[-2]}")
                        elif 'Issue Not Found' in error_data.get('error_message', ''):
                            logger.error(f"GitCode Issue未找到，可能使用了错误的编号")
                    except:
                        pass
                
                # 不要抛出异常，让调用者决定如何处理
                return None
                
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {method} {endpoint} - {e}")
            return None
    
    # Issue operations
    def get_issue(self, owner: str, repo: str, number: int) -> Optional[Dict]:
        """Get issue details"""
        return self._request('GET', f'/repos/{owner}/{repo}/issues/{number}', owner, repo)
    
    def comment_issue(self, owner: str, repo: str, number: int, body: str) -> bool:
        """Add comment to issue"""
        logger.info(f"正在向Issue #{number} ({owner}/{repo})发送评论")
        logger.debug(f"评论内容长度: {len(body)} 字符")
        
        result = self._request('POST', f'/repos/{owner}/{repo}/issues/{number}/comments', 
                             owner, repo, json={'body': body})
        
        success = result is not None
        if success:
            logger.info(f"✅ 成功向Issue #{number}发送评论")
        else:
            logger.error(f"❌ 向Issue #{number}发送评论失败")
            
        return success
    
    def comment_issue_sync(self, owner: str, repo: str, number: int, body: str) -> bool:
        """Add comment to issue (sync version)"""
        return self.comment_issue(owner, repo, number, body)
    
    def create_pr(self, owner: str, repo: str, head: str, base: str, 
                  title: str, body: str, draft: bool = True) -> Optional[Dict]:
        """Create pull request"""
        data: Dict[str, Any] = {
            'title': title,
            'body': body,
            'head': head,
            'base': base
        }
        
        # GitHub支持draft字段，GitCode可能不支持
        if self.platform == 'github':
            data['draft'] = draft
        
        return self._request('POST', f'/repos/{owner}/{repo}/pulls', 
                           owner, repo, json=data)
    
    def update_pr_body(self, owner: str, repo: str, number: int, body: str) -> bool:
        """Update PR description"""
        result = self._request('PATCH', f'/repos/{owner}/{repo}/pulls/{number}', 
                             owner, repo, json={'body': body})
        return result is not None
    
    def mark_pr_ready(self, owner: str, repo: str, number: int) -> bool:
        """Mark PR as ready for review (non-draft)"""
        if self.platform == 'github':
            result = self._request('PATCH', f'/repos/{owner}/{repo}/pulls/{number}', 
                                 owner, repo, json={'draft': False})
        else:
            result = self._request('PATCH', f'/repos/{owner}/{repo}/pulls/{number}', 
                                 owner, repo, json={'draft': False})
        return result is not None
    
    def comment_pr(self, owner: str, repo: str, number: int, body: str) -> bool:
        """Add comment to PR"""
        result = self._request('POST', f'/repos/{owner}/{repo}/issues/{number}/comments', 
                             owner, repo, json={'body': body})
        return result is not None
    
    # Repository operations
    def get_repo(self, owner: str, repo: str) -> Optional[Dict]:
        """Get repository details"""
        return self._request('GET', f'/repos/{owner}/{repo}', owner, repo)
    
    def get_default_branch(self, owner: str, repo: str) -> str:
        """Get repository default branch"""
        repo_data = self.get_repo(owner, repo)
        if repo_data and 'default_branch' in repo_data:
            return repo_data['default_branch']
        return 'main'  # fallback
    
    def create_branch(self, owner: str, repo: str, branch: str, sha: str) -> Optional[Dict]:
        """Create new branch"""
        data = {
            'ref': f'refs/heads/{branch}',
            'sha': sha
        }
        return self._request('POST', f'/repos/{owner}/{repo}/git/refs', 
                           owner, repo, json=data)
    
    def create_or_update_file(self, owner: str, repo: str, path: str, 
                            content: str, message: str, branch: str = 'main',
                            sha: Optional[str] = None) -> Optional[Dict]:
        """Create or update a file"""
        encoded_content = base64.b64encode(content.encode()).decode()
        data = {
            'message': message,
            'content': encoded_content,
            'branch': branch
        }
        if sha:
            data['sha'] = sha
        
        return self._request('PUT', f'/repos/{owner}/{repo}/contents/{path}', 
                           owner, repo, json=data)
    
    def get_file_content(self, owner: str, repo: str, path: str, ref: str = 'main') -> Optional[str]:
        """Get file content from repository"""
        result = self._request('GET', f'/repos/{owner}/{repo}/contents/{path}?ref={ref}', owner, repo)
        
        if result and result.get('content'):
            return base64.b64decode(result['content']).decode()
        return None
