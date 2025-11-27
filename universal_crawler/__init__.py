"""
UniversalAutomaticCrawler package.
"""

from .config import CrawlerSettings
from .crawler import Crawler, PageData
from .report import CrawlerReport

__all__ = ["CrawlerSettings", "Crawler", "PageData", "CrawlerReport"]
