#!/usr/bin/env python3
"""
Example script demonstrating the agent completion evaluation system.

This script shows how to create and use agents with acceptance criteria
for automatic completion evaluation.
"""

import json
from typing import Dict, List, Optional


def create_customer_service_agent() -> Dict:
    """Create a customer service agent with completion criteria."""
    return {
        "sessionId": "customer-service-session",
        "system_prompt": "You are a helpful customer service agent. Help customers resolve their issues efficiently and professionally.",
        "acceptance_criteria": {
            "required_information": ["customer_name", "issue_type", "contact_method"],
            "completion_conditions": ["issue_categorized", "next_steps_provided"],
            "success_indicators": ["customer_acknowledged_solution"]
        },
        "tools": ["calculator", "file_read"],
        "llm_provider": "bedrock"
    }


def create_data_collection_agent() -> Dict:
    """Create a data collection agent with completion criteria."""
    return {
        "sessionId": "data-collection-session",
        "system_prompt": "You are a data collection agent. Gather user information systematically and ensure all required fields are collected.",
        "acceptance_criteria": {
            "required_information": ["user_name", "email_address", "phone_number", "preferences"],
            "completion_conditions": ["all_fields_collected", "data_validated"],
            "success_indicators": ["user_confirmed_data"]
        },
        "tools": ["file_write"],
        "llm_provider": "openai"
    }


def create_technical_support_agent() -> Dict:
    """Create a technical support agent with completion criteria."""
    return {
        "sessionId": "tech-support-session",
        "system_prompt": "You are a technical support agent. Help users resolve technical issues by gathering information and providing solutions.",
        "acceptance_criteria": {
            "required_information": ["problem_description", "system_info", "error_messages"],
            "completion_conditions": ["issue_diagnosed", "solution_provided"],
            "success_indicators": ["user_understands_solution"]
        },
        "tools": ["file_read", "rest_api_request", "calculator"],
        "llm_provider": "bedrock"
    }


def simulate_agent_conversation(agent_config: Dict, conversation: List[str]) -> None:
    """Simulate a conversation with an agent that has completion criteria."""
    print(f"\n🤖 {agent_config['system_prompt']}")
    print("=" * 60)
    print(f"📋 Acceptance Criteria:")
    print(f"   Required Information: {agent_config['acceptance_criteria']['required_information']}")
    print(f"   Completion Conditions: {agent_config['acceptance_criteria']['completion_conditions']}")
    print(f"   Success Indicators: {agent_config['acceptance_criteria']['success_indicators']}")
    print(f"🔧 Tools: {agent_config.get('tools', [])}")
    print()
    
    for i, user_message in enumerate(conversation, 1):
        print(f"👤 User: {user_message}")
        
        # Simulate agent response based on conversation progress
        if i == 1:
            agent_response = {
                "agent_output": "Hello! I'm here to help you. What is your name?",
                "system_status": "continue"
            }
        elif i == 2:
            agent_response = {
                "agent_output": f"Thank you {user_message}! What type of issue are you experiencing?",
                "system_status": "continue"
            }
        elif i == 3:
            agent_response = {
                "agent_output": f"I understand you have a {user_message.lower()} issue. What is your preferred contact method for follow-up?",
                "system_status": "continue"
            }
        elif i == 4:
            agent_response = {
                "agent_output": f"Perfect! I have collected your name, issue type, and contact method. I have categorized your {conversation[2].lower()} issue and provided next steps. Please check your email for confirmation. You have acknowledged the solution.",
                "system_status": "complete"
            }
        
        print(f"🤖 Agent: {agent_response['agent_output']}")
        print(f"📊 Status: {agent_response['system_status'].upper()}")
        
        if agent_response['system_status'] == 'complete':
            print("🎉 Agent has completed its objectives!")
            break
        print()


def main():
    """Demonstrate the completion evaluation system with different agent types."""
    print("Agent Completion Evaluation System Demo")
    print("=" * 50)
    
    # Example conversations
    conversations = {
        "Customer Service": [
            "I have a billing issue",
            "John Smith", 
            "billing",
            "email"
        ],
        "Data Collection": [
            "I want to sign up for your service",
            "Jane Doe",
            "jane.doe@email.com", 
            "555-1234"
        ],
        "Technical Support": [
            "My application keeps crashing",
            "Windows 10, Chrome browser",
            "Error: 'Application has stopped responding'",
            "I understand the solution"
        ]
    }
    
    # Create different agent types
    agents = {
        "Customer Service": create_customer_service_agent(),
        "Data Collection": create_data_collection_agent(),
        "Technical Support": create_technical_support_agent()
    }
    
    # Simulate conversations
    for agent_type, conversation in conversations.items():
        agent_config = agents[agent_type]
        simulate_agent_conversation(agent_config, conversation)
    
    print("\n" + "=" * 50)
    print("✨ Demo completed! The completion evaluation system allows agents to:")
    print("   • Automatically assess completion status")
    print("   • Respond in structured JSON format")
    print("   • Track required information collection")
    print("   • Verify completion conditions")
    print("   • Look for success indicators")
    print("\nThis makes agents more reliable and user-friendly!")


if __name__ == "__main__":
    main()
