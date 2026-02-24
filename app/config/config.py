"""
Configuration module for the application.

Provides type-safe settings using Pydantic.
"""

from functools import lru_cache
from pathlib import Path

from pydantic import Field
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


class AppConfig(BaseSettings):
    """Main application configuration."""

    logger: LoggingConfig = Field(default_factory=LoggingConfig)

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
