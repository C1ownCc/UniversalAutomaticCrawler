import argparse
import json
import threading
from pathlib import Path
from queue import SimpleQueue
from typing import Dict, List

from flask import Flask, Response, abort, render_template_string, request, send_file, stream_with_context

from .config import CrawlerSettings
from .crawler import Crawler, PageData
from .report import CrawlerReport


PAGE_TEMPLATE = """
<!doctype html>
<html lang="en">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>Universal Crawler Dashboard</title>
    <style>
      body { font-family: Arial, sans-serif; margin: 0; padding: 0; background: #f5f7fa; color: #1f2933; }
      header { background: linear-gradient(90deg, #2563eb, #1e3a8a); color: #fff; padding: 1.2rem 2rem; }
      .header-row { display: flex; align-items: center; justify-content: space-between; gap: 1rem; flex-wrap: wrap; }
      h1 { margin: 0; font-size: 1.6rem; }
      .lang-toggle { display: flex; gap: 0.4rem; }
      .lang-toggle button { border: 1px solid rgba(255,255,255,0.5); background: rgba(0,0,0,0.1); color: #fff; padding: 0.4rem 0.7rem; border-radius: 8px; cursor: pointer; font-weight: 700; }
      .lang-toggle button.active { background: #fff; color: #1e3a8a; }
      main { padding: 1.5rem 2rem; max-width: 1200px; margin: 0 auto; }
      form { display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1rem; background: #fff; padding: 1rem; border-radius: 12px; box-shadow: 0 10px 30px rgba(0,0,0,0.08); }
      label { display: flex; flex-direction: column; font-weight: 600; font-size: 0.95rem; color: #334155; }
      input[type="text"], input[type="number"], input[type="checkbox"] { margin-top: 0.35rem; padding: 0.6rem 0.75rem; border: 1px solid #cbd5e1; border-radius: 8px; font-size: 0.95rem; }
      input[type="checkbox"] { width: 18px; height: 18px; }
      .checkbox-row { flex-direction: row; align-items: center; gap: 0.5rem; }
      button { grid-column: 1 / -1; padding: 0.85rem; border: none; border-radius: 10px; background: linear-gradient(90deg, #22c55e, #16a34a); color: #fff; font-weight: 700; font-size: 1rem; cursor: pointer; box-shadow: 0 12px 24px rgba(34,197,94,0.25); transition: transform 120ms ease, box-shadow 120ms ease; }
      button:hover { transform: translateY(-1px); box-shadow: 0 14px 30px rgba(34,197,94,0.35); }
      #status { margin-top: 1rem; font-weight: 600; color: #0f172a; }
      .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 1.25rem; margin-top: 1.25rem; }
      .card { background: #fff; border-radius: 12px; padding: 1rem; box-shadow: 0 10px 30px rgba(0,0,0,0.06); }
      .card h2 { margin-top: 0; font-size: 1.1rem; }
      table { width: 100%; border-collapse: collapse; font-size: 0.9rem; }
      th, td { padding: 0.5rem; border-bottom: 1px solid #e2e8f0; text-align: left; vertical-align: top; }
      tr:hover { background: #f8fafc; }
      .pill { display: inline-block; padding: 0.15rem 0.45rem; border-radius: 999px; font-size: 0.8rem; background: #e0f2fe; color: #075985; font-weight: 700; }
      .reports a { display: block; color: #2563eb; text-decoration: none; margin-bottom: 0.25rem; }
      .reports a:hover { text-decoration: underline; }
      .muted { color: #64748b; font-size: 0.92rem; }
      .section-desc { margin: 0 0 0.35rem; }
      @media (max-width: 960px) { .grid { grid-template-columns: 1fr; } }
    </style>
  </head>
  <body>
    <header>
      <div class="header-row">
        <h1 data-i18n="title">Universal Crawler Web Dashboard</h1>
        <div class="lang-toggle">
          <button type="button" data-lang="en" class="active">English</button>
          <button type="button" data-lang="zh">中文</button>
        </div>
      </div>
    </header>
    <main>
      <form id="crawl-form">
        <label data-i18n="start_url_label">Start URL<input required name="url" type="text" placeholder="https://example.com" /></label>
        <label data-i18n="max_pages_label">Max pages<input name="max_pages" type="number" min="1" max="200" value="20" /></label>
        <label data-i18n="max_depth_label">Max depth<input name="max_depth" type="number" min="0" max="10" value="2" /></label>
        <label class="checkbox-row" data-i18n="follow_external"><input name="include_external" type="checkbox" /> Follow external domains</label>
        <label class="checkbox-row" data-i18n="capture_images"><input name="include_images" type="checkbox" checked /> Capture images</label>
        <label data-i18n="report_name_label">Report name<input name="report_name" type="text" value="crawl-report" /></label>
        <label data-i18n="output_dir_label">Output folder<input name="output_dir" type="text" value="outputs" /></label>
        <button type="submit" data-i18n="start_button">Start crawling</button>
      </form>
      <div id="status" class="muted" data-i18n="status_wait">Waiting to start...</div>
      <div class="grid">
        <div class="card">
          <h2 data-i18n="live_pages">Live pages</h2>
          <table id="results">
            <thead>
              <tr><th>URL</th><th>Status</th><th>Title</th><th>Depth</th></tr>
            </thead>
            <tbody></tbody>
          </table>
        </div>
        <div class="card">
          <h2 data-i18n="reports_header">Reports</h2>
          <p class="muted section-desc" data-i18n="reports_desc">Links appear when the crawl finishes.</p>
          <div id="reports" class="reports"></div>
        </div>
      </div>
    </main>
    <script>
      const translations = {
        en: {
          title: 'Universal Crawler Web Dashboard',
          start_url_label: 'Start URL',
          max_pages_label: 'Max pages',
          max_depth_label: 'Max depth',
          follow_external: 'Follow external domains',
          capture_images: 'Capture images',
          report_name_label: 'Report name',
          output_dir_label: 'Output folder',
          start_button: 'Start crawling',
          status_wait: 'Waiting to start...',
          status_starting: 'Starting crawl...',
          status_crawled: 'Crawled {count} page(s)...',
          status_complete: 'Crawl complete: {count} page(s).',
          status_error: 'Error: {message}',
          live_pages: 'Live pages',
          reports_header: 'Reports',
          reports_desc: 'Links appear when the crawl finishes.',
          table_url: 'URL',
          table_status: 'Status',
          table_title: 'Title',
          table_depth: 'Depth',
          report_link: '{kind} report'
        },
        zh: {
          title: '万能爬虫网页面板',
          start_url_label: '起始网址',
          max_pages_label: '最大页面数',
          max_depth_label: '最大深度',
          follow_external: '允许跨域爬取',
          capture_images: '下载图片',
          report_name_label: '报告名称',
          output_dir_label: '输出目录',
          start_button: '开始爬取',
          status_wait: '等待开始…',
          status_starting: '正在启动爬虫…',
          status_crawled: '已爬取 {count} 个页面…',
          status_complete: '爬取完成：共 {count} 个页面。',
          status_error: '错误：{message}',
          live_pages: '实时页面',
          reports_header: '报告下载',
          reports_desc: '爬取结束后将显示报告链接。',
          table_url: '链接',
          table_status: '状态',
          table_title: '标题',
          table_depth: '深度',
          report_link: '{kind} 报告'
        }
      };

      const form = document.getElementById('crawl-form');
      const statusEl = document.getElementById('status');
      const tbody = document.querySelector('#results tbody');
      const reportsEl = document.getElementById('reports');
      const langButtons = document.querySelectorAll('.lang-toggle button');
      let currentLang = 'en';
      let source;

      function format(key, params = {}) {
        const template = translations[currentLang][key] || key;
        return Object.entries(params).reduce((text, [k, v]) => text.replace(`{${k}}`, v), template);
      }

      function applyTranslations() {
        document.documentElement.lang = currentLang;
        document.querySelectorAll('[data-i18n]').forEach(el => {
          const key = el.getAttribute('data-i18n');
          el.childNodes.forEach(node => {
            if (node.nodeType === Node.TEXT_NODE) {
              node.nodeValue = format(key);
            }
          });
        });
        document.querySelectorAll('#results thead th').forEach((th, index) => {
          const map = ['table_url', 'table_status', 'table_title', 'table_depth'];
          th.textContent = format(map[index]);
        });
        langButtons.forEach(btn => btn.classList.toggle('active', btn.dataset.lang === currentLang));
      }

      langButtons.forEach(btn => {
        btn.addEventListener('click', () => {
          currentLang = btn.dataset.lang;
          applyTranslations();
        });
      });

      applyTranslations();

      form.addEventListener('submit', (event) => {
        event.preventDefault();
        if (source) { source.close(); }
        tbody.innerHTML = '';
        reportsEl.innerHTML = '';
        statusEl.textContent = format('status_starting');
        const params = new URLSearchParams(new FormData(form));
        source = new EventSource(`/crawl?${params.toString()}`);
        source.onmessage = (event) => {
          const data = JSON.parse(event.data);
          const row = document.createElement('tr');
          row.innerHTML = `<td>${data.url}</td><td><span class="pill">${data.status_code}</span></td><td>${data.title || ''}</td><td>${data.depth}</td>`;
          tbody.appendChild(row);
          statusEl.textContent = format('status_crawled', { count: tbody.children.length });
        };
        source.addEventListener('complete', (event) => {
          const payload = JSON.parse(event.data);
          statusEl.textContent = format('status_complete', { count: payload.pages });
          if (payload.reports) {
            reportsEl.innerHTML = Object.entries(payload.reports).map(([key, value]) => `<a href="/reports?path=${encodeURIComponent(value)}" target="_blank">${format('report_link', { kind: key.toUpperCase() })}</a>`).join('');
          }
          source.close();
        });
        source.addEventListener('error', (event) => {
          const msg = event.data ? JSON.parse(event.data).message : 'Unexpected error';
          statusEl.textContent = format('status_error', { message: msg });
          source.close();
        });
      });
    </script>
  </body>
</html>
"""


def _page_to_dict(page: PageData) -> Dict:
    return {
        "url": page.url,
        "status_code": page.status_code,
        "title": page.title,
        "depth": page.depth,
    }


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index():
        return render_template_string(PAGE_TEMPLATE)

    @app.get("/crawl")
    def crawl_stream():
        url = request.args.get("url")
        if not url:
            return {"error": "Missing url"}, 400

        max_pages = int(request.args.get("max_pages", 20))
        max_depth = int(request.args.get("max_depth", 2))
        same_domain_only = request.args.get("include_external") is None
        include_images = request.args.get("include_images") is not None
        report_name = request.args.get("report_name", "crawl-report")
        output_dir = Path(request.args.get("output_dir", "outputs"))

        settings = CrawlerSettings(
            start_url=url,
            max_pages=max_pages,
            same_domain_only=same_domain_only,
            max_depth=max_depth,
            include_images=include_images,
            output_dir=output_dir,
            report_name=report_name,
        )

        queue: "SimpleQueue[str | None]" = SimpleQueue()
        pages: List[PageData] = []

        def progress(page: PageData) -> None:
            pages.append(page)
            queue.put(f"data: {json.dumps(_page_to_dict(page))}\n\n")

        def run_crawl() -> None:
            try:
                crawler = Crawler(settings)
                crawler.crawl(on_progress=progress)
                report = CrawlerReport(pages, settings.ensure_output_dir(), settings.report_name)
                paths = report.save()
                payload = {"pages": len(pages), "reports": {k: str(v) for k, v in paths.items()}}
                queue.put(f"event: complete\ndata: {json.dumps(payload)}\n\n")
            except Exception as exc:  # pragma: no cover - surfaced via SSE
                queue.put(f"event: error\ndata: {json.dumps({'message': str(exc)})}\n\n")
            finally:
                queue.put(None)

        threading.Thread(target=run_crawl, daemon=True).start()

        def event_stream():
            while True:
                message = queue.get()
                if message is None:
                    break
                yield message

        return Response(stream_with_context(event_stream()), mimetype="text/event-stream")

    @app.get("/reports")
    def serve_report():
        path_param = request.args.get("path")
        if not path_param:
            abort(404)
        path = Path(path_param).expanduser().resolve()
        base = Path.cwd().resolve()
        if not str(path).startswith(str(base)) or not path.exists():
            abort(404)
        return send_file(path)

    return app


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Launch the universal crawler web dashboard")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind the server")
    parser.add_argument("--port", type=int, default=8000, help="Port to bind the server")
    return parser.parse_args(argv)


def main(argv=None) -> int:
    args = parse_args(argv)
    app = create_app()
    app.run(host=args.host, port=args.port, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
