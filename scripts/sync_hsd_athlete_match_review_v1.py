from __future__ import annotations

import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SRC = Path("data/asset_registry/wnba/athlete_image_match_review.csv")
OUT_DIR = Path("outputs/latest/review_files")
OUT_CSV = OUT_DIR / "athlete_image_match_review.csv"
OUT_REPORT = OUT_DIR / "athlete_image_match_review_report.md"
SUMMARY = Path("outputs/latest/summary.json")
APPROVAL_SCRIPT = Path("scripts/generate_hsd_athlete_image_approval_pack_v1.py")
APPLY_SCRIPT = Path("scripts/apply_hsd_athlete_image_approvals_v1.py")
SMOKE_SCRIPT = Path("scripts/generate_hsd_render_athlete_smoke_test_v1.py")
PRODUCTION_DIRECTOR_SCRIPT = Path("scripts/generate_hsd_mermaid_production_graphics_director_v4.py")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def run_script(script: Path) -> Dict[str, Any]:
    if not script.exists():
        return {"status": "missing", "returncode": 127}
    proc = subprocess.run([sys.executable, script.as_posix()], text=True, capture_output=True, timeout=420)
    return {"status": "ok" if proc.returncode == 0 else "error", "returncode": proc.returncode, "stdout": proc.stdout[-1200:], "stderr": proc.stderr[-1200:]}


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(SRC)
    if SRC.exists():
        shutil.copy2(SRC, OUT_CSV)
    needs_approval = len([r for r in rows if r.get("status") == "needs_human_approval"])
    highish = len([r for r in rows if float(r.get("confidence") or 0) >= 0.70])
    summary = read_json(SUMMARY)
    summary["athlete_match_review_rows"] = len(rows)
    summary["athlete_matches_need_approval"] = needs_approval
    summary["athlete_order_matches_confidence_70_plus"] = highish
    if SUMMARY.exists():
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    approval_pack = run_script(APPROVAL_SCRIPT)
    approval_apply = run_script(APPLY_SCRIPT)
    smoke_test = run_script(SMOKE_SCRIPT)
    production_director = run_script(PRODUCTION_DIRECTOR_SCRIPT)
    lines = [
        "# HSD Athlete Image Match Review",
        "",
        f"Generated: {now_iso()}",
        "",
        "## Counts",
        "",
        f"- match review rows: {len(rows)}",
        f"- needs human approval: {needs_approval}",
        f"- confidence 0.70 or higher: {highish}",
        "",
        "## Approval Pack",
        "",
        f"- status: {approval_pack.get('status')}",
        f"- returncode: {approval_pack.get('returncode')}",
        "- folder: `outputs/latest/review_files/athlete_image_approval_pack/`",
        "",
        "## Approval Apply",
        "",
        f"- status: {approval_apply.get('status')}",
        f"- returncode: {approval_apply.get('returncode')}",
        "- report: `data/asset_registry/wnba/athlete_image_approval_apply_report.md`",
        "",
        "## Render Smoke Test",
        "",
        f"- status: {smoke_test.get('status')}",
        f"- returncode: {smoke_test.get('returncode')}",
        "- folder: `outputs/latest/review_files/athlete_smoke_test/`",
        "",
        "## Production Graphics Director v4",
        "",
        f"- status: {production_director.get('status')}",
        f"- returncode: {production_director.get('returncode')}",
        "- folder: `outputs/latest/production_graphics_director/`",
        "- graphics folder: `outputs/latest/POSTABLE_GRAPHICS/`",
        "",
        "## Policy",
        "",
        "- Needs-fix and rejected rows remain blocked from graphics.",
        "- Auto-rendered graphics require human visual review before posting.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"match_review_rows": len(rows), "approval_pack": approval_pack.get("status"), "approval_apply": approval_apply.get("status"), "smoke_test": smoke_test.get("status"), "production_director": production_director.get("status")}, indent=2))


if __name__ == "__main__":
    main()
