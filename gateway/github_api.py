"""
GitHub API client for handling GitHub App authentication and API calls
"""

import os
import sys
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional

# Add worker directory to path to import github_app_auth
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'worker'))

try:
    from github_app_auth import GitHubAppAuth
except ImportError:
    # Fallback if github_app_auth is not available
    class GitHubAppAuth:
        def get_installation_token(self, *args, **kwargs):
            return None

logger = logging.getLogger(__name__)

class GitHubAPI:
    """GitHub API client with GitHub App authentication support"""
    
    def __init__(self):
        self.base_url = "https://api.github.com"
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_app_auth = GitHubAppAuth()
    
    def _get_headers(self, installation_id: Optional[int] = None) -> Dict[str, str]:
        """Get headers for GitHub API requests"""
        headers = {
            'Accept': 'application/vnd.github.v3+json',
            'User-Agent': 'Bug-Fix-Agent/1.0'
        }
        
        # Try to use GitHub App authentication first
        if installation_id:
            token = self.github_app_auth.get_installation_token(installation_id)
            if token:
                headers['Authorization'] = f'token {token}'
                return headers
        
        # Fallback to personal access token
        if self.github_token:
            headers['Authorization'] = f'token {self.github_token}'
        
        return headers
    
    async def comment_issue(self, owner: str, repo: str, issue_number: int, comment: str, installation_id: Optional[int] = None) -> bool:
        """Post a comment on an issue"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        headers = self._get_headers(installation_id)
        data = {"body": comment}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        logger.info(f"Successfully posted comment to issue #{issue_number}")
                        return True
                    else:
                        logger.error(f"Failed to post comment: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error posting comment: {e}")
            return False
    
    def comment_issue_sync(self, owner: str, repo: str, issue_number: int, comment: str, installation_id: Optional[int] = None) -> bool:
        """Synchronous version of comment_issue"""
        return asyncio.run(self.comment_issue(owner, repo, issue_number, comment, installation_id))
    
    async def create_pull_request(self, owner: str, repo: str, title: str, body: str, head: str, base: str = "main", installation_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
        """Create a pull request"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        headers = self._get_headers(installation_id)
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base,
            "draft": True  # Create as draft initially
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        pr_data = await response.json()
                        logger.info(f"Successfully created PR #{pr_data['number']}")
                        return pr_data
                    else:
                        logger.error(f"Failed to create PR: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Error creating PR: {e}")
            return None
    
    async def update_pull_request(self, owner: str, repo: str, pr_number: int, title: Optional[str] = None, body: Optional[str] = None, installation_id: Optional[int] = None) -> bool:
        """Update a pull request"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = self._get_headers(installation_id)
        data = {}
        
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        
        if not data:
            return True  # Nothing to update
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"Successfully updated PR #{pr_number}")
                        return True
                    else:
                        logger.error(f"Failed to update PR: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error updating PR: {e}")
            return False
    
    async def comment_pr(self, owner: str, repo: str, pr_number: int, comment: str, installation_id: Optional[int] = None) -> bool:
        """Post a comment on a pull request"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        headers = self._get_headers(installation_id)
        data = {"body": comment}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        logger.info(f"Successfully posted comment to PR #{pr_number}")
                        return True
                    else:
                        logger.error(f"Failed to post PR comment: {response.status}")
                        return False
        except Exception as e:
            logger.error(f"Error posting PR comment: {e}")
            return False
    
    async def get_installation_id(self, owner: str, repo: str) -> Optional[int]:
        """Get installation ID for a repository (for GitHub App)"""
        # This would require GitHub App JWT to get installation info
        # For now, return None and use personal token
        return None
