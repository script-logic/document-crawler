"""
SQLAlchemy ORM models with FTS5 support.
"""

from sqlalchemy import (
    Boolean,
    DateTime,
    Index,
    Integer,
    String,
    Text,
    event,
    func,
)
from sqlalchemy.orm import DeclarativeBase, mapped_column
from sqlalchemy.schema import DDL


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy models."""

    pass


class DocumentModel(Base):
    """Main document storage table."""

    __tablename__ = "documents"

    id = mapped_column(Integer, primary_key=True, autoincrement=True)

    path = mapped_column(String(1024), nullable=False, unique=True)
    relative_path = mapped_column(String(1024), nullable=False)
    file_name = mapped_column(String(512), nullable=False)
    file_size = mapped_column(Integer, nullable=False)
    file_hash = mapped_column(String(64), nullable=False, index=True)

    doc_type = mapped_column(String(50), nullable=False)
    extension = mapped_column(String(20), nullable=False)

    text_content = mapped_column(Text, nullable=True)
    extraction_success = mapped_column(Boolean, default=False, nullable=False)
    extraction_error = mapped_column(Text, nullable=True)

    modified_time = mapped_column(DateTime, nullable=False)
    created_time = mapped_column(DateTime, nullable=True)
    accessed_time = mapped_column(DateTime, nullable=True)
    crawled_at = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    is_from_archive = mapped_column(Boolean, default=False, nullable=False)
    archive_path = mapped_column(String(1024), nullable=True)

    metadata_json = mapped_column(Text, nullable=True)

    __table_args__ = (
        Index("ix_documents_file_hash_modified", "file_hash", "modified_time"),
        Index("ix_documents_doc_type_size", "doc_type", "file_size"),
    )

    def __repr__(self) -> str:
        return f"<DocumentModel(id={self.id}, path={self.path})>"


fts_table_ddl = DDL(
    """
    CREATE VIRTUAL TABLE IF NOT EXISTS documents_fts
    USING fts5(
        content=documents,
        content_rowid=id,
        text_content,
        file_name,
        doc_type UNINDEXED,
        tokenize='porter unicode61'
    );
"""
)

fts_insert_trigger = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS documents_fts_insert AFTER INSERT ON documents
    BEGIN
        INSERT INTO documents_fts(rowid, text_content, file_name, doc_type)
        VALUES (new.id, new.text_content, new.file_name, new.doc_type);
    END;
"""
)

fts_update_trigger = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS documents_fts_update AFTER UPDATE ON documents
    BEGIN
        DELETE FROM documents_fts WHERE rowid = old.id;
        INSERT INTO documents_fts(rowid, text_content, file_name, doc_type)
        VALUES (new.id, new.text_content, new.file_name, new.doc_type);
    END;
"""
)

fts_delete_trigger = DDL(
    """
    CREATE TRIGGER IF NOT EXISTS documents_fts_delete AFTER DELETE ON documents
    BEGIN
        DELETE FROM documents_fts WHERE rowid = old.id;
    END;
"""
)

event.listen(
    DocumentModel.__table__,
    "after_create",
    fts_table_ddl.execute_if(dialect="sqlite"),
)
event.listen(
    DocumentModel.__table__,
    "after_create",
    fts_insert_trigger.execute_if(dialect="sqlite"),
)
event.listen(
    DocumentModel.__table__,
    "after_create",
    fts_update_trigger.execute_if(dialect="sqlite"),
)
event.listen(
    DocumentModel.__table__,
    "after_create",
    fts_delete_trigger.execute_if(dialect="sqlite"),
)
