
"""
Her Sports Daily Results Dashboard Generator
-------------------------------------------

Reads results desk outputs and creates:
    results_dashboard/index.html
"""

from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

RESULTS_BOARD_FILE = "today_results_board.csv"
BOX_SCORES_FILE = "today_box_scores.csv"
TOP_PERFORMERS_FILE = "top_performers.csv"
GRAPHICS_QUEUE_FILE = "results_graphics_queue.md"
HUB_FILE = "results_system_hub.md"
OUTPUT_DIR = Path("results_dashboard")
OUTPUT_FILE = OUTPUT_DIR / "index.html"


def clean(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def load_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_text(path: str) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    return p.read_text(encoding="utf-8")


def split_packets(text: str) -> List[Dict[str, str]]:
    if not text:
        return []
    parts = re.split(r"(?=^## RESULT GRAPHIC\s+\d+:)", text, flags=re.M)
    packets = []
    for part in parts:
        part = part.strip()
        if not part.startswith("## RESULT GRAPHIC"):
            continue
        first = part.splitlines()[0]
        match = re.match(r"## RESULT GRAPHIC\s+(\d+):\s*(.*)", first)
        packets.append({
            "packet_num": match.group(1) if match else "",
            "headline": clean(match.group(2)) if match else first,
            "packet": part,
        })
    return packets


def esc(value: str) -> str:
    return html.escape(clean(value))


def render_cards(rows: List[Dict[str, str]], keys: List[str]) -> str:
    if not rows:
        return '<div class="empty">Nothing to show.</div>'
    cards = []
    for row in rows:
        body = []
        for key in keys:
            if clean(row.get(key, "")):
                label = key.replace("_", " ").title()
                body.append(f"<div class='small'><b>{esc(label)}:</b> {esc(row.get(key, ''))}</div>")
        cards.append("<div class='card'>" + "".join(body) + "</div>")
    return "<div class='grid'>" + "".join(cards) + "</div>"


def main() -> None:
    results = load_csv(RESULTS_BOARD_FILE)
    box = load_csv(BOX_SCORES_FILE)
    performers = load_csv(TOP_PERFORMERS_FILE)
    queue_text = load_text(GRAPHICS_QUEUE_FILE)
    packets = split_packets(queue_text)
    hub = load_text(HUB_FILE)

    results_html = render_cards(
        results,
        ["league_label", "game_state", "matchup", "final_score", "headline", "top_performer_1", "top_performer_1_statline", "confidence", "result_graphic_ready"],
    )
    box_html = render_cards(
        box,
        ["league_label", "matchup", "final_score", "top_performer_1", "top_performer_1_statline", "top_performer_2", "top_performer_2_statline", "period_summary"],
    )
    performers_html = render_cards(
        performers,
        ["league_label", "performer_rank", "player_name", "team", "matchup", "statline"],
    )

    packet_html = []
    for packet in packets:
        packet_html.append(
            "<div class='card'><h3>"
            + esc(packet["headline"])
            + "</h3><pre>"
            + esc(packet["packet"])
            + "</pre></div>"
        )
    packets_html = "<div class='stack'>" + "".join(packet_html) + "</div>" if packet_html else '<div class="empty">No ready packets found.</div>'

    generated_at = datetime.now(timezone.utc).isoformat()

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Her Sports Daily Results Dashboard</title>
<style>
:root {{
  --bg:#0f1020; --panel:#181a2f; --panel2:#242845; --text:#f7f3ff; --muted:#beb6d4;
  --accent:#ff4fd8; --accent2:#7cf7ff; --border:rgba(255,255,255,.14);
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; font-family:Inter,system-ui,sans-serif; color:var(--text);
  background:radial-gradient(circle at 20% 0%, rgba(255,79,216,.18), transparent 30%),
             radial-gradient(circle at 80% 0%, rgba(124,247,255,.12), transparent 30%),
             var(--bg);
}}
header {{
  position:sticky; top:0; z-index:5; background:rgba(15,16,32,.92);
  backdrop-filter:blur(10px); border-bottom:1px solid var(--border); padding:22px;
}}
.wrap {{ max-width:1280px; margin:0 auto; }}
.brand {{ display:flex; gap:14px; align-items:center; }}
.bug {{
  width:54px; height:54px; border-radius:14px; border:2px solid var(--accent);
  display:grid; place-items:center; font-weight:900; font-size:10px; line-height:.92;
  background:linear-gradient(135deg, rgba(255,79,216,.25), rgba(124,247,255,.12));
}}
h1 {{ margin:0; font-size:clamp(26px,4vw,42px); }}
.sub {{ color:var(--muted); font-size:13px; margin-top:4px; }}
main {{ max-width:1280px; margin:0 auto; padding:22px; }}
section {{ margin-bottom:28px; }}
section h2 {{ margin-bottom:12px; }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
@media(max-width:960px) {{ .grid {{ grid-template-columns:1fr; }} }}
.card {{
  background:rgba(24,26,47,.96); border:1px solid var(--border); border-radius:18px;
  padding:16px; box-shadow:0 12px 32px rgba(0,0,0,.24);
}}
.small {{ color:var(--muted); font-size:13px; line-height:1.45; margin-bottom:6px; }}
pre {{
  white-space:pre-wrap; word-wrap:break-word; line-height:1.45; font-size:13px;
  background:rgba(0,0,0,.28); border:1px solid var(--border); padding:14px; border-radius:14px;
}}
.empty {{
  padding:16px; border:1px dashed var(--border); border-radius:14px; color:var(--muted);
}}
.stack > .card {{ margin-bottom:14px; }}
</style>
</head>
<body>
<header>
  <div class="wrap">
    <div class="brand">
      <div class="bug">HER<br>SPORTS<br>DAILY</div>
      <div>
        <h1>Results Dashboard</h1>
        <div class="sub">Generated {esc(generated_at)}. Use this for accurate results, box scores, and postgame packets.</div>
      </div>
    </div>
  </div>
</header>
<main>
  <section>
    <h2>Guide</h2>
    <div class="card">
      <div class="small">1. Open this dashboard after each run.</div>
      <div class="small">2. Use Results Board to review final, live, and upcoming games.</div>
      <div class="small">3. Use Graphic Packets for postgame graphics only when the game is final.</div>
      <div class="small">4. Never change a verified final score or invent a stat line.</div>
    </div>
  </section>

  <section>
    <h2>Results Board</h2>
    {results_html}
  </section>

  <section>
    <h2>Box Scores</h2>
    {box_html}
  </section>

  <section>
    <h2>Top Performers</h2>
    {performers_html}
  </section>

  <section>
    <h2>Graphic Packets</h2>
    {packets_html}
  </section>

  <section>
    <h2>System Hub</h2>
    <div class="card"><pre>{esc(hub)}</pre></div>
  </section>
</main>
</body>
</html>
"""

    OUTPUT_DIR.mkdir(exist_ok=True)
    OUTPUT_FILE.write_text(html_doc, encoding="utf-8")
    print(f"Created {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
