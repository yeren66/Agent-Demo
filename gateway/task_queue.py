import os
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

async def enqueue_task(job: Dict[str, Any]) -> bool:
    """
    Enqueue a job for processing.
    For demo purposes, we'll directly call the worker instead of using a real queue.
    In production, this would use Redis + RQ or similar.
    """
    try:
        # For demo, we'll run the worker directly
        # In production, this would be: redis_queue.enqueue('worker.main.process_job', job)
        
        logger.info(f"Processing job {job['job_id']} directly (demo mode)")
        
        # Import and run worker
        import sys
        sys.path.append(os.path.dirname(os.path.dirname(__file__)))
        
        # Run in background
        asyncio.create_task(run_worker_job(job))
        
        return True
        
    except Exception as e:
        logger.error(f"Error enqueueing job {job.get('job_id')}: {e}")
        return False

async def run_worker_job(job: Dict[str, Any]):
    """Run worker job in background"""
    try:
        # 确保正确的 Python 路径设置
        import sys
        import os
        
        # 获取项目根路径
        current_dir = os.path.dirname(__file__)
        project_root = os.path.dirname(current_dir)
        worker_dir = os.path.join(project_root, 'worker')
        
        # 添加到 Python 路径
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
        if worker_dir not in sys.path:
            sys.path.insert(0, worker_dir)
        
        # 动态导入 worker 模块
        import importlib
        worker_main = importlib.import_module('worker.main')
        
        # 运行处理任务
        await worker_main.process_job(job)
        
    except Exception as e:
        logger.error(f"Worker job failed {job.get('job_id')}: {e}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
