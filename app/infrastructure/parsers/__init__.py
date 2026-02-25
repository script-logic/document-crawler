"""
Document parsers package.
"""

from .doc_parser import DOCParser
from .docx_parser import DOCXParser
from .factory import ParserFactory
from .interfaces import ParseError, Parser
from .pdf_parser import PDFParser
from .txt_parser import TextParser
from .xls_parser import XLSParser
from .xlsx_parser import XLSXParser

__all__ = [
    "DOCParser",
    "DOCXParser",
    "PDFParser",
    "ParseError",
    "Parser",
    "ParserFactory",
    "TextParser",
    "XLSParser",
    "XLSXParser",
]
