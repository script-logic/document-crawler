"""
Archive extraction utilities.
"""

import os
import shutil
import tempfile
from collections.abc import Iterator
from pathlib import Path
from typing import ClassVar

import patoolib  # pyright: ignore[reportMissingTypeStubs]
from patoolib.util import PatoolError  # pyright: ignore
from structlog import get_logger

from .interfaces import CrawlerError

logger = get_logger(__name__)


class PatoolArchiveExtractor:
    """
    Archive extractor using patool library.

    Supports: zip, rar, 7z, tar, gz, bz2, etc.
    Requires external tools (7z, unrar, etc.) to be installed.
    """

    SUPPORTED_EXTENSIONS: ClassVar[set[str]] = {
        ".zip",
        ".rar",
        ".7z",
        ".tar",
        ".gz",
        ".bz2",
        ".xz",
    }

    def __init__(
        self,
        temp_dir: Path | None = None,
        max_depth: int = 3,
        extract_in_place: bool = False,
    ) -> None:
        """
        Initialize archive extractor.

        Args:
            temp_dir: Directory for temporary extraction.
                     If None, uses system temp directory.
            max_depth: Maximum nested archive depth.
            extract_in_place: If True, extract to same directory as archive.
                             If False, extract to temp_dir.
        """
        self.temp_dir = (
            Path(temp_dir) if temp_dir else Path(tempfile.gettempdir())
        )
        self.max_depth = max_depth
        self.extract_in_place = extract_in_place
        self._current_depth = 0

        self.temp_dir.mkdir(parents=True, exist_ok=True)

    def can_extract(self, archive_path: Path) -> bool:
        """
        Check if archive format is supported.

        Args:
            archive_path: Path to archive file.

        Returns:
            True if extension is supported.
        """
        return archive_path.suffix.lower() in self.SUPPORTED_EXTENSIONS

    def _get_extraction_path(self, archive_path: Path) -> Path:
        """
        Determine where to extract the archive.

        Args:
            archive_path: Path to archive file.

        Returns:
            Path to extraction directory.
        """
        if self.extract_in_place:
            extract_path = (
                archive_path.parent / f"{archive_path.stem}_extracted"
            )
        else:
            extract_path = (
                self.temp_dir
                / f"archive_{archive_path.stem}_{os.urandom(4).hex()}"
            )

        extract_path.mkdir(parents=True, exist_ok=True)
        return extract_path

    def extract(self, archive_path: Path) -> Iterator[tuple[Path, bytes]]:
        """
        Extract files from archive and yield their contents.

        Handles nested archives recursively up to max_depth.

        Args:
            archive_path: Path to archive file.

        Yields:
            Tuples of (relative_path_in_archive, file_contents).

        Raises:
            CrawlerError: If extraction fails.
        """
        if self._current_depth >= self.max_depth:
            logger.warning(
                f"Max archive depth ({self.max_depth}) reached, "
                "skipping nested",
                archive=str(archive_path),
            )
            return

        if not self.can_extract(archive_path):
            logger.debug(f"Unsupported archive format: {archive_path}")
            return

        logger.info(
            "Extracting archive",
            archive=str(archive_path),
            depth=self._current_depth,
        )

        extract_path = self._get_extraction_path(archive_path)

        try:
            patoolib.extract_archive(
                str(archive_path),
                outdir=str(extract_path),
                interactive=False,
            )

            self._current_depth += 1
            try:
                for root, _, files in os.walk(extract_path):
                    root_path = Path(root)
                    for file_name in files:
                        file_path = root_path / file_name

                        rel_path = file_path.relative_to(extract_path)

                        try:
                            with open(file_path, "rb") as f:
                                contents = f.read()

                            yield (rel_path, contents)

                        except OSError as e:
                            logger.warning(
                                "Failed to read extracted file",
                                file=str(file_path),
                                error=str(e),
                            )
                            continue

            finally:
                self._current_depth -= 1

        except PatoolError as e:
            raise CrawlerError(
                f"Archive extraction failed: {e}",
                path=archive_path,
            ) from e
        except Exception as e:
            raise CrawlerError(
                f"Unexpected error extracting archive: {e}",
                path=archive_path,
            ) from e
        finally:
            if not self.extract_in_place:
                try:
                    shutil.rmtree(extract_path, ignore_errors=True)
                except Exception as e:
                    logger.warning(
                        "Failed to clean up extraction directory",
                        path=str(extract_path),
                        error=str(e),
                    )
