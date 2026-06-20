from __future__ import annotations

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

VERSION = "v1.0-phase6f-visual-approval-validator"
OUT = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v4")
APPROVAL_DIR = OUT / "approval"
CANDIDATES_CSV = APPROVAL_DIR / "visual_approval_candidates_v4.csv"
DECISIONS_PATHS = [
    Path("config/graphics/v4/approval/visual_approval_decisions_v4.csv"),
    APPROVAL_DIR / "visual_approval_decisions_v4.csv",
]
APPROVED_CSV = APPROVAL_DIR / "visual_approval_approved_assets_v4.csv"
REJECTED_CSV = APPROVAL_DIR / "visual_approval_rejected_assets_v4.csv"
BLOCKED_CSV = APPROVAL_DIR / "visual_approval_blocked_assets_v4.csv"
HANDOFF_CSV = APPROVAL_DIR / "operator_handoff_v4_approved_assets.csv"
CUTOVER_MD = APPROVAL_DIR / "production_cutover_prep_v4.md"
REPORT_JSON = APPROVAL_DIR / "visual_approval_validation_v4_report.json"
REPORT_MD = APPROVAL_DIR / "visual_approval_validation_v4_report.md"

ALLOWED = {"approved", "rejected", "needs_fix", "hold", ""}
FIELDS = ["approval_id", "decision", "reviewer", "reviewed_at", "reason", "render_sha256"]


def clean(value: Any) -> str:
    return str(value or "").strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: Iterable[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def find_decisions(root: Path) -> Optional[Path]:
    for rel in DECISIONS_PATHS:
        path = root / rel
        if path.exists():
            return path
    return None


def candidate_map(rows: List[Dict[str, str]]) -> Dict[str, Dict[str, str]]:
    return {clean(row.get("approval_id")): row for row in rows if clean(row.get("approval_id"))}


def can_approve(candidate: Dict[str, str]) -> List[str]:
    reasons = []
    if clean(candidate.get("approval_status")) != "approval_candidate":
        reasons.append(f"not_approval_candidate:{clean(candidate.get('approval_status'))}")
    if clean(candidate.get("fixture_only_player_asset")).lower() == "true":
        reasons.append("fixture_only_player_asset")
    try:
        if int(float(clean(candidate.get("placeholder_layer_count")) or "0")) > 0:
            reasons.append("placeholder_layers_present")
    except Exception:
        reasons.append("invalid_placeholder_layer_count")
    try:
        if int(float(clean(candidate.get("zone_overflow_count")) or "0")) > 0:
            reasons.append("zone_overflow_present")
    except Exception:
        reasons.append("invalid_zone_overflow_count")
    if clean(candidate.get("near_post_ready_candidate")).lower() != "true":
        reasons.append("near_post_ready_candidate_false")
    return reasons


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root)
    approval_dir = root / APPROVAL_DIR
    approval_dir.mkdir(parents=True, exist_ok=True)
    candidates = read_csv(root / CANDIDATES_CSV)
    cmap = candidate_map(candidates)
    blockers: List[str] = []
    warnings: List[str] = []
    if not candidates:
        blockers.append("visual_approval_candidates_missing")
    decisions_path = find_decisions(root)
    approved: List[Dict[str, str]] = []
    rejected: List[Dict[str, str]] = []
    blocked: List[Dict[str, str]] = []
    decision_count = 0
    if decisions_path is None:
        status = "waiting_for_human_visual_approval"
        warnings.append("visual_approval_decisions_file_missing")
    else:
        decisions = read_csv(decisions_path)
        status = "visual_approval_decisions_validated"
        for idx, decision in enumerate(decisions, start=2):
            approval_id = clean(decision.get("approval_id"))
            if not approval_id:
                continue
            decision_value = clean(decision.get("decision")).lower()
            decision_count += 1
            if decision_value not in ALLOWED:
                blockers.append(f"invalid_decision:{approval_id}:{decision_value}:line_{idx}")
                continue
            candidate = cmap.get(approval_id)
            if not candidate:
                blockers.append(f"unknown_approval_id:{approval_id}:line_{idx}")
                continue
            if clean(decision.get("render_sha256")) and clean(decision.get("render_sha256")) != clean(candidate.get("render_sha256")):
                blockers.append(f"render_sha_mismatch:{approval_id}:line_{idx}")
                continue
            merged = {**candidate, **{f"decision_{key}": value for key, value in decision.items()}, "decision": decision_value}
            if decision_value == "approved":
                reasons = can_approve(candidate)
                if reasons:
                    merged["approval_blockers"] = ";".join(reasons)
                    blocked.append(merged)
                    blockers.append(f"cannot_approve:{approval_id}:{';'.join(reasons)}")
                else:
                    approved.append(merged)
            elif decision_value in {"rejected", "needs_fix", "hold"}:
                rejected.append(merged)
        if not blockers:
            status = "visual_approval_validated_with_approved_assets" if approved else "visual_approval_validated_no_approved_assets"
    fields = sorted(set().union(*(row.keys() for row in candidates + approved + rejected + blocked)) if (candidates or approved or rejected or blocked) else set(FIELDS))
    write_csv(root / APPROVED_CSV, approved, fields)
    write_csv(root / REJECTED_CSV, rejected, fields)
    write_csv(root / BLOCKED_CSV, blocked, fields)
    write_csv(root / HANDOFF_CSV, approved, fields)
    limited_handoff_allowed = bool(approved and not blockers)
    report = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": "blocked_visual_approval_validation" if blockers else status,
        "strict_exit_code": 2 if blockers else 0,
        "candidate_rows": len(candidates),
        "decision_rows": decision_count,
        "approved_count": len(approved),
        "rejected_or_hold_count": len(rejected),
        "blocked_approval_count": len(blocked),
        "blockers": blockers,
        "warnings": warnings,
        "human_visual_approval_required": True,
        "limited_operator_handoff_allowed": limited_handoff_allowed,
        "production_cutover_allowed": False,
        "cutover_prep_required": limited_handoff_allowed,
        "outputs": {
            "approved_csv": (root / APPROVED_CSV).as_posix(),
            "rejected_csv": (root / REJECTED_CSV).as_posix(),
            "blocked_csv": (root / BLOCKED_CSV).as_posix(),
            "operator_handoff_csv": (root / HANDOFF_CSV).as_posix(),
            "cutover_prep_md": (root / CUTOVER_MD).as_posix(),
        },
    }
    CUTOVER_MD_ABS = root / CUTOVER_MD
    CUTOVER_MD_ABS.parent.mkdir(parents=True, exist_ok=True)
    CUTOVER_MD_ABS.write_text("\n".join([
        "# HSD Phase 6F Production Cutover Prep",
        "",
        f"Status: `{report['status']}`",
        f"Approved assets: `{len(approved)}`",
        f"Limited operator handoff allowed: `{limited_handoff_allowed}`",
        "Production cutover allowed: `false`",
        "",
        "## Meaning",
        "",
        "This phase can prepare approved Renderer v4.2 assets for operator handoff after human visual approval.",
        "It does not change production routing, does not publish, and does not replace HSD_QUALITY_GRAPHICS.",
        "",
        "## Next cutover requirements",
        "",
        "- At least one approved render hash in visual_approval_decisions_v4.csv.",
        "- No blocked approval rows.",
        "- Separate cutover PR to route approved Renderer v4.2 assets into the production handoff lane.",
        "",
    ]), encoding="utf-8")
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    (root / REPORT_MD).write_text("\n".join([
        "# HSD Phase 6F Visual Approval Validation Report",
        "",
        f"Status: `{report['status']}`",
        f"Candidate rows: `{len(candidates)}`",
        f"Decision rows: `{decision_count}`",
        f"Approved count: `{len(approved)}`",
        f"Blockers: `{blockers}`",
        f"Warnings: `{warnings}`",
        "",
        "Production cutover remains blocked until a separate cutover PR.",
        "",
    ]), encoding="utf-8")
    print(json.dumps(report, indent=2, sort_keys=True))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
