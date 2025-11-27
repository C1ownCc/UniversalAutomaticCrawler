# Universal Automatic Crawler

A lightweight crawler that streams results while it collects them and produces
multi-format reports after the crawl finishes. Provide any start URL and the crawler
will collect titles, status codes, text previews, links, and images with optional
same-domain filtering. Use either the CLI or the included web dashboard for a richer
experience.

## Features
- **Progressive streaming**: See each page as soon as it is fetched, including title and status.
- **Breadth-first traversal**: Crawl linked pages up to configurable depth and page limits.
- **Reporting**: Generate CSV, JSON, and Markdown summaries with top-word analysis and link listings.
- **Configurable**: Limit domains, set maximum depth, choose output directory and report names.

## Installation
```bash
pip install -r requirements.txt
pip install -e .
```

## Quick start (CLI)
```bash
universal-crawler https://example.com --max-pages 5 --max-depth 1
```
While the crawler runs you will see each fetched page printed to the console. When finished,
reports are written to the `outputs/` directory by default.

## Quick start (Web dashboard)
```bash
universal-crawler-web --port 8000
```
Then open `http://localhost:8000` in your browser, paste a start URL, and watch pages
stream in live while the crawler runs. Completed CSV/JSON/Markdown reports are linked
on the right-hand panel after the crawl finishes.

## Command options
- `url` (positional): Start URL for the crawl.
- `--max-pages`: Maximum pages to crawl (default: 10).
- `--max-depth`: Maximum crawl depth (default: 2).
- `--include-external`: Follow external domains as links are discovered.
- `--output-dir`: Directory to save reports (default: `outputs`).
- `--report-name`: Base filename for reports (default: `crawl-report`).

## Output
The crawler saves three artifacts per run:
- `<report-name>.csv` — tabular export of all crawled pages.
- `<report-name>.json` — JSON export of page details.
- `<report-name>.md` — human-readable summary with status codes, top words, and links.
