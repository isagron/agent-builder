# Agent Forge AI

A comprehensive AI Agent Platform with advanced capabilities including LangChain, LangGraph, and task execution.

## 🚀 Quick Start

### Prerequisites
- Python 3.11 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/isagron/agent-builder.git
   cd agent-builder
   ```

2. **Install dependencies:**
   ```bash
   uv sync
   ```
   
   Or with pip:
   ```bash
   pip install -e .[dev]
   ```

3. **Prepare documentation:**
   Place `.md` or `.txt` files under `doc/`. They will be embedded on startup.

### Running the Application

#### Option 1: Using uv (Recommended)
```bash
uv run python main.py
```

#### Option 2: Using Python directly
```bash
python main.py
```

#### Option 3: Using uvicorn directly
```bash
python -m uvicorn app.server:app --reload --host 0.0.0.0 --port 8000
```

#### Option 4: Using the installed script
```bash
agent-forge
```

### Quick Start for Different Environments

#### 🏢 Corporate Environment (AWS Bedrock)
```bash
# Clone and install
git clone https://github.com/isagron/agent-builder.git
cd agent-builder
uv sync

# Configure for Bedrock
export DOC_INDEX_IMPLEMENTATION=bedrock
export AWS_DEFAULT_REGION=us-east-1
export AWS_PROFILE=your-profile

# Run
python main.py
```

#### 💻 Development Environment (Sentence Transformers)
```bash
# Clone and install
git clone https://github.com/isagron/agent-builder.git
cd agent-builder
uv sync

# Configure for Sentence Transformers
export DOC_INDEX_IMPLEMENTATION=sentence_transformers

# Run
python main.py
```

#### 🤖 Auto-Detection (Recommended)
```bash
# Clone and install
git clone https://github.com/isagron/agent-builder.git
cd agent-builder
uv sync

# Let the system decide (default)
# No configuration needed - will auto-detect

# Run
python main.py
```

### Access the Application

- **API Server**: http://localhost:8000
- **Interactive API Documentation (Swagger UI)**: http://localhost:8000/docs
- **Alternative API Documentation (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI JSON Schema**: http://localhost:8000/openapi.json

### Streamlit Debug UI

```bash
streamlit run streamlit_app.py
```

## 📚 API Endpoints

### Core Agent APIs
- `POST /open-session` - Open a new agent session
- `POST /create-agent` - Create a new AI agent
- `POST /chat` - Chat with an AI agent

### Document Management
- `POST /search-documentation` - Search through documentation
- `POST /get-document` - Get document content by ID
- `POST /find-document` - Find best matching document

### Task Execution
- `POST /api/task-executor/execute` - Execute a task
- `GET /api/task-executor/status` - Get agent status
- `GET /api/task-executor/health` - Health check

### Tools & Utilities
- `GET /tools` - Get available tools
- `GET /tools/names` - Get tool names
- `GET /healthz` - System health check

## 🛠️ Development

### Project Structure
```
agent-forge-ai/
├── app/                    # Main application module
│   ├── agents/            # Agent management
│   ├── memory/            # Session memory
│   ├── models/            # Data models and schemas
│   ├── providers/         # LLM providers
│   ├── services/          # Business logic services
│   ├── tools/             # Agent tools
│   └── server.py          # FastAPI application
├── task_executor_agent/   # Task execution module
│   ├── agent/             # Task execution agents
│   ├── api/               # API endpoints
│   ├── models/            # Task execution schemas
│   └── tools/             # Task execution tools
├── doc/                   # Documentation files
└── main.py               # Application entry point
```

### Environment Variables
Create a `.env` file for configuration:
```env
# Document Index Configuration
DOC_INDEX_IMPLEMENTATION=auto  # "sentence_transformers", "bedrock", or "auto"

# AWS Bedrock Configuration (if using bedrock)
AWS_DEFAULT_REGION=us-east-1
AWS_PROFILE=default
BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v1

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key

# RabbitMQ Configuration
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USERNAME=guest
RABBITMQ_PASSWORD=guest
```

## ⚙️ Configuration

### Document Index Implementations

The application supports two document indexing implementations:

- **Sentence Transformers** (default): Fast, local, requires Hugging Face access
- **AWS Bedrock**: Enterprise-grade, no Hugging Face dependency, requires AWS credentials

### How to Control Which Implementation to Use

#### Method 1: Environment Variable (Recommended)
```bash
# Use Sentence Transformers (default)
export DOC_INDEX_IMPLEMENTATION=sentence_transformers

# Use AWS Bedrock
export DOC_INDEX_IMPLEMENTATION=bedrock

# Auto-detect (tries sentence_transformers first, falls back to bedrock)
export DOC_INDEX_IMPLEMENTATION=auto
```

#### Method 2: .env File
Create a `.env` file in your project root:
```env
# Document Index Configuration
DOC_INDEX_IMPLEMENTATION=bedrock

# AWS Bedrock Configuration (only needed if using bedrock)
AWS_DEFAULT_REGION=us-east-1
AWS_PROFILE=default
BEDROCK_EMBEDDING_MODEL=amazon.titan-embed-text-v1
```

#### Method 3: Command Line Override
```bash
# Force Bedrock implementation
DOC_INDEX_IMPLEMENTATION=bedrock python main.py

# Force Sentence Transformers
DOC_INDEX_IMPLEMENTATION=sentence_transformers python main.py
```

### Configuration Options

| Option | Description | Use Case |
|--------|-------------|----------|
| `sentence_transformers` | Hugging Face Sentence Transformers | Development, when Hugging Face is accessible |
| `bedrock` | AWS Bedrock embeddings | Corporate environments, production |
| `auto` | Auto-detect available implementation | Default, works in most environments |

### Check Available Implementations

```python
from app.services.doc_index_factory import get_available_implementations
print(get_available_implementations())
```

### Test Your Configuration

```bash
python test_doc_index_implementations.py
```

See [CONFIGURATION.md](CONFIGURATION.md) for detailed configuration options.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.


