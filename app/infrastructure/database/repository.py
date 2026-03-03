"""
Repository for document storage and search.
"""

from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, func, text
from sqlalchemy.orm import Session, sessionmaker
from structlog import get_logger

from app.domain.entities import Document, DocumentType
from app.domain.value_objects import FileHash

from .models import Base, DocumentModel

logger = get_logger(__name__)


class DocumentRepository:
    """
    Repository for document operations with FTS support.
    """

    def __init__(self, db_path: Path | str) -> None:
        """
        Initialize repository with database connection.

        Args:
            db_path: Path to SQLite database file.
        """
        self.db_path = str(db_path)
        self.engine = create_engine(
            f"sqlite:///{self.db_path}",
            connect_args={"check_same_thread": False},
        )

        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(bind=self.engine)

        logger.info(f"Document repository initialized at {db_path}")

    def _to_model(self, document: Document) -> DocumentModel:
        """Convert domain Document to ORM model."""
        return DocumentModel(
            id=document.id,
            path=str(document.path).replace("\\", "/"),
            relative_path=document.relative_path,
            file_name=document.file_name,
            file_size=document.file_size,
            file_hash=str(document.file_hash),
            doc_type=document.doc_type.value,
            extension=document.extension,
            text_content=document.text_content,
            extraction_success=document.extraction_success,
            extraction_error=document.extraction_error,
            modified_time=document.modified_time,
            created_time=document.created_time,
            accessed_time=document.accessed_time,
            crawled_at=document.crawled_at,
            is_from_archive=document.is_from_archive,
            archive_path=document.archive_path,
        )

    def _to_domain(self, model: DocumentModel) -> Document:
        """Convert ORM model to domain Document."""
        return Document(
            id=model.id,
            path=Path(model.path),
            relative_path=model.relative_path,
            file_name=model.file_name,
            file_size=model.file_size,
            file_hash=FileHash(model.file_hash),
            doc_type=DocumentType(model.doc_type),
            text_content=model.text_content,
            extraction_success=model.extraction_success,
            extraction_error=model.extraction_error,
            modified_time=model.modified_time,
            created_time=model.created_time,
            accessed_time=model.accessed_time,
            crawled_at=model.crawled_at,
            is_from_archive=model.is_from_archive,
            archive_path=model.archive_path,
        )

    def upsert_many(self, documents: list[Document]) -> list[Document]:
        """
        Bulk upsert multiple documents - update if exists, insert if not.
        """
        if not documents:
            return []

        session: Session = self.Session()
        saved_documents: list[Document] = []

        try:
            for doc in documents:
                path_str = str(doc.path).replace("\\", "/")

                existing = (
                    session.query(DocumentModel)
                    .filter(DocumentModel.path == path_str)
                    .first()
                )

                model = self._to_model(doc)

                if existing:
                    model.id = existing.id
                    merged = session.merge(model)
                    session.flush()
                    saved_documents.append(self._to_domain(merged))
                else:
                    session.add(model)
                    session.flush()
                    saved_documents.append(self._to_domain(model))

            session.commit()
            logger.info(f"Upserted {len(saved_documents)} documents")
            return saved_documents

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to upsert documents: {e}")
            if documents:
                logger.error(f"First document path: {documents[0].path}")
            raise
        finally:
            session.close()

    def save(self, document: Document) -> Document:
        """
        Save document to database.

        Args:
            document: Document entity to save.

        Returns:
            Saved document with ID assigned.
        """
        session: Session = self.Session()

        try:
            model = self._to_model(document)
            merged = session.merge(model)
            session.commit()

            if merged.id:
                session.refresh(merged)

            logger.debug(f"Saved document {merged.id}: {merged.path}")
            return self._to_domain(merged)

        except Exception as e:
            session.rollback()
            logger.error(f"Failed to save document: {e}")
            raise
        finally:
            session.close()

    def get_by_id(self, doc_id: int) -> Document | None:
        """Get document by ID."""
        session: Session = self.Session()

        try:
            model = session.get(DocumentModel, doc_id)
            return self._to_domain(model) if model else None
        finally:
            session.close()

    def get_by_path(self, path: Path) -> Document | None:
        """Get document by file path."""
        session: Session = self.Session()

        try:
            search_path = str(path).replace("\\", "/")

            model = (
                session.query(DocumentModel)
                .filter(DocumentModel.path == search_path)
                .first()
            )
            return self._to_domain(model) if model else None
        finally:
            session.close()

    def get_by_hash(self, file_hash: FileHash) -> Document | None:
        """Get document by file hash."""
        session: Session = self.Session()

        try:
            model = (
                session.query(DocumentModel)
                .filter(DocumentModel.file_hash == str(file_hash))
                .first()
            )
            return self._to_domain(model) if model else None
        finally:
            session.close()

    def exists(self, path: Path) -> bool:
        """Check if document exists by path."""
        session: Session = self.Session()

        try:
            search_path = str(path).replace("\\", "/")

            count = (
                session.query(DocumentModel)
                .filter(DocumentModel.path == search_path)
                .count()
            )
            return count > 0
        finally:
            session.close()

    def search_fts(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0,
    ) -> list[Document]:
        """
        Full-text search using SQLite FTS5.

        Args:
            query: Search query (FTS5 syntax).
            limit: Maximum results to return.
            offset: Pagination offset.

        Returns:
            List of matching documents.
        """
        session: Session = self.Session()

        try:
            sql = text(
                """
                SELECT d.*
                FROM documents d
                JOIN documents_fts f ON d.id = f.rowid
                WHERE documents_fts MATCH :query
                ORDER BY f.rank
                LIMIT :limit OFFSET :offset
            """
            )

            result = session.execute(
                sql,
                {"query": query, "limit": limit, "offset": offset},
            )

            documents: list[Document] = []
            for row in result.mappings():
                row_dict = dict(row)
                model = DocumentModel(**row_dict)
                documents.append(self._to_domain(model))

            logger.info(
                f"FTS search for '{query}'",
                results=len(documents),
                limit=limit,
            )

            return documents

        finally:
            session.close()

    def get_stats(self) -> dict[str, Any]:
        """Get database statistics."""
        session: Session = self.Session()

        try:
            total = session.query(DocumentModel).count()
            with_text = (
                session.query(DocumentModel)
                .filter(DocumentModel.extraction_success.is_(True))
                .count()
            )

            type_counts_raw = (
                session.query(
                    DocumentModel.doc_type,
                    func.count(DocumentModel.id).label("count"),
                )
                .group_by(DocumentModel.doc_type)
                .all()
            )

            type_counts: dict[str, int] = {}
            for doc_type, count in type_counts_raw:
                if doc_type is not None:
                    type_counts[str(doc_type)] = int(count)

            total_size = (
                session.query(func.sum(DocumentModel.file_size)).scalar() or 0
            )

            return {
                "total_documents": total,
                "documents_with_text": with_text,
                "documents_without_text": total - with_text,
                "by_type": type_counts,
                "total_size_bytes": int(total_size),
                "total_size_mb": float(total_size) / (1024 * 1024),
            }

        finally:
            session.close()
