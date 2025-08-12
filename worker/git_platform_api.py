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
            self.base_url = os.getenv('GITCODE_BASE', 'https://gitcode.net/api/v5')
        
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
        
        self.fallback_token = self._get_fallback_token()
        if not self.fallback_token and not (self.platform == 'github' and self._github_app_auth and self._github_app_auth.is_app_available()):
            logger.warning(f"{self.platform.upper()}_TOKEN not found - some operations may fail without GitHub App")
        
        logger.info(f"Initialized {self.platform} API client")
    
    def _get_fallback_token(self) -> Optional[str]:
        """获取回退令牌（Personal Access Token）"""
        if self.platform == 'github':
            return os.getenv('GITHUB_TOKEN')
        else:  # gitcode
            return os.getenv('GITCODE_TOKEN')
    
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
        else:
            # GitCode使用传统token
            if self.fallback_token:
                headers['Authorization'] = f'token {self.fallback_token}'
            else:
                raise ValueError("GITCODE_TOKEN is required")
        
        return headers
    
    def get_token(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Optional[str]:
        """获取当前可用的访问令牌"""
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
        else:
            # GitCode使用传统token
            return self.fallback_token
    
    def _request(self, method: str, endpoint: str, owner: Optional[str] = None, repo: Optional[str] = None, **kwargs) -> Optional[Dict]:
        """Make API request with proxy support"""
        try:
            url = f"{self.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            headers = self._get_auth_headers(owner, repo)
            
            # Add proxy settings if available
            proxies = {}
            proxy_url = os.getenv('HTTP_PROXY') or os.getenv('HTTPS_PROXY') or 'http://127.0.0.1:7890'
            if proxy_url:
                proxies = {
                    'http': proxy_url,
                    'https': proxy_url
                }
                logger.debug(f"Using proxy for API request: {proxy_url}")
            
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                timeout=30,
                proxies=proxies,
                **kwargs
            )
            
            logger.debug(f"{method} {url} - Status: {response.status_code}")
            
            if response.status_code == 404:
                return None
                
            if not response.ok:
                logger.error(f"API request failed: {method} {endpoint} - {response.status_code} {response.reason}")
                logger.error(f"Response body: {response.text}")
                
            response.raise_for_status()
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
        result = self._request('POST', f'/repos/{owner}/{repo}/issues/{number}/comments', 
                             owner, repo, json={'body': body})
        return result is not None
    
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
