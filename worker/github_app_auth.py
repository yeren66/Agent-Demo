import os
import time
import jwt
import requests
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GitHubAppAuth:
    """GitHub App 认证管理器"""
    
    def __init__(self):
        self.app_id = os.getenv('GITHUB_APP_ID')
        self.private_key_path = os.getenv('GITHUB_APP_PRIVATE_KEY_PATH')
        self.client_id = os.getenv('GITHUB_APP_CLIENT_ID') 
        self.client_secret = os.getenv('GITHUB_APP_CLIENT_SECRET')
        
        self._installation_tokens = {}  # 缓存安装令牌
        self._private_key = None
        
        if self.app_id and self.private_key_path:
            self._load_private_key()
    
    def _load_private_key(self):
        """加载私钥"""
        if not self.private_key_path:
            logger.warning("Private key path not configured")
            return
            
        try:
            if os.path.exists(self.private_key_path):
                with open(self.private_key_path, 'r') as key_file:
                    self._private_key = key_file.read()
                logger.info("GitHub App private key loaded")
            else:
                logger.warning(f"Private key file not found: {self.private_key_path}")
        except Exception as e:
            logger.error(f"Failed to load private key: {e}")
    
    def _generate_jwt(self) -> Optional[str]:
        """生成GitHub App JWT令牌"""
        if not self.app_id or not self._private_key:
            return None
            
        try:
            now = int(time.time())
            payload = {
                'iat': now - 60,  # 签发时间（过去1分钟，避免时钟偏差）
                'exp': now + (10 * 60),  # 过期时间（10分钟后）
                'iss': int(self.app_id)  # GitHub App ID
            }
            
            token = jwt.encode(payload, self._private_key, algorithm='RS256')
            return token
            
        except Exception as e:
            logger.error(f"Failed to generate JWT: {e}")
            return None
    
    def get_installation_token(self, installation_id: int) -> Optional[str]:
        """获取安装令牌"""
        # 检查缓存的令牌是否仍然有效
        if installation_id in self._installation_tokens:
            token_data = self._installation_tokens[installation_id]
            if time.time() < token_data['expires_at'] - 300:  # 提前5分钟刷新
                return token_data['token']
        
        # 生成新的安装令牌
        jwt_token = self._generate_jwt()
        if not jwt_token:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Bug-Fix-Agent/1.0'
            }
            
            response = requests.post(
                f'https://api.github.com/app/installations/{installation_id}/access_tokens',
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            token_data = response.json()
            
            # 缓存令牌
            expires_at = time.mktime(time.strptime(token_data['expires_at'], '%Y-%m-%dT%H:%M:%SZ'))
            self._installation_tokens[installation_id] = {
                'token': token_data['token'],
                'expires_at': expires_at
            }
            
            logger.info(f"Generated installation token for installation {installation_id}")
            return token_data['token']
            
        except Exception as e:
            logger.error(f"Failed to get installation token: {e}")
            return None
    
    def get_installation_id(self, owner: str, repo: str) -> Optional[int]:
        """获取仓库的安装ID"""
        jwt_token = self._generate_jwt()
        if not jwt_token:
            return None
            
        try:
            headers = {
                'Authorization': f'Bearer {jwt_token}',
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'Bug-Fix-Agent/1.0'
            }
            
            response = requests.get(
                f'https://api.github.com/repos/{owner}/{repo}/installation',
                headers=headers,
                timeout=30
            )
            
            response.raise_for_status()
            installation_data = response.json()
            
            return installation_data['id']
            
        except Exception as e:
            logger.error(f"Failed to get installation ID for {owner}/{repo}: {e}")
            return None
    
    def is_app_available(self) -> bool:
        """检查GitHub App是否可用"""
        return bool(self.app_id and self._private_key)
