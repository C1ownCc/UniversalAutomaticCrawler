from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class CrawlerSettings:
    """Configuration for the universal crawler."""

    start_url: str
    max_pages: int = 20
    same_domain_only: bool = True
    timeout: int = 10
    user_agent: str = (
        "UniversalCrawler/0.1 (+https://github.com/C1ownCc/UniversalAutomaticCrawler)"
    )
    output_dir: Path = field(default_factory=lambda: Path("outputs"))
    report_name: str = "crawl-report"
    max_depth: int = 2
    respect_robots_txt: bool = False  # Placeholder for future enhancement
    include_images: bool = True
    extract_links: bool = True
    session: Optional[object] = None  # Allows injection for testing

    def ensure_output_dir(self) -> Path:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        return self.output_dir
