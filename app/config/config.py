"""
Configuration module for the application.

Provides type-safe settings using Pydantic.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.infrastructure.logger import ILoggingConfig


class LoggingConfig(BaseSettings):
    """Configuration for the logging system."""

    app_name: str = "Document Crawler"
    debug: bool = True  # if True then color console render, else json render
    log_level: str = "INFO"
    enable_file_logging: bool = False
    logs_dir: Path = Path("logs")
    logs_file_name: str = "app.log"
    max_file_size_mb: int = 10
    backup_count: int = 5


class CrawlerConfig(BaseSettings):
    """Configuration for crawler."""

    storage_path: Path = Field(
        default=Path("data/storage"),
        description="Path to storage directory with files to crawl",
    )
    output_csv_path: Path = Field(
        default=Path("data/output/crawled_files.csv"),
        description="Path to output CSV file",
    )
    max_file_size_mb: int = Field(
        default=100,
        ge=1,
        le=10240,
        description="Maximum file size in MB to process",
    )
    skip_hidden: bool = Field(
        default=True,
        description="Skip hidden files and directories",
    )
    follow_symlinks: bool = Field(
        default=False,
        description="Follow symbolic links",
    )
    extract_archives: bool = Field(
        default=True,
        description="Extract contents of archives",
    )
    max_archive_depth: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum nested archive depth",
    )
    extract_text_from: list[str] = Field(
        default=["pdf", "docx", "xlsx", "txt", "md", "json", "xml", "html"],
        description="File extensions to extract text from",
    )
    archive_extensions: list[str] = Field(
        default=["zip", "rar", "7z"],
        description="Archive extensions to extract",
    )

    @field_validator("storage_path", mode="after")
    @classmethod
    def create_storage_dir(cls, v: Path) -> Path:
        """Ensure storage directory exists."""
        v.mkdir(parents=True, exist_ok=True)
        return v

    @field_validator("output_csv_path", mode="after")
    @classmethod
    def create_output_dir(cls, v: Path) -> Path:
        """Ensure output directory exists."""
        v.parent.mkdir(parents=True, exist_ok=True)
        return v


class DatabaseConfig(BaseSettings):
    """Configuration for database."""

    path: Path = Field(
        default=Path("db/crawler.db"),
        description="Path to SQLite database file",
    )
    fts_enabled: bool = Field(
        default=True,
        description="Enable full-text search",
    )


class AppConfig(BaseSettings):
    """Main application configuration."""

    logger: LoggingConfig = Field(default_factory=LoggingConfig)
    crawler: CrawlerConfig = Field(default_factory=CrawlerConfig)
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        env_nested_delimiter="__",
    )

    @property
    def logger_adapter(self) -> ILoggingConfig:
        """
        Create logging configuration adapter from settings.

        Returns:
            ILoggingConfig: Configuration object for the logging system.
        """
        return LoggingConfig(
            debug=self.logger.debug,
            app_name=self.logger.app_name,
            log_level=self.logger.log_level.upper(),
            enable_file_logging=self.logger.enable_file_logging,
            logs_dir=self.logger.logs_dir,
            logs_file_name=self.logger.logs_file_name,
            max_file_size_mb=self.logger.max_file_size_mb,
            backup_count=self.logger.backup_count,
        )


@lru_cache
def get_config() -> AppConfig:
    config = AppConfig()
    return config
