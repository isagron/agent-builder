"""Dynamic schema parsing service for user-provided JSON schemas."""

import json
from typing import Any, Dict, Optional, Type

from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, create_model


def create_dynamic_model_from_schema(json_schema: str, model_name: str = "DynamicResponse") -> Type[BaseModel]:
    """
    Create a dynamic Pydantic model from a JSON schema.
    
    Args:
        json_schema: JSON schema as string
        model_name: Name for the generated model
        
    Returns:
        Dynamic Pydantic model class
    """
    try:
        schema_dict = json.loads(json_schema)
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON schema: {e}")
    
    if not isinstance(schema_dict, dict):
        raise ValueError("JSON schema must be a dictionary")
    
    # Extract properties from the schema
    properties = schema_dict.get("properties", {})
    required_fields = schema_dict.get("required", [])
    
    if not properties:
        raise ValueError("JSON schema must have 'properties' field")
    
    # Create field definitions for Pydantic
    field_definitions = {}
    
    for field_name, field_schema in properties.items():
        field_type = field_schema.get("type", "string")
        field_description = field_schema.get("description", "")
        
        # Map JSON schema types to Python types
        if field_type == "string":
            python_type = str
        elif field_type == "integer":
            python_type = int
        elif field_type == "number":
            python_type = float
        elif field_type == "boolean":
            python_type = bool
        elif field_type == "array":
            python_type = list
        elif field_type == "object":
            python_type = dict
        else:
            python_type = str  # Default to string for unknown types
        
        # Create Pydantic Field
        from pydantic import Field
        field_definitions[field_name] = (
            python_type,
            Field(
                description=field_description,
                default=None if field_name not in required_fields else ...
            )
        )
    
    # Create the dynamic model
    dynamic_model = create_model(model_name, **field_definitions)
    return dynamic_model


def create_schema_parser(json_schema: str, model_name: str = "DynamicResponse") -> PydanticOutputParser:
    """
    Create a PydanticOutputParser from a JSON schema.
    
    Args:
        json_schema: JSON schema as string
        model_name: Name for the generated model
        
    Returns:
        PydanticOutputParser instance
    """
    try:
        dynamic_model = create_dynamic_model_from_schema(json_schema, model_name)
        return PydanticOutputParser(pydantic_object=dynamic_model)
    except Exception as e:
        raise ValueError(f"Failed to create schema parser: {e}")


def inject_output_schema_instructions(
    base_system_prompt: str,
    json_schema: Optional[str],
    model_name: str = "DynamicResponse"
) -> str:
    """
    Inject output schema instructions into the system prompt.
    
    Args:
        base_system_prompt: The original system prompt
        json_schema: JSON schema for response format
        model_name: Name for the generated model
        
    Returns:
        Enhanced system prompt with schema instructions
    """
    if not json_schema:
        return base_system_prompt
    
    try:
        # Create parser to get format instructions
        parser = create_schema_parser(json_schema, model_name)
        format_instructions = parser.get_format_instructions()
        
        # Add schema instructions to the prompt
        schema_instructions = f"""
OUTPUT FORMAT REQUIREMENTS:
You must format your response according to the provided JSON schema.

{format_instructions}

IMPORTANT:
- Always respond in the exact format specified above
- Ensure all required fields are included
- Use appropriate data types for each field
- Validate your response against the schema before sending
"""
        
        return base_system_prompt + "\n\n" + schema_instructions
        
    except Exception as e:
        # If schema parsing fails, add a warning but don't break the prompt
        warning = f"""
OUTPUT FORMAT WARNING:
The provided JSON schema could not be parsed: {e}
Please ensure your response follows the intended format.
"""
        return base_system_prompt + "\n\n" + warning


def parse_response_with_schema(
    response_text: str,
    json_schema: Optional[str],
    model_name: str = "DynamicResponse"
) -> tuple[str, bool]:
    """
    Parse agent response using the provided JSON schema.
    
    Args:
        response_text: Raw response from the agent
        json_schema: JSON schema for parsing
        model_name: Name for the generated model
        
    Returns:
        Tuple of (parsed_response, success_flag)
    """
    if not json_schema:
        return response_text, True
    
    try:
        parser = create_schema_parser(json_schema, model_name)
        parsed_response = parser.parse(response_text)
        
        # Convert parsed response back to string for consistency
        if hasattr(parsed_response, 'model_dump_json'):
            return parsed_response.model_dump_json(), True
        else:
            return str(parsed_response), True
            
    except Exception as e:
        # Return original response if parsing fails
        return response_text, False
