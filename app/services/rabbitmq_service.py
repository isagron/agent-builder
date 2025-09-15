"""RabbitMQ service for sending agent creation messages."""

import json
import logging
from typing import Dict, Optional

import pika

logger = logging.getLogger(__name__)


class RabbitMQService:
    """Service for sending messages via RabbitMQ."""
    
    def __init__(
        self,
        host: str = "localhost",
        port: int = 5672,
        username: str = "guest",
        password: str = "guest",
        virtual_host: str = "/",
        exchange_name: str = "agent_events",
        routing_key: str = "agent.created"
    ):
        """
        Initialize RabbitMQ service.
        
        Args:
            host: RabbitMQ host
            port: RabbitMQ port
            username: RabbitMQ username
            password: RabbitMQ password
            virtual_host: RabbitMQ virtual host
            exchange_name: Exchange name for agent events
            routing_key: Routing key for agent creation events
        """
        self.host = host
        self.port = port
        self.username = username
        self.password = password
        self.virtual_host = virtual_host
        self.exchange_name = exchange_name
        self.routing_key = routing_key
        self._connection = None
        self._channel = None
    
    def _get_connection(self) -> pika.BlockingConnection:
        """Get or create RabbitMQ connection."""
        if self._connection is None or self._connection.is_closed:
            credentials = pika.PlainCredentials(self.username, self.password)
            parameters = pika.ConnectionParameters(
                host=self.host,
                port=self.port,
                virtual_host=self.virtual_host,
                credentials=credentials
            )
            self._connection = pika.BlockingConnection(parameters)
        return self._connection
    
    def _get_channel(self):
        """Get or create RabbitMQ channel."""
        if self._channel is None or self._channel.is_closed:
            connection = self._get_connection()
            self._channel = connection.channel()
            # Declare exchange
            self._channel.exchange_declare(
                exchange=self.exchange_name,
                exchange_type="topic",
                durable=True
            )
        return self._channel
    
    def send_agent_created_message(
        self,
        agent_id: str,
        session_id: str,
        additional_data: Optional[Dict] = None
    ) -> bool:
        """
        Send agent created message via RabbitMQ.
        
        Args:
            agent_id: The created agent's ID
            session_id: The session ID
            additional_data: Additional data to include in the message
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            channel = self._get_channel()
            
            # Prepare message payload
            message = {
                "event_type": "agent.created",
                "agent_id": agent_id,
                "session_id": session_id,
                "timestamp": self._get_timestamp(),
                "additional_data": additional_data or {}
            }
            
            # Convert to JSON
            message_json = json.dumps(message, indent=2)
            
            # Publish message
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=self.routing_key,
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json"
                )
            )
            
            logger.info(f"Agent created message sent: agent_id={agent_id}, session_id={session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send agent created message: {e}")
            return False
    
    def send_agent_deleted_message(
        self,
        agent_id: str,
        session_id: str,
        additional_data: Optional[Dict] = None
    ) -> bool:
        """
        Send agent deleted message via RabbitMQ.
        
        Args:
            agent_id: The deleted agent's ID
            session_id: The session ID
            additional_data: Additional data to include in the message
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            channel = self._get_channel()
            
            # Prepare message payload
            message = {
                "event_type": "agent.deleted",
                "agent_id": agent_id,
                "session_id": session_id,
                "timestamp": self._get_timestamp(),
                "additional_data": additional_data or {}
            }
            
            # Convert to JSON
            message_json = json.dumps(message, indent=2)
            
            # Publish message
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key="agent.deleted",  # Different routing key for deletion
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json"
                )
            )
            
            logger.info(f"Agent deleted message sent: agent_id={agent_id}, session_id={session_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send agent deleted message: {e}")
            return False
    
    def close(self) -> None:
        """Close RabbitMQ connection and channel."""
        try:
            if self._channel and not self._channel.is_closed:
                self._channel.close()
            if self._connection and not self._connection.is_closed:
                self._connection.close()
        except Exception as e:
            logger.error(f"Error closing RabbitMQ connection: {e}")
    
    def send_task_progress_message(
        self,
        context_id: str,
        event_type: str,
        current_state: str,
        progress_data: Optional[Dict] = None
    ) -> bool:
        """
        Send task execution progress message via RabbitMQ.
        
        Args:
            context_id: The task execution context ID
            event_type: Type of progress event (e.g., 'task.started', 'task.completed')
            current_state: Current execution state
            progress_data: Additional progress data
            
        Returns:
            True if message sent successfully, False otherwise
        """
        try:
            channel = self._get_channel()
            
            # Prepare message payload
            message = {
                "event_type": event_type,
                "context_id": context_id,
                "current_state": current_state,
                "timestamp": self._get_timestamp(),
                "progress_data": progress_data or {},
                "message": progress_data.get("message", f"Task progress: {event_type}") if progress_data else f"Task progress: {event_type}"
            }
            
            # Convert to JSON
            message_json = json.dumps(message, indent=2)
            
            # Publish message with task-specific routing key
            routing_key = f"task.{event_type.split('.')[-1]}"  # e.g., "task.started", "task.completed"
            channel.basic_publish(
                exchange=self.exchange_name,
                routing_key=routing_key,
                body=message_json,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # Make message persistent
                    content_type="application/json"
                )
            )
            
            logger.info(f"Task progress message sent: {event_type} for context {context_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send task progress message: {e}")
            return False
    
    def _get_timestamp(self) -> str:
        """Get current timestamp in ISO format."""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"


# Global RabbitMQ service instance
rabbitmq_service: Optional[RabbitMQService] = None


def get_rabbitmq_service() -> Optional[RabbitMQService]:
    """Get the global RabbitMQ service instance."""
    return rabbitmq_service


def initialize_rabbitmq_service(
    host: str = "localhost",
    port: int = 5672,
    username: str = "guest",
    password: str = "guest",
    virtual_host: str = "/",
    exchange_name: str = "agent_events",
    routing_key: str = "agent.created"
) -> RabbitMQService:
    """
    Initialize the global RabbitMQ service.
    
    Args:
        host: RabbitMQ host
        port: RabbitMQ port
        username: RabbitMQ username
        password: RabbitMQ password
        virtual_host: RabbitMQ virtual host
        exchange_name: Exchange name for agent events
        routing_key: Routing key for agent creation events
        
    Returns:
        Initialized RabbitMQ service
    """
    global rabbitmq_service
    rabbitmq_service = RabbitMQService(
        host=host,
        port=port,
        username=username,
        password=password,
        virtual_host=virtual_host,
        exchange_name=exchange_name,
        routing_key=routing_key
    )
    return rabbitmq_service


def send_agent_created_message(
    agent_id: str,
    session_id: str,
    additional_data: Optional[Dict] = None
) -> bool:
    """
    Send agent created message using the global RabbitMQ service.
    
    Args:
        agent_id: The created agent's ID
        session_id: The session ID
        additional_data: Additional data to include in the message
        
    Returns:
        True if message sent successfully, False otherwise
    """
    service = get_rabbitmq_service()
    if service is None:
        logger.warning("RabbitMQ service not initialized, skipping message")
        return False
    
    return service.send_agent_created_message(agent_id, session_id, additional_data)


def send_task_progress_message(
    context_id: str,
    event_type: str,
    current_state: str,
    progress_data: Optional[Dict] = None
) -> bool:
    """
    Send task execution progress message using the global RabbitMQ service.
    
    Args:
        context_id: The task execution context ID
        event_type: Type of progress event (e.g., 'task.started', 'task.completed')
        current_state: Current execution state
        progress_data: Additional progress data
        
    Returns:
        True if message sent successfully, False otherwise
    """
    service = get_rabbitmq_service()
    if service is None:
        logger.warning("RabbitMQ service not initialized, skipping task progress message")
        return False
    
    return service.send_task_progress_message(context_id, event_type, current_state, progress_data)
