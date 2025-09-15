"""LangGraph-based task execution agent."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from langgraph.graph import StateGraph, END
from langchain.tools import BaseTool

from task_executor_agent.models.schemas import (
    AgentContext,
    AgentState,
    AssignmentType,
    InputAssignment,
    RuntimeVariable,
    TaskInfo,
    TaskProperty,
)
from task_executor_agent.agent.task_selection_agent import TaskSelectionAgent, TaskSelectionRequest
from task_executor_agent.agent.input_mapping_agent import InputMappingAgent, InputMappingRequest

logger = logging.getLogger(__name__)


class TaskExecutionAgent:
    """LangGraph-based agent for automated task execution."""
    
    def __init__(self, llm_provider: str = "openai"):
        """
        Initialize the task execution agent.
        
        Args:
            llm_provider: LLM provider for both task selection and input mapping agents
        """
        self.task_selection_agent = TaskSelectionAgent(llm_provider=llm_provider)
        self.input_mapping_agent = InputMappingAgent(llm_provider=llm_provider)
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        graph = StateGraph(AgentContext)
        
        # Add nodes for each state
        graph.add_node(AgentState.FIND_TASKS, self._find_tasks)
        graph.add_node(AgentState.SELECT_TASK, self._select_task)
        graph.add_node(AgentState.GET_INPUTS, self._get_inputs)
        graph.add_node(AgentState.GET_VARIABLES, self._get_variables)
        graph.add_node(AgentState.MAP_INPUTS, self._map_inputs)
        graph.add_node(AgentState.EXECUTE_TASK, self._execute_task)
        graph.add_node(AgentState.RETURN_RESULT, self._return_result)
        
        # Define the flow
        graph.set_entry_point(AgentState.FIND_TASKS)
        
        graph.add_edge(AgentState.FIND_TASKS, AgentState.SELECT_TASK)
        graph.add_edge(AgentState.SELECT_TASK, AgentState.GET_INPUTS)
        graph.add_edge(AgentState.GET_INPUTS, AgentState.GET_VARIABLES)
        graph.add_edge(AgentState.GET_VARIABLES, AgentState.MAP_INPUTS)
        graph.add_edge(AgentState.MAP_INPUTS, AgentState.EXECUTE_TASK)
        graph.add_edge(AgentState.EXECUTE_TASK, AgentState.RETURN_RESULT)
        graph.add_edge(AgentState.RETURN_RESULT, END)
        
        return graph.compile()
    
    async def _find_tasks(self, context: AgentContext) -> AgentContext:
        """Find relevant tasks based on action description."""
        logger.info(f"Finding tasks for: {context.action_description}")
        
        try:
            # Use the find_tasks tool
            from task_executor_agent.tools.langchain_tools import find_tasks
            tasks_data = await find_tasks(context.action_description)
            
            # Convert to TaskInfo objects
            tasks = []
            for task_data in tasks_data:
                tasks.append(TaskInfo(
                    task_id=task_data["task_id"],
                    task_name=task_data["task_name"],
                    description=task_data["description"]
                ))
            
            context.available_tasks = tasks
            context.current_state = AgentState.SELECT_TASK
            
            logger.info(f"Found {len(tasks)} tasks")
            
        except Exception as e:
            logger.error(f"Failed to find tasks: {e}")
            context.error_message = f"Failed to find tasks: {str(e)}"
            context.current_state = AgentState.RETURN_RESULT
        
        return context
    
    async def _select_task(self, context: AgentContext) -> AgentContext:
        """Select the most suitable task from available options using LLM agent."""
        logger.info(f"Selecting task from {len(context.available_tasks)} options")
        
        if not context.available_tasks:
            context.error_message = "No tasks found for the given action"
            context.current_state = AgentState.RETURN_RESULT
            return context
        
        if len(context.available_tasks) == 1:
            # Only one task available
            context.selected_task = context.available_tasks[0]
            logger.info(f"Only one task available, selected: {context.selected_task.task_name}")
        else:
            # Multiple tasks - use LLM agent to select the best one
            try:
                selection_request = TaskSelectionRequest(
                    action_description=context.action_description,
                    available_tasks=context.available_tasks,
                    context_id=context.context_id
                )
                
                selection_response = await self.task_selection_agent.select_task(selection_request)
                
                if selection_response.selected_task:
                    context.selected_task = selection_response.selected_task
                    logger.info(f"LLM selected task: {context.selected_task.task_name}")
                    logger.info(f"Selection reasoning: {selection_response.reasoning}")
                    logger.info(f"Confidence: {selection_response.confidence}")
                    
                    if selection_response.alternative_tasks:
                        logger.info(f"Alternative tasks: {[t.task_name for t in selection_response.alternative_tasks]}")
                else:
                    # Fallback to first task if LLM couldn't select
                    context.selected_task = context.available_tasks[0]
                    logger.warning("LLM couldn't select a task, using first available task")
                    
            except Exception as e:
                logger.error(f"Task selection failed: {e}")
                # Fallback to first task
                context.selected_task = context.available_tasks[0]
                logger.warning("Task selection failed, using first available task")
        
        context.current_state = AgentState.GET_INPUTS
        logger.info(f"Selected task: {context.selected_task.task_name}")
        
        return context
    
    
    async def _get_inputs(self, context: AgentContext) -> AgentContext:
        """Get input schema for the selected task."""
        logger.info(f"Getting inputs for task: {context.selected_task.task_id}")
        
        try:
            # Use the get_task_inputs tool
            from task_executor_agent.tools.langchain_tools import get_task_inputs
            inputs_data = await get_task_inputs(context.selected_task.task_id)
            
            # Convert to TaskProperty objects
            inputs = []
            for input_data in inputs_data:
                inputs.append(TaskProperty(
                    name=input_data["name"],
                    type=input_data["type"],
                    description=input_data["description"],
                    required=input_data["required"],
                    default_value=input_data.get("default_value")
                ))
            
            context.task_inputs = inputs
            context.current_state = AgentState.GET_VARIABLES
            
            logger.info(f"Retrieved {len(inputs)} input properties")
            
        except Exception as e:
            logger.error(f"Failed to get task inputs: {e}")
            context.error_message = f"Failed to get task inputs: {str(e)}"
            context.current_state = AgentState.RETURN_RESULT
        
        return context
    
    async def _get_variables(self, context: AgentContext) -> AgentContext:
        """Get available runtime variables for the context."""
        logger.info(f"Getting variables for context: {context.context_id}")
        
        try:
            # Use the get_runtime_variables tool
            from task_executor_agent.tools.langchain_tools import get_runtime_variables
            vars_data = await get_runtime_variables(context.context_id)
            
            # Convert to RuntimeVariable objects
            variables = []
            for var_data in vars_data:
                variables.append(RuntimeVariable(
                    variable_id=var_data["variable_id"],
                    name=var_data["name"],
                    type=var_data["type"],
                    description=var_data["description"],
                    value=var_data["value"]
                ))
            
            context.runtime_variables = variables
            context.current_state = AgentState.MAP_INPUTS
            
            logger.info(f"Retrieved {len(variables)} runtime variables")
            
        except Exception as e:
            logger.error(f"Failed to get runtime variables: {e}")
            context.error_message = f"Failed to get runtime variables: {str(e)}"
            context.current_state = AgentState.RETURN_RESULT
        
        return context
    
    async def _map_inputs(self, context: AgentContext) -> AgentContext:
        """Map task inputs to runtime variables using LLM agent."""
        logger.info("Mapping task inputs to runtime variables using LLM agent")
        
        try:
            # Create input mapping request
            mapping_request = InputMappingRequest(
                task_inputs=context.task_inputs,
                runtime_variables=context.runtime_variables,
                agent_memory=context.agent_memory,  # Add agent memory if available
                context_id=context.context_id
            )
            
            # Use LLM agent to map inputs
            mapping_response = await self.input_mapping_agent.map_inputs(mapping_request)
            
            # Log mapping results
            logger.info(f"LLM mapped {len(mapping_response.mapped_assignments)} inputs")
            logger.info(f"Unmapped inputs: {mapping_response.unmapped_inputs}")
            
            # Log reasoning for each mapping
            for input_name, reasoning in mapping_response.mapping_reasoning.items():
                confidence = mapping_response.confidence_scores.get(input_name, 0.0)
                logger.info(f"Mapping '{input_name}': {reasoning} (confidence: {confidence:.2f})")
            
            # Log suggestions for unmapped inputs
            for input_name, suggestions in mapping_response.suggestions.items():
                logger.info(f"Suggestions for unmapped '{input_name}': {suggestions}")
            
            # Validate mappings
            is_valid, validation_errors = self.input_mapping_agent.validate_mappings(
                context.task_inputs,
                mapping_response.mapped_assignments
            )
            
            if not is_valid:
                logger.warning(f"Input mapping validation failed: {validation_errors}")
                # Continue with available mappings, but log warnings
            
            context.mapped_inputs = mapping_response.mapped_assignments
            context.current_state = AgentState.EXECUTE_TASK
            
            logger.info(f"Final mapping: {len(mapping_response.mapped_assignments)} mapped, {len(mapping_response.unmapped_inputs)} unmapped")
            
            if mapping_response.unmapped_inputs:
                logger.warning(f"Unmapped inputs: {mapping_response.unmapped_inputs}")
            
        except Exception as e:
            logger.error(f"Failed to map inputs: {e}")
            context.error_message = f"Failed to map inputs: {str(e)}"
            context.current_state = AgentState.RETURN_RESULT
        
        return context
    
    async def _execute_task(self, context: AgentContext) -> AgentContext:
        """Execute the task with mapped input assignments."""
        logger.info(f"Executing task: {context.selected_task.task_id}")
        
        try:
            # Convert InputAssignment objects to dictionaries for the API
            input_assignments = {}
            for input_name, assignment in context.mapped_inputs.items():
                input_assignments[input_name] = {
                    "value": assignment.value,
                    "assignment_type": assignment.assignment_type.value,
                    "variable_id": assignment.variable_id
                }
            
            # Use the run_task tool
            from task_executor_agent.tools.langchain_tools import run_task
            result = await run_task(
                context.context_id,
                context.selected_task.task_id,
                input_assignments
            )
            
            context.execution_result = result
            context.current_state = AgentState.RETURN_RESULT
            
            if result["success"]:
                logger.info("Task executed successfully")
            else:
                logger.error(f"Task execution failed: {result.get('error_message', 'Unknown error')}")
                context.error_message = result.get("error_message", "Task execution failed")
            
        except Exception as e:
            logger.error(f"Failed to execute task: {e}")
            context.error_message = f"Failed to execute task: {str(e)}"
            context.current_state = AgentState.RETURN_RESULT
        
        return context
    
    async def _return_result(self, context: AgentContext) -> AgentContext:
        """Return the final result."""
        logger.info("Returning execution result")
        
        # Calculate execution time
        execution_time = (datetime.utcnow() - context.start_time).total_seconds()
        
        # Prepare result
        if context.execution_result and context.execution_result.get("success"):
            context.execution_result["execution_time"] = execution_time
            context.execution_result["task_info"] = {
                "task_id": context.selected_task.task_id,
                "task_name": context.selected_task.task_name,
                "description": context.selected_task.description
            }
            context.execution_result["mapped_inputs"] = {
                name: {
                    "value": assignment.value,
                    "assignment_type": assignment.assignment_type.value,
                    "variable_id": assignment.variable_id
                }
                for name, assignment in context.mapped_inputs.items()
            }
        else:
            context.execution_result = {
                "success": False,
                "error_message": context.error_message or "Unknown error",
                "execution_time": execution_time
            }
        
        return context
    
    async def execute(
        self,
        action_description: str,
        context_id: str
    ) -> Dict[str, Any]:
        """
        Execute a task based on action description.
        
        Args:
            action_description: Description of the action to perform
            context_id: Runtime context identifier
            
        Returns:
            Execution result dictionary
        """
        logger.info(f"Starting task execution for action: {action_description}")
        
        # Create initial context
        context = AgentContext(
            action_description=action_description,
            context_id=context_id,
            current_state=AgentState.FIND_TASKS
        )
        
        try:
            # Run the graph
            result_context = await self.graph.ainvoke(context)
            
            # Return the execution result
            return result_context.execution_result or {
                "success": False,
                "error_message": "No result generated",
                "execution_time": 0
            }
            
        except Exception as e:
            logger.error(f"Task execution failed: {e}")
            return {
                "success": False,
                "error_message": str(e),
                "execution_time": 0
            }


def create_task_agent(llm_provider: str = "openai") -> TaskExecutionAgent:
    """
    Create a task execution agent.
    
    Args:
        llm_provider: LLM provider for both task selection and input mapping agents
        
    Returns:
        Task execution agent instance
    """
    return TaskExecutionAgent(llm_provider=llm_provider)
