"""
RAG (Retrieval Augmented Generation) interfaces.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any

from ..entities import (
    Chunk,
    RetrievalContext,
    RetrievalResult,
    ProcessedQuery
)


class RAGStrategy(ABC):
    """
    Interface for RAG retrieval strategy.

    Implementations: VanillaRAGStrategy, HybridRAGStrategy
    """

    @property
    @abstractmethod
    def strategy_name(self) -> str:
        """Get strategy name."""
        pass

    @abstractmethod
    async def retrieve(
        self,
        query: str,
        context: RetrievalContext
    ) -> RetrievalResult:
        """
        Retrieve relevant documents for query.

        Args:
            query: User query
            context: RetrievalContext with tenant, filters, etc.

        Returns:
            RetrievalResult with documents and metadata
        """
        pass


class DocumentChunker(ABC):
    """
    Interface for document chunking.

    Implementations: FixedChunker, SemanticChunker, RecursiveChunker
    """

    @property
    @abstractmethod
    def chunk_size(self) -> int:
        """Get target chunk size in tokens."""
        pass

    @property
    @abstractmethod
    def chunk_overlap(self) -> int:
        """Get overlap between chunks in tokens."""
        pass

    @property
    @abstractmethod
    def chunker_name(self) -> str:
        """Get chunker strategy name."""
        pass

    @abstractmethod
    def chunk(
        self,
        document: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[Chunk]:
        """
        Split document into chunks.

        Args:
            document: Document content
            metadata: Metadata to attach to chunks

        Returns:
            List of Chunk with content and metadata
        """
        pass

    @abstractmethod
    def estimate_chunks(self, document: str) -> int:
        """
        Estimate number of chunks for document.

        Args:
            document: Document content

        Returns:
            Estimated chunk count
        """
        pass


class QueryProcessor(ABC):
    """
    Interface for query preprocessing.

    Implementations: SimpleQueryProcessor, LLMQueryProcessor
    """

    @abstractmethod
    async def process(
        self,
        query: str,
        context: Optional[str] = None
    ) -> ProcessedQuery:
        """
        Process and potentially rewrite query.

        Args:
            query: Original user query
            context: Optional conversation context

        Returns:
            ProcessedQuery with original and processed versions
        """
        pass

    @abstractmethod
    async def expand(
        self,
        query: str,
        num_expansions: int = 3
    ) -> List[str]:
        """
        Generate query expansions for better recall.

        Args:
            query: Original query
            num_expansions: Number of expansions to generate

        Returns:
            List of expanded queries
        """
        pass
