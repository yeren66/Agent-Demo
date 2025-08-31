from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
import hashlib
import hmac
import json
import os
import logging
from typing import Optional
import re

from handlers.gitcode_handler import GitCodeEventHandler
from security import verify_webhook_signature
from task_queue import enqueue_task

# Setup logging
logging.basicConfig(level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

app = FastAPI(title="Bug Fix Agent Gateway", version="1.0.0")

# Initialize handlers
gitcode_handler = GitCodeEventHandler()

@app.get("/")
async def root():
    return {"status": "healthy", "service": "agent-gateway"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "agent-gateway"}

@app.post("/api/webhook")
async def handle_webhook(request: Request, background_tasks: BackgroundTasks):
    """
    Handle webhook events from GitHub or GitCode
    """
    try:
        # Get headers and body
        headers = dict(request.headers)
        body = await request.body()
        
        # 确定平台类型
        platform = os.getenv('PLATFORM', 'github').lower()
        
        # Verify webhook signature (skip in test mode)
        webhook_secret = os.getenv('WEBHOOK_SECRET')
        test_mode = os.getenv('TEST_MODE', 'false').lower() == 'true'
        
        if webhook_secret and not test_mode:
            if not verify_webhook_signature(headers, body, webhook_secret):
                raise HTTPException(status_code=401, detail="Invalid webhook signature")
        elif test_mode:
            logger.info("TEST_MODE enabled - skipping webhook signature verification")
        
        # Parse event
        try:
            payload = json.loads(body)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON payload")
        
        # 获取事件类型
        if platform == 'github':
            event_type = headers.get('x-github-event', '')
        else:  # gitcode
            event_type = headers.get('x-gitcode-event', '')
            
        logger.info(f"Received {platform} event: {event_type}")
        
        # Check if this is a triggering event
        if gitcode_handler.should_process_event(event_type, payload):
            job = gitcode_handler.create_job(event_type, payload)
            
            if job:
                # Send immediate response to issue
                await gitcode_handler.send_initial_response(job)
                
                # Queue the actual work
                background_tasks.add_task(enqueue_task, job)
                
                logger.info(f"Job queued for repo {job.get('owner')}/{job.get('repo')}, issue #{job.get('issue_number')}")
                return {"status": "accepted", "job_id": job.get("job_id")}
        
        return {"status": "ignored", "reason": "Not a triggering event"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Webhook processing error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# 保持GitCode兼容性
@app.post("/api/gitcode/webhook")
async def handle_gitcode_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitCode webhook events (compatibility)"""
    return await handle_webhook(request, background_tasks)

# GitHub webhook endpoint  
@app.post("/api/github/webhook")
async def handle_github_webhook(request: Request, background_tasks: BackgroundTasks):
    """Handle GitHub webhook events"""
    return await handle_webhook(request, background_tasks)

@app.get("/api/status")
async def get_status():
    """Get service status"""
    return {
        "service": "agent-gateway",
        "status": "running",
        "version": "1.0.0"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
