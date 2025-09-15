"""Abstract interface for document indexing implementations."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class DocPointer:
    """Document pointer containing metadata about a document."""
    doc_id: str
    path: str
    title: str


class DocumentIndexInterface(ABC):
    """Abstract interface for document indexing implementations."""

    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the document index."""
        pass

    @abstractmethod
    async def search(self, query: str, k: int = 1) -> List[DocPointer]:
        """Search for documents based on a query."""
        pass

    @abstractmethod
    async def get_document_content(self, doc_id: str) -> Optional[str]:
        """Get the content of a document by its ID."""
        pass

    @abstractmethod
    async def find_best_document_content(self, query: str) -> Optional[str]:
        """Find the best matching document content for a query."""
        pass
