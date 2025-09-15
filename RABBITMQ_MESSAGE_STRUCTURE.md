# RabbitMQ Message Structure Documentation

This document describes the structure and format of RabbitMQ messages sent by the Agent Forge AI system when agents are created.

## Overview

The system automatically sends RabbitMQ messages whenever an agent is created, providing real-time notifications and enabling downstream processing by other services.

## Message Format

### Exchange and Routing
- **Exchange**: `agent_events`
- **Routing Key**: `agent.created`
- **Message Type**: JSON
- **Persistence**: Yes (delivery_mode=2)
- **Content Type**: `application/json`

### Message Structure

```json
{
  "event_type": "agent.created",
  "agent_id": "335150a0-13b0-49ab-aeaf-54c529307e7c",
  "session_id": "1",
  "timestamp": "2025-09-13T19:57:33.542360Z",
  "additional_data": {
    "system_prompt": "you are an assistant specialist",
    "tools": [],
    "has_acceptance_criteria": false,
    "has_output_schema": false,
    "llm_provider": "openai",
    "llm_model": null
  }
}
```

## Field Descriptions

### Top-Level Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `event_type` | string | Yes | Always "agent.created" for agent creation events |
| `agent_id` | string (UUID) | Yes | Unique identifier for the created agent |
| `session_id` | string | Yes | Session identifier where the agent was created |
| `timestamp` | string (ISO 8601) | Yes | UTC timestamp when the agent was created |
| `additional_data` | object | Yes | Additional metadata about the agent configuration |

### Additional Data Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `system_prompt` | string | Yes | The system prompt configured for the agent |
| `tools` | array of strings | Yes | List of tool names enabled for the agent |
| `has_acceptance_criteria` | boolean | Yes | Whether the agent has acceptance criteria configured |
| `has_output_schema` | boolean | Yes | Whether the agent has a JSON output schema configured |
| `llm_provider` | string | Yes | The LLM provider used (e.g., "openai", "bedrock") |
| `llm_model` | string or null | Yes | The specific LLM model used, or null if not specified |

## Example Messages

### Basic Agent Creation

```json
{
  "event_type": "agent.created",
  "agent_id": "335150a0-13b0-49ab-aeaf-54c529307e7c",
  "session_id": "1",
  "timestamp": "2025-09-13T19:57:33.542360Z",
  "additional_data": {
    "system_prompt": "you are an assistant specialist",
    "tools": [],
    "has_acceptance_criteria": false,
    "has_output_schema": false,
    "llm_provider": "openai",
    "llm_model": null
  }
}
```

### Advanced Agent with Tools and Schema

```json
{
  "event_type": "agent.created",
  "agent_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "session_id": "session-123",
  "timestamp": "2025-09-13T20:15:42.123456Z",
  "additional_data": {
    "system_prompt": "You are a problem-understanding specialist. Listen carefully to understand the user's problem.",
    "tools": ["calculator", "file_read", "rest_api_request"],
    "has_acceptance_criteria": true,
    "has_output_schema": true,
    "llm_provider": "bedrock",
    "llm_model": "anthropic.claude-3-sonnet-20240229-v1:0"
  }
}
```

### Agent with Acceptance Criteria

```json
{
  "event_type": "agent.created",
  "agent_id": "f9e8d7c6-b5a4-3210-9876-543210fedcba",
  "session_id": "customer-service-session",
  "timestamp": "2025-09-13T21:30:15.789012Z",
  "additional_data": {
    "system_prompt": "You are a customer service agent. Help customers with their issues and collect required information.",
    "tools": ["file_read"],
    "has_acceptance_criteria": true,
    "has_output_schema": false,
    "llm_provider": "openai",
    "llm_model": "gpt-4"
  }
}
```

## Message Consumption

### Python Consumer Example

```python
import pika
import json
from datetime import datetime

def on_agent_created(ch, method, properties, body):
    """Handle agent created messages."""
    try:
        message = json.loads(body)
        
        # Extract key information
        agent_id = message['agent_id']
        session_id = message['session_id']
        timestamp = message['timestamp']
        additional_data = message['additional_data']
        
        print(f"🎉 New agent created!")
        print(f"   Agent ID: {agent_id}")
        print(f"   Session ID: {session_id}")
        print(f"   Created at: {timestamp}")
        print(f"   Provider: {additional_data['llm_provider']}")
        print(f"   Tools: {additional_data['tools']}")
        
        # Process the message
        process_agent_creation(message)
        
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse message: {e}")
    except KeyError as e:
        print(f"❌ Missing required field: {e}")

def process_agent_creation(message):
    """Process agent creation event."""
    agent_id = message['agent_id']
    session_id = message['session_id']
    additional_data = message['additional_data']
    
    # Log to analytics
    log_agent_creation(agent_id, session_id, additional_data)
    
    # Send notification
    send_agent_creation_notification(agent_id, session_id)
    
    # Update monitoring dashboard
    update_agent_metrics(agent_id, additional_data)

# Set up RabbitMQ consumer
def start_consumer():
    connection = pika.BlockingConnection(
        pika.ConnectionParameters('localhost')
    )
    channel = connection.channel()
    
    # Declare exchange
    channel.exchange_declare(exchange='agent_events', exchange_type='topic')
    
    # Create queue
    result = channel.queue_declare(queue='', exclusive=True)
    queue_name = result.method.queue
    
    # Bind queue to exchange
    channel.queue_bind(
        exchange='agent_events',
        queue=queue_name,
        routing_key='agent.created'
    )
    
    # Set up consumer
    channel.basic_consume(
        queue=queue_name,
        on_message_callback=on_agent_created,
        auto_ack=True
    )
    
    print("🔄 Waiting for agent creation messages...")
    channel.start_consuming()

if __name__ == "__main__":
    start_consumer()
```

### Node.js Consumer Example

```javascript
const amqp = require('amqplib');

async function startConsumer() {
    try {
        const connection = await amqp.connect('amqp://localhost');
        const channel = await connection.createChannel();
        
        // Declare exchange
        await channel.assertExchange('agent_events', 'topic', { durable: true });
        
        // Create queue
        const { queue } = await channel.assertQueue('', { exclusive: true });
        
        // Bind queue to exchange
        await channel.bindQueue(queue, 'agent_events', 'agent.created');
        
        // Set up consumer
        await channel.consume(queue, (msg) => {
            if (msg) {
                const message = JSON.parse(msg.content.toString());
                
                console.log('🎉 New agent created!');
                console.log(`   Agent ID: ${message.agent_id}`);
                console.log(`   Session ID: ${message.session_id}`);
                console.log(`   Created at: ${message.timestamp}`);
                console.log(`   Provider: ${message.additional_data.llm_provider}`);
                console.log(`   Tools: ${message.additional_data.tools.join(', ')}`);
                
                // Process the message
                processAgentCreation(message);
            }
        }, { noAck: true });
        
        console.log('🔄 Waiting for agent creation messages...');
        
    } catch (error) {
        console.error('❌ Consumer error:', error);
    }
}

function processAgentCreation(message) {
    const { agent_id, session_id, additional_data } = message;
    
    // Log to analytics
    logAgentCreation(agent_id, session_id, additional_data);
    
    // Send notification
    sendAgentCreationNotification(agent_id, session_id);
    
    // Update monitoring dashboard
    updateAgentMetrics(agent_id, additional_data);
}

startConsumer();
```

## Use Cases

### 1. Analytics and Monitoring
- Track agent creation patterns and trends
- Monitor system usage and performance
- Generate reports on agent configurations

### 2. Notifications
- Send real-time notifications when agents are created
- Alert administrators about system activity
- Notify users about their agent status

### 3. Logging and Auditing
- Centralized logging of all agent creation events
- Audit trail for compliance and security
- Debugging and troubleshooting support

### 4. Integration with External Systems
- Update external databases with agent information
- Sync with CRM or other business systems
- Trigger workflows in other applications

## Configuration

### Environment Variables

```bash
# RabbitMQ Connection
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
RABBITMQ_VHOST=/

# Optional: Custom exchange and routing key
RABBITMQ_EXCHANGE=agent_events
RABBITMQ_ROUTING_KEY=agent.created
```

### Docker Setup

```bash
# Start RabbitMQ with management UI
docker run -d --name rabbitmq \
  -p 5672:5672 \
  -p 15672:15672 \
  rabbitmq:3-management

# Access management UI at http://localhost:15672
# Default credentials: guest/guest
```

## Error Handling

The system includes robust error handling:

- **Connection Failures**: Graceful fallback if RabbitMQ is unavailable
- **Message Parsing**: Validation of message structure
- **Retry Logic**: Automatic retry for transient failures
- **Logging**: Comprehensive logging of all errors

## Security Considerations

- **Authentication**: Use proper RabbitMQ credentials
- **Network Security**: Secure network connections
- **Message Encryption**: Consider encrypting sensitive data
- **Access Control**: Limit access to RabbitMQ management

## Troubleshooting

### Common Issues

1. **Connection Refused**: Check RabbitMQ is running and accessible
2. **Authentication Failed**: Verify credentials and permissions
3. **Message Not Received**: Check exchange and routing key configuration
4. **Parsing Errors**: Validate message format and required fields

### Debugging

Enable debug logging to troubleshoot issues:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Version History

- **v1.0.0**: Initial implementation with basic agent creation messages
- **v1.1.0**: Added additional_data field with rich metadata
- **v1.2.0**: Added support for acceptance criteria and output schema flags

---

For more information about the Agent Forge AI system, see the main README.md file.
