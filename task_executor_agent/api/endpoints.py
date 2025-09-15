"""API endpoints for the task executor agent."""

import logging
import time
from datetime import datetime
from typing import Any, Dict

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse

from task_executor_agent.agent.task_agent import TaskExecutionAgent
from task_executor_agent.config import get_settings
from task_executor_agent.models.schemas import (
    ExecuteRequest,
    ExecuteResponse,
    StatusResponse,
)
from task_executor_agent.tools.http_client import get_http_client

logger = logging.getLogger(__name__)

# Global agent instance
_agent: TaskExecutionAgent = None
_start_time = None


def set_agent(agent: TaskExecutionAgent):
    """Set the global agent instance."""
    global _agent, _start_time
    _agent = agent
    _start_time = time.time()
    logger.info("Task execution agent set")


async def get_agent() -> TaskExecutionAgent:
    """
    Get the global agent instance.
    
    Returns:
        Task execution agent instance
        
    Raises:
        HTTPException: If agent is not initialized
    """
    global _agent
    if _agent is None:
        raise HTTPException(
            status_code=503,
            detail="Task Executor Agent not initialized. Please wait for startup to complete."
        )
    return _agent


# Create router
router = APIRouter(prefix="/api/task-executor", tags=["task-executor"])


@router.post("/execute", response_model=ExecuteResponse)
async def execute_task(
    request: ExecuteRequest,
    agent: TaskExecutionAgent = Depends(get_agent)
) -> ExecuteResponse:
    """
    Execute a task based on action description.
    
    Args:
        request: Task execution request
        agent: Task execution agent
        
    Returns:
        Task execution result
        
    Raises:
        HTTPException: If execution fails
    """
    logger.info(f"Received execution request: {request.action_description}")
    
    try:
        # Execute the task
        result = await agent.execute(
            action_description=request.action_description,
            context_id=request.context_id
        )
        
        # Create response
        response = ExecuteResponse(
            success=result.get("success", False),
            result=result.get("result"),
            task_info=result.get("task_info"),
            execution_time=result.get("execution_time", 0),
            error_message=result.get("error_message"),
            mapped_inputs=result.get("mapped_inputs")
        )
        
        logger.info(f"Task execution completed: success={response.success}")
        return response
        
    except Exception as e:
        logger.error(f"Task execution failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Task execution failed: {str(e)}"
        )


@router.get("/status", response_model=StatusResponse)
async def get_status(
    agent: TaskExecutionAgent = Depends(get_agent)
) -> StatusResponse:
    """
    Get agent status and health information.
    
    Args:
        agent: Task execution agent
        
    Returns:
        Agent status information
    """
    global _start_time
    settings = get_settings()
    
    # Check task executor connectivity
    try:
        client = await get_http_client()
        is_healthy = await client.health_check()
        task_executor_status = "healthy" if is_healthy else "unhealthy"
    except Exception as e:
        logger.warning(f"Task executor health check failed: {e}")
        task_executor_status = "unreachable"
    
    # Calculate uptime
    uptime = time.time() - _start_time if _start_time else 0
    
    return StatusResponse(
        status="running",
        task_executor_url=settings.task_executor_url,
        current_runtime_context=None,  # Stateless agent
        uptime=uptime,
        version="1.0.0"
    )


@router.get("/health")
async def health_check() -> Dict[str, Any]:
    """
    Simple health check endpoint.
    
    Returns:
        Health status
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }


@router.get("/tools")
async def list_tools() -> Dict[str, Any]:
    """
    List available tools.
    
    Returns:
        List of available tools
    """
    from task_executor_agent.tools.langchain_tools import find_tasks, get_task_inputs, get_runtime_variables, run_task
    
    tools = [find_tasks, get_task_inputs, get_runtime_variables, run_task]
    
    tools_info = []
    for tool in tools:
        tools_info.append({
            "name": tool.name,
            "description": tool.description,
            "args_schema": tool.args_schema.schema() if hasattr(tool, 'args_schema') else None
        })
    
    return {
        "tools": tools_info,
        "count": len(tools_info)
    }
