# Task Executor Agent

A LangGraph-based agent that connects to an existing task executor web server, finds suitable tasks, maps inputs intelligently, and executes tasks automatically.

## Features

- **LangGraph State Machine**: Implements a robust state machine with clear transitions
- **LLM-Based Intelligence**: Uses dedicated LLM agents for task selection and input mapping
- **HTTP API Tools**: Four specialized tools for task executor communication
- **FastAPI Server**: Production-ready API with proper lifespan management
- **Stateless Design**: Supports concurrent requests with different context IDs
- **Comprehensive Error Handling**: Graceful handling of failures at every step
- **Configuration Management**: Environment-based configuration with sensible defaults

## Architecture

### State Machine Flow

```
FIND_TASKS → SELECT_TASK → GET_INPUTS → GET_VARIABLES → MAP_INPUTS → EXECUTE_TASK → RETURN_RESULT
```

1. **FIND_TASKS**: Search for suitable tasks based on user's action description
2. **SELECT_TASK**: Choose the most relevant task from available options
3. **GET_INPUTS**: Retrieve input schema for the selected task
4. **GET_VARIABLES**: Fetch available runtime variables for the context
5. **MAP_INPUTS**: Intelligently map task inputs to runtime variables
6. **EXECUTE_TASK**: Execute the task with mapped input assignments
7. **RETURN_RESULT**: Return the execution result with metadata

### HTTP API Tools

1. **Find Relevant Tasks Tool**: POST to `/api/tasks/search`
2. **Get Task Inputs Tool**: GET from `/api/tasks/{taskId}/inputs`
3. **Get Current Runtime Variables Tool**: GET from `/api/runtime/{contextId}/variables`
4. **Run Task Tool**: POST to `/api/tasks/execute`

## Installation

```bash
# Install dependencies
pip install -e .

# Or install specific dependencies
pip install fastapi uvicorn langgraph langchain httpx tenacity pydantic-settings
```

## Configuration

Create a `.env` file or set environment variables:

```bash
# Task Executor Configuration
TASK_EXECUTOR_URL=http://localhost:8000
TASK_EXECUTOR_TIMEOUT=30
TASK_EXECUTOR_RETRY_ATTEMPTS=3
TASK_EXECUTOR_RETRY_DELAY=1.0

# Agent Configuration
DEFAULT_CONTEXT_ID=default
MAX_EXECUTION_TIME=300

# Logging Configuration
LOG_LEVEL=INFO
ENABLE_LOGGING=true

# Server Configuration
HOST=0.0.0.0
PORT=8001
DEBUG=false
```

## Usage

### Starting the Server

```bash
# Run directly
python -m task_executor_agent.main

# Or with uvicorn
uvicorn task_executor_agent.main:app --host 0.0.0.0 --port 8001
```

### API Endpoints

#### Execute Task

```bash
curl -X POST "http://localhost:8001/api/agent/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "action_description": "Send an email to john@example.com about the project update",
    "context_id": "user-123"
  }'
```

Response:
```json
{
  "success": true,
  "result": {
    "message_id": "msg_123",
    "status": "sent"
  },
  "task_info": {
    "task_id": "send_email",
    "task_name": "Send Email",
    "description": "Send an email to a recipient"
  },
  "execution_time": 2.5,
  "mapped_inputs": {
    "recipient": {
      "value": "john@example.com",
      "assignment_type": "explicit",
      "variable_id": null
    },
    "subject": {
      "value": "Project Update",
      "assignment_type": "variable_reference",
      "variable_id": "var_456"
    }
  }
}
```

#### Get Status

```bash
curl "http://localhost:8001/api/agent/status"
```

Response:
```json
{
  "status": "running",
  "task_executor_url": "http://localhost:8000",
  "current_runtime_context": null,
  "uptime": 3600.5,
  "version": "1.0.0"
}
```

#### Health Check

```bash
curl "http://localhost:8001/health"
```

## LLM-Based Intelligence

The agent uses dedicated LLM agents for intelligent decision-making, with all tools created using the `@tool` annotation decorator for automatic schema generation and type safety:

### Task Selection Agent
- **LLM-based Selection**: Uses natural language understanding to select the most relevant task
- **Context Awareness**: Considers user intent and available task capabilities
- **Reasoning**: Provides clear explanations for task selection decisions
- **Confidence Scoring**: Indicates how certain the selection is
- **Alternative Suggestions**: Offers other potentially suitable tasks
- **Tool Integration**: Uses `@tool` decorated functions for seamless LLM interaction

### Input Mapping Agent
- **Intelligent Mapping**: Uses LLM to map task inputs to runtime variables or explicit values
- **Memory Integration**: Leverages agent memory to find appropriate values
- **Type Compatibility**: Ensures type compatibility between inputs and variables
- **Context Understanding**: Understands the purpose and context of each input
- **Confidence Scoring**: Provides confidence scores for each mapping decision
- **Clear Reasoning**: Explains why each mapping was chosen
- **Alternative Suggestions**: Offers suggestions for unmapped inputs
- **Tool Integration**: Uses `@tool` decorated functions for consistent API interaction

### Tool Creation Best Practices
- **Always Use `@tool` Decorator**: All agent tools must be created using the `@tool` annotation
- **Automatic Schema Generation**: The decorator automatically generates Pydantic schemas from function signatures
- **Type Safety**: Ensures proper type validation and error handling
- **Documentation**: Function docstrings become tool descriptions for the LLM
- **Consistent Interface**: Standardized tool interface across all agents

### Example Tool Implementation

```python
from langchain.tools import tool
from typing import Dict, Any

@tool
def find_tasks(action_description: str) -> Dict[str, Any]:
    """
    Search for suitable tasks based on user's action description.
    
    Args:
        action_description: Description of the action to perform
        
    Returns:
        Dictionary containing list of matching tasks with their details
    """
    # Implementation here
    return {"tasks": [...]}

@tool
def get_task_inputs(task_id: str) -> Dict[str, Any]:
    """
    Retrieve input schema for a specific task.
    
    Args:
        task_id: Task identifier
        
    Returns:
        Dictionary containing task input schema and properties
    """
    # Implementation here
    return {"inputs": [...]}
```

**Benefits of Using `@tool` Decorator:**
- **Automatic Schema**: Pydantic schemas generated from function signatures
- **Type Validation**: Input/output validation handled automatically
- **LLM Integration**: Tools work seamlessly with LangChain agents
- **Documentation**: Docstrings become tool descriptions
- **Error Handling**: Built-in error handling and validation

### Mapping Example

```python
# Task Input
{
  "name": "recipient_email",
  "type": "string",
  "description": "Email address of the recipient",
  "required": true
}

# Runtime Variables
[
  {
    "variable_id": "var_123",
    "name": "email_address",
    "type": "string",
    "description": "User's email address",
    "value": "john@example.com"
  }
]

# Mapping Result
{
  "recipient_email": {
    "value": "john@example.com",
    "assignment_type": "variable_reference",
    "variable_id": "var_123"
  }
}
```

## Error Handling

The agent handles various error scenarios gracefully:

- **Task Executor Unavailable**: Falls back to error response
- **No Tasks Found**: Returns appropriate error message
- **Input Mapping Failures**: Continues with available mappings
- **Task Execution Failures**: Returns detailed error information
- **Network Timeouts**: Implements retry logic with exponential backoff

## Development

### Project Structure

```
task_executor_agent/
├── __init__.py
├── main.py                 # FastAPI application
├── config.py              # Configuration management
├── models/
│   ├── __init__.py
│   └── schemas.py         # Pydantic models
├── tools/
│   ├── __init__.py
│   ├── http_client.py     # HTTP client with retry logic
│   └── langchain_tools.py # LangChain tool wrappers
├── agent/
│   ├── __init__.py
│   ├── task_agent.py           # LangGraph agent implementation
│   ├── task_selection_agent.py # LLM-based task selection
│   └── input_mapping_agent.py  # LLM-based input mapping
└── api/
    ├── __init__.py
    └── endpoints.py       # FastAPI endpoints
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest tests/
```

### Docker Support

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .
RUN pip install -e .

EXPOSE 8001
CMD ["python", "-m", "task_executor_agent.main"]
```

## Production Considerations

- **Concurrency**: The agent is stateless and supports concurrent requests
- **Monitoring**: Includes health checks and status endpoints
- **Logging**: Comprehensive logging with configurable levels
- **Error Recovery**: Graceful handling of partial failures
- **Configuration**: Environment-based configuration for different deployments
- **Security**: CORS configuration and input validation

## License

MIT License - see LICENSE file for details.
