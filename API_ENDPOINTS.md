# API Endpoints

## Tools Endpoints

### GET `/tools`
Returns detailed information about all available tools including their schemas and parameters.

**Response:**
```json
{
  "tools": [
    {
      "name": "calculator",
      "description": "Perform mathematical calculations and evaluate expressions safely.",
      "parameters": {
        "type": "object",
        "properties": {
          "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate (e.g., '2 + 3 * 4')"
          }
        },
        "required": ["expression"]
      }
    }
  ]
}
```

### GET `/tools/names`
Returns a simple list of available tool names only.

**Response:**
```json
{
  "tool_names": ["calculator", "file_read", "file_write", "rest_api_request", "get_request", "post_request", "put_request", "patch_request", "delete_request"]
}
```

## Usage Examples

### Python
```python
import requests

# Get all tools with details
response = requests.get("http://localhost:8000/tools")
tools = response.json()["tools"]

# Get just tool names
response = requests.get("http://localhost:8000/tools/names")
tool_names = response.json()["tool_names"]
```

### JavaScript/Fetch
```javascript
// Get tool names
fetch('http://localhost:8000/tools/names')
  .then(response => response.json())
  .then(data => {
    console.log('Available tools:', data.tool_names);
  });
```

## Streamlit Integration

The Streamlit app automatically uses these endpoints to:
1. Display available tools in a multi-select dropdown
2. Show tool descriptions and parameters
3. Provide a dedicated "Available Tools" tab for exploration
4. Enable users to select multiple tools when creating agents

## Tool Selection in Agent Creation

When creating an agent, users can:
- Select multiple tools from a dropdown list
- See tool descriptions and parameters
- View selected tools with their descriptions
- Create agents with or without tools
