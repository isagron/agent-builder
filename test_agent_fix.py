#!/usr/bin/env python3
"""Test script to verify the agent fix works."""

import asyncio
from app.tools.registry import tool_registry
from app.providers.llm import get_provider


def test_agent_creation():
    """Test that agents can be created without the agent_scratchpad error."""
    print("Testing agent creation...")
    
    # Get some tools
    tools = tool_registry.create_tool_instances(["calculator", "file_read"])
    print(f"Created {len(tools)} tools: {[tool.name for tool in tools]}")
    
    # Test with different providers
    providers = ["echo", "openai", "bedrock"]
    
    for provider_name in providers:
        try:
            print(f"\nTesting {provider_name} provider...")
            provider = get_provider(provider_name, None)
            
            # Create agent
            agent_executor = provider.create_agent(tools, "You are a helpful assistant.")
            print(f"✅ {provider_name} agent created successfully")
            
            # Test running the agent
            result = agent_executor.invoke({"input": "What is 2 + 3?"})
            print(f"Agent response: {result.get('output', 'No output')[:100]}...")
            
        except Exception as e:
            print(f"❌ {provider_name} provider failed: {e}")


if __name__ == "__main__":
    test_agent_creation()
