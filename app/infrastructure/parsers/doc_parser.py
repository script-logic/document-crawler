"""
Legacy DOC document parser using antiword or catdoc.
"""

import subprocess
from pathlib import Path
from typing import ClassVar

from structlog import get_logger

from app.domain.entities import DocumentType

from .base_parser import BaseParser
from .interfaces import ParseError

logger = get_logger(__name__)


class DOCParser(BaseParser):
    """Parser for legacy DOC documents using external tools."""

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {"doc"}
    DOCUMENT_TYPE: ClassVar[DocumentType] = DocumentType.DOC

    def _extract_text(self, file_path: Path) -> str:
        """
        Extract text from DOC using antiword or catdoc.

        Tries antiword first (better formatting), falls back to catdoc.

        Args:
            file_path: Path to DOC file.

        Returns:
            Extracted text.

        Raises:
            ParseError: If extraction fails.
        """
        try:
            result = subprocess.run(
                ["antiword", str(file_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            logger.debug("antiword not available, trying catdoc")

        try:
            result = subprocess.run(
                ["catdoc", str(file_path)],
                capture_output=True,
                text=True,
                check=True,
            )
            return result.stdout
        except subprocess.SubprocessError as e:
            raise ParseError(
                "Failed to extract text from DOC (install antiword or catdoc)",
                file_path=file_path,
                original_error=e,
            ) from e
        except FileNotFoundError as e:
            raise ParseError(
                "Neither antiword nor catdoc found. "
                "Please install one of them.",
                file_path=file_path,
                original_error=e,
            ) from e
