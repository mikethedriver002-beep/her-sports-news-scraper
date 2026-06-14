from __future__ import annotations

import csv
import html
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-operator-command-center-bebe-v2.6.1"
OUT_HTML = Path("operator_command_center.html")
OUT_MD = Path("operator_command_center.md")
OUT_JSON = Path("operator_command_center.json")

ARTIFACTS = [
    ("Install verification", "install_report.md"),
    ("Operator status", "operator_status.md"),
    ("Publish guard", "publish_guard_report.md"),
    ("BeBe daily ops plan", "bebe_daily_ops_plan.md"),
    ("BeBe posting schedule", "bebe_posting_schedule_today.md"),
    ("Preview quality", "preview_bundle_quality.md"),
    ("Graphics upload status", "graphics_upload_pack_status.csv"),
    ("Mermaid Upper Echelon", "mermaid_upper_echelon_report.md"),
    ("Mermaid content board", "mermaid_master_content_board.md"),
    ("Mermaid slots", "mermaid_content_slots_v2.csv"),
    ("Assignment freshness gate", "mermaid_assignment_freshness_gate_report.md"),
    ("Assignment handoff", "assignment_handoff_report.md"),
    ("Assignment handoff publisher", "assignment_handoff_publisher_report.md"),
    ("Manual workflow handoff", "manual_workflow_handoff.md"),
    ("Manual workflow content packets", "manual_workflow_content_packets.csv"),
    ("Manual workflow pack status", "manual_workflow_pack_status.csv"),
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
        return p.read_text(encoding="utf-8", errors="replace")[:max_chars]
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
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def refresh_assignment_handoff() -> Dict[str, Any]:
    script = Path("generate_hsd_mermaid_handoff_publisher_v2_6_1.py")
    if not script.exists():
        return {"status": "missing"}
    proc = subprocess.run([sys.executable, script.as_posix()], text=True, capture_output=True, timeout=260)
    return {"status": "ok" if proc.returncode == 0 else "error", "returncode": proc.returncode, "stdout": proc.stdout[-1000:], "stderr": proc.stderr[-1000:]}


def status_pill(label: str) -> str:
    low = label.lower()
    cls = "warn"
    if any(x in low for x in ["pass", "ready", "ok", "true"]):
        cls = "good"
    if any(x in low for x in ["fail", "blocked", "missing", "error", "no-go", "false"]):
        cls = "bad"
    return f'<span class="pill {cls}">{html.escape(label)}</span>'


def artifact_rows() -> List[Dict[str, Any]]:
    return [{"title": title, "path": path, "exists": exists(path), "snippet": snippet(path, 650)} for title, path in ARTIFACTS]


def top_status(refresh: Dict[str, Any]) -> Dict[str, str]:
    install = read_json("install_report.json")
    ops = read_json("bebe_daily_ops_status.json")
    preview = read_csv("preview_bundle_quality_summary.csv")
    render = read_json("rendered_slide_qa_manifest.json")
    packs = read_csv("graphics_upload_pack_status.csv")
    operator = read_json("operator_status.json")
    guard = read_json("publish_guard_report.json")
    handoff = read_json("assignment_handoff_publisher_manifest.json")
    counts = handoff.get("counts", {}) if isinstance(handoff, dict) else {}
    return {
        "install": "PASS" if not install.get("issues") else "FAIL",
        "preview_gate": preview[0].get("gate_status", "NOT_RUN") if preview else "NOT_RUN",
        "graphics_pack": "; ".join(sorted({clean(r.get("upload_pack_status")) for r in packs if clean(r.get("upload_pack_status"))})) or "not_created",
        "operator_overall": clean(operator.get("overall")) or "not_run",
        "graphics_handoff_allowed": str(bool(guard.get("graphics_handoff_allowed"))),
        "publish_allowed": str(bool(guard.get("publish_allowed"))),
        "rendered_slide_qa": str((render.get("counts", {}) or {}).get("decision", "not_run")) if render else "not_run",
        "day_type": clean(ops.get("day_type")) or "normal_day",
        "weekday": clean(ops.get("weekday")) or "",
        "assignment_handoff_refresh": clean(refresh.get("status")) or "not_run",
        "handoff_packets": str(counts.get("handoff_packets", "0")),
        "manual_zip_count": str(counts.get("manual_zip_count", "0")),
    }


def main() -> None:
    refresh = refresh_assignment_handoff()
    rows = artifact_rows()
    status = top_status(refresh)
    payload = {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "status": status, "handoff_refresh": refresh, "artifacts": rows}
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = ["# HSD Operator Command Center", "", f"Generated: {payload['generated_at_utc']}", f"Version: {VERSION}", "", "## Status", ""]
    for key, value in status.items():
        md.append(f"- {key.replace('_', ' ').title()}: {value}")
    md += ["", "## Review order", ""]
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
    metrics = "".join(f"<div class='metric'><strong>{html.escape(k.replace('_',' ').title())}</strong><span>{status_pill(str(v))}</span></div>" for k, v in status.items())
    html_doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>HSD Operator Command Center</title><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;margin:0;background:#f7f7fb;color:#181821}}header{{background:#181821;color:white;padding:28px 32px}}main{{padding:24px 32px 48px;max-width:1180px;margin:0 auto}}.grid{{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;margin-top:18px}}.metric,.card{{background:white;border:1px solid #e6e6ee;border-radius:14px;padding:16px;box-shadow:0 1px 3px rgba(0,0,0,.04)}}.metric strong{{display:block;font-size:13px;color:#666;text-transform:uppercase;letter-spacing:.04em}}.metric span{{display:block;margin-top:8px;font-size:20px;font-weight:700}}.pill{{display:inline-block;border-radius:999px;padding:3px 9px;font-size:12px;font-weight:700;background:#fff2bd;color:#574400}}.pill.good{{background:#d9f7e3;color:#10451f}}.pill.bad{{background:#ffe0df;color:#74110c}}.card.missing{{opacity:.64}}pre{{white-space:pre-wrap;max-height:220px;overflow:auto;background:#fafafa;border-radius:10px;padding:10px;font-size:12px}}code{{background:#f0f0f5;padding:2px 5px;border-radius:5px}}</style></head><body><header><h1>HSD Operator Command Center</h1><div>generated {html.escape(payload['generated_at_utc'])}</div></header><main><section class='grid'>{metrics}</section><h2>Review order</h2><section class='grid'>{''.join(cards)}</section></main></body></html>"""
    OUT_HTML.write_text(html_doc, encoding="utf-8")
    print(json.dumps({"artifacts": len(rows), "handoff_refresh": refresh.get("status"), "html": OUT_HTML.as_posix()}, indent=2))


if __name__ == "__main__":
    main()
