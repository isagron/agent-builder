from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

from tenacity import retry, wait_exponential, stop_after_attempt
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate


# Reusable ReAct prompt fallback when LangChain Hub is not accessible
REACT_PROMPT_FALLBACK = PromptTemplate.from_template(
    """You are a helpful assistant. You have access to the following tools:

{tools}

You can use these tools when needed, but you can also have normal conversations without using tools.

When you need to use a tool, use this format:
Thought: I need to use a tool to help answer this question
Action: the action to take, should be one of [{tool_names}]
Action Input: the input to the action
Observation: the result of the action
Thought: I now know the final answer
Final Answer: the final answer to the original input question

When you don't need tools, just respond naturally:
Final Answer: your natural response

IMPORTANT: After getting a tool result, always provide a Final Answer. Do not repeat the same action multiple times.

Question: {input}
Thought:"""
)


def get_react_prompt(system_prompt: str) -> PromptTemplate:
    """Get the ReAct prompt template with system prompt prepended."""
    try:
        # Try to use the standard ReAct prompt from LangChain Hub
        from langchain import hub
        prompt = hub.pull("hwchase17/react")
    except Exception:
        # Fallback to our custom prompt if hub is not accessible
        prompt = REACT_PROMPT_FALLBACK
    
    # Prepend the system prompt to the ReAct prompt
    prompt.template = f"{system_prompt}\n\n{prompt.template}"
    return prompt


class LLMProvider:
    async def generate(self, system: str, messages: List[tuple[str, str]], model: Optional[str]) -> str:
        raise NotImplementedError
    
    def create_agent(self, tools: List[Any], system_prompt: str) -> AgentExecutor:
        """Create a ReAct agent with the given tools and system prompt.
        Only needed when using tools - simple chat doesn't need this."""
        raise NotImplementedError


class EchoProvider(LLMProvider):
    def __init__(self) -> None:
        # Create a simple mock LLM for echo provider
        from langchain.llms.base import LLM
        from typing import Any, List, Optional
        
        class EchoLLM(LLM):
            def _call(self, prompt: str, stop: Optional[List[str]] = None) -> str:
                return f"[echo] {prompt}"
            
            @property
            def _llm_type(self) -> str:
                return "echo"
        
        self.client = EchoLLM()
    
    async def generate(self, system: str, messages: List[tuple[str, str]], model: Optional[str]) -> str:
        last = messages[-1][1] if messages else ""
        return f"[echo] {last}"
    
    def create_agent(self, tools: List[Any], system_prompt: str) -> AgentExecutor:
        # For echo provider, return a simple mock agent
        from langchain.agents import Tool
        from langchain.agents import AgentExecutor
        
        def echo_tool(input_text: str) -> str:
            return f"[echo tool] {input_text}"
        
        echo_tool_obj = Tool(name="echo", description="Echo the input", func=echo_tool)
        
        # Use the reusable prompt helper
        prompt = get_react_prompt(system_prompt)
        
        agent = create_react_agent(self.client, [echo_tool_obj], prompt)
        return AgentExecutor(agent=agent, tools=[echo_tool_obj], verbose=True, handle_parsing_errors=True, max_iterations=5)


class OpenAIProvider(LLMProvider):
    def __init__(self, model_override: Optional[str] = None) -> None:
        from langchain_openai import ChatOpenAI  # lazy import

        api_key = os.getenv("OPENAI_API_KEY")
        base_url = os.getenv("OPENAI_BASE_URL")
        model_name = model_override or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.client = ChatOpenAI(api_key=api_key, base_url=base_url, model=model_name, temperature=0.2)

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def generate(self, system: str, messages: List[tuple[str, str]], model: Optional[str]) -> str:
        from langchain.schema import SystemMessage, HumanMessage

        lc_messages = [SystemMessage(content=system)] + [HumanMessage(content=m[1]) for m in messages]
        res = await self.client.ainvoke(lc_messages)
        return res.content if hasattr(res, "content") else str(res)
    
    def create_agent(self, tools: List[Any], system_prompt: str) -> AgentExecutor:
        from langchain.agents import create_react_agent, AgentExecutor
        
        # Use the reusable prompt helper
        prompt = get_react_prompt(system_prompt)
        
        agent = create_react_agent(self.client, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=2)


class BedrockProvider(LLMProvider):
    def __init__(self, model_override: Optional[str] = None) -> None:
        from langchain_aws import ChatBedrock

        model_name = model_override or os.getenv("BEDROCK_MODEL_ID", "anthropic.claude-3-haiku-20240307-v1:0")
        region = os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        # ChatBedrock picks up AWS credentials from env and shared config automatically
        self.client = ChatBedrock(model=model_name, region_name=region, temperature=0.2)

    @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
    async def generate(self, system: str, messages: List[tuple[str, str]], model: Optional[str]) -> str:
        from langchain.schema import SystemMessage, HumanMessage

        lc_messages = [SystemMessage(content=system)] + [HumanMessage(content=m[1]) for m in messages]
        res = await self.client.ainvoke(lc_messages)
        return res.content if hasattr(res, "content") else str(res)
    
    def create_agent(self, tools: List[Any], system_prompt: str) -> AgentExecutor:
        from langchain.agents import create_react_agent, AgentExecutor
        
        # Use the reusable prompt helper
        prompt = get_react_prompt(system_prompt)
        
        agent = create_react_agent(self.client, tools, prompt)
        return AgentExecutor(agent=agent, tools=tools, verbose=True, handle_parsing_errors=True, max_iterations=5)


def get_provider(name: Optional[str], model: Optional[str]) -> LLMProvider:
    name = (name or "bedrock").lower()
    try:
        if name == "openai" and os.getenv("OPENAI_API_KEY"):
            return OpenAIProvider(model_override=model)
        if name == "bedrock":
            return BedrockProvider(model_override=model)
    except Exception:
        pass
    return EchoProvider()


