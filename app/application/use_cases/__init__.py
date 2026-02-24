"""
Application use cases for document crawler.
"""

from .crawl import CrawlUseCase
from .search import SearchUseCase

__all__ = [
    "CrawlUseCase",
    "SearchUseCase",
]
