"""
Interfaces for document parsers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar, Protocol, runtime_checkable

from app.domain.entities import DocumentType


@runtime_checkable
class Parser(Protocol):
    """
    Protocol defining the interface for all document parsers.

    Each parser should be able to:
    1. Check if it can handle a given file
    2. Extract text content from the file
    3. Extract metadata when possible
    """

    SUPPORTED_EXTENSIONS: ClassVar[set[str]]
    SUPPORTED_MIME_TYPES: ClassVar[set[str]]
    DOCUMENT_TYPE: ClassVar[DocumentType]

    def can_parse(self, file_path: Path) -> bool:
        """
        Check if this parser can handle the given file.

        Args:
            file_path: Path to the file to check.

        Returns:
            True if this parser can parse the file, False otherwise.
        """
        ...

    def parse(self, file_path: Path) -> str:
        """
        Extract text content from the file.

        Args:
            file_path: Path to the file to parse.

        Returns:
            Extracted text content as string.

        Raises:
            ParseError: If parsing fails for any reason.
        """
        ...

    def extract_metadata(self, file_path: Path) -> dict[str, str | int | None]:
        """
        Extract metadata from the file (optional).

        Args:
            file_path: Path to the file.

        Returns:
            Dictionary with metadata (author, page_count, etc.).
        """
        ...


class ParseError(Exception):
    """Raised when document parsing fails."""

    def __init__(
        self,
        message: str,
        file_path: Path,
        original_error: Exception | None = None,
    ) -> None:
        self.file_path = file_path
        self.original_error = original_error
        super().__init__(f"Failed to parse {file_path}: {message}")


class BaseParserFactory(ABC):
    """Factory for creating appropriate parsers."""

    @abstractmethod
    def get_parser(self, doc_type: DocumentType) -> Parser | None:
        """
        Get parser for specific document type.

        Args:
            doc_type: Type of document to parse.

        Returns:
            Parser instance or None if no parser available.
        """
        pass

    @abstractmethod
    def get_parser_for_file(self, file_path: Path) -> Parser | None:
        """
        Get parser that can handle the given file.

        Args:
            file_path: Path to the file.

        Returns:
            Parser instance or None if no parser available.
        """
        pass
