"""RAG backend abstraction."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Dict


@dataclass(frozen=True)
class RetrievalHit:
    content: str
    source: str
    score: float


class KnowledgeBase(ABC):
    """Abstract interface for any RAG backend."""

    @abstractmethod
    def retrieve(self, query: str, top_k: int = 5) -> List[RetrievalHit]:
        """Return semantically relevant chunks for `query`."""

    @abstractmethod
    def add_documents(
        self,
        docs: List[str],
        metadatas: Optional[List[Dict]] = None,
    ) -> None:
        """Index documents (local-development only)."""

    @abstractmethod
    def name(self) -> str:
        """Backend identifier for logs/metrics."""