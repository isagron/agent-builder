# Configuration Guide

## Document Index Implementation

The application supports two different document indexing implementations:

### 1. Sentence Transformers (Default)
- **Implementation**: `sentence_transformers`
- **Model**: `all-MiniLM-L6-v2`
- **Pros**: Fast, local, no API costs
- **Cons**: Requires Hugging Face access, larger memory usage
- **Use Case**: Development, environments with internet access

### 2. AWS Bedrock
- **Implementation**: `bedrock`
- **Models**: `amazon.titan-embed-text-v1`, `amazon.titan-embed-text-v2`, etc.
- **Pros**: Enterprise-grade, no Hugging Face dependency, managed service
- **Cons**: Requires AWS credentials, API costs, network dependency
- **Use Case**: Corporate environments, production deployments

## Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Document Index Configuration
# Options: "sentence_transformers", "bedrock", "auto"
# "auto" will try sentence_transformers first, then fall back to bedrock
DOC_INDEX_IMPLEMENTATION=auto

# AWS Bedrock Configuration (only needed if using bedrock implementation)
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
RABBITMQ_VHOST=/
```

## Configuration Options

### DOC_INDEX_IMPLEMENTATION
- `sentence_transformers`: Use Hugging Face Sentence Transformers
- `bedrock`: Use AWS Bedrock embeddings
- `auto`: Auto-detect (try sentence_transformers first, fall back to bedrock)

### AWS Bedrock Models
- `amazon.titan-embed-text-v1`: 384 dimensions, good for most use cases
- `amazon.titan-embed-text-v2`: 1024 dimensions, higher quality
- `cohere.embed-english-v3`: 1024 dimensions, Cohere model
- `cohere.embed-multilingual-v3`: 1024 dimensions, multilingual support

## Usage Examples

### For Development (Sentence Transformers)
```bash
export DOC_INDEX_IMPLEMENTATION=sentence_transformers
python main.py
```

### For Corporate Environment (Bedrock)
```bash
export DOC_INDEX_IMPLEMENTATION=bedrock
export AWS_DEFAULT_REGION=us-east-1
export AWS_PROFILE=your-profile
python main.py
```

### Auto-detect (Recommended)
```bash
# Will try sentence_transformers first, fall back to bedrock if needed
export DOC_INDEX_IMPLEMENTATION=auto
python main.py
```

## Checking Available Implementations

You can check which implementations are available by running:

```python
from app.services.doc_index_factory import get_available_implementations
print(get_available_implementations())
```

## Troubleshooting

### Hugging Face Blocked
If you get errors about Hugging Face being blocked:
1. Set `DOC_INDEX_IMPLEMENTATION=bedrock`
2. Configure AWS credentials
3. Ensure you have the required AWS permissions

### AWS Bedrock Not Available
If Bedrock is not available:
1. Set `DOC_INDEX_IMPLEMENTATION=sentence_transformers`
2. Ensure Hugging Face is accessible
3. Install required dependencies

### Auto-detection Issues
If auto-detection fails:
1. Check your internet connection
2. Verify AWS credentials (if using Bedrock)
3. Check Hugging Face access (if using sentence_transformers)
