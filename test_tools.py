#!/usr/bin/env python3
"""Test script to demonstrate tool functionality."""

import json
from app.tools.registry import tool_registry


def test_tools():
    """Test the tool system."""
    print("Available tools:")
    tools = tool_registry.get_available_tools()
    for tool in tools:
        print(f"- {tool.name}: {tool.description}")
        if hasattr(tool, 'args_schema') and tool.args_schema:
            schema = tool.args_schema.schema()
            properties = schema.get('properties', {})
            print(f"  Parameters: {list(properties.keys())}")
    
    print("\nTesting calculator tool:")
    calc_tool = tool_registry.get_tool("calculator")
    if calc_tool:
        result = calc_tool.run("2 + 3 * 4")
        print(f"Result: {result}")
    
    print("\nTesting file read tool:")
    file_tool = tool_registry.get_tool("file_read")
    if file_tool:
        result = file_tool.run("README.md")
        print(f"File content (first 100 chars): {result[:100]}...")
    
    print("\nTesting REST API tools:")
    get_tool = tool_registry.get_tool("get_request")
    if get_tool:
        # Test with a simple public API
        result = get_tool.run("https://httpbin.org/get")
        print(f"GET request result (first 200 chars): {result[:200]}...")
    


if __name__ == "__main__":
    test_tools()
