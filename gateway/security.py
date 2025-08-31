import hmac
import hashlib
import logging
from typing import Dict, Union

logger = logging.getLogger(__name__)

import hmac
import hashlib
import logging
import os
from typing import Dict, Union

logger = logging.getLogger(__name__)

def verify_webhook_signature(headers: Dict[str, str], body: bytes, secret: str) -> bool:
    """
    Verify webhook signature for GitHub or GitCode
    """
    try:
        platform = os.getenv('PLATFORM', 'github').lower()
        
        # 调试：打印所有头部信息
        logger.debug(f"Webhook headers: {dict(headers)}")
        
        if platform == 'github':
            # GitHub uses X-Hub-Signature-256 header
            received_signature = headers.get('x-hub-signature-256', '')
            
            if not received_signature:
                logger.warning("No GitHub webhook signature found in headers")
                return False
            
            # GitHub signature format: sha256=<signature>
            if not received_signature.startswith('sha256='):
                logger.warning("Invalid GitHub signature format")
                return False
            
            received_signature = received_signature[7:]  # Remove 'sha256=' prefix
            
            # Create expected signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
            
        else:  # gitcode
            # GitCode 可能使用不同的头部名称，尝试多种可能性
            possible_headers = [
                'x-gitcode-token',
                'x-gitcode-signature', 
                'x-gitcode-sign',
                'x-signature',
                'x-gitcode-webhook-signature'
            ]
            
            received_signature = None
            header_used = None
            
            for header in possible_headers:
                if header in headers:
                    received_signature = headers[header]
                    header_used = header
                    break
            
            if not received_signature:
                logger.warning("No GitCode webhook signature found in headers")
                logger.warning(f"Available headers: {list(headers.keys())}")
                # 在测试模式下允许无签名请求
                test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
                if test_mode:
                    logger.info("TEST_MODE enabled, skipping signature verification")
                    return True
                return False
            
            logger.debug(f"Using GitCode signature from header: {header_used}")
            
            # GitCode 可能使用不同的签名格式，尝试直接比较
            if received_signature.startswith('sha256='):
                received_signature = received_signature[7:]
            
            # Create expected signature
            expected_signature = hmac.new(
                secret.encode('utf-8'),
                body,
                hashlib.sha256
            ).hexdigest()
        
        # Compare signatures securely
        result = hmac.compare_digest(received_signature, expected_signature)
        if not result:
            logger.warning(f"Signature mismatch. Expected: {expected_signature[:8]}..., Received: {received_signature[:8]}...")
        
        return result
        
    except Exception as e:
        logger.error(f"Signature verification error: {e}")
        return False

def is_authorized_user(username: str, allowed_users: str = "") -> bool:
    """
    Check if user is authorized to trigger the agent
    """
    if not allowed_users:
        return True  # Allow all users if no restriction set
    
    allowed_list = [user.strip() for user in allowed_users.split(',') if user.strip()]
    return username in allowed_list

def is_authorized_repo(owner: str, repo: str, allowed_repos: str = "") -> bool:
    """
    Check if repository is authorized for agent usage
    """
    if not allowed_repos:
        return True  # Allow all repos if no restriction set
    
    repo_full_name = f"{owner}/{repo}"
    allowed_list = [repo.strip() for repo in allowed_repos.split(',') if repo.strip()]
    return repo_full_name in allowed_list
