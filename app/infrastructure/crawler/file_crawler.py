"""
File system crawler implementation.
"""

import os
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path

from structlog import get_logger

from app.domain.entities import Document, DocumentType
from app.domain.value_objects import FileHash
from app.infrastructure.parsers import ParseError, ParserFactory

from .interfaces import (
    ArchiveExtractor,
    CrawlerError,
    FileScanner,
    FileTooLargeError,
)

logger = get_logger(__name__)


class FileSystemScanner:
    """
    Simple file system scanner that walks directories.
    """

    def __init__(
        self,
        skip_hidden: bool = True,
        follow_symlinks: bool = False,
        max_depth: int | None = None,
    ) -> None:
        """
        Initialize scanner.

        Args:
            skip_hidden: Whether to skip hidden files/directories.
            follow_symlinks: Whether to follow symbolic links.
            max_depth: Maximum directory depth to traverse (None = unlimited).
        """
        self.skip_hidden = skip_hidden
        self.follow_symlinks = follow_symlinks
        self.max_depth = max_depth

    def _is_hidden(self, path: Path) -> bool:
        """Check if file or directory is hidden."""
        if os.name == "nt":
            try:
                attrs = os.stat(str(path)).st_file_attributes
                return bool(attrs & 2)
            except (OSError, AttributeError):
                return path.name.startswith(".")
        else:
            return path.name.startswith(".")

    def scan(self, root_path: Path) -> Iterator[Path]:
        """
        Recursively scan directory and yield file paths.

        Args:
            root_path: Root directory to scan.

        Yields:
            Path objects for each file found.

        Raises:
            FileNotFoundError: If root_path doesn't exist.
            NotADirectoryError: If root_path is not a directory.
        """
        if not root_path.exists():
            raise FileNotFoundError(f"Path does not exist: {root_path}")

        if not root_path.is_dir():
            raise NotADirectoryError(f"Path is not a directory: {root_path}")

        logger.info(f"Starting scan of {root_path}")

        file_count = 0
        dir_count = 0
        skipped_count = 0

        for root, dirs, files in os.walk(
            str(root_path),
            followlinks=self.follow_symlinks,
            topdown=True,
        ):
            current_path = Path(root)

            if self.max_depth is not None:
                rel_depth = len(current_path.relative_to(root_path).parts)
                if rel_depth > self.max_depth:
                    dirs.clear()
                    continue

            if self.skip_hidden:
                dirs[:] = [
                    d for d in dirs if not self._is_hidden(current_path / d)
                ]

            for file_name in files:
                file_path = current_path / file_name

                if self.skip_hidden and self._is_hidden(file_path):
                    skipped_count += 1
                    continue

                yield file_path
                file_count += 1

                if file_count % 1000 == 0:
                    logger.debug(f"Found {file_count} files so far...")

            dir_count += len(dirs)

        logger.info(
            "Scan complete",
            files_found=file_count,
            directories=dir_count,
            skipped=skipped_count,
        )


class FileCrawler:
    """
    Main crawler that orchestrates file discovery, parsing, and
    document creation.
    """

    def __init__(
        self,
        parser_factory: ParserFactory,
        scanner: FileScanner | None = None,
        archive_extractor: ArchiveExtractor | None = None,
        max_file_size_mb: int = 100,
        storage_root: Path | None = None,
    ) -> None:
        """
        Initialize crawler.

        Args:
            parser_factory: Factory for creating document parsers.
            scanner: File system scanner (creates default if None).
            archive_extractor: Archive extractor (None = skip archives).
            max_file_size_mb: Maximum file size in MB to process.
            storage_root: Root path for calculating relative paths.
        """
        self.parser_factory = parser_factory
        self.scanner = scanner or FileSystemScanner()
        self.archive_extractor = archive_extractor
        self.max_file_size = max_file_size_mb * 1024 * 1024
        self.storage_root = storage_root
        self.archive_temp_dir: Path | None = None

    def _get_relative_path(self, file_path: Path) -> str:
        """Get path relative to storage root."""
        if self.storage_root:
            try:
                rel_path = str(file_path.relative_to(self.storage_root))
            except ValueError:
                rel_path = file_path.name
        else:
            rel_path = file_path.name

        return rel_path.replace("\\", "/")

    def _check_file_size(self, file_path: Path) -> None:
        """Check if file exceeds size limit."""
        try:
            size = file_path.stat().st_size
            if size > self.max_file_size:
                raise FileTooLargeError(file_path, size, self.max_file_size)
        except OSError as e:
            raise CrawlerError("Cannot access file", path=file_path) from e

    def _create_document(
        self,
        file_path: Path,
        relative_path: str,
        text_content: str | None = None,
        extraction_success: bool = False,
        extraction_error: str | None = None,
        is_from_archive: bool = False,
        archive_path: str | None = None,
        is_virtual: bool = False,
    ) -> Document | None:
        """
        Create Document entity from file.

        Args:
            file_path: Path to the file (real or virtual).
            text_content: Extracted text (if any).
            extraction_success: Whether extraction succeeded.
            extraction_error: Error message if extraction failed.
            is_from_archive: Whether file is from archive.
            archive_path: Path to source archive if from archive.
            is_virtual: Whether file is virtual (not on disk).

        Returns:
            Document entity or None if file cannot be processed.
        """
        try:
            if is_virtual:
                file_size = len(text_content) if text_content else 0
                modified_time = datetime.now()
                created_time = None
                accessed_time = None
                file_hash_val = FileHash(
                    text_content.encode() if text_content else b""
                )
            else:
                stat = file_path.stat()
                file_size = stat.st_size
                modified_time = datetime.fromtimestamp(stat.st_mtime)

                created_time = None
                if hasattr(stat, "st_birthtime"):
                    birthtime = stat.st_birthtime  # type: ignore[attr-defined]
                    created_time = datetime.fromtimestamp(birthtime)
                elif hasattr(stat, "st_ctime"):
                    ctime = stat.st_ctime  # pyright: ignore[reportDeprecated]
                    created_time = datetime.fromtimestamp(ctime)

                accessed_time = (
                    datetime.fromtimestamp(stat.st_atime)
                    if hasattr(stat, "st_atime")
                    else None
                )

                file_hash_val = FileHash(file_path)

            doc_type = DocumentType.from_extension(file_path.suffix)

            return Document(
                path=relative_path,
                relative_path=relative_path,
                file_name=file_path.name,
                file_size=file_size,
                file_hash=file_hash_val,
                doc_type=doc_type,
                text_content=text_content,
                extraction_success=extraction_success,
                extraction_error=extraction_error,
                modified_time=modified_time,
                created_time=created_time,
                accessed_time=accessed_time,
                is_from_archive=is_from_archive,
                archive_path=archive_path,
                is_virtual=is_virtual,
            )

        except (OSError, ValueError) as e:
            logger.error(
                "Failed to create document from file",
                file=str(file_path),
                error=str(e),
            )
            return None

    def is_archive(self, file_path: Path) -> bool:
        """
        Check if file is an archive that can be extracted.

        Args:
            file_path: Path to file.

        Returns:
            True if file is an archive and extractor is available.
        """
        return bool(
            self.archive_extractor
            and self.archive_extractor.can_extract(file_path)
        )

    def crawl_file(self, file_path: Path) -> Document | None:
        """
        Crawl a single file: extract text and create document.
        If file is an archive, returns None (archives are handled separately).

        Args:
            file_path: Path to file to crawl.

        Returns:
            Document entity or None if file cannot be processed or is archive.
        """
        rel_path = self._get_relative_path(file_path)
        logger.debug(f"Crawling file: {file_path}")

        if self.is_archive(file_path):
            logger.debug(
                "Skipping archive file (will be processed separately): "
                f"{file_path}"
            )
            return None

        try:
            self._check_file_size(file_path)
        except FileTooLargeError as e:
            logger.warning(f"File too large: {file_path}")
            return self._create_document(
                file_path,
                relative_path=rel_path,
                extraction_error=str(e),
            )

        parser = self.parser_factory.get_parser_for_file(file_path)
        if not parser:
            logger.debug(f"No parser for file: {file_path}")
            return self._create_document(
                file_path,
                relative_path=rel_path,
                extraction_error="No parser available",
            )

        try:
            text_content = parser.parse(file_path)
            return self._create_document(
                file_path,
                relative_path=rel_path,
                text_content=text_content,
                extraction_success=True,
            )

        except ParseError as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return self._create_document(
                file_path,
                relative_path=rel_path,
                extraction_error=str(e),
            )

    def crawl_directory(self, root_path: Path) -> Iterator[Document]:
        """
        Crawl entire directory, processing all files.

        Args:
            root_path: Root directory to crawl.

        Yields:
            Document entities for each processed file.
        """
        logger.info(f"Starting directory crawl: {root_path}")

        processed = 0
        failed = 0

        for file_path in self.scanner.scan(root_path):
            try:
                doc = self.crawl_file(file_path)
                if doc:
                    yield doc
                    processed += 1
                else:
                    failed += 1

                if (processed + failed) % 100 == 0:
                    logger.info(
                        "Crawl progress",
                        processed=processed,
                        failed=failed,
                        total=processed + failed,
                    )

            except Exception as e:
                logger.exception(
                    f"Unexpected error processing {file_path}",
                    error=str(e),
                )
                failed += 1

        logger.info(
            "Crawl complete",
            processed=processed,
            failed=failed,
        )

    def scan_directory(self, root_path: Path) -> Iterator[Path]:
        """
        Scan directory and yield file paths (wrapper for scanner.scan).

        Args:
            root_path: Root directory to scan.

        Yields:
            Path objects for each file found.
        """
        yield from self.scanner.scan(root_path)
