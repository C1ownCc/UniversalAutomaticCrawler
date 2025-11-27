import argparse
import sys
from pathlib import Path
from typing import Callable

from .config import CrawlerSettings
from .crawler import Crawler, PageData
from .report import CrawlerReport


def _progress_printer() -> Callable[[PageData], None]:
    def printer(page: PageData) -> None:
        title_display = page.title[:80] if page.title else "<no title>"
        print(
            f"[depth={page.depth}] {page.status_code} {page.url}\n  Title: {title_display}",
            flush=True,
        )

    return printer


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the universal web crawler")
    parser.add_argument("url", help="Start URL for the crawl")
    parser.add_argument("--max-pages", type=int, default=10, help="Maximum pages to crawl")
    parser.add_argument("--max-depth", type=int, default=2, help="Maximum crawl depth")
    parser.add_argument(
        "--include-external",
        action="store_true",
        help="Allow the crawler to follow external domains",
    )
    parser.add_argument(
        "--output-dir", type=Path, default=Path("outputs"), help="Where to write reports"
    )
    parser.add_argument(
        "--report-name", default="crawl-report", help="Base filename for reports"
    )
    return parser


def run_from_args(args: argparse.Namespace) -> int:
    settings = CrawlerSettings(
        start_url=args.url,
        max_pages=args.max_pages,
        same_domain_only=not args.include_external,
        output_dir=args.output_dir,
        report_name=args.report_name,
        max_depth=args.max_depth,
    )

    crawler = Crawler(settings)
    pages = crawler.crawl(on_progress=_progress_printer())

    report = CrawlerReport(pages, settings.ensure_output_dir(), settings.report_name)
    paths = report.save()

    print("\nCrawl complete! Reports written to:")
    for key, path in paths.items():
        print(f"- {key}: {path}")

    return 0


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return run_from_args(args)
    except KeyboardInterrupt:
        print("\nCrawl interrupted.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
