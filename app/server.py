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
        description="""
        # Agent Forge AI - Comprehensive AI Agent Platform
        
        A powerful platform for building, managing, and executing AI agents with advanced capabilities including:
        
        ## Core Features
        - **Agent Management**: Create and manage AI agents with custom configurations
        - **Task Execution**: Multi-agent task processing and workflow orchestration
        - **Document Search**: Intelligent document indexing and retrieval
        - **Memory Management**: Session-based conversation memory
        - **Tool Integration**: Extensible tool system for agent capabilities
        
        ## API Capabilities
        - **Agent Creation**: Dynamic agent instantiation with custom prompts and tools
        - **Chat Interface**: Interactive conversation with agents
        - **Document Processing**: Search and retrieve documentation
        - **Task Orchestration**: Execute complex multi-step tasks
        - **Health Monitoring**: System status and agent health checks
        
        ## Authentication
        Currently no authentication required for development. In production, implement proper API key or OAuth2 authentication.
        
        ## Rate Limiting
        No rate limiting currently implemented. Consider adding rate limiting for production use.
        """,
        contact={
            "name": "Agent Forge AI Support",
            "url": "https://github.com/isagron/agent-builder",
            "email": "support@agentforge.ai",
        },
        license_info={
            "name": "MIT License",
            "url": "https://opensource.org/licenses/MIT",
        },
        servers=[
            {
                "url": "http://localhost:8000",
                "description": "Development server"
            },
            {
                "url": "https://api.agentforge.ai",
                "description": "Production server"
            }
        ],
        openapi_tags=[
            {
                "name": "agents",
                "description": "Agent management operations - create, configure, and manage AI agents"
            },
            {
                "name": "chat",
                "description": "Chat and conversation operations with agents"
            },
            {
                "name": "documents",
                "description": "Document search and retrieval operations"
            },
            {
                "name": "tools",
                "description": "Tool management and discovery operations"
            },
            {
                "name": "task-executor",
                "description": "Task execution and workflow operations"
            },
            {
                "name": "health",
                "description": "Health check and system status operations"
            }
        ]
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
        
        # Set tokenizers parallelism to avoid warnings
        import os
        os.environ["TOKENIZERS_PARALLELISM"] = "false"
        
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

    @app.post(
        "/open-session",
        tags=["agents"],
        summary="Open a new agent session",
        description="Creates or ensures a session exists for agent conversations. Sessions maintain conversation history and context.",
        response_description="Session status confirmation"
    )
    async def open_session(req: OpenSessionRequest) -> Dict[str, str]:
        """
        Open a new agent session.
        
        This endpoint creates or ensures a session exists for agent conversations.
        Sessions maintain conversation history and context across multiple interactions.
        
        Args:
            req: Session request containing the session ID
            
        Returns:
            Status confirmation that the session was opened
            
        Raises:
            HTTPException: If session creation fails
        """
        session_memory.ensure_session(req.sessionId)
        return {"status": "opened"}

    @app.post(
        "/search-documentation", 
        response_model=SearchResponse,
        tags=["documents"],
        summary="Search documentation",
        description="Search through indexed documentation using semantic search to find relevant content.",
        response_description="List of matching document pointers with metadata"
    )
    async def search_documentation(req: SearchRequest) -> SearchResponse:
        """
        Search through documentation using semantic search.
        
        This endpoint performs semantic search across all indexed documentation
        to find the most relevant content based on the search query.
        
        Args:
            req: Search request containing query text and result count
            
        Returns:
            Search results with document pointers and metadata
            
        Raises:
            HTTPException: If search fails or no documents are indexed
        """
        pointers = await doc_index.search(query=req.search_text, k=req.number_of_results or 1)
        results = [DocPointerModel(doc_id=p.doc_id, path=p.path, title=p.title) for p in pointers]
        return SearchResponse(results=results)

    @app.post(
        "/get-document", 
        response_model=GetDocumentResponse,
        tags=["documents"],
        summary="Get document content",
        description="Retrieve the full content of a specific document by its ID.",
        response_description="Document content with metadata"
    )
    async def get_document(req: GetDocumentRequest) -> GetDocumentResponse:
        """
        Get the full content of a specific document.
        
        This endpoint retrieves the complete content of a document
        using its document ID from a previous search result.
        
        Args:
            req: Document request containing the document pointer
            
        Returns:
            Document content and metadata
            
        Raises:
            HTTPException: If document is not found
        """
        content = await doc_index.get_document_content(doc_id=req.doc_pointer.doc_id)
        if content is None:
            raise HTTPException(status_code=404, detail="Document not found")
        return GetDocumentResponse(content=content)

    @app.post(
        "/find-document", 
        response_model=GetDocumentResponse,
        tags=["documents"],
        summary="Find best matching document",
        description="Find and retrieve the best matching document content for a search query.",
        response_description="Best matching document content"
    )
    async def find_document(req: FindDocumentRequest) -> GetDocumentResponse:
        """
        Find the best matching document for a search query.
        
        This endpoint performs semantic search and returns the content
        of the most relevant document for the given query.
        
        Args:
            req: Find document request with search text
            
        Returns:
            Best matching document content
            
        Raises:
            HTTPException: If no documents are available or found
        """
        content = await doc_index.find_best_document_content(query=req.search_text)
        if content is None:
            raise HTTPException(status_code=404, detail="No documents available")
        return GetDocumentResponse(content=content)

    @app.post(
        "/create-agent", 
        response_model=CreateAgentResponse,
        tags=["agents"],
        summary="Create a new AI agent",
        description="Create a new AI agent with custom configuration, tools, and capabilities.",
        response_description="Created agent information with unique ID"
    )
    async def create_agent(req: CreateAgentRequest) -> CreateAgentResponse:
        """
        Create a new AI agent with custom configuration.
        
        This endpoint creates a new AI agent with the specified configuration,
        including system prompt, tools, and other parameters.
        
        Args:
            req: Agent creation request with configuration details
            
        Returns:
            Created agent information including unique agent ID
            
        Raises:
            HTTPException: If agent creation fails due to invalid configuration
        """
        try:
            agent_id = await agent_registry.create_agent(req)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return CreateAgentResponse(agentId=agent_id)

    @app.post(
        "/chat", 
        response_model=ChatResponse,
        tags=["chat"],
        summary="Chat with an AI agent",
        description="Send a message to an AI agent and receive a response. Maintains conversation context.",
        response_description="Agent response with optional system status"
    )
    async def chat(req: ChatRequest) -> ChatResponse:
        """
        Send a message to an AI agent and receive a response.
        
        This endpoint allows you to have a conversation with a specific AI agent.
        The agent maintains conversation context and can use tools as needed.
        
        Args:
            req: Chat request containing message and agent ID
            
        Returns:
            Agent response with optional system status information
            
        Raises:
            HTTPException: If agent is not found or chat fails
        """
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

    @app.get(
        "/tools",
        tags=["tools"],
        summary="Get available tools",
        description="Retrieve a list of all available tools with their schemas and descriptions.",
        response_description="List of available tools with metadata and parameter schemas"
    )
    async def get_available_tools() -> Dict[str, Any]:
        """
        Get list of available tools and their schemas.
        
        This endpoint returns all available tools that agents can use,
        including their descriptions and parameter schemas.
        
        Returns:
            Dictionary containing list of tools with metadata
        """
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
    
    @app.get(
        "/tools/names",
        tags=["tools"],
        summary="Get tool names",
        description="Get a simple list of available tool names only.",
        response_description="List of tool names"
    )
    async def get_tool_names() -> Dict[str, List[str]]:
        """
        Get list of available tool names only.
        
        This endpoint returns just the names of available tools
        without detailed schemas or descriptions.
        
        Returns:
            Dictionary containing list of tool names
        """
        tool_names = tool_registry.get_tool_names()
        return {"tool_names": tool_names}

    # Include Task Executor Agent router
    app.include_router(task_executor_router)
    
    # Health
    @app.get(
        "/healthz",
        tags=["health"],
        summary="Health check",
        description="Check the health status of the API server.",
        response_description="Health status of the server"
    )
    async def health() -> Dict[str, str]:
        """
        Check the health status of the API server.
        
        This endpoint provides a simple health check to verify
        that the API server is running and responsive.
        
        Returns:
            Health status information
        """
        return {"status": "ok"}

    return app


app = create_app()


