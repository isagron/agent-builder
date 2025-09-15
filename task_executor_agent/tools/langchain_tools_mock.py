"""LangChain tools for task executor communication."""

import logging
from typing import Any, Dict, List, Optional

from langchain.tools import tool

from task_executor_agent.tools.http_client import get_http_client

logger = logging.getLogger(__name__)


@tool
async def find_tasks(action_description: str) -> List[Dict[str, Any]]:
    """
    Search for suitable tasks based on user's action description.
    
    Args:
        action_description: Description of the action to perform
        
    Returns:
        List of task information dictionaries with task_id, task_name, and description
    """
    try:
        
        tasks = []
        tasks.append({
            "task_id": 1,
            "task_name": "Ping remote server",
            "description": "Ping a remote server, receive the server IP address and a threshold number for the number of packets per minute"
        },
        {
            "task_id": 2,
            "task_name": "Run telnet from remote server",
            "description": "Receive the source IP, target IP, target port. Login via SSH to the target IP and run telnet to the target port"
        },
        {
            "task_id": 3,
            "task_name": "Run commands on a network element",
            "description": "Receive the remote network element IP (under the assumption that the network element credentials is known) and list of commands to run. Connect via SSH to the network element and run the list of given commands one by one"
        }
        )
        
        logger.info(f"Found {len(tasks)} tasks for action: {action_description}")
        return tasks
        



@tool
async def get_task_inputs(task_id: str) -> List[Dict[str, Any]]:
    """
    Retrieve input schema for a specific task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        List of input property dictionaries with name, type, description, required, and default_value
    """
    try:
        client = await get_http_client()
        response = await client.get_task_inputs(task_id)
        
        inputs = []
        for input_prop in response.inputs:
            inputs.append({
                "name": input_prop.name,
                "type": input_prop.type.value,
                "description": input_prop.description,
                "required": input_prop.required,
                "default_value": input_prop.default_value
            })
        
        logger.info(f"Retrieved {len(inputs)} inputs for task: {task_id}")
        return inputs
        
    except Exception as e:
        logger.error(f"Failed to get task inputs: {e}")
        return []


@tool
async def get_runtime_variables(context_id: str) -> List[Dict[str, Any]]:
    """
    Fetch available variables from runtime context.
    
    Args:
        context_id: Runtime context identifier
        
    Returns:
        List of variable dictionaries with variable_id, name, type, description, and value
    """
    try:
        client = await get_http_client()
        response = await client.get_runtime_variables(context_id)
        
        variables = []
        for variable in response.variables:
            variables.append({
                "variable_id": variable.variable_id,
                "name": variable.name,
                "type": variable.type.value,
                "description": variable.description,
                "value": variable.value
            })
        
        logger.info(f"Retrieved {len(variables)} variables for context: {context_id}")
        return variables
        
    except Exception as e:
        logger.error(f"Failed to get runtime variables: {e}")
        return []


@tool
async def run_task(
    context_id: str,
    task_id: str,
    input_assignments: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Execute task with mapped input assignments.
    
    Args:
        context_id: Runtime context identifier
        task_id: Task identifier
        input_assignments: Input assignments for the task
        
    Returns:
        Task execution result with success status, result data, and error message
    """
    try:
        client = await get_http_client()
        response = await client.run_task(context_id, task_id, input_assignments)
        
        result = {
            "success": response.success,
            "result": response.result,
            "error_message": response.error_message
        }
        
        if response.success:
            logger.info(f"Successfully executed task: {task_id}")
        else:
            logger.error(f"Task execution failed: {response.error_message}")
        
        return result
        
    except Exception as e:
        logger.error(f"Failed to run task: {e}")
        return {
            "success": False,
            "result": None,
            "error_message": str(e)
        }


def get_all_tools() -> List:
    """
    Get all available tools.
    
    Returns:
        List of tool functions decorated with @tool
    """
    return [
        find_tasks,
        get_task_inputs,
        get_runtime_variables,
        run_task,
    ]
