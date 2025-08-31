import os
import time
import requests
import logging
import secrets
import urllib.parse
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class GitCodeOAuthAuth:
    """GitCode OAuth 认证管理器
    
    实现标准的 OAuth 2.0 授权码流程：
    1. 生成授权 URL (用户访问授权)
    2. 接收授权码 (callback处理)
    3. 交换访问令牌 (使用授权码)
    4. 使用访问令牌调用 API
    5. 刷新令牌 (当令牌过期时)
    """
    
    def __init__(self):
        # GitCode OAuth 配置
        self.client_id = os.getenv('GITCODE_CLIENT_ID')
        self.client_secret = os.getenv('GITCODE_CLIENT_SECRET') 
        self.redirect_uri = os.getenv('GITCODE_REDIRECT_URI')
        
        # 备用认证 - Private Token
        self.private_token = os.getenv('GITCODE_PRIVATE_TOKEN')
        
        # API URLs
        self.api_base = 'https://api.gitcode.com/api/v5'
        self.oauth_base = 'https://gitcode.com/oauth'
        
        # 令牌缓存
        self._token_cache = {}
        
        self._validate_config()
    
    def _validate_config(self):
        """验证配置"""
        if self.is_oauth_available():
            logger.info("GitCode OAuth 应用配置已加载")
            logger.info(f"Client ID: {self.client_id}")
            logger.info(f"Redirect URI: {self.redirect_uri}")
        elif self.private_token:
            logger.info("GitCode Private Token 配置已加载")
        else:
            logger.warning("未找到 GitCode 认证配置")
    
    def is_oauth_available(self) -> bool:
        """检查 OAuth 配置是否可用"""
        return bool(self.client_id and self.client_secret and self.redirect_uri)
    
    def is_auth_available(self) -> bool:
        """检查任何形式的认证是否可用"""
        return self.is_oauth_available() or bool(self.private_token)
    
    def get_application_info(self) -> Dict[str, str]:
        """获取应用信息，用于用户配置 GitCode OAuth 应用"""
        return {
            "应用名称": "GitCode Bug Fix Agent",
            "应用描述": "智能代码问题修复助手，自动分析 Issue 并生成修复 PR",
            "应用主页": "https://github.com/yeren66/Agent-Demo",
            "授权回调地址": self.redirect_uri or "https://your-domain.com/api/callback",
            "权限范围": "api (访问 GitCode API 的完整权限)",
            "说明": "请在 GitCode 中创建 OAuth 应用，然后将 Client ID 和 Client Secret 配置到环境变量中"
        }
    
    def generate_authorization_url(self, scope: str = "api", state: Optional[str] = None) -> tuple[str, str]:
        """生成 OAuth 授权 URL
        
        用户需要访问这个 URL 来授权应用
        
        Returns:
            tuple: (authorization_url, state)
        """
        if not self.is_oauth_available():
            raise ValueError("OAuth 配置不完整，请检查 GITCODE_CLIENT_ID、GITCODE_CLIENT_SECRET 和 GITCODE_REDIRECT_URI")
        
        if state is None:
            state = secrets.token_urlsafe(32)
        
        params = {
            'client_id': self.client_id,
            'redirect_uri': self.redirect_uri,
            'response_type': 'code',
            'scope': scope,
            'state': state
        }
        
        auth_url = f"{self.oauth_base}/authorize?" + urllib.parse.urlencode(params)
        logger.info(f"生成授权 URL，权限范围: {scope}")
        return auth_url, state
    
    def exchange_code_for_token(self, code: str) -> Optional[Dict[str, Any]]:
        """用授权码换取访问令牌
        
        这个方法在用户授权后，使用授权码换取访问令牌
        """
        if not self.is_oauth_available():
            logger.error("OAuth 配置不可用")
            return None
        
        try:
            # 根据 GitCode 文档，使用 POST 请求，参数放在 URL 中
            params = {
                'grant_type': 'authorization_code',
                'code': code,
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
            
            url = f'{self.oauth_base}/token?' + urllib.parse.urlencode(params)
            
            response = requests.post(
                url,
                headers={
                    'User-Agent': 'GitCode-Bug-Fix-Agent/1.0',
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                # 缓存令牌
                self._token_cache['access_token'] = {
                    'token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token'),
                    'expires_at': time.time() + token_data.get('expires_in', 3600),
                    'scope': token_data.get('scope'),
                    'created_at': token_data.get('created_at')
                }
                
                logger.info("成功使用授权码换取访问令牌")
                logger.debug(f"令牌权限范围: {token_data.get('scope')}")
                return token_data
            else:
                logger.error(f"换取访问令牌失败: {response.status_code} - {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"换取访问令牌时发生错误: {e}")
            return None
    
    def get_access_token(self) -> Optional[str]:
        """获取有效的访问令牌"""
        # 优先使用 Private Token (更简单，适合机器人应用)
        if self.private_token:
            logger.debug("使用 Private Token 认证")
            return self.private_token
        
        # 检查缓存的 OAuth token
        if 'access_token' in self._token_cache:
            token_data = self._token_cache['access_token']
            # 提前 5 分钟检查过期时间
            if time.time() < token_data['expires_at'] - 300:
                logger.debug("使用缓存的 OAuth 访问令牌")
                return token_data['token']
            else:
                logger.info("访问令牌即将过期，尝试刷新")
                # 尝试刷新令牌
                if self._refresh_token():
                    return self._token_cache['access_token']['token']
        
        logger.warning("没有可用的访问令牌")
        return None
    
    def _refresh_token(self) -> bool:
        """刷新访问令牌"""
        if 'access_token' not in self._token_cache:
            logger.error("没有找到缓存的令牌数据")
            return False
        
        refresh_token = self._token_cache['access_token'].get('refresh_token')
        if not refresh_token:
            logger.error("没有刷新令牌")
            return False
        
        try:
            params = {
                'grant_type': 'refresh_token',
                'refresh_token': refresh_token
            }
            
            url = f'{self.oauth_base}/token?' + urllib.parse.urlencode(params)
            
            response = requests.post(
                url,
                headers={
                    'User-Agent': 'GitCode-Bug-Fix-Agent/1.0',
                    'Accept': 'application/json'
                },
                timeout=30
            )
            
            if response.status_code == 200:
                token_data = response.json()
                
                # 更新缓存
                self._token_cache['access_token'] = {
                    'token': token_data.get('access_token'),
                    'refresh_token': token_data.get('refresh_token', refresh_token),
                    'expires_at': time.time() + token_data.get('expires_in', 3600),
                    'scope': token_data.get('scope'),
                    'created_at': token_data.get('created_at')
                }
                
                logger.info("成功刷新访问令牌")
                return True
            else:
                logger.error(f"刷新令牌失败: {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"刷新令牌时发生错误: {e}")
            return False
    
    def get_auth_headers(self) -> Dict[str, str]:
        """获取用于 API 请求的认证头部"""
        headers = {
            'User-Agent': 'GitCode-Bug-Fix-Agent/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        }
        
        token = self.get_access_token()
        if token:
            headers['Authorization'] = f'Bearer {token}'
        else:
            logger.warning("没有可用的访问令牌用于认证")
        
        return headers
    
    def test_authentication(self) -> bool:
        """测试认证是否有效"""
        try:
            headers = self.get_auth_headers()
            
            if 'Authorization' not in headers:
                logger.error("没有可用的认证令牌")
                return False
            
            response = requests.get(
                f'{self.api_base}/user',
                headers=headers,
                timeout=30
            )
            
            if response.status_code == 200:
                user_data = response.json()
                username = user_data.get('username', user_data.get('login', 'unknown'))
                user_id = user_data.get('id', 'unknown')
                logger.info(f"GitCode 认证测试成功，用户: {username} (ID: {user_id})")
                return True
            elif response.status_code == 401:
                logger.error("GitCode 认证失败: 令牌无效或已过期")
                return False
            else:
                logger.error(f"GitCode 认证测试失败: HTTP {response.status_code} - {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"GitCode 认证测试时发生错误: {e}")
            return False
    
    def clear_token_cache(self):
        """清除令牌缓存"""
        self._token_cache.clear()
        logger.info("已清除令牌缓存")
