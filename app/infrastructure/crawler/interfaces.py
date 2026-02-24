"""
Interfaces for file crawler.
"""

from collections.abc import Iterator
from pathlib import Path
from typing import Protocol, runtime_checkable


@runtime_checkable
class FileScanner(Protocol):
    """
    Protocol for file system scanners.

    Responsible for traversing directories and finding files.
    """

    def scan(self, root_path: Path) -> Iterator[Path]:
        """
        Scan directory and yield file paths.

        Args:
            root_path: Root directory to scan.

        Yields:
            Path objects for each file found.
        """
        ...


@runtime_checkable
class ArchiveExtractor(Protocol):
    """
    Protocol for archive extractors.

    Responsible for extracting files from archives (zip, rar, 7z).
    """

    def can_extract(self, archive_path: Path) -> bool:
        """
        Check if this extractor can handle the archive.

        Args:
            archive_path: Path to archive file.

        Returns:
            True if this extractor can extract the archive.
        """
        ...

    def extract(self, archive_path: Path) -> Iterator[tuple[Path, bytes]]:
        """
        Extract files from archive.

        Args:
            archive_path: Path to archive file.

        Yields:
            Tuples of (file_path_inside_archive, file_contents).
        """
        ...


class CrawlerError(Exception):
    """Base exception for crawler errors."""

    def __init__(self, message: str, path: Path | None = None) -> None:
        self.path = path
        super().__init__(f"{message}: {path}" if path else message)


class FileTooLargeError(CrawlerError):
    """Raised when file exceeds size limit."""

    def __init__(self, path: Path, size: int, limit: int) -> None:
        self.size = size
        self.limit = limit
        super().__init__(
            f"File too large: {size} bytes > {limit} bytes",
            path=path,
        )


class UnsupportedFileTypeError(CrawlerError):
    """Raised when file type is not supported."""

    def __init__(self, path: Path, reason: str = "") -> None:
        msg = "Unsupported file type"
        if reason:
            msg += f": {reason}"
        super().__init__(msg, path=path)
