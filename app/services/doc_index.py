from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

import faiss  # type: ignore
from sentence_transformers import SentenceTransformer


@dataclass
class DocPointer:
    doc_id: str
    path: str
    title: str


class DocumentIndex:
    def __init__(self, doc_root: str = "doc", model_name: str = "all-MiniLM-L6-v2") -> None:
        self.doc_root = Path(doc_root)
        self.model_name = model_name
        self._model: Optional[SentenceTransformer] = None
        self._index: Optional[faiss.IndexFlatIP] = None
        self._id_to_doc: dict[int, DocPointer] = {}
        self._embeddings_dim: Optional[int] = None

    async def initialize(self) -> None:
        self.doc_root.mkdir(parents=True, exist_ok=True)
        model = await asyncio.get_event_loop().run_in_executor(None, self._load_model)
        docs = await asyncio.get_event_loop().run_in_executor(None, self._scan_docs)
        if not docs:
            self._index = None
            self._id_to_doc = {}
            return
        texts = [self._read_file_text(Path(d.path)) for d in docs]
        embeddings = await asyncio.get_event_loop().run_in_executor(
            None, lambda: model.encode(texts, normalize_embeddings=True)
        )
        self._embeddings_dim = embeddings.shape[1]
        index = faiss.IndexFlatIP(self._embeddings_dim)
        index.add(embeddings)
        self._model = model
        self._index = index
        self._id_to_doc = {i: doc for i, doc in enumerate(docs)}

    def _load_model(self) -> SentenceTransformer:
        return SentenceTransformer(self.model_name)

    def _scan_docs(self) -> List[DocPointer]:
        docs: List[DocPointer] = []
        for path in self.doc_root.rglob("*"):
            if path.is_file() and path.suffix.lower() in {".md", ".txt"}:
                title = path.stem.replace("_", " ")
                docs.append(
                    DocPointer(doc_id=str(len(docs)), path=str(path), title=title)
                )
        return docs

    def _read_file_text(self, path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except Exception:
            return ""

    async def search(self, query: str, k: int = 1) -> List[DocPointer]:
        if not query.strip() or self._index is None or self._model is None:
            return []
        embedding = await asyncio.get_event_loop().run_in_executor(
            None, lambda: self._model.encode([query], normalize_embeddings=True)
        )
        D, I = self._index.search(embedding, min(k, len(self._id_to_doc)))
        indices = I[0].tolist()
        return [self._id_to_doc[i] for i in indices]

    async def get_document_content(self, doc_id: str) -> Optional[str]:
        try:
            idx = int(doc_id)
        except ValueError:
            return None
        doc = self._id_to_doc.get(idx)
        if not doc:
            return None
        return self._read_file_text(Path(doc.path))

    async def find_best_document_content(self, query: str) -> Optional[str]:
        pointers = await self.search(query=query, k=1)
        if not pointers:
            return None
        return await self.get_document_content(doc_id=pointers[0].doc_id)


