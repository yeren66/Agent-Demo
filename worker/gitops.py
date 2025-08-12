import os
import asyncio
import logging
import subprocess
from typing import Optional

logger = logging.getLogger(__name__)

class GitOps:
    """Git operations wrapper"""
    
    def __init__(self):
        # Configure git globally for the bot
        self._setup_git_config()
    
    def _setup_git_config(self):
        """Setup git configuration for the bot"""
        try:
            subprocess.run(['git', 'config', '--global', 'user.name', 'Bug Fix Agent'], 
                          check=True, capture_output=True)
            subprocess.run(['git', 'config', '--global', 'user.email', 'agent@example.com'], 
                          check=True, capture_output=True)
            subprocess.run(['git', 'config', '--global', 'init.defaultBranch', 'main'], 
                          check=True, capture_output=True)
        except subprocess.CalledProcessError as e:
            logger.warning(f"Git config setup failed: {e}")
    
    async def clone_repo(self, clone_url: str, destination: str) -> bool:
        """Clone repository"""
        try:
            logger.info(f"Cloning repository to {destination}")
            
            # 支持GitHub和GitCode的认证URL格式
            platform = os.getenv('PLATFORM', 'github').lower()
            if platform == 'github':
                token = os.getenv('GITHUB_TOKEN')
                # GitHub格式: https://token@github.com/owner/repo.git
                auth_url = clone_url.replace('https://github.com', f'https://{token}@github.com')
            else:
                token = os.getenv('GITCODE_TOKEN') 
                # GitCode格式: https://oauth2:token@gitcode.net/owner/repo.git
                auth_url = clone_url.replace('https://gitcode.net', f'https://oauth2:{token}@gitcode.net')
            
            result = await asyncio.create_subprocess_exec(
                'git', 'clone', auth_url, destination,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"Git clone failed: {stderr.decode()}")
                return False
            
            logger.info("Repository cloned successfully")
            return True
            
        except Exception as e:
            logger.error(f"Clone error: {e}")
            return False
    
    async def create_branch(self, repo_path: str, branch_name: str, base_branch: str = 'main') -> bool:
        """Create and checkout new branch"""
        try:
            logger.info(f"Creating branch {branch_name} from {base_branch}")
            
            # Change to repo directory and create branch
            result = await asyncio.create_subprocess_exec(
                'git', 'checkout', '-b', branch_name, f'origin/{base_branch}',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"Branch creation failed: {stderr.decode()}")
                return False
            
            logger.info(f"Branch {branch_name} created successfully")
            return True
            
        except Exception as e:
            logger.error(f"Branch creation error: {e}")
            return False
    
    async def add_file(self, repo_path: str, file_path: str) -> bool:
        """Add file to git"""
        try:
            result = await asyncio.create_subprocess_exec(
                'git', 'add', file_path,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Git add error: {e}")
            return False
    
    async def add_all(self, repo_path: str) -> bool:
        """Add all changes to git"""
        try:
            result = await asyncio.create_subprocess_exec(
                'git', 'add', '.',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            return result.returncode == 0
            
        except Exception as e:
            logger.error(f"Git add all error: {e}")
            return False
    
    async def commit(self, repo_path: str, message: str) -> bool:
        """Commit changes"""
        try:
            result = await asyncio.create_subprocess_exec(
                'git', 'commit', '-m', message,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                # Check if it's just "nothing to commit"
                if "nothing to commit" in stderr.decode().lower():
                    logger.info("Nothing to commit")
                    return True
                logger.error(f"Git commit failed: {stderr.decode()}")
                return False
            
            logger.info(f"Committed: {message}")
            return True
            
        except Exception as e:
            logger.error(f"Git commit error: {e}")
            return False
    
    async def push(self, repo_path: str, branch_name: str) -> bool:
        """Push branch to remote"""
        try:
            logger.info(f"Pushing branch {branch_name}")
            
            result = await asyncio.create_subprocess_exec(
                'git', 'push', '-u', 'origin', branch_name,
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"Git push failed: {stderr.decode()}")
                return False
            
            logger.info(f"Branch {branch_name} pushed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Git push error: {e}")
            return False
    
    async def commit_changes(self, repo_path: str, message: str) -> bool:
        """Add all changes and commit them"""
        try:
            # Add all changes
            success = await self.add_all(repo_path)
            if not success:
                return False
            
            # Commit changes
            return await self.commit(repo_path, message)
            
        except Exception as e:
            logger.error(f"Commit changes error: {e}")
            return False
    
    async def push_branch(self, repo_path: str, branch_name: str) -> bool:
        """Push branch to remote (alias for push method)"""
        return await self.push(repo_path, branch_name)
    
    async def get_changed_files(self, repo_path: str) -> list:
        """Get list of changed files"""
        try:
            result = await asyncio.create_subprocess_exec(
                'git', 'diff', '--name-status', 'HEAD',
                cwd=repo_path,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await result.communicate()
            
            if result.returncode != 0:
                logger.error(f"Git diff failed: {stderr.decode()}")
                return []
            
            # Parse output: "A    filename" or "M    filename"
            changes = []
            for line in stdout.decode().strip().split('\n'):
                if line.strip():
                    parts = line.split('\t')
                    if len(parts) >= 2:
                        status = parts[0]
                        filename = parts[1]
                        changes.append({'status': status, 'file': filename})
            
            return changes
            
        except Exception as e:
            logger.error(f"Get changed files error: {e}")
            return []
    
    async def write_file(self, repo_path: str, file_path: str, content: str) -> bool:
        """Write content to file in repo"""
        try:
            full_path = os.path.join(repo_path, file_path)
            
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Created/updated file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Write file error: {e}")
            return False
    
    async def append_file(self, repo_path: str, file_path: str, content: str) -> bool:
        """Append content to file"""
        try:
            full_path = os.path.join(repo_path, file_path)
            
            with open(full_path, 'a', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"Appended to file: {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Append file error: {e}")
            return False
    
    def file_exists(self, repo_path: str, file_path: str) -> bool:
        """Check if file exists in repo"""
        full_path = os.path.join(repo_path, file_path)
        return os.path.exists(full_path)
    
    def list_files(self, repo_path: str, pattern: str = "*") -> list:
        """List files in repo matching pattern"""
        try:
            import glob
            full_pattern = os.path.join(repo_path, "**", pattern)
            files = glob.glob(full_pattern, recursive=True)
            # Return relative paths
            return [os.path.relpath(f, repo_path) for f in files if os.path.isfile(f)]
        except Exception as e:
            logger.error(f"List files error: {e}")
            return []
