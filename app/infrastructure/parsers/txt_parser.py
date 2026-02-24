"""
Plain text file parser.
"""

from pathlib import Path
from typing import ClassVar

from app.domain.entities import DocumentType

from .base_parser import BaseParser
from .interfaces import ParseError


class TextParser(BaseParser):
    """Parser for plain text files."""

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {
        "txt",
        "md",
        "markdown",
        "json",
        "xml",
        "html",
        "htm",
        "csv",
    }
    DOCUMENT_TYPE: ClassVar[DocumentType] = DocumentType.TXT

    def _extract_text(self, file_path: Path) -> str:
        """
        Read text file with encoding detection.

        Args:
            file_path: Path to text file.

        Returns:
            File contents as string.

        Raises:
            ParseError: If file cannot be read.
        """
        encodings = ["utf-8", "cp1251", "latin-1", "utf-16"]

        for encoding in encodings:
            try:
                with open(file_path, encoding=encoding) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except FileNotFoundError as e:
                raise ParseError("File not found", file_path=file_path) from e
            except PermissionError as e:
                raise ParseError(
                    "Permission denied", file_path=file_path
                ) from e
            except Exception as e:
                raise ParseError(
                    f"Failed to read file: {e}",
                    file_path=file_path,
                    original_error=e,
                ) from e

        raise ParseError(
            "Could not determine file encoding",
            file_path=file_path,
        )
