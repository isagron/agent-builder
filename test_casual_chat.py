#!/usr/bin/env python3
"""Test script to verify casual chat works with tools-enabled agents."""

import asyncio
from app.agents.registry import Agent
from app.providers.llm import get_provider


async def test_casual_chat_with_tools():
    """Test that agents with tools can handle casual conversation."""
    print("Testing Casual Chat with Tools")
    print("=" * 40)
    
    # Create agent with tools
    agent = Agent(
        agent_id="casual-agent",
        session_id="test-session",
        system_prompt="You are a friendly and helpful assistant.",
        provider="echo",  # Use echo for testing
        model=None,
        tools=["calculator", "file_read"]  # With tools
    )
    
    print(f"Agent created with tools: {agent.tools}")
    
    # Test casual conversation
    test_messages = [
        "Hi",
        "How are you?",
        "What's your name?",
        "Can you help me?",
        "What is 2 + 3?",  # This should trigger calculator
        "Thanks!"
    ]
    
    provider = get_provider("echo", None)
    agent_executor = provider.create_agent(agent.langchain_tools, agent.system_prompt)
    
    for message in test_messages:
        print(f"\nUser: {message}")
        try:
            result = agent_executor.invoke({"input": message})
            response = result.get('output', 'No output')
            print(f"Agent: {response}")
        except Exception as e:
            print(f"Error: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Casual chat test completed!")


if __name__ == "__main__":
    asyncio.run(test_casual_chat_with_tools())
