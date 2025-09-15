#!/usr/bin/env python3
"""Test single-shot agent behavior - agents without acceptance criteria complete after first response."""

import json
from typing import Dict, Any

# Mock the langchain import for testing
import sys
sys.modules['langchain'] = type('MockLangChain', (), {})()
sys.modules['langchain.output_parsers'] = type('MockOutputParsers', (), {})()

# Create a mock PydanticOutputParser
class MockPydanticOutputParser:
    def __init__(self, pydantic_object):
        self.pydantic_object = pydantic_object
    
    def parse(self, text: str):
        """Mock parse method that tries to extract JSON."""
        try:
            import re
            json_match = re.search(r'\{[^}]*\}', text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                data = json.loads(json_str)
                return self.pydantic_object(**data)
            else:
                raise ValueError("No valid JSON found")
        except Exception as e:
            raise ValueError(f"Failed to parse: {e}")
    
    def get_format_instructions(self) -> str:
        """Mock format instructions."""
        return """
The output should be formatted as a JSON instance that conforms to the JSON schema below.

Here is the output schema:
```
{"properties": {"agent_output": {"title": "Agent Output", "description": "The agent's response to the user", "type": "string"}, "system_status": {"title": "System Status", "description": "Either 'continue' or 'complete' based on acceptance criteria", "type": "string"}}, "required": ["agent_output", "system_status"]}
```"""

# Mock the PydanticOutputParser
sys.modules['langchain.output_parsers'].PydanticOutputParser = MockPydanticOutputParser

# Mock Pydantic
class MockBaseModel:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
    
    def model_dump_json(self):
        return json.dumps(self.__dict__)

class MockField:
    def __init__(self, description="", default=...):
        self.description = description
        self.default = default

def create_model(name, **fields):
    return type(name, (MockBaseModel,), fields)

sys.modules['pydantic'] = type('MockPydantic', (), {
    'BaseModel': MockBaseModel,
    'Field': MockField,
    'create_model': create_model
})()

# Now import our completion evaluation service
from app.services.completion_evaluation import (
    inject_acceptance_criteria,
    parse_agent_response_with_schema_and_completion
)


def test_single_shot_agent_behavior():
    """Test that agents without acceptance criteria complete after first response."""
    print("Single-Shot Agent Behavior Test")
    print("=" * 40)
    
    # Test 1: Agent without acceptance criteria
    print("\n🧪 Test 1: Agent without acceptance criteria")
    print("-" * 50)
    
    base_prompt = "You are a helpful assistant that answers questions."
    enhanced_prompt = inject_acceptance_criteria(base_prompt, None, None)
    
    print("Enhanced prompt for single-shot agent:")
    print(enhanced_prompt)
    
    # Simulate agent response
    agent_response = "I understand you need help with Python programming. Here's a comprehensive guide to get you started..."
    
    # Parse the response
    agent_output, system_status, schema_success = parse_agent_response_with_schema_and_completion(
        agent_response,
        None,  # No output schema
        None,  # No acceptance criteria
        []     # No conversation history
    )
    
    print(f"\nAgent Response: {agent_output}")
    print(f"System Status: {system_status}")
    print(f"Schema Success: {schema_success}")
    
    # Verify single-shot behavior
    assert system_status == "complete", f"Expected 'complete', got '{system_status}'"
    print("✅ Single-shot agent correctly returns 'complete' status")
    
    # Test 2: Agent with acceptance criteria (should continue)
    print("\n🧪 Test 2: Agent with acceptance criteria")
    print("-" * 50)
    
    from app.models.schemas import AcceptanceCriteria
    
    acceptance_criteria = AcceptanceCriteria(
        required_information=["problem_description", "user_context"],
        completion_conditions=["problem_understood"],
        success_indicators=["user_confirms_understanding"]
    )
    
    enhanced_prompt_with_criteria = inject_acceptance_criteria(base_prompt, acceptance_criteria, None)
    
    print("Enhanced prompt for agent with acceptance criteria:")
    print(enhanced_prompt_with_criteria[:200] + "...")
    
    # Simulate agent response
    agent_response_with_criteria = "I understand you have a problem. Can you tell me more about what's happening?"
    
    # Parse the response
    agent_output, system_status, schema_success = parse_agent_response_with_schema_and_completion(
        agent_response_with_criteria,
        None,  # No output schema
        acceptance_criteria,  # Has acceptance criteria
        []     # No conversation history
    )
    
    print(f"\nAgent Response: {agent_output}")
    print(f"System Status: {system_status}")
    print(f"Schema Success: {schema_success}")
    
    # Verify multi-turn behavior
    assert system_status == "continue", f"Expected 'continue', got '{system_status}'"
    print("✅ Agent with acceptance criteria correctly returns 'continue' status")


def test_single_shot_with_schema():
    """Test single-shot agent with JSON schema."""
    print("\n🧪 Test 3: Single-shot agent with JSON schema")
    print("-" * 50)
    
    # Define a simple schema for single-shot responses
    output_schema = '''{
      "type": "object",
      "properties": {
        "answer": {"type": "string", "description": "The answer to the user's question"},
        "confidence": {"type": "string", "enum": ["low", "medium", "high"], "description": "Confidence level in the answer"},
        "sources": {"type": "array", "items": {"type": "string"}, "description": "Sources used for the answer"}
      },
      "required": ["answer", "confidence"]
    }'''
    
    base_prompt = "You are a knowledge assistant that provides accurate answers."
    enhanced_prompt = inject_acceptance_criteria(base_prompt, None, output_schema)
    
    print("Enhanced prompt for single-shot agent with schema:")
    print(enhanced_prompt[:300] + "...")
    
    # Simulate agent response
    agent_response = '{"answer": "Python is a high-level programming language known for its simplicity and readability.", "confidence": "high", "sources": ["Python.org", "Wikipedia"]}'
    
    # Parse the response
    agent_output, system_status, schema_success = parse_agent_response_with_schema_and_completion(
        agent_response,
        output_schema,  # Has output schema
        None,           # No acceptance criteria
        []              # No conversation history
    )
    
    print(f"\nAgent Response: {agent_output}")
    print(f"System Status: {system_status}")
    print(f"Schema Success: {schema_success}")
    
    # Verify single-shot behavior with schema
    assert system_status == "complete", f"Expected 'complete', got '{system_status}'"
    print("✅ Single-shot agent with schema correctly returns 'complete' status")


def show_behavior_comparison():
    """Show the difference between single-shot and multi-turn agents."""
    print("\n" + "=" * 60)
    print("Single-Shot vs Multi-Turn Agent Behavior")
    print("=" * 60)
    
    print("🔄 Multi-Turn Agent (with acceptance criteria):")
    print("   - Continues conversation until criteria are met")
    print("   - Asks clarifying questions")
    print("   - Evaluates completion based on user-defined criteria")
    print("   - Returns 'continue' until all criteria satisfied")
    print("   - Returns 'complete' when criteria are met")
    
    print("\n⚡ Single-Shot Agent (no acceptance criteria):")
    print("   - Responds once and completes")
    print("   - Provides comprehensive answer in one interaction")
    print("   - Always returns 'complete' after first response")
    print("   - Perfect for simple Q&A, calculations, translations")
    print("   - 'Do one thing and die' behavior")
    
    print("\n📋 Use Cases:")
    print("   Single-Shot: Q&A, calculations, translations, simple tasks")
    print("   Multi-Turn: Problem understanding, data collection, complex workflows")


def main():
    """Run all single-shot agent tests."""
    print("Single-Shot Agent Behavior Tests")
    print("=" * 50)
    
    try:
        test_single_shot_agent_behavior()
        test_single_shot_with_schema()
        show_behavior_comparison()
        
        print("\n" + "=" * 50)
        print("🎉 All single-shot agent tests passed!")
        print("=" * 50)
        print("\nKey Features:")
        print("• ✅ Agents without acceptance criteria are single-shot")
        print("• ✅ Single-shot agents complete after first response")
        print("• ✅ Multi-turn agents continue until criteria met")
        print("• ✅ Works with or without JSON schemas")
        print("• ✅ Clear behavior distinction based on configuration")
        print("• ✅ 'Do one thing and die' philosophy implemented")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
