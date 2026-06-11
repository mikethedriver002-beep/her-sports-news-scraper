from __future__ import annotations

import csv
import html
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-operator-command-center-bebe-v2.2"
OUT_HTML = Path("operator_command_center.html")
OUT_MD = Path("operator_command_center.md")
OUT_JSON = Path("operator_command_center.json")

ARTIFACTS = [
    ("Install verification", "install_report.md"),
    ("Operator status", "operator_status.md"),
    ("Publish guard", "publish_guard_report.md"),
    ("BeBe daily ops plan", "bebe_daily_ops_plan.md"),
    ("BeBe posting schedule", "bebe_posting_schedule_today.md"),
    ("BeBe priority board", "bebe_priority_board.md"),
    ("Daily slate", "daily_slate_plan.md"),
    ("Manual story inbox", "manual_story_inbox_report.md"),
    ("Discovery sources", "discovery_sources_report.md"),
    ("Source registry audit", "source_registry_audit.md"),
    ("Preview build", "studio_preview_build_v2_report.md"),
    ("Preview quality", "preview_bundle_quality.md"),
    ("Graphics upload status", "graphics_upload_pack_status.csv"),
    ("Graphics handoff", "graphics_chat_direct_handoff.md"),
    ("Graphics QA", "graphics_qa_report.md"),
    ("Rendered slide QA", "rendered_slide_qa_report.md"),
]


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def exists(path: str) -> bool:
    return Path(path).exists()


def snippet(path: str, max_chars: int = 900) -> str:
    p = Path(path)
    if not p.exists():
        return ""
    try:
        text = p.read_text(encoding="utf-8", errors="replace")
        return text[:max_chars]
    except Exception:
        return ""


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def status_pill(label: str) -> str:
    low = label.lower()
    cls = "warn"
    if any(x in low for x in ["pass", "ready_for_graphics", "post_ready", "yes", "0 fail"]):
        cls = "good"
    if any(x in low for x in ["ready_with_review", "review_ready", "needs_manual_review", "pending", "not_checked"]):
        cls = "warn"
    if any(x in low for x in ["fail", "blocked", "missing", "error", "no-go"]):
        cls = "bad"
    return f'<span class="pill {cls}">{html.escape(label)}</span>'


def artifact_rows() -> List[Dict[str, Any]]:
    rows = []
    for title, path in ARTIFACTS:
        rows.append({"title": title, "path": path, "exists": exists(path), "snippet": snippet(path, 450)})
    return rows


def top_status() -> Dict[str, str]:
    install = read_json("install_report.json")
    ops = read_json("bebe_daily_ops_status.json")
    preview = read_csv("preview_bundle_quality_summary.csv")
    render = read_json("rendered_slide_qa_manifest.json")
    packs = read_csv("graphics_upload_pack_status.csv")
    operator = read_json("operator_status.json")
    guard = read_json("publish_guard_report.json")
    return {
        "install": "PASS" if not install.get("issues") else "FAIL",
        "preview_gate": preview[0].get("gate_status", "NOT_RUN") if preview else "NOT_RUN",
        "graphics_pack": "; ".join(sorted({clean(r.get("upload_pack_status")) for r in packs if clean(r.get("upload_pack_status"))})) or "not_created",
        "operator_overall": clean(operator.get("overall")) or "not_run",
        "graphics_handoff_allowed": str(bool(guard.get("graphics_handoff_allowed"))),
        "publish_allowed": str(bool(guard.get("publish_allowed"))),
        "rendered_slide_qa": (render.get("counts", {}) or {}).get("decision", "see_report") if render else "not_run",
        "day_type": clean(ops.get("day_type")) or "normal_day",
        "weekday": clean(ops.get("weekday")) or "",
    }


def main() -> None:
    rows = artifact_rows()
    status = top_status()
    payload = {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": status, "artifacts": rows}
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = [
        "# HSD Operator Command Center",
        "",
        f"Generated: {payload['generated_at_utc']}",
        f"Version: {VERSION}",
        "",
        "## Status",
        "",
        f"- Install: {status['install']}",
        f"- Preview gate: {status['preview_gate']}",
        f"- Graphics pack: {status['graphics_pack']}",
        f"- Operator overall: {status['operator_overall']}",
        f"- Graphics handoff allowed: {status['graphics_handoff_allowed']}",
        f"- Publish allowed: {status['publish_allowed']}",
        f"- Rendered slide QA: {status['rendered_slide_qa']}",
        f"- Day type: {status['day_type']}",
        "",
        "## Review order",
        "",
    ]
    for title, path in ARTIFACTS:
        md.append(f"- {'✅' if exists(path) else '⬜'} `{path}` — {title}")
    OUT_MD.write_text("\n".join(md) + "\n", encoding="utf-8")

    cards = []
    for r in rows:
        cards.append(f"""
        <section class="card {'missing' if not r['exists'] else ''}">
          <h3>{html.escape(r['title'])}</h3>
          <p><code>{html.escape(r['path'])}</code> {status_pill('found' if r['exists'] else 'missing')}</p>
          <pre>{html.escape(r['snippet'])}</pre>
        </section>
        """)

    html_doc = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>HSD Operator Command Center</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif; margin: 0; background: #f7f7fb; color: #181821; }}
    header {{ background: #181821; color: white; padding: 28px 32px; }}
    main {{ padding: 24px 32px 48px; max-width: 1180px; margin: 0 auto; }}
    h1 {{ margin: 0 0 8px; font-size: 30px; }}
    h2 {{ margin-top: 32px; }}
    .grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 14px; margin-top: 18px; }}
    .metric, .card {{ background: white; border: 1px solid #e6e6ee; border-radius: 14px; padding: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }}
    .metric strong {{ display: block; font-size: 13px; color: #666; text-transform: uppercase; letter-spacing: .04em; }}
    .metric span {{ display: block; margin-top: 8px; font-size: 20px; font-weight: 700; }}
    .pill {{ display: inline-block; border-radius: 999px; padding: 3px 9px; font-size: 12px; font-weight: 700; background: #fff2bd; color: #574400; }}
    .pill.good {{ background: #d9f7e3; color: #10451f; }}
    .pill.bad {{ background: #ffe0df; color: #74110c; }}
    .card.missing {{ opacity: .64; }}
    pre {{ white-space: pre-wrap; max-height: 220px; overflow: auto; background: #fafafa; border-radius: 10px; padding: 10px; font-size: 12px; }}
    code {{ background: #f0f0f5; padding: 2px 5px; border-radius: 5px; }}
  </style>
</head>
<body>
  <header>
    <h1>HSD Operator Command Center</h1>
    <div>BeBe Ops v2 · generated {html.escape(payload['generated_at_utc'])}</div>
  </header>
  <main>
    <section class="grid">
      <div class="metric"><strong>Install</strong><span>{status_pill(status['install'])}</span></div>
      <div class="metric"><strong>Preview gate</strong><span>{status_pill(status['preview_gate'])}</span></div>
      <div class="metric"><strong>Graphics pack</strong><span>{status_pill(status['graphics_pack'])}</span></div>
      <div class="metric"><strong>Operator overall</strong><span>{status_pill(status['operator_overall'])}</span></div>
      <div class="metric"><strong>Graphics handoff</strong><span>{status_pill(status['graphics_handoff_allowed'])}</span></div>
      <div class="metric"><strong>Publish allowed</strong><span>{status_pill(status['publish_allowed'])}</span></div>
      <div class="metric"><strong>Rendered slide QA</strong><span>{status_pill(status['rendered_slide_qa'])}</span></div>
      <div class="metric"><strong>Desk day</strong><span>{html.escape(status['weekday'] or 'today')} · {html.escape(status['day_type'])}</span></div>
    </section>
    <h2>Review order</h2>
    <p>Use this page as the lite artifact index. Post manually to Instagram and Threads only after the relevant gates pass.</p>
    <section class="grid">
      {''.join(cards)}
    </section>
  </main>
</body>
</html>
"""
    OUT_HTML.write_text(html_doc, encoding="utf-8")
    print(json.dumps({"artifacts": len(rows), "html": OUT_HTML.as_posix()}, indent=2))


if __name__ == "__main__":
    main()
