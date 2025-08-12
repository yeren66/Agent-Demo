import os
import time
import jwt
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GitCodeAppAuth:
    """GitCode App 认证管理器
    
    GitCode 平台支持 OAuth 应用和访问令牌认证。
    根据 GitCode API 文档，支持以下认证方式：
    1. Authorization Bearer token
    2. PRIVATE-TOKEN header
    3. access_token query parameter
    """
    
    def __init__(self):
        # GitCode App 配置
        self.app_id = os.getenv('GITCODE_APP_ID')
        self.app_secret = os.getenv('GITCODE_APP_SECRET')
        self.private_token = os.getenv('GITCODE_PRIVATE_TOKEN')
        
        # API 基础URL
        self.base_url = os.getenv('GITCODE_BASE', 'https://api.gitcode.com/api/v5')
        
        # 访问令牌缓存
        self._access_tokens = {}
        
        if self.app_id and self.app_secret:
            logger.info("GitCode App configuration loaded")
        elif self.private_token:
            logger.info("GitCode Private Token configuration loaded")
        else:
            logger.warning("No GitCode authentication configuration found")
    
    def is_app_available(self) -> bool:
        """检查GitCode App是否可用"""
        return bool(self.app_id and self.app_secret) or bool(self.private_token)
    
    def get_access_token(self, owner: str, repo: str) -> Optional[str]:
        """获取访问令牌
        
        对于 GitCode，我们主要使用 Private Token，
        但也支持 OAuth App 的 client_credentials 流程
        """
        # 如果有 Private Token，直接使用
        if self.private_token:
            return self.private_token
        
        # 否则尝试使用 OAuth App 获取 access token
        return self._get_oauth_token()
    
    def _get_oauth_token(self) -> Optional[str]:
        """通过 OAuth App 获取访问令牌"""
        if not (self.app_id and self.app_secret):
            return None
        
        # 检查缓存的令牌
        cache_key = f"{self.app_id}:{self.app_secret}"
        if cache_key in self._access_tokens:
            token_data = self._access_tokens[cache_key]
            if time.time() < token_data['expires_at'] - 300:  # 提前5分钟刷新
                return token_data['token']
        
        try:
            # GitCode OAuth 的 client_credentials 流程
            # 注意：这里的实现取决于 GitCode 的具体 OAuth 实现
            # 可能需要根据实际的 GitCode OAuth 文档进行调整
            
            response = requests.post(
                f'{self.base_url}/oauth/token',
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.app_id,
                    'client_secret': self.app_secret,
                    'scope': 'api'  # 根据需要的权限调整
                },
                headers={
                    'User-Agent': 'Bug-Fix-Agent/1.0',
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                access_token = token_data.get('access_token')
                expires_in = token_data.get('expires_in', 3600)
                
                # 缓存令牌
                self._access_tokens[cache_key] = {
                    'token': access_token,
                    'expires_at': time.time() + expires_in
                }
                
                logger.info("Successfully obtained GitCode OAuth access token")
                return access_token
            else:
                logger.error(f"Failed to get GitCode OAuth token: {response.status_code} {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Error getting GitCode OAuth token: {e}")
            return None
    
    def get_auth_headers(self, owner: Optional[str] = None, repo: Optional[str] = None) -> Dict[str, str]:
        """获取认证头部"""
        headers = {
            'User-Agent': 'Bug-Fix-Agent/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        token = self.get_access_token(owner or '', repo or '')
        if token:
            # GitCode 支持多种认证方式，我们使用 Authorization Bearer
            headers['Authorization'] = f'Bearer {token}'
        
        return headers
    
    def test_authentication(self) -> bool:
        """测试认证是否有效"""
        try:
            headers = self.get_auth_headers()
            response = requests.get(
                f'{self.base_url}/user',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('username', 'unknown')
                logger.info(f"GitCode authentication test successful for user: {username}")
                return True
            else:
                logger.error(f"GitCode authentication test failed: {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"GitCode authentication test error: {e}")
            return False
