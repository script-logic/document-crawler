"""
Base classes for document parsers.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import ClassVar

from structlog import get_logger

from app.domain.entities import DocumentType

from .interfaces import ParseError, Parser

logger = get_logger(__name__)


class BaseParser(ABC, Parser):
    """
    Base class for all document parsers.

    Provides common functionality and enforces the interface.
    """

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = set()
    SUPPORTED_MIME_TYPES: ClassVar[set[str]] = set()
    DOCUMENT_TYPE: ClassVar[DocumentType] = DocumentType.UNKNOWN

    def can_parse(self, file_path: Path) -> bool:
        """
        Check if file can be parsed based on extension.

        Args:
            file_path: Path to the file.

        Returns:
            True if file extension is supported.
        """
        if not self.SUPPORTED_EXTENSIONS:
            logger.warning(
                f"Parser {self.__class__.__name__} has no supported extensions"
            )
            return False

        ext = file_path.suffix.lower().lstrip(".")
        return ext in self.SUPPORTED_EXTENSIONS

    @abstractmethod
    def _extract_text(self, file_path: Path) -> str:
        """
        Actual text extraction implementation.

        Args:
            file_path: Path to the file.

        Returns:
            Extracted text.

        Raises:
            ParseError: If extraction fails.
        """
        pass

    def parse(self, file_path: Path) -> str:
        """
        Extract text with error handling and logging.

        Args:
            file_path: Path to the file.

        Returns:
            Extracted text.

        Raises:
            ParseError: If parsing fails.
        """
        logger.debug(
            "Parsing document",
            file=str(file_path),
            parser=self.__class__.__name__,
        )

        try:
            text = self._extract_text(file_path)

            text = self._clean_text(text)

            logger.debug(
                "Successfully parsed document",
                file=str(file_path),
                text_length=len(text),
            )

            return text

        except ParseError:
            raise
        except Exception as e:
            logger.exception(
                "Failed to parse document",
                file=str(file_path),
                error=str(e),
            )
            raise ParseError(
                f"Unexpected error: {e}",
                file_path=file_path,
                original_error=e,
            ) from e

    def _clean_text(self, text: str) -> str:
        """
        Basic text cleaning.

        Args:
            text: Raw extracted text.

        Returns:
            Cleaned text.
        """
        if not text:
            return ""

        text = "".join(
            char if char >= " " or char in "\n\t" else " " for char in text
        )

        return text.strip()

    def extract_metadata(self, file_path: Path) -> dict[str, str | int | None]:
        """
        Default metadata extraction (to be overridden).

        Args:
            file_path: Path to the file.

        Returns:
            Empty dict or basic metadata.
        """
        return {}
