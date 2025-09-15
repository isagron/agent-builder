#!/usr/bin/env python3
"""Test script to demonstrate simple chat vs tools-enabled chat."""

import asyncio
from app.agents.registry import Agent
from app.providers.llm import get_provider


async def test_simple_chat():
    """Test simple chat without tools."""
    print("🚀 Testing Simple Chat (No Tools)")
    print("=" * 50)
    
    # Create simple agent
    agent = Agent(
        agent_id="simple-agent",
        session_id="test-session",
        system_prompt="You are a helpful assistant.",
        provider="echo",  # Use echo for testing
        model=None,
        tools=[]  # No tools = simple chat
    )
    
    # Test simple conversation
    print("Agent created with no tools - using simple chat mode")
    print(f"Tools: {agent.tools}")
    print(f"LangChain tools: {len(agent.langchain_tools)}")
    
    # Simulate a simple chat
    provider = get_provider("echo", None)
    response = await provider.generate(
        agent.system_prompt,
        [("user", "Hello, how are you?")],
        agent.model
    )
    
    print(f"Response: {response}")
    print("✅ Simple chat works perfectly!")


async def test_tools_chat():
    """Test chat with tools."""
    print("\n🔧 Testing Tools-Enabled Chat")
    print("=" * 50)
    
    # Create agent with tools
    agent = Agent(
        agent_id="tools-agent",
        session_id="test-session",
        system_prompt="You are a helpful assistant with access to tools.",
        provider="echo",
        model=None,
        tools=["calculator", "file_read"]  # With tools
    )
    
    print("Agent created with tools - using ReAct agent mode")
    print(f"Tools: {agent.tools}")
    print(f"LangChain tools: {len(agent.langchain_tools)}")
    
    # Test tools-enabled chat
    provider = get_provider("echo", None)
    agent_executor = provider.create_agent(agent.langchain_tools, agent.system_prompt)
    
    result = agent_executor.invoke({"input": "What is 2 + 3?"})
    print(f"Response: {result.get('output', 'No output')}")
    print("✅ Tools-enabled chat works!")


async def main():
    """Run both tests."""
    await test_simple_chat()
    await test_tools_chat()
    
    print("\n" + "=" * 50)
    print("🎯 Summary:")
    print("- Simple chat: Fast, reliable, no complexity")
    print("- Tools chat: Powerful, can use external capabilities")
    print("- Choose based on your needs!")


if __name__ == "__main__":
    asyncio.run(main())
