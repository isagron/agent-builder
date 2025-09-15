"""REST API tool for making HTTP requests."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional

import requests
from langchain.tools import tool


@tool
def rest_api_request(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, Any]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    data: Optional[str] = None,
    timeout: int = 30
) -> str:
    """
    Make HTTP requests to REST APIs supporting GET, POST, PUT, PATCH, and DELETE methods.
    
    Args:
        url: The URL to make the request to
        method: HTTP method (GET, POST, PUT, PATCH, DELETE) - default: GET
        headers: Optional headers as a dictionary (e.g., {"Authorization": "Bearer token"})
        params: Optional query parameters as a dictionary
        json_data: Optional JSON data to send in the request body (for POST, PUT, PATCH)
        data: Optional raw data to send in the request body (alternative to json_data)
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Formatted response with status code, headers, and body
    """
    try:
        # Validate method
        method = method.upper()
        if method not in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            return f"Error: Invalid HTTP method '{method}'. Supported methods: GET, POST, PUT, PATCH, DELETE"
        
        # Prepare headers
        request_headers = headers or {}
        if json_data and "Content-Type" not in request_headers:
            request_headers["Content-Type"] = "application/json"
        
        # Prepare request arguments
        request_kwargs = {
            "url": url,
            "method": method,
            "headers": request_headers,
            "timeout": timeout
        }
        
        # Add query parameters for GET requests
        if params:
            request_kwargs["params"] = params
        
        # Add body data for POST, PUT, PATCH requests
        if method in ["POST", "PUT", "PATCH"]:
            if json_data:
                request_kwargs["json"] = json_data
            elif data:
                request_kwargs["data"] = data
        
        # Make the request
        response = requests.request(**request_kwargs)
        
        # Format the response
        result = {
            "status_code": response.status_code,
            "status_text": response.reason,
            "url": response.url,
            "headers": dict(response.headers),
            "success": response.ok
        }
        
        # Try to parse JSON response
        try:
            result["json"] = response.json()
            result["body"] = json.dumps(result["json"], indent=2)
        except (ValueError, json.JSONDecodeError):
            # If not JSON, return text
            result["body"] = response.text
            result["json"] = None
        
        # Format the output
        output = f"HTTP {method} Request to {url}\n"
        output += f"Status: {result['status_code']} {result['status_text']}\n"
        output += f"Success: {result['success']}\n\n"
        
        if result['headers']:
            output += "Response Headers:\n"
            for key, value in result['headers'].items():
                output += f"  {key}: {value}\n"
            output += "\n"
        
        output += "Response Body:\n"
        output += result['body']
        
        return output
        
    except requests.exceptions.Timeout:
        return f"Error: Request to {url} timed out after {timeout} seconds"
    except requests.exceptions.ConnectionError:
        return f"Error: Could not connect to {url}. Check if the URL is correct and accessible"
    except requests.exceptions.RequestException as e:
        return f"Error making request to {url}: {str(e)}"
    except Exception as e:
        return f"Unexpected error: {str(e)}"


@tool
def get_request(url: str, headers: Optional[Dict[str, str]] = None, params: Optional[Dict[str, Any]] = None, timeout: int = 30) -> str:
    """
    Make a GET request to a REST API.
    
    Args:
        url: The URL to make the GET request to
        headers: Optional headers as a dictionary
        params: Optional query parameters as a dictionary
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Formatted response with status code, headers, and body
    """
    return rest_api_request(url=url, method="GET", headers=headers, params=params, timeout=timeout)


@tool
def post_request(
    url: str, 
    json_data: Optional[Dict[str, Any]] = None, 
    data: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None, 
    timeout: int = 30
) -> str:
    """
    Make a POST request to a REST API.
    
    Args:
        url: The URL to make the POST request to
        json_data: Optional JSON data to send in the request body
        data: Optional raw data to send in the request body (alternative to json_data)
        headers: Optional headers as a dictionary
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Formatted response with status code, headers, and body
    """
    return rest_api_request(url=url, method="POST", json_data=json_data, data=data, headers=headers, timeout=timeout)


@tool
def put_request(
    url: str, 
    json_data: Optional[Dict[str, Any]] = None, 
    data: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None, 
    timeout: int = 30
) -> str:
    """
    Make a PUT request to a REST API.
    
    Args:
        url: The URL to make the PUT request to
        json_data: Optional JSON data to send in the request body
        data: Optional raw data to send in the request body (alternative to json_data)
        headers: Optional headers as a dictionary
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Formatted response with status code, headers, and body
    """
    return rest_api_request(url=url, method="PUT", json_data=json_data, data=data, headers=headers, timeout=timeout)


@tool
def patch_request(
    url: str, 
    json_data: Optional[Dict[str, Any]] = None, 
    data: Optional[str] = None,
    headers: Optional[Dict[str, str]] = None, 
    timeout: int = 30
) -> str:
    """
    Make a PATCH request to a REST API.
    
    Args:
        url: The URL to make the PATCH request to
        json_data: Optional JSON data to send in the request body
        data: Optional raw data to send in the request body (alternative to json_data)
        headers: Optional headers as a dictionary
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Formatted response with status code, headers, and body
    """
    return rest_api_request(url=url, method="PATCH", json_data=json_data, data=data, headers=headers, timeout=timeout)


@tool
def delete_request(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> str:
    """
    Make a DELETE request to a REST API.
    
    Args:
        url: The URL to make the DELETE request to
        headers: Optional headers as a dictionary
        timeout: Request timeout in seconds (default: 30)
    
    Returns:
        Formatted response with status code, headers, and body
    """
    return rest_api_request(url=url, method="DELETE", headers=headers, timeout=timeout)
