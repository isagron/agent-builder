#!/usr/bin/env python3
"""Test script to verify the prompt refactoring works correctly."""

from app.providers.llm import get_react_prompt, REACT_PROMPT_FALLBACK
from app.tools.registry import tool_registry


def test_prompt_refactoring():
    """Test that the prompt refactoring works correctly."""
    print("Testing Prompt Refactoring")
    print("=" * 40)
    
    # Test the fallback prompt
    print("1. Testing fallback prompt:")
    fallback_prompt = REACT_PROMPT_FALLBACK
    print(f"   Template length: {len(fallback_prompt.template)} characters")
    print(f"   Has tools placeholder: {'{tools}' in fallback_prompt.template}")
    print(f"   Has input placeholder: {'{input}' in fallback_prompt.template}")
    print(f"   Has agent_scratchpad: {'{agent_scratchpad}' in fallback_prompt.template}")
    
    # Test the get_react_prompt function
    print("\n2. Testing get_react_prompt function:")
    system_prompt = "You are a helpful assistant."
    prompt = get_react_prompt(system_prompt)
    print(f"   System prompt prepended: {system_prompt in prompt.template}")
    print(f"   Template length: {len(prompt.template)} characters")
    
    # Test with different providers
    print("\n3. Testing with different providers:")
    providers = ["echo", "openai", "bedrock"]
    
    for provider_name in providers:
        try:
            provider = get_provider(provider_name, None)
            tools = tool_registry.create_tool_instances(["calculator"])
            agent_executor = provider.create_agent(tools, "Test system prompt")
            print(f"   ✅ {provider_name} provider: Agent created successfully")
        except Exception as e:
            print(f"   ❌ {provider_name} provider: {e}")
    
    print("\n" + "=" * 40)
    print("✅ Prompt refactoring test completed!")


if __name__ == "__main__":
    test_prompt_refactoring()
