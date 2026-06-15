from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

SUMMARY = Path("outputs/latest/summary.json")
OUT_REPORT = Path("outputs/latest/integrity_report.md")
ROOT_REPORT = Path("render_integrity_report.md")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_summary() -> dict:
    if not SUMMARY.exists():
        return {}
    try:
        return json.loads(SUMMARY.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def main() -> None:
    data = read_summary()
    graphics = int(data.get("graphics_files", 0) or 0)
    rendered = int(data.get("rendered_packets", 0) or 0)
    zips = int(data.get("zip_files", 0) or 0)
    errors = []
    if graphics > 0 and rendered == 0:
        errors.append("graphics_files_gt_zero_but_rendered_packets_zero")
    if rendered > 0 and zips == 0:
        errors.append("rendered_packets_gt_zero_but_zip_files_zero")
    status = "fail" if errors else "pass"
    data["integrity_status"] = status
    data["integrity_errors"] = errors
    data["integrity_checked_at"] = now_iso()
    if SUMMARY.exists():
        SUMMARY.write_text(json.dumps(data, indent=2), encoding="utf-8")
    lines = [
        "# HSD Render Integrity Report",
        "",
        f"Generated: {data.get('integrity_checked_at')}",
        f"Status: **{status}**",
        "",
        "## Counts",
        "",
        f"- graphics_files: {graphics}",
        f"- rendered_packets: {rendered}",
        f"- zip_files: {zips}",
        "",
        "## Integrity errors",
        "",
    ]
    lines += [f"- {e}" for e in errors] if errors else ["- None"]
    text = "\n".join(lines) + "\n"
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text(text, encoding="utf-8")
    ROOT_REPORT.write_text(text, encoding="utf-8")
    print(json.dumps({"integrity_status": status, "integrity_errors": errors}, indent=2))


if __name__ == "__main__":
    main()
