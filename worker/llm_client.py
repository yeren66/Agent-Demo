"""
LLM Client for Bug Fix Agent
Integrates with OpenAI-compatible API to generate bug analysis and fixes
"""

import os
import json
import logging
import httpx
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class LLMClient:
    def __init__(self, base_url: Optional[str] = None, api_key: Optional[str] = None, model: Optional[str] = None):
        self.base_url = base_url or os.getenv("LLM_BASE_URL", "https://api.geekai.pro/v1/chat/completions")
        self.api_key = api_key or os.getenv("LLM_API_KEY", "sk-SnbItL2wOmzHVHOl55A7B609Bc7c4c04Ac2885325aFeB98d")
        self.model = model or os.getenv("LLM_MODEL", "gpt-4o-mini")
        self.client = httpx.AsyncClient(timeout=60.0)
    
    async def chat_completion(self, messages: List[Dict[str, str]], model: Optional[str] = None, max_tokens: int = 1000) -> Optional[str]:
        """Make a chat completion request"""
        try:
            payload = {
                "model": model or self.model,
                "messages": messages,
                "max_tokens": max_tokens,
                "temperature": 0.7
            }
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }
            
            response = await self.client.post(
                self.base_url,
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"LLM API error: {response.status_code} - {response.text}")
                return None
        
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            return None
    
    async def analyze_bug(self, issue_title: str, issue_body: str, file_list: List[str]) -> Dict[str, Any]:
        """Analyze a bug report and suggest candidate files"""
        
        prompt = f"""作为一个资深的软件工程师，请分析以下bug报告并识别可能相关的文件。

Issue标题: {issue_title}
Issue描述: {issue_body}

仓库文件列表:
{chr(10).join(f'- {f}' for f in file_list[:50])}  # 限制文件数量避免token超限

请分析：
1. 这个bug可能涉及哪些技术领域或功能模块？
2. 根据文件名和路径，哪些文件最可能包含相关代码？
3. 请按相关性排序，选择最多5个最相关的文件。

请以JSON格式回复：
{{
    "analysis": "bug分析总结",
    "technical_areas": ["涉及的技术领域"],
    "candidate_files": ["按相关性排序的候选文件"],
    "reasoning": "选择这些文件的理由"
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat_completion(messages, max_tokens=800)
        
        if response:
            try:
                # 尝试提取JSON部分
                if "```json" in response:
                    json_part = response.split("```json")[1].split("```")[0].strip()
                elif "{" in response and "}" in response:
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_part = response[start:end]
                else:
                    json_part = response
                
                return json.loads(json_part)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM JSON response: {response}")
                return self._fallback_analysis(issue_title, issue_body, file_list)
        
        return self._fallback_analysis(issue_title, issue_body, file_list)
    
    async def generate_fix_plan(self, issue_title: str, issue_body: str, candidate_files: List[str], 
                               file_contents: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Generate a fix plan for the identified bug"""
        
        file_context = ""
        if file_contents:
            file_context = "\n\n文件内容预览:\n"
            for file, content in file_contents.items():
                # 限制每个文件内容的长度
                preview = content[:500] + "..." if len(content) > 500 else content
                file_context += f"\n=== {file} ===\n{preview}\n"
        
        prompt = f"""作为一个资深的软件工程师，请为以下bug制定修复方案。

Issue标题: {issue_title}
Issue描述: {issue_body}

相关文件: {', '.join(candidate_files)}
{file_context}

请生成一个具体的修复方案，包括：
1. 问题的根本原因分析
2. 具体的修复步骤
3. 需要修改的文件和大致的修改内容
4. 风险评估和注意事项

请以JSON格式回复：
{{
    "root_cause": "问题根本原因",
    "fix_strategy": "修复策略概述", 
    "changes": [
        {{
            "file": "文件路径",
            "type": "modify|create|delete",
            "description": "修改描述",
            "priority": "high|medium|low"
        }}
    ],
    "risks": ["潜在风险"],
    "testing_suggestions": ["测试建议"]
}}"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat_completion(messages, max_tokens=1200)
        
        if response:
            try:
                if "```json" in response:
                    json_part = response.split("```json")[1].split("```")[0].strip()
                elif "{" in response and "}" in response:
                    start = response.find("{")
                    end = response.rfind("}") + 1
                    json_part = response[start:end]
                else:
                    json_part = response
                
                return json.loads(json_part)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse LLM JSON response: {response}")
                return self._fallback_fix_plan(issue_title, candidate_files)
        
        return self._fallback_fix_plan(issue_title, candidate_files)
    
    async def generate_code_fix(self, file_path: str, file_content: str, issue_description: str, fix_plan: str) -> Optional[str]:
        """Generate actual code fix for a specific file"""
        
        prompt = f"""作为一个资深的软件工程师，请对以下文件进行修复。

文件路径: {file_path}
问题描述: {issue_description}
修复方案: {fix_plan}

原始文件内容:
```
{file_content}
```

请提供修复后的完整文件内容。只返回修复后的代码，不要包含其他解释文字。"""

        messages = [{"role": "user", "content": prompt}]
        response = await self.chat_completion(messages, max_tokens=2000)
        
        return response if response else file_content
    
    def _fallback_analysis(self, issue_title: str, issue_body: str, file_list: List[str]) -> Dict[str, Any]:
        """Fallback analysis when LLM fails"""
        # 基于关键词的简单匹配
        keywords = issue_title.lower() + " " + issue_body.lower()
        
        relevant_files = []
        for file in file_list[:20]:  # 只检查前20个文件
            file_lower = file.lower()
            if any(keyword in file_lower for keyword in ['main', 'index', 'app', 'server']):
                relevant_files.append(file)
        
        if not relevant_files and file_list:
            relevant_files = file_list[:3]  # 取前3个文件作为默认
        
        return {
            "analysis": f"基于关键词分析，该问题可能与以下方面相关：{issue_title}",
            "technical_areas": ["代码逻辑", "功能实现"],
            "candidate_files": relevant_files[:5],
            "reasoning": "基于文件名和路径的启发式匹配"
        }
    
    def _fallback_fix_plan(self, issue_title: str, candidate_files: List[str]) -> Dict[str, Any]:
        """Fallback fix plan when LLM fails"""
        return {
            "root_cause": f"需要进一步调查：{issue_title}相关的问题",
            "fix_strategy": "进行代码审查和测试修复", 
            "changes": [
                {
                    "file": candidate_files[0] if candidate_files else "README.md",
                    "type": "modify",
                    "description": "需要详细检查和可能的修复",
                    "priority": "high"
                }
            ],
            "risks": ["需要充分测试"],
            "testing_suggestions": ["单元测试", "集成测试"]
        }
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# 全局LLM客户端实例
_llm_client = None

def get_llm_client() -> LLMClient:
    """Get global LLM client instance"""
    global _llm_client
    if _llm_client is None:
        _llm_client = LLMClient()
    return _llm_client
