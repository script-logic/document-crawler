"""
PDF document parser using PyPDF2.
"""

from pathlib import Path
from typing import Any, ClassVar, cast

import PyPDF2
from structlog import get_logger

from app.domain.entities import DocumentType

from .base_parser import BaseParser
from .interfaces import ParseError


class PDFParser(BaseParser):
    """Parser for PDF documents."""

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {"pdf"}
    DOCUMENT_TYPE: ClassVar[DocumentType] = DocumentType.PDF

    def _extract_text(self, file_path: Path) -> str:
        """
        Extract text from PDF using PyPDF2.

        Args:
            file_path: Path to PDF file.

        Returns:
            Extracted text from all pages.

        Raises:
            ParseError: If PDF cannot be read or decrypted.
        """
        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)

                if reader.is_encrypted:
                    try:
                        reader.decrypt("")
                    except Exception as e:
                        raise ParseError(
                            "Encrypted PDF - decryption failed",
                            file_path=file_path,
                        ) from e

                text_parts: list[str] = []
                for page_num, page in enumerate(reader.pages, 1):
                    try:
                        text = page.extract_text()
                        if text:
                            text_parts.append(text)
                    except Exception as e:
                        raise ParseError(
                            f"Failed to extract page {page_num}: {e}",
                            file_path=file_path,
                            original_error=e,
                        ) from e

                return "\n\n".join(text_parts)

        except FileNotFoundError as e:
            raise ParseError("File not found", file_path=file_path) from e
        except PermissionError as e:
            raise ParseError("Permission denied", file_path=file_path) from e
        except Exception as e:
            raise ParseError(
                f"PDF parsing failed: {e}",
                file_path=file_path,
                original_error=e,
            ) from e

    def extract_metadata(self, file_path: Path) -> dict[str, str | int | None]:
        """
        Extract PDF metadata.

        Returns:
            Dict with author, page_count, etc.
        """
        try:
            with open(file_path, "rb") as file:
                reader = PyPDF2.PdfReader(file)

                metadata: dict[str, str | int | None] = {}

                metadata["page_count"] = len(reader.pages)

                if reader.metadata:
                    metadata_dict = cast(dict[str, Any], reader.metadata)

                    for key, value in metadata_dict.items():
                        if value is not None:
                            clean_key = str(key).strip("/").lower()
                            metadata[clean_key] = str(value)

                return metadata

        except Exception as e:
            logger = get_logger(__name__)
            logger.warning(
                "Failed to extract PDF metadata",
                file=str(file_path),
                error=str(e),
            )
            return {}
