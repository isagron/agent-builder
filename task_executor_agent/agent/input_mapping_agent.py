"""
Input Mapping Agent

This agent receives task inputs and available runtime variables,
then uses LLM reasoning to intelligently map inputs to variables
or explicit values from agent memory.
"""

import json
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock

from task_executor_agent.models.schemas import TaskProperty, RuntimeVariable, InputAssignment, AssignmentType
from task_executor_agent.config import get_settings

logger = logging.getLogger(__name__)


@dataclass
class InputMappingRequest:
    """Request for input mapping."""
    task_inputs: List[TaskProperty]
    runtime_variables: List[RuntimeVariable]
    agent_memory: Optional[Dict[str, Any]] = None
    context_id: Optional[str] = None


@dataclass
class InputMappingResponse:
    """Response from input mapping."""
    mapped_assignments: Dict[str, InputAssignment]
    unmapped_inputs: List[str]
    mapping_reasoning: Dict[str, str]  # Reasoning for each mapping
    confidence_scores: Dict[str, float]  # Confidence for each mapping
    suggestions: Dict[str, List[str]]  # Suggestions for unmapped inputs


class InputMappingAgent:
    """
    LLM-based agent for intelligently mapping task inputs to runtime variables.
    
    This agent uses natural language understanding to:
    - Match inputs to variables by name, description, and context
    - Use agent memory to find explicit values
    - Handle type compatibility and validation
    - Provide reasoning for mapping decisions
    - Suggest alternatives for unmapped inputs
    """
    
    def __init__(self, llm_provider: str = "openai", model_name: Optional[str] = None):
        """
        Initialize the input mapping agent.
        
        Args:
            llm_provider: LLM provider to use ("openai" or "bedrock")
            model_name: Specific model name to use
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.settings = get_settings()
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # System prompt for input mapping
        self.system_prompt = self._create_system_prompt()
        
        logger.info(f"InputMappingAgent initialized with {llm_provider}")
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider."""
        if self.llm_provider.lower() == "openai":
            model = self.model_name or "gpt-4o-mini"
            return ChatOpenAI(
                model=model,
                temperature=0.1,  # Low temperature for consistent reasoning
                max_tokens=2000
            )
        elif self.llm_provider.lower() == "bedrock":
            model = self.model_name or "anthropic.claude-3-5-sonnet-20241022-v2:0"
            return ChatBedrock(
                model_id=model,
                temperature=0.1,
                max_tokens=2000
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for input mapping."""
        return """You are an expert input mapping agent. Your job is to intelligently map task inputs to available runtime variables or explicit values from agent memory.

## Your Task:
1. Analyze each required task input
2. Find the best match from available runtime variables
3. Use agent memory to find explicit values when appropriate
4. Ensure type compatibility and validation
5. Provide clear reasoning for each mapping decision
6. Suggest alternatives for unmapped inputs

## Mapping Strategies:
- **Name Similarity**: Match by similar names (e.g., "user_email" → "email")
- **Description Matching**: Match by semantic meaning in descriptions
- **Type Compatibility**: Ensure types are compatible (string → string, int → int)
- **Context Relevance**: Consider the context and purpose of the input
- **Memory Lookup**: Use agent memory to find explicit values
- **Conversation History**: Use previous conversation context to understand what values might be needed
- **Default Values**: Use task input default values when available

## Assignment Types:
- **EXPLICIT**: Direct value assignment (from memory or default)
- **VARIABLE_REFERENCE**: Reference to a runtime variable

## Response Format:
You must respond with a JSON object in this exact format:
```json
{
  "mapped_assignments": {
    "input_name": {
      "value": "actual_value_or_variable_id",
      "assignment_type": "EXPLICIT" or "VARIABLE_REFERENCE",
      "variable_id": "variable_id_if_referencing_variable"
    }
  },
  "unmapped_inputs": ["input_name1", "input_name2"],
  "mapping_reasoning": {
    "input_name": "Clear explanation of why this mapping was chosen"
  },
  "confidence_scores": {
    "input_name": 0.85
  },
  "suggestions": {
    "unmapped_input_name": ["suggestion1", "suggestion2"]
  }
}
```

## Important Rules:
- Always prioritize required inputs
- Ensure type compatibility (string → string, int → int, etc.)
- Use agent memory values when they match the input purpose
- Provide confidence scores (0.0 to 1.0) for each mapping
- Give clear reasoning for each mapping decision
- Suggest alternatives for unmapped inputs
- If no good match exists, leave the input unmapped
- Consider the context and purpose of each input"""
    
    async def map_inputs(self, request: InputMappingRequest) -> InputMappingResponse:
        """
        Map task inputs to runtime variables or explicit values.
        
        Args:
            request: Input mapping request with inputs, variables, and memory
            
        Returns:
            Input mapping response with assignments and reasoning
        """
        try:
            # Prepare the human message with input information
            human_message = self._create_human_message(request)
            
            # Get LLM response
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=human_message)
            ]
            
            response = await self.llm.ainvoke(messages)
            response_text = response.content.strip()
            
            # Parse the response
            mapping_result = self._parse_response(response_text, request)
            
            logger.info(f"Input mapping completed: {len(mapping_result.mapped_assignments)} mapped, {len(mapping_result.unmapped_inputs)} unmapped")
            return mapping_result
            
        except Exception as e:
            import traceback
            logger.error(f"Exception stacktrace:\n{traceback.format_exc()}")
            logger.error(f"Input mapping failed: {e}")
            return InputMappingResponse(
                mapped_assignments={},
                unmapped_inputs=[inp.name for inp in request.task_inputs if inp.required],
                mapping_reasoning={},
                confidence_scores={},
                suggestions={}
            )
    
    def _create_human_message(self, request: InputMappingRequest) -> str:
        """Create the human message with input and variable information."""
        # Format task inputs
        inputs_info = []
        for inp in request.task_inputs:
            required = "Required" if inp.required else "Optional"
            default = f" (default: {inp.default_value})" if inp.default_value else ""
            inputs_info.append(f"- {inp.name} ({inp.type}): {inp.description} [{required}]{default}")
        
        # Format runtime variables
        variables_info = []
        for var in request.runtime_variables:
            variables_info.append(f"- {var.name} ({var.var_type}): {var.description} [ID: {var.variable_id}]")
        
        # Format agent memory (including session memory)
        memory_info = ""
        if request.agent_memory:
            # Check if this is session memory data
            if "conversation_history" in request.agent_memory:
                # Format conversation history for better readability
                conversation_history = request.agent_memory.get("conversation_history", [])
                message_count = request.agent_memory.get("message_count", 0)
                session_id = request.agent_memory.get("session_id", "unknown")
                
                memory_info = f"\nSession Memory (Session: {session_id}, Messages: {message_count}):\n"
                for i, (role, content) in enumerate(conversation_history[-10:], 1):  # Show last 10 messages
                    memory_info += f"  {i}. {role}: {content[:200]}{'...' if len(content) > 200 else ''}\n"
            else:
                # Regular agent memory
                memory_info = f"\nAgent Memory:\n{json.dumps(request.agent_memory, indent=2)}"
        
        context_info = f"\nContext ID: {request.context_id}" if request.context_id else ""
        
        return f"""Task Inputs to Map:
{chr(10).join(inputs_info)}

Available Runtime Variables:
{chr(10).join(variables_info)}{memory_info}{context_info}

Please map the task inputs to the most appropriate runtime variables or explicit values from memory."""
    
    def _parse_response(self, response_text: str, request: InputMappingRequest) -> InputMappingResponse:
        """Parse the LLM response and extract input mappings."""
        try:
            # Try to extract JSON from the response
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON found in response")
            
            json_text = response_text[json_start:json_end]
            result = json.loads(json_text)
            
            # Convert to InputAssignment objects
            mapped_assignments = {}
            for input_name, assignment_data in result.get("mapped_assignments", {}).items():
                try:
                    assignment_type = AssignmentType(assignment_data["assignment_type"])
                    mapped_assignments[input_name] = InputAssignment(
                        value=assignment_data["value"],
                        assignment_type=assignment_type,
                        variable_id=assignment_data.get("variable_id")
                    )
                except (KeyError, ValueError) as e:
                    logger.warning(f"Invalid assignment data for {input_name}: {e}")
                    continue
            
            return InputMappingResponse(
                mapped_assignments=mapped_assignments,
                unmapped_inputs=result.get("unmapped_inputs", []),
                mapping_reasoning=result.get("mapping_reasoning", {}),
                confidence_scores=result.get("confidence_scores", {}),
                suggestions=result.get("suggestions", {})
            )
            
        except (json.JSONDecodeError, ValueError, KeyError) as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            logger.warning(f"Response text: {response_text}")
            
            # Fallback: try to map based on name similarity
            return self._fallback_mapping(request)
    
    def _fallback_mapping(self, request: InputMappingRequest) -> InputMappingResponse:
        """Fallback mapping using simple name similarity."""
        mapped_assignments = {}
        unmapped_inputs = []
        mapping_reasoning = {}
        confidence_scores = {}
        suggestions = {}
        
        for inp in request.task_inputs:
            if inp.required:
                # Try to find a variable with similar name
                best_match = None
                best_score = 0
                
                for var in request.runtime_variables:
                    # Simple name similarity
                    if inp.name.lower() in var.name.lower() or var.name.lower() in inp.name.lower():
                        score = 0.7
                        if inp.type == var.type:
                            score += 0.2
                        if score > best_score:
                            best_score = score
                            best_match = var
                
                if best_match and best_score > 0.5:
                    mapped_assignments[inp.name] = InputAssignment(
                        value=best_match.variable_id,
                        assignment_type=AssignmentType.VARIABLE_REFERENCE,
                        variable_id=best_match.variable_id
                    )
                    mapping_reasoning[inp.name] = f"Matched by name similarity with {best_match.name}"
                    confidence_scores[inp.name] = best_score
                else:
                    unmapped_inputs.append(inp.name)
                    suggestions[inp.name] = [var.name for var in request.runtime_variables[:3]]
        
        return InputMappingResponse(
            mapped_assignments=mapped_assignments,
            unmapped_inputs=unmapped_inputs,
            mapping_reasoning=mapping_reasoning,
            confidence_scores=confidence_scores,
            suggestions=suggestions
        )
    
    def validate_mappings(self, task_inputs: List[TaskProperty], mapped_assignments: Dict[str, InputAssignment]) -> Tuple[bool, List[str]]:
        """
        Validate the input mappings.
        
        Args:
            task_inputs: List of task input properties
            mapped_assignments: Mapped input assignments
            
        Returns:
            Tuple of (is_valid, validation_errors)
        """
        validation_errors = []
        
        # Check if all required inputs are mapped
        required_inputs = {inp.name for inp in task_inputs if inp.required}
        mapped_inputs = set(mapped_assignments.keys())
        missing_required = required_inputs - mapped_inputs
        
        if missing_required:
            validation_errors.append(f"Missing required inputs: {list(missing_required)}")
        
        # Check type compatibility
        for input_name, assignment in mapped_assignments.items():
            input_prop = next((inp for inp in task_inputs if inp.name == input_name), None)
            if input_prop:
                # Type validation would go here
                # For now, we'll assume the LLM handled type compatibility
                pass
        
        is_valid = len(validation_errors) == 0
        return is_valid, validation_errors


# Factory function for easy creation
def create_input_mapping_agent(
    llm_provider: str = "openai",
    model_name: Optional[str] = None
) -> InputMappingAgent:
    """
    Create an input mapping agent.
    
    Args:
        llm_provider: LLM provider to use
        model_name: Specific model name
        
    Returns:
        Configured InputMappingAgent instance
    """
    return InputMappingAgent(llm_provider=llm_provider, model_name=model_name)
