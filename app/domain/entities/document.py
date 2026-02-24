"""
Document entity representing a crawled file.
"""

from datetime import datetime
from enum import StrEnum, auto
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

from app.domain.value_objects.file_hash import FileHash


class DocumentType(StrEnum):
    """Supported document types."""

    PDF = auto()
    DOCX = auto()
    XLSX = auto()
    TXT = auto()
    MD = "markdown"
    JSON = auto()
    XML = auto()
    HTML = auto()
    UNKNOWN = auto()

    @classmethod
    def from_extension(cls, ext: str) -> "DocumentType":
        """
        Determine document type from file extension.

        Args:
            ext: File extension (with or without dot).

        Returns:
            DocumentType enum value.
        """
        ext = ext.lower().lstrip(".")
        mapping = {
            "pdf": cls.PDF,
            "docx": cls.DOCX,
            "xlsx": cls.XLSX,
            "txt": cls.TXT,
            "md": cls.MD,
            "markdown": cls.MD,
            "json": cls.JSON,
            "xml": cls.XML,
            "html": cls.HTML,
            "htm": cls.HTML,
        }
        return mapping.get(ext, cls.UNKNOWN)


class Document(BaseModel):
    """
    Document domain entity.

    Represents a file discovered by crawler with its metadata and content.
    """

    id: int | None = Field(
        default=None, description="Database ID (if persisted)"
    )
    path: Path = Field(
        ..., description="Path to file (real or virtual for archives)"
    )
    relative_path: str = Field(
        ...,
        description="Path relative to storage root (or virtual for archives)",
    )
    file_name: str = Field(..., description="File name with extension")
    file_size: int = Field(..., gt=0, description="File size in bytes")
    file_hash: FileHash = Field(..., description="SHA-256 hash of content")
    doc_type: DocumentType = Field(..., description="Detected document type")
    content_type: str | None = Field(
        default=None, description="MIME type if available"
    )

    text_content: str | None = Field(
        default=None, description="Extracted text for indexing"
    )
    extraction_success: bool = Field(
        default=False, description="Whether text extraction succeeded"
    )
    extraction_error: str | None = Field(
        default=None, description="Error message if extraction failed"
    )

    modified_time: datetime = Field(..., description="File modification time")
    created_time: datetime | None = Field(
        default=None, description="File creation time (if available)"
    )
    accessed_time: datetime | None = Field(
        default=None, description="File access time (if available)"
    )

    crawled_at: datetime = Field(
        default_factory=datetime.now,
        description="When this file was crawled",
    )
    is_from_archive: bool = Field(
        default=False,
        description="Whether file was extracted from archive",
    )
    archive_path: str | None = Field(
        default=None,
        description="Path to source archive if from archive",
    )
    is_virtual: bool = Field(
        default=False,
        description="Whether file is virtual (from archive, not on disk)",
    )

    @field_validator("path", mode="before")
    @classmethod
    def validate_path(cls, v: Path | str) -> Path:
        """Ensure path is Path object."""
        return Path(v) if isinstance(v, str) else v

    @field_validator("file_size")
    @classmethod
    def validate_size(cls, v: int) -> int:
        """Validate file size is positive and reasonable."""
        if v <= 0:
            raise ValueError(f"File size must be positive: {v}")
        if v > 10 * 1024 * 1024 * 1024:
            raise ValueError(f"File too large ( >10GB): {v}")
        return v

    @field_validator("relative_path")
    @classmethod
    def validate_relative_path(cls, v: str) -> str:
        """Prevent path traversal."""
        if ".." in v.split("/") or ".." in v.split("\\"):
            raise ValueError(f"Path traversal detected: {v}")
        return v

    @property
    def extension(self) -> str:
        """Get file extension without dot."""
        return self.path.suffix.lower().lstrip(".")

    @property
    def stem(self) -> str:
        """Get file name without extension."""
        return self.path.stem

    @property
    def has_text(self) -> bool:
        """Check if document has extracted text."""
        return bool(self.text_content and self.text_content.strip())

    @property
    def display_path(self) -> str:
        """
        Get user-friendly display path.
        For archive files, shows archive:internal_path format.
        For virtual files, shows the virtual path.
        For regular files, shows the real path.
        """
        if self.is_from_archive and self.archive_path:
            archive_name = Path(self.archive_path).name
            return f"{archive_name}:{self.relative_path}"
        return str(self.path)

    model_config = {
        "frozen": True,
        "json_encoders": {
            Path: str,
            FileHash: str,
            datetime: lambda v: v.isoformat(),
        },
    }
