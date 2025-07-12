"""FastAPI webhook server for Code Researcher."""

import os
import json
import yaml
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn

from ..core.code_researcher_system import CodeResearcherSystem

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Pydantic models for request/response
class CloudWatchWebhookRequest(BaseModel):
    """CloudWatch webhook request model."""
    Type: Optional[str] = None
    MessageId: Optional[str] = None
    TopicArn: Optional[str] = None
    Subject: Optional[str] = None
    Message: Optional[str] = None
    Timestamp: Optional[str] = None
    SignatureVersion: Optional[str] = None
    Signature: Optional[str] = None
    SigningCertURL: Optional[str] = None
    UnsubscribeURL: Optional[str] = None

class JobStatusResponse(BaseModel):
    """Job status response model."""
    job_id: str
    status: str
    alert: Dict[str, Any]
    repositories_configured: int
    pull_requests_created: int
    error_message: Optional[str] = None
    has_orchestrator_response: bool
    created_at: Optional[str] = None
    completed_at: Optional[str] = None

class HealthResponse(BaseModel):
    """Health check response model."""
    status: str
    timestamp: str
    version: str
    active_jobs: int

# Global system instance
code_researcher_system: Optional[CodeResearcherSystem] = None

def load_config() -> Dict[str, Any]:
    """Load configuration from file."""
    config_path = os.environ.get('CONFIG_PATH', 'config/config.yaml')
    
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except FileNotFoundError:
        logger.error(f"Configuration file not found: {config_path}")
        raise
    except yaml.YAMLError as e:
        logger.error(f"Error parsing configuration file: {e}")
        raise

def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Code Researcher",
        description="AI-powered automated bug investigation and fix platform",
        version="0.1.0"
    )
    
    return app

# Create FastAPI app
app = create_app()

@app.on_event("startup")
async def startup_event():
    """Initialize the system on startup."""
    global code_researcher_system
    
    try:
        config = load_config()
        code_researcher_system = CodeResearcherSystem(config)
        logger.info("Code Researcher system initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Code Researcher system: {e}")
        raise

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    if not code_researcher_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    active_jobs = len(code_researcher_system.active_jobs)
    
    return HealthResponse(
        status="healthy",
        timestamp=datetime.now().isoformat(),
        version="0.1.0",
        active_jobs=active_jobs
    )

@app.post("/webhook/cloudwatch")
async def cloudwatch_webhook(
    request: CloudWatchWebhookRequest,
    background_tasks: BackgroundTasks,
    raw_request: Request
):
    """Handle CloudWatch webhook notifications."""
    if not code_researcher_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Log the incoming request
        logger.info(f"Received CloudWatch webhook: {request.Type}")
        
        # Handle SNS subscription confirmation
        if request.Type == "SubscriptionConfirmation":
            logger.info("SNS subscription confirmation received")
            # In a production system, you would confirm the subscription
            return {"message": "Subscription confirmation received"}
        
        # Handle SNS notifications
        if request.Type == "Notification":
            # Parse the SNS message
            alert_data = request.dict()
            
            # Process the alert in the background
            background_tasks.add_task(process_alert_background, alert_data)
            
            return {
                "message": "Alert received and queued for processing",
                "timestamp": datetime.now().isoformat()
            }
        
        # Handle other message types
        logger.warning(f"Unknown message type: {request.Type}")
        return {"message": "Message type not supported"}
        
    except Exception as e:
        logger.error(f"Error processing CloudWatch webhook: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Get status of a research job."""
    if not code_researcher_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    job_status = code_researcher_system.get_job_status(job_id)
    
    if not job_status:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JobStatusResponse(**job_status)

@app.get("/jobs")
async def list_jobs():
    """List all active jobs."""
    if not code_researcher_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    jobs = code_researcher_system.list_active_jobs()
    return {"jobs": jobs, "count": len(jobs)}

@app.post("/test/alert")
async def test_alert(alert_data: Dict[str, Any], background_tasks: BackgroundTasks):
    """Test endpoint for manual alert processing."""
    if not code_researcher_system:
        raise HTTPException(status_code=503, detail="System not initialized")
    
    try:
        # Process the test alert
        background_tasks.add_task(process_alert_background, alert_data)
        
        return {
            "message": "Test alert queued for processing",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error processing test alert: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def process_alert_background(alert_data: Dict[str, Any]):
    """Background task to process alerts."""
    try:
        logger.info("Processing alert in background")
        job_id = await code_researcher_system.process_alert(alert_data)
        
        if job_id:
            logger.info(f"Alert processing started with job ID: {job_id}")
        else:
            logger.info("Alert was skipped (validation failed)")
            
    except Exception as e:
        logger.error(f"Error in background alert processing: {e}")

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "timestamp": datetime.now().isoformat()}
    )

def main():
    """Main entry point for the webhook server."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Code Researcher Webhook Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind to")
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload")
    parser.add_argument("--config", help="Path to configuration file")
    
    args = parser.parse_args()
    
    # Set config path if provided
    if args.config:
        os.environ['CONFIG_PATH'] = args.config
    
    # Run the server
    uvicorn.run(
        "src.api.webhook_server:app",
        host=args.host,
        port=args.port,
        reload=args.reload,
        log_level="info"
    )

if __name__ == "__main__":
    main()
