# Agent Completion Evaluation System

This system allows agents to automatically evaluate whether they have completed their objectives using user-defined acceptance criteria and respond in a structured format.

## Core Features

- **Structured Acceptance Criteria**: Define required information, completion conditions, and success indicators
- **Automatic Evaluation**: Agents automatically assess completion status based on criteria
- **Structured Response Format**: Consistent JSON response format with agent output and system status
- **Flexible Parsing**: Robust response parsing with fallback mechanisms

## Response Format

Agents with acceptance criteria respond in this format:

```json
{
  "agent_output": "[original response]",
  "system_status": "continue" or "complete"
}
```

## Usage Examples

### 1. Customer Service Agent

```python
from app.models.schemas import AcceptanceCriteria, CreateAgentRequest

# Define acceptance criteria
criteria = AcceptanceCriteria(
    required_information=["customer_name", "issue_type", "contact_method"],
    completion_conditions=["issue_categorized", "next_steps_provided"],
    success_indicators=["customer_acknowledged_solution"]
)

# Create agent with criteria
agent_request = CreateAgentRequest(
    sessionId="session-123",
    system_prompt="You are a customer service agent. Help customers with their issues.",
    acceptance_criteria=criteria,
    tools=["calculator"]
)
```

### 2. Data Collection Agent

```python
criteria = AcceptanceCriteria(
    required_information=["user_name", "email_address", "phone_number", "preferences"],
    completion_conditions=["all_fields_collected", "data_validated"],
    success_indicators=["user_confirmed_data"]
)

agent_request = CreateAgentRequest(
    sessionId="session-456",
    system_prompt="You are a data collection agent. Gather user information for our database.",
    acceptance_criteria=criteria
)
```

### 3. Technical Support Agent

```python
criteria = AcceptanceCriteria(
    required_information=["problem_description", "system_info", "error_messages"],
    completion_conditions=["issue_diagnosed", "solution_provided"],
    success_indicators=["user_understands_solution"]
)

agent_request = CreateAgentRequest(
    sessionId="session-789",
    system_prompt="You are a technical support agent. Help users resolve technical issues.",
    acceptance_criteria=criteria,
    tools=["file_read", "rest_api_request"]
)
```

## How It Works

### 1. Criteria Injection with PydanticOutputParser

When an agent is created with acceptance criteria, the system automatically injects evaluation logic and format instructions into the system prompt using LangChain's `PydanticOutputParser`:

```
ACCEPTANCE CRITERIA FOR COMPLETION:
REQUIRED INFORMATION TO COLLECT:
- customer_name
- issue_type
- contact_method

COMPLETION CONDITIONS:
- issue_categorized
- next_steps_provided

SUCCESS INDICATORS:
- customer_acknowledged_solution

COMPLETION EVALUATION:
Before responding, evaluate if you should set status to "complete":
- Check if you've collected all required information
- Verify these completion conditions are met
- Look for these success indicators

RESPONSE FORMAT:
You MUST respond in this exact JSON format:
{
  "agent_output": "[your response to the user]",
  "system_status": "complete" if all criteria are met, otherwise "continue"
}
```

### 2. Response Parsing with PydanticOutputParser

The system parses agent responses using LangChain's `PydanticOutputParser` with robust fallback strategies:

1. **PydanticOutputParser**: Primary parsing with built-in validation and type checking
2. **JSON Parsing**: Fallback for malformed responses
3. **Pattern Matching**: Additional fallback for edge cases
4. **Default Fallback**: Returns original response with "continue" status

### 3. Completion Evaluation

The system evaluates completion using:

- **Required Information**: Checks if all specified information has been collected
- **Completion Conditions**: Verifies that all conditions are met
- **Success Indicators**: Looks for positive completion signals

## API Integration

### Creating an Agent with Criteria

```python
POST /create-agent
{
  "sessionId": "session-123",
  "system_prompt": "You are a helpful assistant...",
  "acceptance_criteria": {
    "required_information": ["field1", "field2"],
    "completion_conditions": ["condition1", "condition2"],
    "success_indicators": ["indicator1", "indicator2"]
  },
  "tools": ["calculator", "file_read"]
}
```

### Chat Response Format

```python
POST /chat
{
  "sessionId": "session-123",
  "agentId": "agent-456",
  "user_message": "I need help with my account"
}

# Response
{
  "agent_response": "I'd be happy to help with your account. What is your name?",
  "system_status": "continue"
}
```

## Best Practices

### 1. Define Clear Criteria

- Use specific, measurable criteria
- Avoid ambiguous terms
- Include both objective and subjective indicators

### 2. Test Your Criteria

- Test with sample conversations
- Verify completion detection works correctly
- Adjust criteria based on real usage

### 3. Leverage PydanticOutputParser Benefits

- **Automatic Validation**: Built-in type checking and field validation
- **Format Instructions**: Automatic generation of clear format instructions for LLMs
- **Error Handling**: Robust parsing with multiple fallback strategies
- **Type Safety**: Ensures consistent data structure across all responses

### 4. Handle Edge Cases

- PydanticOutputParser provides built-in fallback mechanisms
- Handles malformed responses gracefully
- Consider partial completion scenarios

### 5. Monitor Performance

- Track completion rates
- Analyze common failure patterns
- Iterate on criteria based on data

## Advanced Features

### PydanticOutputParser Integration

The system uses LangChain's `PydanticOutputParser` for robust response parsing:

```python
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    agent_output: str = Field(description="The agent's response to the user")
    system_status: str = Field(description="Either 'continue' or 'complete' based on acceptance criteria")

# Automatic format instruction generation
parser = PydanticOutputParser(pydantic_object=AgentResponse)
format_instructions = parser.get_format_instructions()
```

**Benefits:**
- **Automatic Validation**: Built-in type checking and field validation
- **Format Instructions**: Generates clear instructions for LLMs automatically
- **Error Handling**: Robust parsing with multiple fallback strategies
- **Type Safety**: Ensures consistent data structure
- **LangChain Integration**: Consistent with LangChain ecosystem

### Custom Evaluation Logic

You can extend the completion evaluation by modifying the `evaluate_completion_status` function in `app/services/completion_evaluation.py`.

### Multiple Criteria Types

The system supports different types of criteria:

- **Required Information**: Data that must be collected
- **Completion Conditions**: Actions that must be completed
- **Success Indicators**: Signs that objectives are achieved

### Integration with Tools

Agents can use tools while still maintaining completion evaluation:

```python
agent_request = CreateAgentRequest(
    sessionId="session-123",
    system_prompt="You are a research assistant...",
    acceptance_criteria=criteria,
    tools=["web_search", "file_write", "calculator"]
)
```

## Troubleshooting

### Common Issues

1. **Agent not returning structured format**: Check if acceptance criteria are properly defined
2. **Completion not detected**: Verify criteria are realistic and test with sample data
3. **Parsing errors**: Ensure response format matches expected structure

### Debug Mode

Enable debug logging to see detailed evaluation process:

```python
# The system automatically logs evaluation steps when criteria are defined
```

## Examples in Action

### Customer Service Scenario

```
User: "I have a billing issue"
Agent: {"agent_output": "I'd be happy to help with your billing issue. What is your name?", "system_status": "continue"}

User: "John Smith"
Agent: {"agent_output": "Thank you John! What type of billing issue are you experiencing?", "system_status": "continue"}

User: "I was charged twice for the same service"
Agent: {"agent_output": "I understand you were double-charged. What is your preferred contact method for follow-up?", "system_status": "continue"}

User: "Email"
Agent: {"agent_output": "Thank you John! I have categorized your double-charging issue and provided next steps. Please check your email for confirmation. I have collected your customer name, issue type, and contact method. The issue has been categorized and next steps provided. You have acknowledged the solution.", "system_status": "complete"}
```

This system provides a robust framework for creating agents that can automatically determine when they've completed their objectives, making them more reliable and user-friendly.
