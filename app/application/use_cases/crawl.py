"""
Crawl use case: Scan storage, parse documents, save to database and CSV.
"""

import csv
import tempfile
from collections.abc import Iterator
from datetime import datetime
from pathlib import Path
from typing import Any

from structlog import get_logger

from app.config import AppConfig
from app.domain.entities import Document, DocumentType
from app.domain.value_objects import FileHash
from app.infrastructure.crawler import (
    ArchiveExtractor,
    FileCrawler,
    PatoolArchiveExtractor,
)
from app.infrastructure.database import DocumentRepository
from app.infrastructure.parsers import ParseError, ParserFactory

logger = get_logger(__name__)


class CrawlUseCase:
    """
    Orchestrates the crawling process:
    1. Scan storage directory
    2. Parse documents (including archives)
    3. Save to database
    4. Export to CSV
    """

    def __init__(
        self,
        config: AppConfig,
        repository: DocumentRepository | None = None,
        crawler: FileCrawler | None = None,
    ) -> None:
        """
        Initialize crawl use case.

        Args:
            config: Application configuration.
            repository: Document repository (creates default if None).
            crawler: File crawler (creates default if None).
        """
        self.config = config

        self.repository = repository or DocumentRepository(
            config.database.path
        )

        parser_factory = ParserFactory()

        archive_extractor = None
        if config.crawler.extract_archives:
            archive_extractor = PatoolArchiveExtractor(
                max_depth=config.crawler.max_archive_depth,
            )

        self.crawler = crawler or FileCrawler(
            parser_factory=parser_factory,
            archive_extractor=archive_extractor,
            max_file_size_mb=config.crawler.max_file_size_mb,
            storage_root=config.crawler.storage_path,
        )

        self.stats: dict[str, Any] = {
            "files_found": 0,
            "files_processed": 0,
            "files_failed": 0,
            "files_skipped": 0,
            "archives_extracted": 0,
            "start_time": None,
            "end_time": None,
        }

    def _should_process(self, file_path: Path) -> bool:
        """
        Check if file should be processed (not already in DB with same hash).

        Args:
            file_path: Path to file.

        Returns:
            True if file should be processed, False if it can be skipped.
        """
        existing = self.repository.get_by_path(file_path)

        if not existing:
            return True

        try:
            current_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            if existing.modified_time < current_mtime:
                logger.debug(f"File modified, reprocessing: {file_path}")
                return True
        except OSError:
            return True

        logger.debug(f"File unchanged, skipping: {file_path}")
        return False

    def _process_archive(
        self,
        archive_path: Path,
        extractor: ArchiveExtractor,
    ) -> Iterator[Document]:
        """
        Process archive and yield documents from extracted files.

        Args:
            archive_path: Path to archive.
            extractor: Archive extractor instance.

        Yields:
            Documents from files inside archive with proper paths.
        """
        logger.info(f"Processing archive: {archive_path}")

        if self.config.crawler.storage_path:
            try:
                archive_rel_path = str(
                    archive_path.relative_to(self.config.crawler.storage_path)
                )
            except ValueError:
                archive_rel_path = archive_path.name
        else:
            archive_rel_path = archive_path.name

        try:
            for rel_path, contents in extractor.extract(archive_path):
                virtual_path = f"{archive_rel_path}/{rel_path}"

                doc = self._create_document_from_bytes(
                    file_name=rel_path.name,
                    virtual_path=virtual_path,
                    contents=contents,
                    archive_path=str(archive_path),
                    archive_rel_path=archive_rel_path,
                )

                if doc:
                    yield doc
                    self.stats["files_processed"] += 1

            self.stats["archives_extracted"] += 1

        except Exception as e:
            logger.error(
                f"Failed to process archive {archive_path}",
                error=str(e),
            )
            self.stats["files_failed"] += 1

    def _create_document_from_bytes(
        self,
        file_name: str,
        virtual_path: str,
        contents: bytes,
        archive_path: str,
        archive_rel_path: str,
    ) -> Document | None:
        """
        Create document directly from bytes without temporary file.

        Args:
            file_name: Original file name from archive.
            virtual_path: Virtual path (archive_name/path/inside/archive).
            contents: File contents as bytes.
            archive_path: Full path to archive file.
            archive_rel_path: Archive path relative to storage.

        Returns:
            Document entity or None if creation fails.
        """
        try:
            with tempfile.NamedTemporaryFile(
                suffix=Path(file_name).suffix,
                delete=False,
            ) as tmp_file:
                tmp_file.write(contents)
                tmp_path = Path(tmp_file.name)

            try:
                doc = self.crawler.crawl_file(tmp_path)

                if doc:
                    virtual_file_path = Path(virtual_path)

                    parser = self.crawler.parser_factory.get_parser_for_file(
                        virtual_file_path
                    )

                    text_content = None
                    extraction_success = False
                    extraction_error = None

                    if parser:
                        try:
                            text_content = parser.parse(tmp_path)
                            extraction_success = True
                        except ParseError as e:
                            extraction_error = str(e)

                    return Document(
                        path=virtual_file_path,
                        relative_path=virtual_path,
                        file_name=file_name,
                        file_size=len(contents),
                        file_hash=FileHash(contents),
                        doc_type=DocumentType.from_extension(
                            virtual_file_path.suffix
                        ),
                        text_content=text_content,
                        extraction_success=extraction_success,
                        extraction_error=extraction_error,
                        modified_time=datetime.now(),
                        crawled_at=datetime.now(),
                        is_from_archive=True,
                        archive_path=str(archive_path),
                        is_virtual=True,
                    )
                return None

            finally:
                tmp_path.unlink(missing_ok=True)

        except Exception as e:
            logger.error(
                "Failed to create document from archive contents",
                file=file_name,
                archive=archive_path,
                error=str(e),
            )
            return None

    def execute(
        self,
        storage_path: Path | None = None,
        output_csv: Path | None = None,
        limit: int | None = None,
    ) -> dict[str, Any]:
        """
        Execute the crawl process.

        Args:
            storage_path: Path to crawl (uses config if None).
            output_csv: Path to output CSV file (uses config if None).
            limit: Maximum number of files to process (None = no limit).

        Returns:
            Dictionary with crawl statistics.
        """
        crawl_path = storage_path or self.config.crawler.storage_path
        csv_path = output_csv or self.config.crawler.output_csv_path

        if not crawl_path.exists():
            raise FileNotFoundError(f"Storage path not found: {crawl_path}")

        logger.info(f"Starting crawl of {crawl_path}")

        self.stats["start_time"] = datetime.now()
        processed_count = 0
        documents: list[Document] = []

        with open(csv_path, "w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(
                csvfile,
                fieldnames=[
                    "path",
                    "relative_path",
                    "file_name",
                    "file_size",
                    "file_hash",
                    "doc_type",
                    "extension",
                    "extraction_success",
                    "extraction_error",
                    "modified_time",
                    "crawled_at",
                    "is_from_archive",
                    "archive_path",
                    "is_virtual",
                    "text_preview",
                ],
            )
            writer.writeheader()

            for file_path in self.crawler.scan_directory(crawl_path):
                self.stats["files_found"] += 1

                if (
                    self.crawler.archive_extractor
                    and self.crawler.archive_extractor.can_extract(file_path)
                ):
                    logger.info(f"Found archive: {file_path}")

                    archive_docs = list(
                        self._process_archive(
                            file_path, self.crawler.archive_extractor
                        )
                    )

                    for doc in archive_docs:
                        documents.append(doc)
                        processed_count += 1

                        writer.writerow({
                            "path": doc.display_path,
                            "relative_path": doc.relative_path,
                            "file_name": doc.file_name,
                            "file_size": doc.file_size,
                            "file_hash": str(doc.file_hash),
                            "doc_type": doc.doc_type.value,
                            "extension": doc.extension,
                            "extraction_success": doc.extraction_success,
                            "extraction_error": doc.extraction_error or "",
                            "modified_time": doc.modified_time.isoformat(),
                            "crawled_at": doc.crawled_at.isoformat(),
                            "is_from_archive": doc.is_from_archive,
                            "archive_path": doc.archive_path or "",
                            "is_virtual": doc.is_virtual,
                            "text_preview": (
                                doc.text_content[:200] + "..."
                                if doc.text_content
                                and len(doc.text_content) > 200
                                else doc.text_content or ""
                            ),
                        })

                    continue

                if not self._should_process(file_path):
                    self.stats["files_skipped"] += 1
                    continue

                doc_result = self.crawler.crawl_file(file_path)

                if doc_result:
                    documents.append(doc_result)
                    processed_count += 1

                    writer.writerow({
                        "path": doc_result.display_path,
                        "relative_path": doc_result.relative_path,
                        "file_name": doc_result.file_name,
                        "file_size": doc_result.file_size,
                        "file_hash": str(doc_result.file_hash),
                        "doc_type": doc_result.doc_type.value,
                        "extension": doc_result.extension,
                        "extraction_success": (doc_result.extraction_success),
                        "extraction_error": doc_result.extraction_error or "",
                        "modified_time": (
                            doc_result.modified_time.isoformat()
                        ),
                        "crawled_at": doc_result.crawled_at.isoformat(),
                        "is_from_archive": doc_result.is_from_archive,
                        "archive_path": doc_result.archive_path or "",
                        "is_virtual": doc_result.is_virtual,
                        "text_preview": (
                            doc_result.text_content[:200] + "..."
                            if doc_result.text_content
                            and len(doc_result.text_content) > 200
                            else doc_result.text_content or ""
                        ),
                    })

                if len(documents) >= 100:
                    self.repository.save_many(documents)
                    documents.clear()

                if limit and processed_count >= limit:
                    logger.info(f"Reached limit of {limit} files")
                    break

            if documents:
                self.repository.save_many(documents)

        self.stats["end_time"] = datetime.now()
        self.stats["files_processed"] = processed_count
        self.stats["duration_seconds"] = (
            self.stats["end_time"] - self.stats["start_time"]
        ).total_seconds()

        self.stats["database"] = self.repository.get_stats()

        logger.info(
            "Crawl completed",
            **self.stats,
        )

        return self.stats
