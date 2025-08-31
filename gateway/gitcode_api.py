"""
GitCode API 客户端
专门用于处理 GitCode 平台的 API 调用
"""

import os
import sys
import asyncio
import aiohttp
import logging
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# 导入 GitCode PAT 认证模块
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'worker'))

try:
    from gitcode_pat_auth import GitCodeAuth
except ImportError as e:
    logger.error(f"无法导入 GitCode 认证模块: {e}")
    # 创建一个简单的备用认证类
    class GitCodeAuth:
        def __init__(self):
            self.token = os.getenv('GITCODE_PAT', '')
            
        def get_access_token(self):
            return self.token
            
        def is_auth_available(self):
            return bool(self.token)
            
        def get_auth_headers(self):
            headers = {'User-Agent': 'GitCode-Bug-Fix-Agent/1.0'}
            if self.token:
                headers['Authorization'] = f'Bearer {self.token}'
            return headers

class GitCodeAPI:
    """GitCode API 客户端，使用机器人 PAT 认证"""
    
    def __init__(self):
        self.base_url = 'https://api.gitcode.com/api/v5'
        self.auth = GitCodeAuth()
        
        logger.info("GitCode API 客户端已初始化")
    
    def _get_headers(self) -> Dict[str, str]:
        """获取 GitCode API 请求的认证头部"""
        return self.auth.get_auth_headers()
    
    async def comment_issue(self, owner: str, repo: str, issue_number: int, comment: str) -> bool:
        """在 Issue 中发表评论"""
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{issue_number}/comments"
        headers = self._get_headers()
        data = {"body": comment}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        logger.info(f"成功在 Issue #{issue_number} 中发表评论")
                        return True
                    else:
                        logger.error(f"发表 Issue 评论失败: HTTP {response.status}")
                        response_text = await response.text()
                        logger.error(f"响应内容: {response_text}")
                        return False
        except Exception as e:
            logger.error(f"发表 Issue 评论时发生错误: {e}")
            return False
    
    def comment_issue_sync(self, owner: str, repo: str, issue_number: int, comment: str) -> bool:
        """同步版本的 comment_issue"""
        return asyncio.run(self.comment_issue(owner, repo, issue_number, comment))
    
    async def create_pull_request(self, owner: str, repo: str, title: str, body: str, head: str, base: str = "master", draft: bool = False) -> Optional[Dict[str, Any]]:
        """创建 Pull Request"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls"
        headers = self._get_headers()
        data = {
            "title": title,
            "body": body,
            "head": head,
            "base": base
        }
        
        # GitCode 可能不支持 draft 参数，需要根据实际测试调整
        # if draft:
        #     data["draft"] = True
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        pr_data = await response.json()
                        pr_number = pr_data.get('number', 'unknown')
                        logger.info(f"成功创建 PR #{pr_number}")
                        return pr_data
                    else:
                        logger.error(f"创建 PR 失败: HTTP {response.status}")
                        response_text = await response.text()
                        logger.error(f"响应内容: {response_text}")
                        return None
        except Exception as e:
            logger.error(f"创建 PR 时发生错误: {e}")
            return None
    
    async def update_pull_request(self, owner: str, repo: str, pr_number: int, title: Optional[str] = None, body: Optional[str] = None) -> bool:
        """更新 Pull Request"""
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}"
        headers = self._get_headers()
        data = {}
        
        if title:
            data["title"] = title
        if body:
            data["body"] = body
        
        if not data:
            return True  # 没有需要更新的内容
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.patch(url, json=data, headers=headers) as response:
                    if response.status == 200:
                        logger.info(f"成功更新 PR #{pr_number}")
                        return True
                    else:
                        logger.error(f"更新 PR 失败: HTTP {response.status}")
                        response_text = await response.text()
                        logger.error(f"响应内容: {response_text}")
                        return False
        except Exception as e:
            logger.error(f"更新 PR 时发生错误: {e}")
            return False
    
    async def comment_pr(self, owner: str, repo: str, pr_number: int, comment: str) -> bool:
        """在 Pull Request 中发表评论"""
        # GitCode 中 PR 评论使用 issues API
        url = f"{self.base_url}/repos/{owner}/{repo}/issues/{pr_number}/comments"
        headers = self._get_headers()
        data = {"body": comment}
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(url, json=data, headers=headers) as response:
                    if response.status == 201:
                        logger.info(f"成功在 PR #{pr_number} 中发表评论")
                        return True
                    else:
                        logger.error(f"发表 PR 评论失败: HTTP {response.status}")
                        response_text = await response.text()
                        logger.error(f"响应内容: {response_text}")
                        return False
        except Exception as e:
            logger.error(f"发表 PR 评论时发生错误: {e}")
            return False
    
    async def get_repo(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """获取仓库信息"""
        url = f"{self.base_url}/repos/{owner}/{repo}"
        headers = self._get_headers()
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, headers=headers) as response:
                    if response.status == 200:
                        repo_data = await response.json()
                        logger.info(f"成功获取仓库信息: {owner}/{repo}")
                        return repo_data
                    else:
                        logger.error(f"获取仓库信息失败: HTTP {response.status}")
                        return None
        except Exception as e:
            logger.error(f"获取仓库信息时发生错误: {e}")
            return None
    
    def get_repo_sync(self, owner: str, repo: str) -> Optional[Dict[str, Any]]:
        """同步版本的 get_repo"""
        return asyncio.run(self.get_repo(owner, repo))
    
    async def create_pr_with_issue_binding(self, owner: str, repo: str, title: str, head: str, base: str, issue_number: int, job_id: str, actor: str) -> Optional[Dict[str, Any]]:
        """创建绑定 Issue 的 Pull Request"""
        
        # 构建 PR 描述，包含 Issue 绑定
        body = f"""## 🤖 Agent 修复报告

**修复 Issue:** #{issue_number}
**触发者:** @{actor}
**任务 ID:** `{job_id}`
**创建时间:** {asyncio.get_event_loop().time()}

---

### 📋 修复进度

- [x] **初始化** - 仓库和分支设置完成
- [ ] **定位** - 识别问题文件和根本原因  
- [ ] **方案** - 生成详细修复策略
- [ ] **修复** - 应用代码修改
- [ ] **验证** - 验证更改和测试结果
- [ ] **完成** - 完成并准备审查

### 📁 生成文件
- `agent/analysis.md` - 详细问题分析和诊断
- `agent/patch_plan.json` - 综合修复策略和实施计划
- `agent/report.txt` - 验证结果和变更验证

---
*🚀 Agent 自动化 Bug 分析和修复*

**关闭 Issue:** #{issue_number}
"""
        
        return await self.create_pull_request(
            owner=owner,
            repo=repo, 
            title=title,
            body=body,
            head=head,
            base=base,
            draft=True
        )
