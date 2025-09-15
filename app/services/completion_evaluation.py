"""Agent completion evaluation service."""

import json
import re
from typing import Dict, List, Optional, Tuple, Union

from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field

from app.models.schemas import AcceptanceCriteria, AgentCompletionResponse
from app.services.schema_parser import (
    inject_output_schema_instructions,
    parse_response_with_schema
)


class AgentResponse(BaseModel):
    """Pydantic model for agent response parsing."""
    agent_output: str = Field(description="The agent's response to the user")
    system_status: str = Field(description="Either 'continue' or 'complete' based on acceptance criteria")


def inject_acceptance_criteria(
    base_system_prompt: str, 
    acceptance_criteria: Optional[AcceptanceCriteria],
    output_schema: Optional[str] = None
) -> str:
    """
    Inject acceptance criteria and output schema into the agent's system prompt.
    
    Args:
        base_system_prompt: The original system prompt
        acceptance_criteria: Structured acceptance criteria
        output_schema: JSON schema for response format
        
    Returns:
        Enhanced system prompt with completion evaluation logic and schema instructions
    """
    # First inject output schema instructions if provided
    enhanced_prompt = inject_output_schema_instructions(base_system_prompt, output_schema)
    
    if not acceptance_criteria:
        # Add single-shot agent instructions
        single_shot_instructions = """

SINGLE-SHOT AGENT BEHAVIOR:
You are a single-shot agent. This means:
- You will respond to the user's request once
- After providing your response, your task is complete
- You do not need to continue the conversation
- Focus on providing a complete, helpful response in one interaction

RESPONSE FORMAT:
{
  "agent_output": [your response to the user],
  "system_status": "complete"
}

IMPORTANT:
- Always respond in the exact format specified above
- Set system_status to "complete" after your response
- Provide a thorough, complete response since this is your only interaction
"""
        return enhanced_prompt + single_shot_instructions
    
    # Create PydanticOutputParser for format instructions
    parser = PydanticOutputParser(pydantic_object=AgentResponse)
    
    # Build criteria sections
    criteria_sections = []
    
    if acceptance_criteria.required_information:
        criteria_sections.append(
            f"REQUIRED INFORMATION TO COLLECT:\n" +
            "\n".join(f"- {info}" for info in acceptance_criteria.required_information)
        )
    
    if acceptance_criteria.completion_conditions:
        criteria_sections.append(
            f"COMPLETION CONDITIONS:\n" +
            "\n".join(f"- {condition}" for condition in acceptance_criteria.completion_conditions)
        )
    
    if acceptance_criteria.success_indicators:
        criteria_sections.append(
            f"SUCCESS INDICATORS:\n" +
            "\n".join(f"- {indicator}" for indicator in acceptance_criteria.success_indicators)
        )
    
    # Build the completion evaluation section with PydanticOutputParser format
    completion_evaluation = f"""
ACCEPTANCE CRITERIA FOR COMPLETION:
{chr(10).join(criteria_sections)}

COMPLETION EVALUATION:
Before responding, evaluate if you should set status to "complete":
- Check if you've collected all required information: {acceptance_criteria.required_information or 'None specified'}
- Verify these completion conditions are met: {acceptance_criteria.completion_conditions or 'None specified'}
- Look for these success indicators: {acceptance_criteria.success_indicators or 'None specified'}

{parser.get_format_instructions()}

IMPORTANT:
- Always respond in the exact format specified above
- Set system_status to "complete" only when ALL criteria are satisfied
- Set system_status to "continue" if any criteria are not yet met
- The agent_output should be your natural response to the user
- Ensure the response follows the exact format requirements
"""
    
    return enhanced_prompt + "\n\n" + completion_evaluation


def parse_agent_response(response_text: str) -> Tuple[str, str]:
    """
    Parse agent response to extract agent output and system status using PydanticOutputParser.
    
    Args:
        response_text: Raw response from the agent
        
    Returns:
        Tuple of (agent_output, system_status)
    """
    if not response_text:
        return response_text, "continue"
    
    # Initialize PydanticOutputParser
    parser = PydanticOutputParser(pydantic_object=AgentResponse)
    
    try:
        # Try to parse the response using PydanticOutputParser
        parsed_response = parser.parse(response_text)
        return parsed_response.agent_output, parsed_response.system_status
    except Exception:
        # If parsing fails, try to extract JSON manually as fallback
        try:
            # Look for JSON in the response
            json_match = re.search(r'\{[^}]*"agent_output"[^}]*\}', response_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                response_data = json.loads(json_str)
                
                agent_output = response_data.get("agent_output", response_text)
                system_status = response_data.get("system_status", "continue")
                
                # Validate system_status
                if system_status not in ["continue", "complete"]:
                    system_status = "continue"
                    
                return agent_output, system_status
        except (json.JSONDecodeError, KeyError, AttributeError):
            pass
        
        # If all parsing fails, return the original response with "continue" status
        return response_text, "continue"


def evaluate_completion_status(
    agent_output: str,
    acceptance_criteria: Optional[AcceptanceCriteria],
    conversation_history: List[Tuple[str, str]]
) -> str:
    """
    Evaluate if the agent has completed its objectives based on acceptance criteria.
    
    Args:
        agent_output: The agent's current response
        acceptance_criteria: The acceptance criteria to evaluate against
        conversation_history: Full conversation history
        
    Returns:
        "complete" if all criteria are met, "continue" otherwise
    """
    if not acceptance_criteria:
        return "continue"
    
    # Combine all text for analysis
    full_text = agent_output + " " + " ".join([msg for _, msg in conversation_history])
    full_text = full_text.lower()
    
    # Check required information
    if acceptance_criteria.required_information:
        for info in acceptance_criteria.required_information:
            if info.lower() not in full_text:
                return "continue"
    
    # Check completion conditions
    if acceptance_criteria.completion_conditions:
        for condition in acceptance_criteria.completion_conditions:
            if condition.lower() not in full_text:
                return "continue"
    
    # Check success indicators
    if acceptance_criteria.success_indicators:
        for indicator in acceptance_criteria.success_indicators:
            if indicator.lower() not in full_text:
                return "continue"
    
    return "complete"


def parse_agent_response_with_schema_and_completion(
    response_text: str,
    output_schema: Optional[str] = None,
    acceptance_criteria: Optional[AcceptanceCriteria] = None,
    conversation_history: List[Tuple[str, str]] = None
) -> Tuple[str, str, bool]:
    """
    Parse agent response with both schema formatting and completion evaluation.
    
    Args:
        response_text: Raw response from the agent
        output_schema: JSON schema for response format
        acceptance_criteria: Acceptance criteria for completion evaluation
        conversation_history: Full conversation history
        
    Returns:
        Tuple of (formatted_response, system_status, schema_success)
    """
    # First, try to parse with output schema if provided
    if output_schema:
        formatted_response, schema_success = parse_response_with_schema(response_text, output_schema)
    else:
        formatted_response = response_text
        schema_success = True
    
    # Then handle completion evaluation if criteria are provided
    if acceptance_criteria:
        # Parse the response for completion evaluation
        agent_output, system_status = parse_agent_response(formatted_response)
        
        # If parsing failed, try to evaluate completion status manually
        if system_status == "continue" and agent_output == formatted_response:
            if conversation_history:
                system_status = evaluate_completion_status(
                    agent_output, 
                    acceptance_criteria, 
                    conversation_history
                )
    else:
        # No completion evaluation - single-shot agent (complete after first response)
        agent_output = formatted_response
        system_status = "complete"
    
    return agent_output, system_status, schema_success


def format_completion_response(agent_output: str, system_status: str) -> str:
    """
    Format the agent response in the required completion format.
    
    Args:
        agent_output: The agent's response content
        system_status: The completion status
        
    Returns:
        Formatted JSON response string
    """
    response = AgentCompletionResponse(
        agent_output=agent_output,
        system_status=system_status
    )
    return response.model_dump_json(indent=2)
