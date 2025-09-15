"""File operation tools for reading and writing files."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from langchain.tools import tool


@tool
def file_read(file_path: str, encoding: str = "utf-8") -> str:
    """
    Read the contents of a file.
    
    Args:
        file_path: Path to the file to read (relative to project root)
        encoding: File encoding (default: utf-8)
    
    Returns:
        The contents of the file as a string
    """
    try:
        # Security check - only allow reading from project directory
        project_root = Path(__file__).parent.parent.parent
        full_path = project_root / file_path
        full_path = full_path.resolve()
        
        if not str(full_path).startswith(str(project_root.resolve())):
            return "Error: File path is outside project directory"
        
        if not full_path.exists():
            return f"Error: File not found: {file_path}"
        
        if not full_path.is_file():
            return f"Error: Path is not a file: {file_path}"
        
        content = full_path.read_text(encoding=encoding)
        return f"File contents ({len(content)} characters):\n{content}"
        
    except Exception as e:
        return f"Error reading file: {str(e)}"


@tool
def file_write(file_path: str, content: str, encoding: str = "utf-8", overwrite: bool = False) -> str:
    """
    Write content to a file.
    
    Args:
        file_path: Path to the file to write (relative to project root)
        content: Content to write to the file
        encoding: File encoding (default: utf-8)
        overwrite: Whether to overwrite existing file (default: false)
    
    Returns:
        Success message with file details
    """
    try:
        # Security check - only allow writing to project directory
        project_root = Path(__file__).parent.parent.parent
        full_path = project_root / file_path
        full_path = full_path.resolve()
        
        if not str(full_path).startswith(str(project_root.resolve())):
            return "Error: File path is outside project directory"
        
        if full_path.exists() and not overwrite:
            return f"Error: File already exists: {file_path}. Use overwrite=true to overwrite."
        
        # Create directory if it doesn't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)
        
        full_path.write_text(content, encoding=encoding)
        return f"Successfully wrote {len(content)} characters to {file_path}"
        
    except Exception as e:
        return f"Error writing file: {str(e)}"
