from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

DECISIONS = Path("outputs/latest/review_files/athlete_image_approval_pack/approval_decisions.csv")
OVERRIDES = Path("data/asset_registry/wnba/athlete_image_decision_overrides.csv")
REPORT_JSON = Path("data/asset_registry/wnba/athlete_image_approval_apply_report.json")
REPORT_MD = Path("data/asset_registry/wnba/athlete_image_approval_apply_report.md")
APPROVED_CSV = Path("data/asset_registry/wnba/athlete_image_approved_assets.csv")
NEEDS_FIX_CSV = Path("data/asset_registry/wnba/athlete_image_needs_fix.csv")
REJECTED_CSV = Path("data/asset_registry/wnba/athlete_image_rejected.csv")
SUMMARY = Path("outputs/latest/summary.json")
PACK_DIR = Path("outputs/latest/review_files/athlete_image_approval_pack")

APPROVED_FIELDS = ["athlete_id", "display_name", "team_id", "provider_player_id", "approved_file", "approved_marker", "source_file", "approved_at_utc", "decision_source"]
NEEDS_FIX_FIELDS = ["athlete_id", "display_name", "team_id", "provider_player_id", "downloaded_file", "approval_target_path", "reason"]
REJECTED_FIELDS = ["athlete_id", "display_name", "team_id", "provider_player_id", "downloaded_file", "approval_target_path", "reason"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def normalize_decision(value: str) -> str:
    value = str(value or "").strip().lower().replace(" ", "_")
    if value in {"approve", "approved", "yes", "y"}:
        return "approve"
    if value in {"reject", "rejected", "no", "n"}:
        return "reject"
    if value in {"needs_fix", "needsfix", "fix", "blank", "generic"}:
        return "needs_fix"
    return value


def load_overrides() -> tuple[str, Dict[str, Dict[str, str]]]:
    default = ""
    overrides: Dict[str, Dict[str, str]] = {}
    for row in read_csv(OVERRIDES):
        athlete_id = str(row.get("athlete_id", "")).strip()
        decision = normalize_decision(row.get("decision", ""))
        if athlete_id == "*":
            default = decision
        elif athlete_id:
            overrides[athlete_id] = {"decision": decision, "reason": row.get("reason", "")}
    return default, overrides


def safe_target(path: str) -> bool:
    p = Path(path)
    text = p.as_posix()
    return text.startswith("assets/leagues/wnba/athletes/") and text.endswith("/headshot.png") and ".." not in p.parts


def safe_source(path: str) -> bool:
    p = Path(path)
    text = p.as_posix()
    return text.startswith("outputs/latest/review_files/athlete_image_approval_pack/downloads/") and text.endswith(".png") and ".." not in p.parts


def decide(row: Dict[str, str], default: str, overrides: Dict[str, Dict[str, str]]) -> tuple[str, str, str]:
    athlete_id = row.get("athlete_id", "")
    if athlete_id in overrides:
        item = overrides[athlete_id]
        return item.get("decision", ""), item.get("reason", ""), "override"
    decision = normalize_decision(row.get("decision", ""))
    if decision:
        return decision, row.get("reviewer_notes", ""), "approval_csv"
    return default, "default_decision_from_overrides", "default"


def apply_one(row: Dict[str, str], decision: str, reason: str, source_name: str) -> Dict[str, Any]:
    src = Path(row.get("downloaded_file", ""))
    dst = Path(row.get("approval_target_path", ""))
    base = {
        "athlete_id": row.get("athlete_id", ""),
        "display_name": row.get("display_name", ""),
        "team_id": row.get("team_id", ""),
        "provider_player_id": row.get("provider_player_id", ""),
        "downloaded_file": src.as_posix(),
        "approval_target_path": dst.as_posix(),
        "reason": reason,
        "decision_source": source_name,
    }
    if decision != "approve":
        return {**base, "status": decision or "skipped"}
    if not safe_source(src.as_posix()) or not src.exists() or src.stat().st_size < 100:
        return {**base, "status": "failed", "reason": "missing or unsafe source file"}
    if not safe_target(dst.as_posix()):
        return {**base, "status": "failed", "reason": "unsafe target path"}
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    marker = Path(dst.as_posix() + ".approved")
    marker.write_text(json.dumps({
        "approved_at_utc": now_iso(),
        "athlete_id": row.get("athlete_id", ""),
        "display_name": row.get("display_name", ""),
        "team_id": row.get("team_id", ""),
        "provider_player_id": row.get("provider_player_id", ""),
        "source_file": src.as_posix(),
        "decision_source": source_name,
        "policy": "human_reviewed_contact_sheet_then_approved",
    }, indent=2), encoding="utf-8")
    return {**base, "status": "approved", "approved_file": dst.as_posix(), "approved_marker": marker.as_posix(), "approved_at_utc": now_iso()}


def update_summary(fields: Dict[str, Any]) -> None:
    summary = read_json(SUMMARY)
    summary.update(fields)
    if SUMMARY.parent.exists():
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def mirror_to_pack() -> None:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    mirrors = [
        (REPORT_MD, PACK_DIR / "athlete_image_approval_apply_report.md"),
        (REPORT_JSON, PACK_DIR / "athlete_image_approval_apply_report.json"),
        (APPROVED_CSV, PACK_DIR / "approved_assets.csv"),
        (NEEDS_FIX_CSV, PACK_DIR / "needs_fix.csv"),
        (REJECTED_CSV, PACK_DIR / "rejected.csv"),
    ]
    for src, dst in mirrors:
        if src.exists():
            shutil.copy2(src, dst)


def main() -> None:
    rows = read_csv(DECISIONS)
    default, overrides = load_overrides()
    applied: List[Dict[str, Any]] = []
    for row in rows:
        decision, reason, source_name = decide(row, default, overrides)
        applied.append(apply_one(row, decision, reason, source_name))
    approved = [r for r in applied if r.get("status") == "approved"]
    needs_fix = [r for r in applied if r.get("status") == "needs_fix"]
    rejected = [r for r in applied if r.get("status") == "reject"]
    failed = [r for r in applied if r.get("status") == "failed"]
    write_csv(APPROVED_CSV, [{
        "athlete_id": r.get("athlete_id"),
        "display_name": r.get("display_name"),
        "team_id": r.get("team_id"),
        "provider_player_id": r.get("provider_player_id"),
        "approved_file": r.get("approved_file"),
        "approved_marker": r.get("approved_marker"),
        "source_file": r.get("downloaded_file"),
        "approved_at_utc": r.get("approved_at_utc"),
        "decision_source": r.get("decision_source"),
    } for r in approved], APPROVED_FIELDS)
    write_csv(NEEDS_FIX_CSV, needs_fix, NEEDS_FIX_FIELDS)
    write_csv(REJECTED_CSV, rejected, REJECTED_FIELDS)
    report = {
        "version": "hsd-athlete-image-approval-apply-v1",
        "generated_at_utc": now_iso(),
        "decision_rows": len(rows),
        "default_decision": default,
        "override_rows": len(overrides),
        "approved": len(approved),
        "needs_fix": len(needs_fix),
        "rejected": len(rejected),
        "failed": len(failed),
        "approved_csv": APPROVED_CSV.as_posix(),
        "needs_fix_csv": NEEDS_FIX_CSV.as_posix(),
        "rejected_csv": REJECTED_CSV.as_posix(),
        "failed_rows": failed,
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# HSD Athlete Image Approval Apply v1",
        "",
        f"Generated: {report['generated_at_utc']}",
        "",
        "## Counts",
        "",
        f"- decision rows: {len(rows)}",
        f"- default decision: {default}",
        f"- override rows: {len(overrides)}",
        f"- approved: {len(approved)}",
        f"- needs_fix: {len(needs_fix)}",
        f"- rejected: {len(rejected)}",
        f"- failed: {len(failed)}",
        "",
        "## Needs fix policy",
        "",
        "- Needs-fix rows are not public-use approved.",
        "- Generic official blank headshots should remain blocked until a real approved image is supplied or the WNBA roster page updates.",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    update_summary({
        "athlete_approval_apply_approved": len(approved),
        "athlete_approval_apply_needs_fix": len(needs_fix),
        "athlete_approval_apply_rejected": len(rejected),
        "athlete_approval_apply_failed": len(failed),
    })
    mirror_to_pack()
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
