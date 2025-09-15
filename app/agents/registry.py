from __future__ import annotations

import json
import uuid
from typing import Any, Dict, List, Optional

from app.memory.session_memory import SessionMemoryStore
from app.models.schemas import AcceptanceCriteria, ChatRequest, CreateAgentRequest
from app.providers.llm import get_provider
from app.services.completion_evaluation import (
    inject_acceptance_criteria,
    parse_agent_response,
    evaluate_completion_status,
    parse_agent_response_with_schema_and_completion
)
from app.services.rabbitmq_service import send_agent_created_message
from app.services.doc_index import DocumentIndex
from app.tools.registry import tool_registry


class Agent:
    def __init__(
        self, 
        agent_id: str, 
        session_id: str, 
        system_prompt: str, 
        provider: str, 
        model: Optional[str],
        tools: Optional[List[str]] = None,
        acceptance_criteria: Optional[AcceptanceCriteria] = None,
        output_schema: Optional[str] = None
    ) -> None:
        self.agent_id = agent_id
        self.session_id = session_id
        self.system_prompt = system_prompt
        self.provider = provider
        self.model = model
        self.tools = tools or []
        self.acceptance_criteria = acceptance_criteria
        self.output_schema = output_schema
        self.langchain_tools = tool_registry.create_tool_instances(self.tools) if self.tools else []
        self.agent_executor = None  # Will be created when needed


class AgentRegistry:
    def __init__(self, session_memory: SessionMemoryStore, doc_index: DocumentIndex) -> None:
        self._agents: Dict[str, Agent] = {}
        self.session_memory = session_memory
        self.doc_index = doc_index

    async def create_agent(self, req: CreateAgentRequest) -> str:
        session_memory = self.session_memory.ensure_session(req.sessionId)

        context_docs: List[str] = []
        if req.docs:
            for p in req.docs:
                content = await self.doc_index.get_document_content(doc_id=p.doc_id)
                if content:
                    context_docs.append(f"# {p.title}\n{content}")

        # Named formatting using {arg_name} in prompt and a dict in prompt_args
        prompt_args = req.prompt_args or {}
        try:
            system_prompt = req.system_prompt.format(**prompt_args)
        except Exception:
            # Fallback to the raw prompt if formatting fails
            system_prompt = req.system_prompt
        if context_docs:
            system_prompt = system_prompt + "\n\n" + "\n\n".join(context_docs)

        # Inject acceptance criteria and output schema into system prompt
        enhanced_system_prompt = inject_acceptance_criteria(system_prompt, req.acceptance_criteria, req.output_schema)

        agent_id = str(uuid.uuid4())
        provider_name = (req.llm_provider or "bedrock").lower()
        agent = Agent(
            agent_id=agent_id, 
            session_id=req.sessionId, 
            system_prompt=enhanced_system_prompt, 
            provider=provider_name, 
            model=req.llm_model,
            tools=req.tools,
            acceptance_criteria=req.acceptance_criteria,
            output_schema=req.output_schema
        )
        self._agents[f"{req.sessionId}:{agent_id}"] = agent

        if req.opening_message:
            session_memory.append("assistant", req.opening_message)

        # Send RabbitMQ message for agent creation
        try:
            additional_data = {
                "system_prompt": req.system_prompt,
                "tools": req.tools or [],
                "has_acceptance_criteria": req.acceptance_criteria is not None,
                "has_output_schema": req.output_schema is not None,
                "llm_provider": req.llm_provider,
                "llm_model": req.llm_model
            }
            send_agent_created_message(agent_id, req.sessionId, additional_data)
        except Exception as e:
            # Log error but don't fail agent creation
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Failed to send RabbitMQ message for agent creation: {e}")

        return agent_id

    async def chat(self, req: ChatRequest) -> str:
        key = f"{req.sessionId}:{req.agentId}"
        if key not in self._agents:
            raise KeyError("Agent not found")
        agent = self._agents[key]
        session_memory = self.session_memory.get(req.sessionId)

        user_message = req.user_message.format(*(req.user_args or []))
        session_memory.append("user", user_message)

        provider = get_provider(name=agent.provider, model=agent.model)
        
        # If agent has tools, use LangChain ReAct agent
        if agent.langchain_tools:
            response = await self._chat_with_react_agent(agent, provider, user_message)
        else:
            # Simple chat without tools - much simpler!
            conversation_history = session_memory.get_conversation_history()
            response = await provider.generate(
                agent.system_prompt, 
                conversation_history + [("user", user_message)], 
                model=agent.model
            )

        # Handle schema formatting and completion evaluation
        if agent.output_schema or agent.acceptance_criteria:
            conversation_history = session_memory.get_conversation_history()
            agent_output, system_status, schema_success = parse_agent_response_with_schema_and_completion(
                response,
                agent.output_schema,
                agent.acceptance_criteria,
                conversation_history
            )
            
            # Store the parsed response
            session_memory.append("assistant", agent_output)
            
            # Return the structured response
            return json.dumps({
                "agent_output": agent_output,
                "system_status": system_status,
                "schema_success": schema_success
            })
        else:
            # No schema or completion evaluation - single-shot agent (complete after first response)
            session_memory.append("assistant", response)
            return json.dumps({
                "agent_output": response,
                "system_status": "complete",
                "schema_success": True
            })
    
    async def _chat_with_react_agent(self, agent: Agent, provider: Any, user_message: str) -> str:
        """Handle chat using LangChain ReAct agent."""
        # Create agent executor if not already created
        if agent.agent_executor is None:
            agent.agent_executor = provider.create_agent(agent.langchain_tools, agent.system_prompt)
        
        # Run the agent with the user message
        try:
            result = await agent.agent_executor.ainvoke({"input": user_message})
            return result.get("output", "No response generated")
        except Exception as e:
            return f"Error running agent: {str(e)}"


