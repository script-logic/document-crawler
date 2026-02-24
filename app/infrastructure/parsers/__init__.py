"""
Document parsers package.
"""

from .docx_parser import DOCXParser
from .factory import ParserFactory
from .interfaces import ParseError, Parser
from .pdf_parser import PDFParser
from .txt_parser import TextParser
from .xlsx_parser import XLSXParser

__all__ = [
    "DOCXParser",
    "PDFParser",
    "ParseError",
    "Parser",
    "ParserFactory",
    "TextParser",
    "XLSXParser",
]
