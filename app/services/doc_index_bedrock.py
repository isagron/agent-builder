"""AWS Bedrock-based document indexing implementation."""

from __future__ import annotations

import asyncio
import os
from pathlib import Path
from typing import List, Optional

import faiss  # type: ignore
import numpy as np
from langchain_aws import BedrockEmbeddings

from app.services.doc_index_interface import DocPointer, DocumentIndexInterface


class DocumentIndexBedrock(DocumentIndexInterface):
    """AWS Bedrock-based document indexing implementation."""

    def __init__(
        self, 
        doc_root: str = "doc", 
        embedding_model: str = "amazon.titan-embed-text-v1",
        region_name: str = "us-east-1",
        credentials_profile_name: Optional[str] = None
    ) -> None:
        self.doc_root = Path(doc_root)
        self.embedding_model = embedding_model
        self.region_name = region_name
        self.credentials_profile_name = credentials_profile_name
        self._model: Optional[BedrockEmbeddings] = None
        self._index: Optional[faiss.IndexFlatIP] = None
        self._id_to_doc: dict[int, DocPointer] = {}
        self._embeddings_dim: Optional[int] = None

    async def initialize(self) -> None:
        """Initialize the Bedrock-based document index."""
        self.doc_root.mkdir(parents=True, exist_ok=True)
        
        # Load Bedrock embeddings model
        model = await asyncio.get_event_loop().run_in_executor(None, self._load_model)
        
        # Scan documents
        docs = await asyncio.get_event_loop().run_in_executor(None, self._scan_docs)
        if not docs:
            self._index = None
            self._id_to_doc = {}
            return
        
        # Read document texts
        texts = [self._read_file_text(Path(d.path)) for d in docs]
        
        # Generate embeddings using Bedrock
        embeddings = await self._generate_embeddings(texts)
        
        # Create FAISS index
        self._embeddings_dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(self._embeddings_dim)
        index.add(embeddings)
        
        self._model = model
        self._index = index
        self._id_to_doc = {i: doc for i, doc in enumerate(docs)}

    def _load_model(self) -> BedrockEmbeddings:
        """Load the Bedrock embeddings model."""
        return BedrockEmbeddings(
            model_id=self.embedding_model,
            region_name=self.region_name,
            credentials_profile_name=self.credentials_profile_name
        )

    def _scan_docs(self) -> List[DocPointer]:
        """Scan the document directory for markdown and text files."""
        docs: List[DocPointer] = []
        for path in self.doc_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
                title = path.stem.replace("_", " ")
                docs.append(
                    DocPointer(doc_id=str(len(docs)), path=str(path), title=title)
                )
        return docs

    def _read_file_text(self, path: Path) -> str:
        """Read text content from a file."""
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    async def _generate_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings using Bedrock."""
        if not self._model:
            raise RuntimeError("Model not initialized")
        
        # Use asyncio to run the synchronous embed_documents method
        embeddings = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._model.embed_documents(texts)
        )
        return np.array(embeddings)

    async def search(self, query: str, k: int = 1) -> List[DocPointer]:
        """Search for documents based on a query."""
        if not query.strip() or self._index is None or self._model is None:
            return []
        
        # Generate query embedding
        query_embedding = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._model.embed_query(query)
        )
        
        # Search in FAISS index
        query_embedding = np.array([query_embedding])
        D, I = self._index.search(query_embedding, min(k, len(self._id_to_doc)))
        indices = I[0].tolist()
        return [self._id_to_doc[i] for i in indices]

    async def get_document_content(self, doc_id: str) -> Optional[str]:
        """Get the content of a document by its ID."""
        try:
            idx = int(doc_id)
        except ValueError:
            return None
        doc = self._id_to_doc.get(idx)
        if not doc:
            return None
        return self._read_file_text(Path(doc.path))

    async def find_best_document_content(self, query: str) -> Optional[str]:
        """Find the best matching document content for a query."""
        pointers = await self.search(query=query, k=1)
        if not pointers:
            return None
        return await self.get_document_content(doc_id=pointers[0].doc_id)
