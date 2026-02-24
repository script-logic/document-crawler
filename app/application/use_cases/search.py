"""
Search use case: Full-text search across crawled documents.
"""

from pathlib import Path
from typing import Any

from structlog import get_logger

from app.config import AppConfig
from app.domain.entities import Document, DocumentType
from app.infrastructure.database import DocumentRepository

logger = get_logger(__name__)


class SearchUseCase:
    """
    Search across crawled documents using FTS.
    """

    def __init__(
        self,
        config: AppConfig,
        repository: DocumentRepository | None = None,
    ) -> None:
        """
        Initialize search use case.

        Args:
            config: Application configuration.
            repository: Document repository (creates default if None).
        """
        self.config = config
        self.repository = repository or DocumentRepository(
            config.database.path
        )

    def search(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
        doc_type: DocumentType | None = None,
    ) -> dict[str, Any]:
        """
        Execute search query with optional filters.

        Args:
            query: Search query (FTS5 syntax).
            limit: Maximum results to return.
            offset: Pagination offset.
            doc_type: Filter by document type.

        Returns:
            Dictionary with search results and metadata.
        """
        logger.info(
            f"Searching for: {query}",
            limit=limit,
            offset=offset,
            doc_type=doc_type.value if doc_type else None,
        )

        results = self.repository.search_fts(
            query=query,
            limit=limit,
            offset=offset,
        )

        if doc_type:
            results = [r for r in results if r.doc_type == doc_type]

        total_count: int | str = len(results)
        if total_count == limit and offset == 0:
            total_count = ">=" + str(limit)

        formatted_results: list[dict[str, Any]] = []
        for doc in results:
            formatted_results.append({
                "id": doc.id,
                "path": doc.relative_path,
                "file_name": doc.file_name,
                "doc_type": doc.doc_type.value,
                "file_size": doc.file_size,
                "modified": doc.modified_time.isoformat(),
                "text_preview": (
                    doc.text_content[:300] + "..."
                    if doc.text_content and len(doc.text_content) > 300
                    else doc.text_content or ""
                ),
                "from_archive": doc.is_from_archive,
                "archive_path": doc.archive_path,
            })

        result: dict[str, Any] = {
            "query": query,
            "total": total_count,
            "returned": len(results),
            "offset": offset,
            "limit": limit,
            "results": formatted_results,
        }

        logger.info(f"Found {len(results)} results")
        return result

    def get_document(self, doc_id: int) -> Document | None:
        """Get full document by ID."""
        return self.repository.get_by_id(doc_id)

    def get_document_by_path(self, path: Path) -> Document | None:
        """Get document by file path."""
        return self.repository.get_by_path(path)

    def get_stats(self) -> dict[str, Any]:
        """Get search statistics."""
        return self.repository.get_stats()
