from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field


class OpenSessionRequest(BaseModel):
    sessionId: str


class DocPointerModel(BaseModel):
    doc_id: str
    path: str
    title: str


class SearchRequest(BaseModel):
    search_text: str
    number_of_results: Optional[int] = Field(default=1, ge=1, le=20)


class SearchResponse(BaseModel):
    results: List[DocPointerModel]


class GetDocumentRequest(BaseModel):
    doc_pointer: DocPointerModel


class GetDocumentResponse(BaseModel):
    content: str


class FindDocumentRequest(BaseModel):
    search_text: str


class AcceptanceCriteria(BaseModel):
    """Structured acceptance criteria for agent completion evaluation."""
    required_information: Optional[List[str]] = Field(
        default=None,
        description="List of required information fields that must be collected"
    )
    completion_conditions: Optional[List[str]] = Field(
        default=None,
        description="List of conditions that must be met for completion"
    )
    success_indicators: Optional[List[str]] = Field(
        default=None,
        description="List of success indicators to look for"
    )


class CreateAgentRequest(BaseModel):
    sessionId: str
    system_prompt: str
    prompt_args: Optional[Dict[str, Any]] = None
    opening_message: Optional[str] = None
    tools: Optional[List[str]] = Field(
        default=None, 
        description="List of tool names to enable for this agent. Available tools: calculator, file_read, file_write, rest_api_request, get_request, post_request, put_request, patch_request, delete_request"
    )
    output_schema: Optional[str] = Field(
        default=None,
        description="JSON Schema for agent response format. If provided, agent will format responses according to this schema."
    )
    acceptance_criteria: Optional[AcceptanceCriteria] = Field(
        default=None,
        description="Structured acceptance criteria for completion evaluation"
    )
    docs: Optional[List[DocPointerModel]] = None
    llm_provider: Optional[str] = Field(default="bedrock")
    llm_model: Optional[str] = None


class CreateAgentResponse(BaseModel):
    agentId: str


class ChatRequest(BaseModel):
    sessionId: str
    agentId: str
    user_message: str
    user_args: Optional[List[str]] = None


class ToolCall(BaseModel):
    name: str
    arguments: Dict[str, Any]


class ToolResult(BaseModel):
    success: bool
    content: str
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class AgentCompletionResponse(BaseModel):
    """Response format for agents with completion evaluation."""
    agent_output: str
    system_status: str = Field(
        description="Either 'continue' or 'complete' based on acceptance criteria"
    )


class ChatResponse(BaseModel):
    agent_response: str
    tool_calls: Optional[List[ToolCall]] = None
    tool_results: Optional[List[ToolResult]] = None
    system_status: Optional[str] = Field(
        default=None,
        description="Agent completion status: 'continue' or 'complete'"
    )


