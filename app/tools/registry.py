"""Tool registry for managing available tools."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from langchain.tools import Tool


class ToolRegistry:
    """Registry for managing available tools."""
    
    def __init__(self) -> None:
        self._tools: Dict[str, Tool] = {}
    
    def register_tool(self, tool: Tool) -> None:
        """Register a LangChain tool."""
        self._tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self._tools.get(name)
    
    def get_tool_names(self) -> List[str]:
        """Get all registered tool names."""
        return list(self._tools.keys())
    
    def get_tool_schemas(self) -> List[Dict[str, Any]]:
        """Get schemas for all registered tools."""
        return [
            {
                "name": tool.name,
                "description": tool.description,
                "parameters": tool.args_schema.schema() if hasattr(tool, 'args_schema') else {}
            }
            for tool in self._tools.values()
        ]
    
    def create_tool_instances(self, tool_names: List[str]) -> List[Tool]:
        """Get tool instances from a list of tool names."""
        tools = []
        for name in tool_names:
            if name in self._tools:
                tools.append(self._tools[name])
        return tools
    
    def get_available_tools(self) -> List[Tool]:
        """Get all available tool instances."""
        return list(self._tools.values())


# Global registry instance
tool_registry = ToolRegistry()

# Register all available tools
def register_default_tools() -> None:
    """Register all default tools."""
    from .calculator import calculator
    from .file_operations import file_read, file_write
    from .rest_api import rest_api_request, get_request, post_request, put_request, patch_request, delete_request
    
    tool_registry.register_tool(calculator)
    tool_registry.register_tool(file_read)
    tool_registry.register_tool(file_write)
    tool_registry.register_tool(rest_api_request)
    tool_registry.register_tool(get_request)
    tool_registry.register_tool(post_request)
    tool_registry.register_tool(put_request)
    tool_registry.register_tool(patch_request)
    tool_registry.register_tool(delete_request)

# Auto-register tools when module is imported
register_default_tools()
