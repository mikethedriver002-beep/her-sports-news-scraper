from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

PACKETS_CSV = "news_fact_packets.csv"
OBS_CSV = "news_source_observations.csv"
HUB_MD = "news_sync_hub.md"
QUEUE_MD = "news_brief_queue.md"
OUTPUT_DIR = Path("news_dashboard")
OUTPUT_FILE = OUTPUT_DIR / "index.html"
INPUT_STATUS_CSV = "news_input_status_report.csv"


def clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def esc(value) -> str:
    return html.escape(clean(value))


def load_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8") if p.exists() else ""


def card_grid(rows: List[Dict[str, str]], empty: str = "Nothing to show.") -> str:
    if not rows:
        return f'<div class="empty">{esc(empty)}</div>'
    cards = []
    for row in rows:
        cards.append(f"""
        <div class="card">
          <div class="meta">
            <span class="pill">{esc(row.get('urgency'))}</span>
            <span class="pill">{esc(row.get('content_family'))}</span>
            <span class="pill">Review: {esc(row.get('manual_review'))}</span>
          </div>
          <h3>{esc(row.get('headline'))}</h3>
          <div class="small"><b>Recommendation:</b> {esc(row.get('publish_recommendation'))}</div>
          <div class="small"><b>Sport/League:</b> {esc(row.get('sport'))} | {esc(row.get('league'))}</div>
          <div class="small"><b>Source depth:</b> {esc(row.get('source_count'))} usable / {esc(row.get('primary_source_count'))} primary</div>
          <div class="small"><b>Context:</b> {esc(row.get('context_signal'))}</div>
          <p>{esc(row.get('brief_120w'))}</p>
          <div class="small"><b>Caption:</b> {esc(row.get('caption_voice'))}</div>
          <div class="small"><b>Review flags:</b> {esc(row.get('review_flags')) or 'None'}</div>
        </div>
        """)
    return '<div class="grid">' + "\n".join(cards) + "</div>"


def input_status_table(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return '<div class="empty">No input status rows.</div>'
    trs = []
    for row in rows:
        trs.append(
            "<tr>"
            f"<td>{esc(row.get('input_name'))}</td>"
            f"<td>{esc(row.get('resolved_path'))}</td>"
            f"<td>{esc(row.get('exists'))}</td>"
            f"<td>{esc(row.get('size_bytes'))}</td>"
            f"<td>{esc(row.get('has_result_graphic'))}</td>"
            f"<td>{esc(row.get('has_must_post'))}</td>"
            f"<td>{esc(row.get('notes'))}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Input</th><th>Resolved Path</th><th>Exists</th><th>Bytes</th><th>Result Blocks</th><th>Priority Sections</th><th>Notes</th></tr></thead><tbody>" + "".join(trs) + "</tbody></table>"


def obs_table(rows: List[Dict[str, str]]) -> str:
    trs = []
    for row in rows:
        trs.append(
            "<tr>"
            f"<td>{esc(row.get('source_name'))}</td>"
            f"<td>{esc(row.get('source_type'))}</td>"
            f"<td>{esc(row.get('fetch_status'))}</td>"
            f"<td>{esc(row.get('usable_context'))}</td>"
            f"<td>{esc(row.get('title'))}</td>"
            f"<td><a href='{esc(row.get('url'))}' target='_blank'>Open</a></td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Source</th><th>Type</th><th>Fetch</th><th>Usable</th><th>Title</th><th>URL</th></tr></thead><tbody>" + "".join(trs) + "</tbody></table>"


def main() -> None:
    packets = load_csv(PACKETS_CSV)
    observations = load_csv(OBS_CSV)
    input_status = load_csv(INPUT_STATUS_CSV)
    hub = load_text(HUB_MD)
    queue = load_text(QUEUE_MD)

    publish = [p for p in packets if p.get("manual_review") != "Yes"]
    review = [p for p in packets if p.get("manual_review") == "Yes"]

    html_doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Her Sports Daily News Sync v1</title>
<style>
:root {{
  --bg:#0f1020; --panel:#181a2f; --text:#f8f4ff; --muted:#c5bdd9;
  --accent:#ff4fd8; --accent2:#7cf7ff; --border:rgba(255,255,255,.14);
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; font-family:Inter,system-ui,sans-serif; color:var(--text);
  background:radial-gradient(circle at 15% 0%, rgba(255,79,216,.18), transparent 30%),
             radial-gradient(circle at 85% 0%, rgba(124,247,255,.12), transparent 30%),
             var(--bg);
}}
header {{ position:sticky; top:0; z-index:5; background:rgba(15,16,32,.93); border-bottom:1px solid var(--border); padding:22px; }}
.wrap {{ max-width:1280px; margin:0 auto; }}
.brand {{ display:flex; gap:14px; align-items:center; }}
.bug {{ width:54px; height:54px; border-radius:14px; border:2px solid var(--accent); display:grid; place-items:center; font-weight:900; font-size:10px; line-height:.92; text-align:center; background:linear-gradient(135deg, rgba(255,79,216,.25), rgba(124,247,255,.12)); }}
h1 {{ margin:0; font-size:clamp(26px,4vw,42px); }}
.sub {{ color:var(--muted); font-size:13px; }}
main {{ max-width:1280px; margin:0 auto; padding:22px; }}
section {{ margin-bottom:28px; }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
@media(max-width:960px) {{ .grid {{ grid-template-columns:1fr; }} }}
.card {{ background:rgba(24,26,47,.96); border:1px solid var(--border); border-radius:18px; padding:16px; box-shadow:0 12px 32px rgba(0,0,0,.24); }}
.card h3 {{ margin:10px 0; font-size:18px; line-height:1.15; }}
.card p {{ color:var(--text); line-height:1.5; }}
.meta {{ display:flex; flex-wrap:wrap; gap:6px; }}
.pill {{ display:inline-flex; border:1px solid var(--border); color:var(--muted); padding:5px 8px; border-radius:999px; font-size:12px; font-weight:800; }}
.small {{ color:var(--muted); font-size:13px; line-height:1.45; margin-bottom:6px; }}
pre {{ white-space:pre-wrap; word-wrap:break-word; line-height:1.45; font-size:13px; background:rgba(0,0,0,.28); border:1px solid var(--border); padding:14px; border-radius:14px; }}
.empty {{ padding:16px; border:1px dashed var(--border); border-radius:14px; color:var(--muted); }}
table {{ width:100%; border-collapse:collapse; background:rgba(24,26,47,.96); border-radius:18px; overflow:hidden; }}
td, th {{ padding:10px; border-bottom:1px solid var(--border); font-size:12px; text-align:left; color:var(--muted); }}
th {{ color:var(--text); }}
a {{ color:var(--accent2); }}
</style>
</head>
<body>
<header><div class="wrap brand"><div class="bug">HER<br>SPORTS<br>DAILY</div><div><h1>News Sync v1</h1><div class="sub">Generated {esc(datetime.now(timezone.utc).isoformat())}. Source-backed news packets on top of Results Desk.</div></div></div></header>
<main>
<section><h2>System Hub</h2><div class="card"><pre>{esc(hub)}</pre></div></section>
<section><h2>Input Status</h2>{input_status_table(input_status)}</section>
<section><h2>Publish Ready</h2>{card_grid(publish, "No publish-ready packets.")}</section>
<section><h2>Manual Review</h2>{card_grid(review, "No manual review packets.")}</section>
<section><h2>Source Observations</h2>{obs_table(observations)}</section>
<section><h2>Brief Queue</h2><div class="card"><pre>{esc(queue)}</pre></div></section>
</main>
</body>
</html>"""

    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(html_doc, encoding="utf-8")
    print(f"Created {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
