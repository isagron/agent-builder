"""HTTP client for task executor communication."""

import asyncio
import logging
from typing import Any, Dict, Optional

import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from task_executor_agent.config import get_settings
from task_executor_agent.models.schemas import (
    FindTasksRequest,
    FindTasksResponse,
    GetTaskInputsResponse,
    GetVariablesResponse,
    RunTaskRequest,
    RunTaskResponse,
    TaskInfo,
    TaskProperty,
    RuntimeVariable,
)

logger = logging.getLogger(__name__)


class TaskExecutorHTTPClient:
    """HTTP client for communicating with the task executor server."""
    
    def __init__(self, base_url: str, timeout: int = 30):
        """
        Initialize the HTTP client.
        
        Args:
            base_url: Base URL of the task executor server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self.timeout)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=10)
    )
    async def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> httpx.Response:
        """
        Make an HTTP request with retry logic.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: Query parameters
            
        Returns:
            HTTP response
            
        Raises:
            httpx.HTTPError: If the request fails after retries
        """
        if not self._client:
            raise RuntimeError("HTTP client not initialized. Use async context manager.")
        
        url = f"{self.base_url}{endpoint}"
        
        try:
            response = await self._client.request(
                method=method,
                url=url,
                json=data,
                params=params
            )
            response.raise_for_status()
            return response
        except httpx.HTTPError as e:
            logger.error(f"HTTP request failed: {method} {url} - {e}")
            raise
    
    async def find_tasks(self, action_description: str) -> FindTasksResponse:
        """
        Find relevant tasks based on action description.
        
        Args:
            action_description: Description of the action to perform
            
        Returns:
            List of matching tasks
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        logger.info(f"Finding tasks for action: {action_description}")
        
        request_data = FindTasksRequest(action_description=action_description)
        response = await self._make_request(
            method="POST",
            endpoint="/api/tasks/search",
            data=request_data.dict()
        )
        
        response_data = response.json()
        return FindTasksResponse(**response_data)
    
    async def get_task_inputs(self, task_id: str) -> GetTaskInputsResponse:
        """
        Get input schema for a specific task.
        
        Args:
            task_id: Task identifier
            
        Returns:
            Task input properties
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        logger.info(f"Getting inputs for task: {task_id}")
        
        response = await self._make_request(
            method="GET",
            endpoint=f"/api/tasks/{task_id}/inputs"
        )
        
        response_data = response.json()
        return GetTaskInputsResponse(**response_data)
    
    async def get_runtime_variables(self, context_id: str) -> GetVariablesResponse:
        """
        Get available runtime variables for a context.
        
        Args:
            context_id: Runtime context identifier
            
        Returns:
            List of runtime variables
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        logger.info(f"Getting runtime variables for context: {context_id}")
        
        response = await self._make_request(
            method="GET",
            endpoint=f"/api/runtime/{context_id}/variables"
        )
        
        response_data = response.json()
        return GetVariablesResponse(**response_data)
    
    async def run_task(
        self,
        context_id: str,
        task_id: str,
        input_assignments: Dict[str, Any]
    ) -> RunTaskResponse:
        """
        Execute a task with input assignments.
        
        Args:
            context_id: Runtime context identifier
            task_id: Task identifier
            input_assignments: Input assignments for the task
            
        Returns:
            Task execution result
            
        Raises:
            httpx.HTTPError: If the request fails
        """
        logger.info(f"Running task {task_id} in context {context_id}")
        
        request_data = RunTaskRequest(
            context_id=context_id,
            task_id=task_id,
            input_assignments=input_assignments
        )
        
        response = await self._make_request(
            method="POST",
            endpoint="/api/tasks/execute",
            data=request_data.dict()
        )
        
        response_data = response.json()
        return RunTaskResponse(**response_data)
    
    async def health_check(self) -> bool:
        """
        Check if the task executor server is healthy.
        
        Returns:
            True if healthy, False otherwise
        """
        try:
            response = await self._make_request(
                method="GET",
                endpoint="/health"
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Global HTTP client instance
_http_client: Optional[TaskExecutorHTTPClient] = None


async def get_http_client() -> TaskExecutorHTTPClient:
    """
    Get the global HTTP client instance.
    
    Returns:
        HTTP client instance
    """
    global _http_client
    if _http_client is None:
        settings = get_settings()
        _http_client = TaskExecutorHTTPClient(
            base_url=settings.task_executor_url,
            timeout=settings.task_executor_timeout
        )
    return _http_client


async def close_http_client():
    """Close the global HTTP client."""
    global _http_client
    if _http_client and _http_client._client:
        await _http_client._client.aclose()
        _http_client = None
