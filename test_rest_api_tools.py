#!/usr/bin/env python3
"""Test script specifically for REST API tools."""

import json
from app.tools.registry import tool_registry


def test_rest_api_tools():
    """Test the REST API tools."""
    print("Testing REST API Tools")
    print("=" * 50)
    
    # Test GET request
    print("\n1. Testing GET request:")
    get_tool = tool_registry.get_tool("get_request")
    if get_tool:
        result = get_tool.run("https://httpbin.org/get")
        print(f"GET result (first 300 chars):\n{result[:300]}...")
    
    # Test POST request
    print("\n2. Testing POST request:")
    post_tool = tool_registry.get_tool("post_request")
    if post_tool:
        # Test with JSON data
        json_data = {"name": "John Doe", "email": "john@example.com"}
        result = post_tool.run("https://httpbin.org/post", json_data)
        print(f"POST result (first 300 chars):\n{result[:300]}...")
    
    # Test PUT request
    print("\n3. Testing PUT request:")
    put_tool = tool_registry.get_tool("put_request")
    if put_tool:
        json_data = {"name": "Jane Doe", "email": "jane@example.com"}
        result = put_tool.run("https://httpbin.org/put", json_data)
        print(f"PUT result (first 300 chars):\n{result[:300]}...")
    
    # Test PATCH request
    print("\n4. Testing PATCH request:")
    patch_tool = tool_registry.get_tool("patch_request")
    if patch_tool:
        json_data = {"email": "updated@example.com"}
        result = patch_tool.run("https://httpbin.org/patch", json_data)
        print(f"PATCH result (first 300 chars):\n{result[:300]}...")
    
    # Test DELETE request
    print("\n5. Testing DELETE request:")
    delete_tool = tool_registry.get_tool("delete_request")
    if delete_tool:
        result = delete_tool.run("https://httpbin.org/delete")
        print(f"DELETE result (first 300 chars):\n{result[:300]}...")
    
    # Test generic REST API request
    print("\n6. Testing generic REST API request:")
    rest_tool = tool_registry.get_tool("rest_api_request")
    if rest_tool:
        # Test with headers and query parameters
        headers = {"User-Agent": "Agent-Forge-Test/1.0"}
        params = {"param1": "value1", "param2": "value2"}
        result = rest_tool.run("https://httpbin.org/get", "GET", headers, params)
        print(f"Generic REST result (first 300 chars):\n{result[:300]}...")
    
    # Test error handling
    print("\n7. Testing error handling (invalid URL):")
    if get_tool:
        result = get_tool.run("https://invalid-url-that-does-not-exist.com/api")
        print(f"Error result: {result}")
    
    print("\n" + "=" * 50)
    print("REST API Tools test completed!")


if __name__ == "__main__":
    test_rest_api_tools()
