"""
Script to create a test archive in storage/ with sample files.
"""

import zipfile
from pathlib import Path


def create_test_archive() -> None:
    """Create a test ZIP archive with sample files."""
    storage_dir = Path("data/storage")
    archive_path = storage_dir / "test_archive.zip"

    test_files: list[Path] = []

    for i in range(3):
        test_file = storage_dir / f"archive_test_{i}.txt"
        test_file.write_text(f"This is test file {i}\nLine 2\nLine 3")
        test_files.append(test_file)

    with zipfile.ZipFile(archive_path, "w") as zf:
        for test_file in test_files:
            zf.write(test_file, test_file.name)
            test_file.unlink()

    print(f"Created test archive: {archive_path}")
    print(f"Archive contains {len(test_files)} files")


if __name__ == "__main__":
    create_test_archive()
