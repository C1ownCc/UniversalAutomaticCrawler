import collections
import re
import time
from dataclasses import dataclass, field
from typing import Callable, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .config import CrawlerSettings


@dataclass
class PageData:
    url: str
    status_code: int
    title: str
    text_preview: str
    links: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)
    fetched_at: float = field(default_factory=time.time)
    depth: int = 0


class Crawler:
    """A simple breadth-first crawler with progressive reporting."""

    def __init__(self, settings: CrawlerSettings):
        self.settings = settings
        self.visited: Set[str] = set()
        self.session = settings.session or requests.Session()
        self.session.headers.update({"User-Agent": settings.user_agent})

    def crawl(
        self,
        on_progress: Optional[Callable[[PageData], None]] = None,
    ) -> List[PageData]:
        """Crawl starting from the configured URL.

        Args:
            on_progress: Optional callback invoked as soon as each page is parsed.
        """

        settings = self.settings
        queue = collections.deque([(settings.start_url, 0)])
        results: List[PageData] = []
        domain = urlparse(settings.start_url).netloc

        while queue and len(results) < settings.max_pages:
            url, depth = queue.popleft()
            if url in self.visited or depth > settings.max_depth:
                continue

            self.visited.add(url)
            try:
                response = self.session.get(url, timeout=settings.timeout)
                status_code = response.status_code
            except requests.RequestException:
                status_code = 0
                response = None

            page_data = self._parse_page(url, status_code, response, depth)
            results.append(page_data)

            if on_progress:
                on_progress(page_data)

            if status_code != 200 or not response:
                continue

            if settings.extract_links:
                for link in page_data.links:
                    full_link = urljoin(url, link)
                    if settings.same_domain_only and urlparse(full_link).netloc != domain:
                        continue
                    if full_link not in self.visited:
                        queue.append((full_link, depth + 1))

        return results

    def _parse_page(
        self, url: str, status_code: int, response: Optional[requests.Response], depth: int
    ) -> PageData:
        title = ""
        text_preview = ""
        links: List[str] = []
        images: List[str] = []

        if response and response.content:
            soup = BeautifulSoup(response.content, "lxml")
            title_tag = soup.find("title")
            title = title_tag.text.strip() if title_tag else ""
            text_preview = self._clean_text(soup.get_text())[:500]
            if self.settings.extract_links:
                links = [a.get("href") for a in soup.find_all("a", href=True)]
            if self.settings.include_images:
                images = [img.get("src") for img in soup.find_all("img", src=True)]

        return PageData(
            url=url,
            status_code=status_code,
            title=title,
            text_preview=text_preview,
            links=links,
            images=images,
            depth=depth,
        )

    @staticmethod
    def _clean_text(raw_text: str) -> str:
        cleaned = re.sub(r"\s+", " ", raw_text)
        return cleaned.strip()
