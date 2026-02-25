# app/infrastructure/parsers/xls_parser.py
"""
Legacy XLS parser using xlrd.
"""

from pathlib import Path
from typing import ClassVar

import xlrd
from structlog import get_logger
from xlrd.biffh import XLRDError

from app.domain.entities import DocumentType

from .base_parser import BaseParser
from .interfaces import ParseError

logger = get_logger(__name__)


class XLSParser(BaseParser):
    """Parser for legacy XLS spreadsheets."""

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {"xls"}
    DOCUMENT_TYPE: ClassVar[DocumentType] = DocumentType.XLS

    def _extract_text(self, file_path: Path) -> str:
        """
        Extract text from XLS using xlrd.

        Args:
            file_path: Path to XLS file.

        Returns:
            Extracted text from all cells in all sheets.

        Raises:
            ParseError: If XLS cannot be read.
        """
        try:
            workbook = xlrd.open_workbook(
                str(file_path), encoding_override="utf-8"
            )
            text_parts: list[str] = []

            for sheet_idx in range(workbook.nsheets):
                sheet = workbook.sheet_by_index(sheet_idx)
                text_parts.append(f"--- Sheet: {sheet.name} ---")

                for row_idx in range(sheet.nrows):
                    row_values: list[str] = []
                    for col_idx in range(sheet.ncols):
                        cell = sheet.cell(row_idx, col_idx)

                        if cell.ctype != 0:
                            value = str(cell.value)
                            if value.strip():
                                row_values.append(value)

                    if row_values:
                        text_parts.append(" | ".join(row_values))

            return "\n".join(text_parts)

        except XLRDError as e:
            raise ParseError(
                f"Invalid XLS file: {e}",
                file_path=file_path,
                original_error=e,
            ) from e
        except FileNotFoundError as e:
            raise ParseError("File not found", file_path=file_path) from e
        except PermissionError as e:
            raise ParseError("Permission denied", file_path=file_path) from e
        except Exception as e:
            raise ParseError(
                f"XLS parsing failed: {e}",
                file_path=file_path,
                original_error=e,
            ) from e
