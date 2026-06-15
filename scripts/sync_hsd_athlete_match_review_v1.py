from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

SRC = Path("data/asset_registry/wnba/athlete_image_match_review.csv")
OUT_DIR = Path("outputs/latest/review_files")
OUT_CSV = OUT_DIR / "athlete_image_match_review.csv"
OUT_REPORT = OUT_DIR / "athlete_image_match_review_report.md"
SUMMARY = Path("outputs/latest/summary.json")


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
        "## Usage policy",
        "",
        "- These are order-based candidate matches only.",
        "- Do not use any athlete image in public graphics until the image is reviewed, placed at the approval target path, and an `.approved` marker exists.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"match_review_rows": len(rows), "needs_human_approval": needs_approval, "confidence_70_plus": highish}, indent=2))


if __name__ == "__main__":
    main()
