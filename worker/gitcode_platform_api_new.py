import os
import requests
import logging
from typing import Dict, Any, Optional, List
import json
import base64
from gitcode_pat_auth import GitCodeAuth

logger = logging.getLogger(__name__)

class GitCodePlatformAPI:
    """GitCode 平台 API 适配器 - 使用机器人 PAT 认证"""
    
    def __init__(self):
        self.platform = 'gitcode'
        self.base_url = os.getenv('GITCODE_BASE', 'https://api.gitcode.com/api/v5')
        self.auth = GitCodeAuth()
        
        if not self.auth.is_auth_available():
            logger.warning("未找到 GitCode PAT 认证信息 - 某些操作可能失败")
        else:
            logger.info("GitCode PAT 认证已初始化")
        
        logger.info("GitCode 平台 API 客户端已初始化")
    
    def _get_auth_headers(self) -> Dict[str, str]:
        """获取认证头部"""
        return self.auth.get_auth_headers()
    
    def _make_request(self, method: str, url: str, **kwargs) -> requests.Response:
        """发起认证的 API 请求"""
        headers = self._get_auth_headers()
        if 'headers' in kwargs:
            headers.update(kwargs['headers'])
        kwargs['headers'] = headers
        
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            logger.debug(f"{method} {url} -> {response.status_code}")
            return response
        except requests.RequestException as e:
            logger.error(f"API 请求失败: {e}")
            raise
    
    # Issue 相关操作
    def get_issue(self, owner: str, repo: str, issue_number: int) -> Optional[Dict[str, Any]]:
        """获取 Issue 信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        response = self._make_request('GET', url)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"获取 Issue 失败: {response.status_code} - {response.text}")
            return None
    
    def comment_issue(self, owner: str, repo: str, issue_number: int, comment: str) -> bool:
        """在 Issue 上添加评论"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        data = {"body": comment}
        
        response = self._make_request('POST', url, json=data)
        
        if response.status_code == 201:
            logger.info(f"成功在 Issue #{issue_number} 添加评论")
            return True
        else:
            logger.error(f"添加评论失败: {response.status_code} - {response.text}")
            return False
    
    def update_issue(self, owner: str, repo: str, issue_number: int, **kwargs) -> bool:
        """更新 Issue"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}"
        
        response = self._make_request('PATCH', url, json=kwargs)
        
        if response.status_code == 200:
            logger.info(f"成功更新 Issue #{issue_number}")
            return True
        else:
            logger.error(f"更新 Issue 失败: {response.status_code} - {response.text}")
            return False
    
    def assign_issue(self, owner: str, repo: str, issue_number: int, assignees: List[str]) -> bool:
        """指派 Issue"""
        return self.update_issue(owner, repo, issue_number, assignees=assignees)
    
    def add_labels(self, owner: str, repo: str, issue_number: int, labels: List[str]) -> bool:
        """给 Issue 添加标签"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/labels"
        data = {"labels": labels}
        
        response = self._make_request('POST', url, json=data)
        
        if response.status_code == 200:
            logger.info(f"成功给 Issue #{issue_number} 添加标签: {labels}")
            return True
        else:
            logger.error(f"添加标签失败: {response.status_code} - {response.text}")
            return False
    
    # 仓库相关操作
    def get_repository_info(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """获取仓库信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        response = self._make_request('GET', url)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"获取仓库信息失败: {response.status_code} - {response.text}")
            return None
    
    def get_file_content(self, owner: str, repo: str, path: str, ref: Optional[str] = None) -> Optional[str]:
        """获取文件内容"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref} if ref else {}
        
        response = self._make_request('GET', url, params=params)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('type') == 'file':
                # GitCode API 返回 base64 编码的内容
                content = base64.b64decode(data['content']).decode('utf-8')
                return content
            else:
                logger.error(f"路径 {path} 不是文件")
                return None
        elif response.status_code == 404:
            logger.info(f"文件 {path} 不存在")
            return None
        else:
            logger.error(f"获取文件内容失败: {response.status_code} - {response.text}")
            return None
    
    def create_or_update_file(self, owner: str, repo: str, path: str, content: str, 
                            message: str, branch: Optional[str] = None, sha: Optional[str] = None) -> bool:
        """创建或更新文件"""
        url = f"{self.base_url}/repos/{owner}/{repo}/contents/{path}"
        
        # Base64 编码内容
        encoded_content = base64.b64encode(content.encode('utf-8')).decode('utf-8')
        
        data = {
            "message": message,
            "content": encoded_content
        }
        
        if branch:
            data["branch"] = branch
        if sha:
            data["sha"] = sha
        
        response = self._make_request('PUT', url, json=data)
        
        if response.status_code in [200, 201]:
            action = "更新" if sha else "创建"
            logger.info(f"成功{action}文件: {path}")
            return True
        else:
            logger.error(f"创建/更新文件失败: {response.status_code} - {response.text}")
            return False
    
    # 分支相关操作
    def get_branch(self, owner: str, repo: str, branch: str) -> Optional[Dict[str, Any]]:
        """获取分支信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}/branches/{branch}"
        response = self._make_request('GET', url)
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 404:
            logger.info(f"分支 {branch} 不存在")
            return None
        else:
            logger.error(f"获取分支信息失败: {response.status_code} - {response.text}")
            return None
    
    def create_branch(self, owner: str, repo: str, branch: str, from_branch: str = "master") -> bool:
        """创建分支"""
        # 首先获取源分支的最新 commit SHA
        source_branch_info = self.get_branch(owner, repo, from_branch)
        if not source_branch_info:
            logger.error(f"源分支 {from_branch} 不存在")
            return False
        
        source_sha = source_branch_info['commit']['sha']
        
        # 创建新分支
        url = f"{self.base_url}/repos/{owner}/{repo}/branches"
        data = {
            "branch_name": branch,
            "sha": source_sha
        }
        
        response = self._make_request('POST', url, json=data)
        
        if response.status_code == 201:
            logger.info(f"成功创建分支: {branch}")
            return True
        else:
            logger.error(f"创建分支失败: {response.status_code} - {response.text}")
            return False
    
    # Pull Request 相关操作
    def create_pull_request(self, owner: str, repo: str, title: str, body: str,
                          head: str, base: str) -> Optional[Dict[str, Any]]:
        """创建 Pull Request"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        
        response = self._make_request('POST', url, json=data)
        
        if response.status_code == 201:
            pr_data = response.json()
            logger.info(f"成功创建 PR #{pr_data.get('number', 'unknown')}: {title}")
            return pr_data
        else:
            logger.error(f"创建 PR 失败: {response.status_code} - {response.text}")
            return None
    
    def update_pull_request(self, owner: str, repo: str, pr_number: int, **kwargs) -> bool:
        """更新 Pull Request"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        
        response = self._make_request('PATCH', url, json=kwargs)
        
        if response.status_code == 200:
            logger.info(f"成功更新 PR #{pr_number}")
            return True
        else:
            logger.error(f"更新 PR 失败: {response.status_code} - {response.text}")
            return False
    
    def comment_pull_request(self, owner: str, repo: str, pr_number: int, comment: str) -> bool:
        """在 PR 上添加评论"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/comments"
        data = {"body": comment}
        
        response = self._make_request('POST', url, json=data)
        
        if response.status_code == 201:
            logger.info(f"成功在 PR #{pr_number} 添加评论")
            return True
        else:
            logger.error(f"PR 评论失败: {response.status_code} - {response.text}")
            return False
    
    # 工具方法
    def test_access(self, owner: str, repo: str) -> Dict[str, Any]:
        """测试对指定仓库的访问权限"""
        return self.auth.test_repository_access(owner, repo)
    
    def get_authenticated_user(self) -> Optional[Dict[str, Any]]:
        """获取当前认证用户信息"""
        return self.auth.get_user_info()
