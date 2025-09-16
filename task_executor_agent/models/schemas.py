"""Pydantic schemas for the task executor agent."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class AgentState(str, Enum):
    """Agent state enumeration."""
    FIND_TASKS = "find_tasks"
    SELECT_TASK = "select_task"
    GET_INPUTS = "get_inputs"
    GET_VARIABLES = "get_variables"
    MAP_INPUTS = "map_inputs"
    EXECUTE_TASK = "execute_task"
    RETURN_RESULT = "return_result"


class AssignmentType(str, Enum):
    """Assignment type enumeration."""
    EXPLICIT = "EXPLICIT"
    VARIABLE_REFERENCE = "VARIABLE_REFERENCE"


class TaskPropertyType(str, Enum):
    """Task property type enumeration."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


class VariableType(str, Enum):
    """Variable type enumeration."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"


# API Request/Response Models
class ExecuteRequest(BaseModel):
    """Request model for task execution."""
    action_description: str = Field(..., description="Description of the action to perform")
    context_id: str = Field(..., description="Runtime context identifier")
    session_id: Optional[str] = Field(default=None, description="Session ID for accessing shared memory")
    timeout: Optional[int] = Field(default=30, description="Execution timeout in seconds")


class ExecuteResponse(BaseModel):
    """Response model for task execution."""
    success: bool = Field(..., description="Whether the execution was successful")
    result: Optional[Any] = Field(default=None, description="Task execution result")
    task_info: Optional[Dict[str, Any]] = Field(default=None, description="Information about the executed task")
    execution_time: float = Field(..., description="Execution time in seconds")
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed")
    mapped_inputs: Optional[Dict[str, Any]] = Field(default=None, description="Inputs that were mapped and used")


class StatusResponse(BaseModel):
    """Response model for agent status."""
    status: str = Field(..., description="Agent status")
    task_executor_url: str = Field(..., description="Task executor server URL")
    current_runtime_context: Optional[str] = Field(default=None, description="Current runtime context")
    uptime: float = Field(..., description="Server uptime in seconds")
    version: str = Field(..., description="Agent version")


# Task Executor Models
class TaskInfo(BaseModel):
    """Task information model."""
    task_id: int  = Field(..., description="Unique task identifier")
    task_name: str = Field(..., description="Human-readable task name")
    description: str = Field(..., description="Task description")


class TaskProperty(BaseModel):
    """Task property definition model."""
    name: str = Field(..., description="Property name")
    type: TaskPropertyType = Field(..., description="Property type")
    description: str = Field(..., description="Property description")
    required: bool = Field(default=False, description="Whether the property is required")
    default_value: Optional[Any] = Field(default=None, description="Default value for the property")


class RuntimeVariable(BaseModel):
    """Runtime variable model."""
    variable_id: str = Field(..., description="Unique variable identifier")
    name: str = Field(..., description="Variable name")
    var_type: str = Field(..., description="Variable type")
    description: str = Field(..., description="Variable description")

class InputAssignment(BaseModel):
    """Input assignment model."""
    value: Any = Field(..., description="Assigned value")
    assignment_type: AssignmentType = Field(..., description="Type of assignment")
    variable_id: Optional[str] = Field(default=None, description="Variable ID if using variable reference")


# Agent State Models
class AgentContext(BaseModel):
    """Agent execution context."""
    action_description: str = Field(..., description="Original action description")
    context_id: str = Field(..., description="Runtime context identifier")
    session_id: Optional[str] = Field(default=None, description="Session ID for accessing shared memory")
    current_state: AgentState = Field(default=AgentState.FIND_TASKS, description="Current agent state")
    available_tasks: List[TaskInfo] = Field(default_factory=list, description="Available tasks")
    selected_task: Optional[TaskInfo] = Field(default=None, description="Selected task")
    task_inputs: List[TaskProperty] = Field(default_factory=list, description="Task input properties")
    runtime_variables: List[RuntimeVariable] = Field(default_factory=list, description="Available runtime variables")
    mapped_inputs: Dict[str, InputAssignment] = Field(default_factory=dict, description="Mapped input assignments")
    execution_result: Optional[Any] = Field(default=None, description="Task execution result")
    error_message: Optional[str] = Field(default=None, description="Error message if any")
    agent_memory: Optional[Dict[str, Any]] = Field(default=None, description="Agent memory for context")
    start_time: datetime = Field(default_factory=datetime.utcnow, description="Execution start time")

# HTTP Tool Models
class FindTasksRequest(BaseModel):
    """Request model for finding tasks."""
    action_description: str = Field(..., description="Action description to search for")


class FindTasksResponse(BaseModel):
    """Response model for finding tasks."""
    tasks: List[TaskInfo] = Field(..., description="List of matching tasks")


class GetTaskInputsResponse(BaseModel):
    """Response model for getting task inputs."""
    inputs: List[TaskProperty] = Field(..., description="Task input properties")


class GetVariablesResponse(BaseModel):
    """Response model for getting runtime variables."""
    variables: List[RuntimeVariable] = Field(..., description="Runtime variables")


class RunTaskRequest(BaseModel):
    """Request model for running a task."""
    context_id: str = Field(..., description="Runtime context identifier")
    task_id: str = Field(..., description="Task identifier")
    input_assignments: Dict[str, InputAssignment] = Field(..., description="Input assignments")


class RunTaskResponse(BaseModel):
    """Response model for running a task."""
    success: bool = Field(..., description="Whether the task execution was successful")
    result: Optional[Any] = Field(default=None, description="Task execution result")
    error_message: Optional[str] = Field(default=None, description="Error message if execution failed")


# Configuration Models
class TaskExecutorConfig(BaseModel):
    """Task executor configuration."""
    base_url: str = Field(..., description="Task executor server base URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    retry_attempts: int = Field(default=3, description="Number of retry attempts")
    retry_delay: float = Field(default=1.0, description="Delay between retries in seconds")


class AgentConfig(BaseModel):
    """Agent configuration."""
    task_executor: TaskExecutorConfig = Field(..., description="Task executor configuration")
    default_context_id: Optional[str] = Field(default=None, description="Default runtime context ID")
    max_execution_time: int = Field(default=300, description="Maximum execution time in seconds")
    enable_logging: bool = Field(default=True, description="Enable detailed logging")
    log_level: str = Field(default="INFO", description="Logging level")
