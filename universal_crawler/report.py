import json
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

import pandas as pd

from .crawler import PageData


@dataclass
class CrawlerReport:
    pages: List[PageData]
    output_dir: Path
    report_name: str

    def to_dataframe(self) -> pd.DataFrame:
        return pd.DataFrame(
            [
                {
                    "url": page.url,
                    "status_code": page.status_code,
                    "title": page.title,
                    "text_preview": page.text_preview,
                    "links": page.links,
                    "images": page.images,
                    "fetched_at": page.fetched_at,
                    "depth": page.depth,
                }
                for page in self.pages
            ]
        )

    def save(self) -> Dict[str, Path]:
        self.output_dir.mkdir(parents=True, exist_ok=True)
        df = self.to_dataframe()
        paths = {
            "csv": self.output_dir / f"{self.report_name}.csv",
            "json": self.output_dir / f"{self.report_name}.json",
            "markdown": self.output_dir / f"{self.report_name}.md",
        }
        df.to_csv(paths["csv"], index=False)
        df.to_json(paths["json"], orient="records", indent=2)
        paths["markdown"].write_text(self._markdown_report())
        return paths

    def _markdown_report(self) -> str:
        lines = ["# Crawl Report / 爬取报告", ""]
        lines.append(f"Total pages crawled: {len(self.pages)} (总计页面数)")
        lines.append("")
        lines.extend(self._status_summary())
        lines.append("")
        lines.extend(self._top_words_section())
        lines.append("")
        lines.extend(self._link_section())
        return "\n".join(lines)

    def _status_summary(self) -> List[str]:
        counter = Counter(page.status_code for page in self.pages)
        lines = ["## Status codes / 状态码"]
        for code, count in sorted(counter.items()):
            lines.append(f"- {code}: {count} (次数)")
        return lines

    def _top_words_section(self, limit: int = 20) -> List[str]:
        text = " ".join(page.text_preview for page in self.pages)
        words = [w.lower() for w in text.split() if w.isalpha() and len(w) > 3]
        common = Counter(words).most_common(limit)
        lines = ["## Top words / 高频词汇", "| Word / 词语 | Count / 次数 |", "| --- | --- |"]
        for word, count in common:
            lines.append(f"| {word} | {count} |")
        return lines

    def _link_section(self) -> List[str]:
        lines = ["## Links discovered / 发现的链接"]
        for page in self.pages:
            if not page.links:
                continue
            lines.append(f"### {page.url}")
            for link in page.links[:20]:
                lines.append(f"- {link}")
        return lines
