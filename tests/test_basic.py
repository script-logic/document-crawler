"""Basic tests to verify imports work."""

from app.config import get_config
from app.domain.entities import DocumentType
from app.domain.value_objects import FileHash
from app.infrastructure.parsers import ParserFactory


def test_imports():
    """Test that all imports work."""
    config = get_config()
    assert config is not None

    factory = ParserFactory()
    assert factory is not None

    doc_type = DocumentType.from_extension(".pdf")
    assert doc_type == DocumentType.PDF


def test_file_hash():
    """Test FileHash creation."""
    hash_str = "a" * 64
    file_hash = FileHash(hash_str)
    assert str(file_hash) == hash_str
    assert len(file_hash.value) == 64
