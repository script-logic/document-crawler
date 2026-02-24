"""
Factory for creating appropriate document parsers.
"""

from pathlib import Path

from structlog import get_logger

from app.domain.entities import DocumentType

from .docx_parser import DOCXParser
from .interfaces import Parser
from .pdf_parser import PDFParser
from .txt_parser import TextParser
from .xlsx_parser import XLSXParser

logger = get_logger(__name__)


class ParserFactory:
    """
    Factory that provides appropriate parsers for document types.

    Uses lazy initialization of parsers to avoid unnecessary imports.
    """

    def __init__(self) -> None:
        """Initialize factory with empty parser registry."""
        self._parsers_by_type: dict[DocumentType, Parser] = {}
        self._parsers_by_ext: dict[str, Parser] = {}
        self._initialize_parsers()

    def _initialize_parsers(self) -> None:
        """Register all available parsers."""
        parsers: list[Parser] = [
            PDFParser(),
            DOCXParser(),
            XLSXParser(),
            TextParser(),
        ]

        for parser in parsers:
            if hasattr(parser, "DOCUMENT_TYPE"):
                doc_type = parser.DOCUMENT_TYPE
                if doc_type and doc_type != DocumentType.UNKNOWN:
                    self._parsers_by_type[doc_type] = parser

            if hasattr(parser, "SUPPORTED_EXTENSIONS"):
                extensions = parser.SUPPORTED_EXTENSIONS
                for ext in extensions:
                    if ext in self._parsers_by_ext:
                        logger.warning(
                            f"Overwriting parser for extension .{ext}"
                        )
                    self._parsers_by_ext[ext] = parser

        logger.info(
            "Parser factory initialized",
            parsers_count=len(parsers),
            extensions_count=len(self._parsers_by_ext),
        )

    def get_parser(self, doc_type: DocumentType) -> Parser | None:
        """
        Get parser for specific document type.

        Args:
            doc_type: Type of document to parse.

        Returns:
            Parser instance or None if no parser available.
        """
        parser = self._parsers_by_type.get(doc_type)

        if not parser:
            logger.debug(f"No parser registered for type: {doc_type}")

        return parser

    def get_parser_for_file(self, file_path: Path) -> Parser | None:
        """
        Get parser that can handle the given file based on extension.

        Args:
            file_path: Path to the file.

        Returns:
            Parser instance or None if no parser available.
        """
        ext = file_path.suffix.lower().lstrip(".")

        parser = self._parsers_by_ext.get(ext)

        if not parser:
            logger.debug(f"No parser registered for extension: .{ext}")

        return parser

    def register_parser(self, parser: Parser) -> None:
        """
        Register a new parser dynamically.

        Args:
            parser: Parser instance to register.
        """
        if hasattr(parser, "DOCUMENT_TYPE"):
            doc_type = parser.DOCUMENT_TYPE
            if doc_type:
                self._parsers_by_type[doc_type] = parser

        if hasattr(parser, "SUPPORTED_EXTENSIONS"):
            extensions = parser.SUPPORTED_EXTENSIONS
            for ext in extensions:
                self._parsers_by_ext[ext] = parser

        logger.info(f"Registered new parser: {parser.__class__.__name__}")
