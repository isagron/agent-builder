"""
Task Selection Agent

This agent receives a list of available tasks and an action description,
then uses LLM reasoning to select the most suitable task.
"""

import json
import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import PydanticOutputParser
from langchain_openai import ChatOpenAI
from langchain_aws import ChatBedrock
from pydantic import BaseModel, Field

from task_executor_agent.models.schemas import TaskInfo
from task_executor_agent.config import get_settings

logger = logging.getLogger(__name__)


class TaskSelectionLLMResponse(BaseModel):
    """Structured response model for LLM task selection."""
    selected_task_id: str = Field(description="The ID of the selected task")
    reasoning: str = Field(description="Detailed reasoning for the task selection")
    confidence: float = Field(description="Confidence score between 0.0 and 1.0", ge=0.0, le=1.0)
    alternative_task_ids: List[str] = Field(default=[], description="List of alternative task IDs")
    analysis: Optional[Dict[str, Any]] = Field(default=None, description="Additional analysis data")


@dataclass
class TaskSelectionRequest:
    """Request for task selection."""
    action_description: str
    available_tasks: List[TaskInfo]
    context_id: Optional[str] = None


@dataclass
class TaskSelectionResponse:
    """Response from task selection."""
    selected_task: Optional[TaskInfo]
    reasoning: str
    confidence: float  # 0.0 to 1.0
    alternative_tasks: List[TaskInfo]  # Other potentially suitable tasks


class TaskSelectionAgent:
    """
    LLM-based agent for selecting the most relevant task from available options.
    
    This agent uses natural language understanding to match user actions
    with the most suitable available tasks, considering context, requirements,
    and task capabilities.
    """
    
    def __init__(self, llm_provider: str = "openai", model_name: Optional[str] = None):
        """
        Initialize the task selection agent.
        
        Args:
            llm_provider: LLM provider to use ("openai" or "bedrock")
            model_name: Specific model name to use
        """
        self.llm_provider = llm_provider
        self.model_name = model_name
        self.settings = get_settings()
        
        # Initialize LLM
        self.llm = self._initialize_llm()
        
        # Initialize structured output parser
        self.output_parser = PydanticOutputParser(pydantic_object=TaskSelectionLLMResponse)
        
        # System prompt for task selection
        self.system_prompt = self._create_system_prompt()
        
        logger.info(f"TaskSelectionAgent initialized with {llm_provider}")
    
    def _initialize_llm(self):
        """Initialize the LLM based on provider."""
        if self.llm_provider.lower() == "openai":
            model = self.model_name or "gpt-4o-mini"
            return ChatOpenAI(
                model=model,
                temperature=0.1,  # Low temperature for consistent reasoning
                max_tokens=1000
            )
        elif self.llm_provider.lower() == "bedrock":
            model = self.model_name or "anthropic.claude-3-5-sonnet-20241022-v2:0"
            return ChatBedrock(
                model_id=model,
                temperature=0.1,
                max_tokens=1000
            )
        else:
            raise ValueError(f"Unsupported LLM provider: {self.llm_provider}")
    
    def _create_system_prompt(self) -> str:
        """Create the system prompt for task selection."""
        return f"""You are an expert task selection agent. Your job is to analyze a user's action description and select the most suitable task from a list of available tasks.

## Your Task:
1. Analyze the user's action description carefully
2. Review all available tasks and their capabilities
3. Select the ONE most suitable task that best matches the user's intent
4. Provide clear reasoning for your selection
5. Assess your confidence level (0.0 to 1.0)
6. Identify alternative tasks that could also work

## Selection Criteria:
- **Intent Matching**: Does the task's purpose align with the user's goal?
- **Capability Alignment**: Can the task actually accomplish what the user wants?
- **Context Relevance**: Does the task fit the user's specific context?
- **Completeness**: Will this task fully address the user's request?
- **Efficiency**: Is this the most direct path to the user's goal?

## Response Format:
{self.output_parser.get_format_instructions()}

## Important Notes:
- If no task is suitable, set "selected_task_id" to null
- Confidence should reflect how certain you are about the selection
- Include 1-3 alternative tasks that could also work
- Be specific in your reasoning
- Consider the user's context and specific needs
- If multiple tasks could work, choose the most comprehensive one"""
    
    async def select_task(self, request: TaskSelectionRequest) -> TaskSelectionResponse:
        """
        Select the most suitable task for the given action.
        
        Args:
            request: Task selection request with action and available tasks
            
        Returns:
            Task selection response with selected task and reasoning
        """
        try:
            # Prepare the human message with task information
            human_message = self._create_human_message(request)
            print(f"Human message text: {human_message}")



            # Get LLM response
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=human_message)
            ]
            print(f"going to invoke llm to find selected task")
            response = await self.llm.ainvoke(messages)
            print(f"LLM response: {response}")
            response_text = response.content.strip()

            logger.info(f"Task selection response: {response_text}")
            
            # Parse using structured output parser
            parsed_response = self.output_parser.parse(response_text)
            logger.info(f"Parsed response: {parsed_response}")
            
            # Convert to TaskSelectionResponse
            selection_result = self._convert_to_task_selection_response(parsed_response, request.available_tasks)
            
            logger.info(f"Task selection completed: {selection_result.selected_task.task_id if selection_result.selected_task else 'None'}")
            return selection_result
            
        except Exception as e:
            import traceback
            logger.error(f"Exception stacktrace:\n{traceback.format_exc()}")
            logger.error(f"Task selection failed: {e}")
            return TaskSelectionResponse(
                selected_task=None,
                reasoning=f"Task selection failed: {str(e)}",
                confidence=0.0,
                alternative_tasks=[]
            )
    
    def _create_human_message(self, request: TaskSelectionRequest) -> str:
        """Create the human message with task information."""
        tasks_info = []
        
        for i, task in enumerate(request.available_tasks, 1):
            task_info = f"""
Task {i}:
- ID: {task.task_id}
- Name: {task.task_name}
- Description: {task.description}
"""
            
            tasks_info.append(task_info.strip())
        
        context_info = f"\nContext ID: {request.context_id}" if request.context_id else ""
        
        return f"""User Action Description: {request.action_description}{context_info}

Available Tasks:
{chr(10).join(tasks_info)}

Please select the most suitable task for this action and provide your reasoning."""
    
    def _parse_response(self, response_text: str, available_tasks: List[TaskInfo]) -> TaskSelectionResponse:
        """Parse the LLM response using structured output parser."""
        try:
            # Use the structured output parser
            parsed_response = self.output_parser.parse(response_text)
            
            # Find the selected task
            selected_task = None
            if parsed_response.selected_task_id:
                selected_task = next(
                    (task for task in available_tasks if str(task.task_id) == parsed_response.selected_task_id),
                    None
                )
            
            # Find alternative tasks
            alternative_tasks = []
            for alt_id in parsed_response.alternative_task_ids:
                alt_task = next(
                    (task for task in available_tasks if str(task.task_id) == alt_id),
                    None
                )
                if alt_task and alt_task != selected_task:
                    alternative_tasks.append(alt_task)
            
            return TaskSelectionResponse(
                selected_task=selected_task,
                reasoning=parsed_response.reasoning,
                confidence=parsed_response.confidence,
                alternative_tasks=alternative_tasks
            )
            
        except Exception as e:
            import traceback
            logger.error(f"Exception stacktrace:\n{traceback.format_exc()}")
            logger.warning(f"Failed to parse LLM response with structured parser: {e}")
            logger.warning(f"Response text: {response_text}")
            
            # Fallback: try to extract task ID from text
            selected_task = self._extract_task_id_from_text(response_text, available_tasks)
            
            return TaskSelectionResponse(
                selected_task=selected_task,
                reasoning=f"Parsed with fallback method. Original response: {response_text[:200]}...",
                confidence=0.3,
                alternative_tasks=[]
            )
    
    def _convert_to_task_selection_response(self, parsed_response: TaskSelectionLLMResponse, available_tasks: List[TaskInfo]) -> TaskSelectionResponse:
        """Convert structured LLM response to TaskSelectionResponse."""
        # Find the selected task
        selected_task = None
        if parsed_response.selected_task_id:
            selected_task = next(
                (task for task in available_tasks if str(task.task_id) == parsed_response.selected_task_id),
                None
            )
        
        # Find alternative tasks
        alternative_tasks = []
        for alt_id in parsed_response.alternative_task_ids:
            alt_task = next(
                (task for task in available_tasks if str(task.task_id) == alt_id),
                None
            )
            if alt_task and alt_task != selected_task:
                alternative_tasks.append(alt_task)
        
        return TaskSelectionResponse(
            selected_task=selected_task,
            reasoning=parsed_response.reasoning,
            confidence=parsed_response.confidence,
            alternative_tasks=alternative_tasks
        )
    
    def _extract_task_id_from_text(self, text: str, available_tasks: List[TaskInfo]) -> Optional[TaskInfo]:
        """Fallback method to extract task ID from unstructured text."""
        # Look for task IDs in the text
        for task in available_tasks:
            if task.task_id in text or task.task_name.lower() in text.lower():
                return task
        
        # If no specific match, return the first task as fallback
        return available_tasks[0] if available_tasks else None


# Factory function for easy creation
def create_task_selection_agent(
    llm_provider: str = "openai",
    model_name: Optional[str] = None
) -> TaskSelectionAgent:
    """
    Create a task selection agent.
    
    Args:
        llm_provider: LLM provider to use
        model_name: Specific model name
        
    Returns:
        Configured TaskSelectionAgent instance
    """
    return TaskSelectionAgent(llm_provider=llm_provider, model_name=model_name)
