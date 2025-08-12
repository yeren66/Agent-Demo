"""
Deploy Stage - Deploy and provide demo URL (demo version)
"""

import logging
import uuid
from typing import Dict, Any

try:
    from ..templates import render_deploy_info
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    from templates import render_deploy_info

logger = logging.getLogger(__name__)

async def run_deploy_stage(job: Dict[str, Any], repo_path: str, api, gitops) -> Dict[str, Any]:
    """
    Run the deploy stage - deploy to demo environment
    
    In a real implementation, this would:
    - Build the application
    - Deploy to staging/preview environment
    - Run smoke tests
    - Generate preview URLs
    - Set up monitoring
    
    For demo, we'll simulate a deployment and generate a fake preview URL.
    """
    try:
        logger.info("Starting deploy stage (demo mode)")
        
        # Generate demo deployment info
        deploy_id = str(uuid.uuid4())[:8]
        deploy_url = f"https://demo-{deploy_id}.agent-fix.example.com"
        
        # Append deploy info to report
        deploy_info = render_deploy_info(deploy_url)
        await gitops.append_file(repo_path, 'agent/report.txt', deploy_info)
        
        # Commit deploy info
        await gitops.add_file(repo_path, 'agent/report.txt')
        await gitops.commit(repo_path, 'chore(agent): add deployment info (demo)')
        await gitops.push(repo_path, job['branch'])
        
        # Store deployment info in job
        job['deploy_url'] = deploy_url
        job['deploy_id'] = deploy_id
        
        comment = f"""🚀 **部署阶段完成**

**演示环境已部署:**
🔗 **预览地址:** {deploy_url}
📋 **部署ID:** `{deploy_id}`
⏰ **有效期:** 24小时（演示环境）

**部署状态:** ✅ 成功
**环境类型:** Demo/Staging

*(这是模拟的部署环境，用于演示目的)*"""
        
        return {
            'success': True,
            'deploy_url': deploy_url,
            'deploy_id': deploy_id,
            'comment': comment
        }
        
    except Exception as e:
        logger.error(f"Deploy stage failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }
