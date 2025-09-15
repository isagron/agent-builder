#!/usr/bin/env python3
"""Test script to verify the API endpoints work correctly."""

import requests
import json


def test_api_endpoints():
    """Test the API endpoints."""
    base_url = "http://localhost:8000"
    
    print("Testing API endpoints...")
    
    # Test health endpoint
    try:
        response = requests.get(f"{base_url}/healthz")
        print(f"✅ Health check: {response.status_code} - {response.json()}")
    except Exception as e:
        print(f"❌ Health check failed: {e}")
        return
    
    # Test tools endpoint
    try:
        response = requests.get(f"{base_url}/tools")
        tools_data = response.json()
        print(f"✅ Tools endpoint: {response.status_code}")
        print(f"   Found {len(tools_data.get('tools', []))} tools")
        for tool in tools_data.get('tools', []):
            print(f"   - {tool['name']}: {tool['description']}")
    except Exception as e:
        print(f"❌ Tools endpoint failed: {e}")
    
    # Test tool names endpoint
    try:
        response = requests.get(f"{base_url}/tools/names")
        names_data = response.json()
        print(f"✅ Tool names endpoint: {response.status_code}")
        print(f"   Tool names: {names_data.get('tool_names', [])}")
    except Exception as e:
        print(f"❌ Tool names endpoint failed: {e}")
    
    # Test session creation
    try:
        session_data = {"sessionId": "test-session"}
        response = requests.post(f"{base_url}/open-session", json=session_data)
        print(f"✅ Session creation: {response.status_code}")
    except Exception as e:
        print(f"❌ Session creation failed: {e}")


if __name__ == "__main__":
    test_api_endpoints()
