from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.services.doc_index import DocumentIndex, DocPointer
from app.memory.session_memory import SessionMemoryStore
from app.agents.registry import AgentRegistry
from app.services.rabbitmq_service import initialize_rabbitmq_service
from app.models.schemas import (
    OpenSessionRequest,
    SearchRequest,
    SearchResponse,
    DocPointerModel,
    GetDocumentRequest,
    GetDocumentResponse,
    FindDocumentRequest,
    CreateAgentRequest,
    CreateAgentResponse,
    ChatRequest,
    ChatResponse,
)
from app.tools.registry import tool_registry

# Import Task Executor Agent components
from task_executor_agent.api.endpoints import router as task_executor_router, set_agent as set_task_executor_agent
from task_executor_agent.agent.task_agent import create_task_agent
from task_executor_agent.tools.http_client import close_http_client


def create_app() -> FastAPI:
    app = FastAPI(
        title="Agent Forge AI", 
        version="0.1.0",
        description="AI Agent Platform with Task Executor Agent"
    )

    # CORS for local dev and Streamlit
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Shared singletons
    session_memory = SessionMemoryStore()
    doc_index = DocumentIndex(doc_root="doc")
    agent_registry = AgentRegistry(session_memory=session_memory, doc_index=doc_index)
    
    # Initialize Task Executor Agent
    task_executor_agent = None

    @app.on_event("startup")
    async def on_startup() -> None:
        # Load .env if present
        try:
            from dotenv import load_dotenv

            load_dotenv()
        except Exception:
            pass
        
        # Initialize RabbitMQ service
        try:
            import os
            rabbitmq_host = os.getenv("RABBITMQ_HOST", "localhost")
            rabbitmq_port = int(os.getenv("RABBITMQ_PORT", "5672"))
            rabbitmq_username = os.getenv("RABBITMQ_USERNAME", "guest")
            rabbitmq_password = os.getenv("RABBITMQ_PASSWORD", "guest")
            rabbitmq_vhost = os.getenv("RABBITMQ_VHOST", "/")
            
            initialize_rabbitmq_service(
                host=rabbitmq_host,
                port=rabbitmq_port,
                username=rabbitmq_username,
                password=rabbitmq_password,
                virtual_host=rabbitmq_vhost
            )
            print(f"✅ RabbitMQ service initialized: {rabbitmq_host}:{rabbitmq_port}")
        except Exception as e:
            print(f"⚠️ RabbitMQ service initialization failed: {e}")
            print("   Agent creation messages will not be sent via RabbitMQ")
        
        await doc_index.initialize()
        
        # Initialize Task Executor Agent
        try:
            nonlocal task_executor_agent
            task_executor_agent = create_task_agent(llm_provider="openai")
            set_task_executor_agent(task_executor_agent)
            print("✅ Task Executor Agent initialized")
        except Exception as e:
            print(f"⚠️ Task Executor Agent initialization failed: {e}")
            print("   Task execution endpoints will not be available")

    @app.post("/open-session")
    async def open_session(req: OpenSessionRequest) -> Dict[str, str]:
        session_memory.ensure_session(req.sessionId)
        return {"status": "opened"}

    @app.post("/search-documentation", response_model=SearchResponse)
    async def search_documentation(req: SearchRequest) -> SearchResponse:
        pointers = await doc_index.search(query=req.search_text, k=req.number_of_results or 1)
        results = [DocPointerModel(doc_id=p.doc_id, path=p.path, title=p.title) for p in pointers]
        return SearchResponse(results=results)

    @app.post("/get-document", response_model=GetDocumentResponse)
    async def get_document(req: GetDocumentRequest) -> GetDocumentResponse:
        content = await doc_index.get_document_content(doc_id=req.doc_pointer.doc_id)
        if content is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return GetDocumentResponse(content=content)

    @app.post("/find-document", response_model=GetDocumentResponse)
    async def find_document(req: FindDocumentRequest) -> GetDocumentResponse:
        content = await doc_index.find_best_document_content(query=req.search_text)
        if content is None:
            raise HTTPException(status_code=404, detail="No documents available")
        return GetDocumentResponse(content=content)

    @app.post("/create-agent", response_model=CreateAgentResponse)
    async def create_agent(req: CreateAgentRequest) -> CreateAgentResponse:
        try:
            agent_id = await agent_registry.create_agent(req)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return CreateAgentResponse(agentId=agent_id)

    @app.post("/chat", response_model=ChatResponse)
    async def chat(req: ChatRequest) -> ChatResponse:
        try:
            reply = await agent_registry.chat(req)
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        
        # Try to parse as structured response with completion status
        try:
            import json
            parsed_reply = json.loads(reply)
            if isinstance(parsed_reply, dict) and "agent_output" in parsed_reply and "system_status" in parsed_reply:
                return ChatResponse(
                    agent_response=parsed_reply["agent_output"],
                    system_status=parsed_reply["system_status"]
                )
        except (json.JSONDecodeError, KeyError, TypeError):
            pass
        
        # Fallback to simple response
        return ChatResponse(agent_response=reply)

    @app.get("/tools")
    async def get_available_tools() -> Dict[str, Any]:
        """Get list of available tools and their schemas."""
        tools = tool_registry.get_available_tools()
        return {
            "tools": [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.args_schema.schema() if hasattr(tool, 'args_schema') and tool.args_schema else {}
                }
                for tool in tools
            ]
        }
    
    @app.get("/tools/names")
    async def get_tool_names() -> Dict[str, List[str]]:
        """Get list of available tool names only."""
        tool_names = tool_registry.get_tool_names()
        return {"tool_names": tool_names}

    # Include Task Executor Agent router
    app.include_router(task_executor_router)
    
    # Health
    @app.get("/healthz")
    async def health() -> Dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()


