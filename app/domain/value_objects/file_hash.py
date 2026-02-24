"""
File hash value object for deduplication and integrity checking.
"""

import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class FileHash:
    """
    File hash value object using SHA-256.

    Attributes:
        value: Hexadecimal SHA-256 hash string.
    """

    value: str

    def __init__(self, value: str | Path | bytes) -> None:
        """
        Create hash from string, file path, or bytes.

        Args:
            value: Either:
                - Existing hash string (64 hex chars)
                - Path to file to hash
                - Bytes to hash

        Raises:
            ValueError: If hash is invalid or file cannot be read.
        """
        if isinstance(value, Path):
            hash_value = self._hash_file(value)
        elif isinstance(value, bytes):
            hash_value = self._hash_bytes(value)
        else:
            hash_value = str(value)

        self._validate_hash(hash_value)
        object.__setattr__(self, "value", hash_value)

    @staticmethod
    def _hash_file(path: Path) -> str:
        """Calculate SHA-256 hash of file contents."""
        sha256 = hashlib.sha256()
        try:
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except OSError as e:
            raise ValueError(f"Cannot read file {path}: {e}") from e

    @staticmethod
    def _hash_bytes(data: bytes) -> str:
        """Calculate SHA-256 hash of bytes."""
        return hashlib.sha256(data).hexdigest()

    @staticmethod
    def _validate_hash(hash_str: str) -> None:
        """Validate hash format."""
        if len(hash_str) != 64:
            raise ValueError(
                f"Hash must be 64 hex characters, got {len(hash_str)}"
            )
        try:
            int(hash_str, 16)
        except ValueError as e:
            raise ValueError(f"Invalid hex characters in hash: {e}") from e

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return f"FileHash('{self.value}')"
