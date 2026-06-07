from __future__ import annotations

import csv
import html
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

QUEUE = "studio_graphics_queue.csv"
CENTER = "studio_command_center.md"
TOP = "studio_top_graphic_packets.md"
SCHEDULE = "studio_post_schedule.md"
CHECKLIST = "studio_accuracy_checklist.csv"
OUT_DIR = Path("studio_dashboard")
OUT_FILE = OUT_DIR / "index.html"


def clean(value) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def esc(value) -> str:
    return html.escape(clean(value))


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def cards(rows: List[Dict[str, str]]) -> str:
    if not rows:
        return '<div class="empty">No studio graphics queued.</div>'
    out = []
    for row in rows:
        out.append(f"""
        <div class="card">
          <div class="meta">
            <span>{esc(row.get('production_bucket'))}</span>
            <span>{esc(row.get('asset_type'))}</span>
            <span>{esc(row.get('graphics_safety_mode'))}</span>
          </div>
          <h3>{esc(row.get('studio_rank'))}. {esc(row.get('headline'))}</h3>
          <p><b>Score:</b> {esc(row.get('final_score'))}</p>
          <p><b>Template:</b> {esc(row.get('template'))}</p>
          <p><b>Caption:</b> {esc(row.get('caption_seed'))}</p>
          <details><summary>Prompt</summary><pre>{esc(row.get('graphic_prompt'))}</pre></details>
        </div>
        """)
    return '<div class="grid">' + "\n".join(out) + "</div>"


def checklist_table(rows: List[Dict[str, str]]) -> str:
    trs = []
    for r in rows[:200]:
        trs.append(
            "<tr>"
            f"<td>{esc(r.get('headline'))}</td>"
            f"<td>{esc(r.get('check_type'))}</td>"
            f"<td>{esc(r.get('status'))}</td>"
            f"<td>{esc(r.get('instruction'))}</td>"
            "</tr>"
        )
    return "<table><thead><tr><th>Graphic</th><th>Check</th><th>Status</th><th>Instruction</th></tr></thead><tbody>" + "".join(trs) + "</tbody></table>"


def main() -> None:
    rows = read_csv(QUEUE)
    center = read_text(CENTER)
    top = read_text(TOP)
    schedule = read_text(SCHEDULE)
    checklist = read_csv(CHECKLIST)

    doc = f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>HSD Studio Bridge</title>
<style>
:root {{
  --bg:#0f1020; --panel:#181a2f; --text:#f8f4ff; --muted:#c5bdd9;
  --pink:#ff4fd8; --cyan:#7cf7ff; --border:rgba(255,255,255,.14);
}}
* {{ box-sizing:border-box; }}
body {{
  margin:0; font-family:Inter,system-ui,sans-serif; color:var(--text); background:
  radial-gradient(circle at 15% 0%, rgba(255,79,216,.18), transparent 30%),
  radial-gradient(circle at 85% 0%, rgba(124,247,255,.12), transparent 30%),
  var(--bg);
}}
header {{ position:sticky; top:0; background:rgba(15,16,32,.94); border-bottom:1px solid var(--border); padding:20px; z-index:10; }}
.wrap {{ max-width:1280px; margin:0 auto; }}
.brand {{ display:flex; gap:14px; align-items:center; }}
.bug {{ width:54px; height:54px; border:2px solid var(--pink); border-radius:14px; display:grid; place-items:center; text-align:center; font-size:10px; font-weight:900; line-height:.95; }}
h1 {{ margin:0; font-size:clamp(26px,4vw,42px); }}
main {{ max-width:1280px; margin:0 auto; padding:22px; }}
.grid {{ display:grid; grid-template-columns:repeat(3,minmax(0,1fr)); gap:14px; }}
@media(max-width:960px) {{ .grid {{ grid-template-columns:1fr; }} }}
.card {{ background:rgba(24,26,47,.96); border:1px solid var(--border); border-radius:18px; padding:16px; box-shadow:0 12px 32px rgba(0,0,0,.24); }}
.card h3 {{ margin:10px 0; line-height:1.15; }}
.meta {{ display:flex; flex-wrap:wrap; gap:6px; }}
.meta span {{ border:1px solid var(--border); color:var(--muted); border-radius:999px; padding:5px 8px; font-size:12px; font-weight:800; }}
pre {{ white-space:pre-wrap; overflow:auto; background:rgba(0,0,0,.25); border:1px solid var(--border); border-radius:14px; padding:14px; color:var(--text); }}
table {{ width:100%; border-collapse:collapse; background:rgba(24,26,47,.96); border-radius:18px; overflow:hidden; }}
td, th {{ padding:10px; border-bottom:1px solid var(--border); font-size:12px; text-align:left; color:var(--muted); }}
th {{ color:var(--text); }}
.empty {{ padding:16px; border:1px dashed var(--border); border-radius:14px; color:var(--muted); }}
</style>
</head>
<body>
<header><div class="wrap brand"><div class="bug">HER<br>SPORTS<br>DAILY</div><div><h1>Studio Bridge</h1><div>Generated {esc(datetime.now(timezone.utc).isoformat())}</div></div></div></header>
<main>
<section><h2>Queued Graphics</h2>{cards(rows)}</section>
<section><h2>Post Schedule</h2><div class="card"><pre>{esc(schedule)}</pre></div></section>
<section><h2>Command Center</h2><div class="card"><pre>{esc(center)}</pre></div></section>
<section><h2>Accuracy Checklist</h2>{checklist_table(checklist)}</section>
<section><h2>Top Packets</h2><div class="card"><pre>{esc(top)}</pre></div></section>
</main>
</body>
</html>"""
    OUT_DIR.mkdir(exist_ok=True)
    OUT_FILE.write_text(doc, encoding="utf-8")
    print(f"Created {OUT_FILE}")


if __name__ == "__main__":
    main()
