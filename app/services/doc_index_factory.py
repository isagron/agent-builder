"""Factory for creating document index implementations."""

import os
from typing import Union

from app.services.doc_index import DocumentIndex
from app.services.doc_index_bedrock import DocumentIndexBedrock
from app.services.doc_index_interface import DocumentIndexInterface


def create_document_index(
    doc_root: str = "doc",
    implementation: str = "auto"
) -> DocumentIndexInterface:
    """
    Create a document index implementation based on configuration.
    
    Args:
        doc_root: Root directory for documents
        implementation: Implementation to use ("sentence_transformers", "bedrock", or "auto")
        
    Returns:
        Document index implementation
        
    Raises:
        ValueError: If implementation is not supported
    """
    # Auto-detect implementation if not specified
    if implementation == "auto":
        # Check if Hugging Face is blocked by trying to import sentence_transformers
        try:
            import sentence_transformers  # type: ignore
            implementation = "sentence_transformers"
        except ImportError:
            implementation = "bedrock"
    
    if implementation == "sentence_transformers":
        return DocumentIndex(doc_root=doc_root)
    
    elif implementation == "bedrock":
        # Get Bedrock configuration from environment variables
        embedding_model = os.getenv("BEDROCK_EMBEDDING_MODEL", "amazon.titan-embed-text-v1")
        region_name = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
        credentials_profile_name = os.getenv("AWS_PROFILE")
        
        return DocumentIndexBedrock(
            doc_root=doc_root,
            embedding_model=embedding_model,
            region_name=region_name,
            credentials_profile_name=credentials_profile_name
        )
    
    else:
        raise ValueError(f"Unsupported implementation: {implementation}")


def get_available_implementations() -> list[str]:
    """Get list of available document index implementations."""
    implementations = []
    
    # Check if sentence_transformers is available
    try:
        import sentence_transformers  # type: ignore
        implementations.append("sentence_transformers")
    except ImportError:
        pass
    
    # Check if Bedrock is available
    try:
        import boto3  # type: ignore
        import langchain_aws  # type: ignore
        implementations.append("bedrock")
    except ImportError:
        pass
    
    return implementations
