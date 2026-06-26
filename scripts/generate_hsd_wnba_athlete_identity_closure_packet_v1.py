from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Sequence, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hsd_run_io import output_path, write_csv as write_run_csv, write_json, write_text

import report_hsd_wnba_athlete_identity_audit_v1 as identity_audit


ROOT = Path("data/asset_registry/wnba")
ATHLETES = ROOT / "athletes.csv"
ATHLETE_IMAGES = ROOT / "athlete_images.csv"
APPROVED_ASSETS = ROOT / "athlete_image_approved_assets.csv"
MATCH_REVIEW = ROOT / "athlete_image_match_review.csv"
APPROVAL_DECISIONS = Path("outputs/latest/review_files/athlete_image_approval_pack/approval_decisions.csv")

OUT_CLOSURE_CSV = "data/asset_registry/wnba/athlete_identity_issue_closure_template.csv"
OUT_BACKFILL_CSV = "data/asset_registry/wnba/athlete_identity_provider_id_backfill_template.csv"
OUT_JSON = "data/asset_registry/wnba/athlete_identity_closure_packet.json"
OUT_MD = "data/asset_registry/wnba/athlete_identity_closure_packet.md"

VERSION = "hsd-wnba-athlete-identity-closure-packet-v1-review-only"
REVIEW_ONLY_POLICY = "manual_closure_packet_only_no_auto_approval_no_registry_write_no_file_movement_no_publish_ready_lane"

CLOSURE_FIELDS = [
    "issue_key",
    "severity",
    "issue_code",
    "athlete_id",
    "display_name",
    "team_id",
    "provider_player_id",
    "asset_path",
    "approved_marker_path",
    "evidence",
    "recommendation",
    "allowed_closure_decisions",
    "operator_closure_decision",
    "manual_identity_verified",
    "provider_id_verified",
    "registry_backfill_needed",
    "reviewer",
    "reviewed_at_utc",
    "operator_notes",
    "review_only_policy",
    "auto_approval",
    "auto_publish",
    "move_files",
    "publish_ready",
]

BACKFILL_FIELDS = [
    "backfill_key",
    "target_csv",
    "match_key",
    "athlete_id",
    "display_name",
    "team_id",
    "target_field",
    "current_value",
    "proposed_value",
    "candidate_sources",
    "backfill_status",
    "allowed_decisions",
    "operator_decision",
    "reviewer",
    "reviewed_at_utc",
    "operator_notes",
    "manual_edit_target",
    "review_only_policy",
    "auto_apply",
    "auto_approval",
    "auto_publish",
    "move_files",
    "publish_ready",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def stable_key(*parts: Any, size: int = 16) -> str:
    raw = "|".join(clean(part) for part in parts)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:size]


def by_athlete(rows: Iterable[Mapping[str, str]]) -> Dict[str, List[Mapping[str, str]]]:
    out: Dict[str, List[Mapping[str, str]]] = {}
    for row in rows:
        athlete_id = clean(row.get("athlete_id"))
        if athlete_id:
            out.setdefault(athlete_id, []).append(row)
    return out


def one_by_athlete(rows: Iterable[Mapping[str, str]]) -> Dict[str, Mapping[str, str]]:
    out: Dict[str, Mapping[str, str]] = {}
    for row in rows:
        athlete_id = clean(row.get("athlete_id"))
        if athlete_id and athlete_id not in out:
            out[athlete_id] = row
    return out


def parse_provider_id_from_text(value: Any) -> str:
    text = clean(value)
    if not text:
        return ""
    headshot_match = re.search(r"/260x190/(\d{4,10})\.png(?:$|\?)", text)
    if headshot_match:
        return headshot_match.group(1)
    file_match = re.search(r"__(\d{4,10})\.png(?:$|\?)", text)
    if file_match:
        return file_match.group(1)
    return ""


def add_candidate(candidates: Dict[str, List[str]], provider_id: str, source: str) -> None:
    provider_id = clean(provider_id)
    if not provider_id:
        return
    candidates.setdefault(provider_id, [])
    if source not in candidates[provider_id]:
        candidates[provider_id].append(source)


def provider_candidates(
    athlete_id: str,
    athlete_row: Mapping[str, str],
    image_rows: Sequence[Mapping[str, str]],
    approved_rows: Sequence[Mapping[str, str]],
    review_rows: Sequence[Mapping[str, str]],
) -> Dict[str, List[str]]:
    candidates: Dict[str, List[str]] = {}
    add_candidate(candidates, athlete_row.get("provider_player_id", ""), "athletes.csv")
    for row in image_rows:
        kind = clean(row.get("image_type")) or "image"
        add_candidate(candidates, row.get("provider_player_id", ""), f"athlete_images.csv:{kind}")
    for row in approved_rows:
        add_candidate(candidates, row.get("provider_player_id", ""), "athlete_image_approved_assets.csv")
        add_candidate(candidates, parse_provider_id_from_text(row.get("source_file", "")), "approved_assets.source_file")
        marker_payload = read_json(Path(clean(row.get("approved_marker"))))
        add_candidate(candidates, marker_payload.get("provider_player_id", ""), "approved_marker")
    for row in review_rows:
        add_candidate(candidates, row.get("provider_player_id", ""), "athlete_image_match_review.csv")
        add_candidate(candidates, parse_provider_id_from_text(row.get("image_url", "")), "match_review.image_url")
    return candidates


def selected_provider_candidate(candidates: Mapping[str, Sequence[str]]) -> Tuple[str, str, str]:
    if not candidates:
        return "", "", "no_provider_id_candidate_found"
    values = sorted(candidates)
    sources = "; ".join(f"{value}: {', '.join(candidates[value])}" for value in values)
    if len(values) == 1:
        return values[0], sources, "manual_review_required"
    return "", sources, "provider_id_conflict_manual_resolution"


def build_closure_rows(issues: Sequence[Mapping[str, str]]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for issue in issues:
        issue_key = stable_key(
            issue.get("severity"),
            issue.get("issue_code"),
            issue.get("athlete_id"),
            issue.get("asset_path"),
            issue.get("evidence"),
        )
        rows.append({
            "issue_key": issue_key,
            "severity": clean(issue.get("severity")),
            "issue_code": clean(issue.get("issue_code")),
            "athlete_id": clean(issue.get("athlete_id")),
            "display_name": clean(issue.get("display_name")),
            "team_id": clean(issue.get("team_id")),
            "provider_player_id": clean(issue.get("provider_player_id")),
            "asset_path": clean(issue.get("asset_path")),
            "approved_marker_path": clean(issue.get("approved_marker_path")),
            "evidence": clean(issue.get("evidence")),
            "recommendation": clean(issue.get("recommendation")),
            "allowed_closure_decisions": "close_after_manual_identity_verification|keep_open|needs_registry_backfill|hold_asset|mark_false_positive",
            "operator_closure_decision": "",
            "manual_identity_verified": "",
            "provider_id_verified": "",
            "registry_backfill_needed": "",
            "reviewer": "",
            "reviewed_at_utc": "",
            "operator_notes": "",
            "review_only_policy": REVIEW_ONLY_POLICY,
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "publish_ready": "false",
        })
    return rows


def backfill_row(
    *,
    target_csv: str,
    match_key: str,
    athlete_id: str,
    display_name: str,
    team_id: str,
    current_value: str,
    proposed_value: str,
    candidate_sources: str,
    status: str,
) -> Dict[str, str]:
    return {
        "backfill_key": stable_key(target_csv, match_key, "provider_player_id", current_value, proposed_value, candidate_sources),
        "target_csv": target_csv,
        "match_key": match_key,
        "athlete_id": athlete_id,
        "display_name": display_name,
        "team_id": team_id,
        "target_field": "provider_player_id",
        "current_value": current_value,
        "proposed_value": proposed_value,
        "candidate_sources": candidate_sources,
        "backfill_status": status,
        "allowed_decisions": "apply_manual_backfill|keep_blank|needs_more_research|reject_candidate",
        "operator_decision": "",
        "reviewer": "",
        "reviewed_at_utc": "",
        "operator_notes": "",
        "manual_edit_target": f"Open {target_csv} and edit provider_player_id only after manual identity verification.",
        "review_only_policy": REVIEW_ONLY_POLICY,
        "auto_apply": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "publish_ready": "false",
    }


def build_backfill_rows(
    athlete_rows: Sequence[Mapping[str, str]],
    image_rows: Sequence[Mapping[str, str]],
    approved_rows: Sequence[Mapping[str, str]],
    review_rows: Sequence[Mapping[str, str]],
) -> List[Dict[str, str]]:
    athletes = one_by_athlete(athlete_rows)
    images = by_athlete(image_rows)
    approved = by_athlete(approved_rows)
    reviews = by_athlete(review_rows)
    athlete_ids = sorted(set(athletes) | set(images) | set(approved) | set(reviews))
    rows: List[Dict[str, str]] = []

    for athlete_id in athlete_ids:
        athlete = athletes.get(athlete_id, {})
        image_group = images.get(athlete_id, [])
        approved_group = approved.get(athlete_id, [])
        review_group = reviews.get(athlete_id, [])
        candidate, sources, status = selected_provider_candidate(
            provider_candidates(athlete_id, athlete, image_group, approved_group, review_group)
        )
        display_name = (
            clean(athlete.get("display_name"))
            or clean((image_group or approved_group or review_group or [{}])[0].get("display_name"))
        )
        team_id = clean(athlete.get("team_id")) or clean((image_group or approved_group or review_group or [{}])[0].get("team_id"))

        athlete_current = clean(athlete.get("provider_player_id"))
        if athlete and (not athlete_current or status != "manual_review_required"):
            rows.append(backfill_row(
                target_csv=ATHLETES.as_posix(),
                match_key=f"athlete_id={athlete_id}",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                current_value=athlete_current,
                proposed_value=candidate if not athlete_current else "",
                candidate_sources=sources,
                status=status,
            ))

        for image in image_group:
            if clean(image.get("image_type")) != "headshot":
                continue
            image_current = clean(image.get("provider_player_id"))
            if not image_current or status != "manual_review_required":
                rows.append(backfill_row(
                    target_csv=ATHLETE_IMAGES.as_posix(),
                    match_key=f"athlete_id={athlete_id}; image_type=headshot",
                    athlete_id=athlete_id,
                    display_name=display_name or clean(image.get("display_name")),
                    team_id=team_id or clean(image.get("team_id")),
                    current_value=image_current,
                    proposed_value=candidate if not image_current else "",
                    candidate_sources=sources,
                    status=status,
                ))

    return sorted(rows, key=lambda row: (row["backfill_status"], row["team_id"], row["display_name"], row["target_csv"]))


def summarize(
    closure_rows: Sequence[Mapping[str, str]],
    backfill_rows: Sequence[Mapping[str, str]],
    out_closure: Path,
    out_backfill: Path,
    out_json: Path,
    out_md: Path,
) -> Dict[str, Any]:
    by_severity: Dict[str, int] = {}
    by_backfill_status: Dict[str, int] = {}
    for row in closure_rows:
        severity = clean(row.get("severity")) or "unknown"
        by_severity[severity] = by_severity.get(severity, 0) + 1
    for row in backfill_rows:
        status = clean(row.get("backfill_status")) or "unknown"
        by_backfill_status[status] = by_backfill_status.get(status, 0) + 1
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "review_only": True,
        "status": "manual_identity_closure_ready" if closure_rows or backfill_rows else "no_identity_closure_rows",
        "closure_rows": len(closure_rows),
        "backfill_rows": len(backfill_rows),
        "closure_severity_counts": dict(sorted(by_severity.items())),
        "backfill_status_counts": dict(sorted(by_backfill_status.items())),
        "closure_template_csv": out_closure.as_posix(),
        "provider_id_backfill_template_csv": out_backfill.as_posix(),
        "packet_json": out_json.as_posix(),
        "packet_md": out_md.as_posix(),
        "policy": {
            "paid_apis": False,
            "auto_apply": False,
            "auto_approval": False,
            "auto_publish": False,
            "move_files": False,
            "publish_ready": False,
            "canonical_registries_unchanged": True,
        },
    }


def write_markdown(path: Path, report: Mapping[str, Any], closure_rows: Sequence[Mapping[str, str]], backfill_rows: Sequence[Mapping[str, str]]) -> None:
    lines = [
        "# HSD WNBA Athlete Identity Closure Packet v1",
        "",
        f"Generated: {report.get('generated_at_utc')}",
        f"Status: **{report.get('status')}**",
        "",
        "## Policy",
        "",
        "- Review-only manual closure packet.",
        "- No provider ID was written to canonical registries by this packet.",
        "- No athlete image was approved, rejected, copied, moved, fetched, published, or marked publish-ready by this packet.",
        "- Operator decisions in these CSVs are evidence for a later manual registry edit only.",
        "",
        "## Files",
        "",
        f"- Issue closure template: `{report.get('closure_template_csv')}`",
        f"- Provider ID backfill template: `{report.get('provider_id_backfill_template_csv')}`",
        "",
        "## Counts",
        "",
        f"- issue closure rows: {report.get('closure_rows')}",
        f"- provider ID backfill rows: {report.get('backfill_rows')}",
    ]
    for status, count in (report.get("backfill_status_counts") or {}).items():
        lines.append(f"- {status}: {count}")
    lines += ["", "## Priority Issue Closure Sample", ""]
    if closure_rows:
        for row in closure_rows[:30]:
            lines.append(
                f"- {row.get('severity')} | {row.get('issue_code')} | "
                f"{row.get('display_name')} | {row.get('team_id')} | decision blank"
            )
    else:
        lines.append("- None")
    lines += ["", "## Provider ID Backfill Sample", ""]
    if backfill_rows:
        for row in backfill_rows[:30]:
            proposed = row.get("proposed_value") or "manual resolution required"
            lines.append(f"- {row.get('target_csv')} | {row.get('match_key')} | proposed `{proposed}` | {row.get('backfill_status')}")
    else:
        lines.append("- None")
    write_text(path, "\n".join(lines) + "\n")


def main() -> int:
    athlete_rows = read_csv(ATHLETES)
    image_rows = read_csv(ATHLETE_IMAGES)
    approved_rows = read_csv(APPROVED_ASSETS)
    review_rows = read_csv(MATCH_REVIEW)
    decision_rows = read_csv(APPROVAL_DECISIONS)
    issues = identity_audit.audit_approved_assets(athlete_rows, image_rows, approved_rows, review_rows, decision_rows)
    closure_rows = build_closure_rows(issues)
    backfill_rows = build_backfill_rows(athlete_rows, image_rows, approved_rows, review_rows)

    out_closure = output_path(OUT_CLOSURE_CSV)
    out_backfill = output_path(OUT_BACKFILL_CSV)
    out_json = output_path(OUT_JSON)
    out_md = output_path(OUT_MD)
    report = summarize(closure_rows, backfill_rows, out_closure, out_backfill, out_json, out_md)

    write_run_csv(OUT_CLOSURE_CSV, closure_rows, CLOSURE_FIELDS)
    write_run_csv(OUT_BACKFILL_CSV, backfill_rows, BACKFILL_FIELDS)
    write_json(OUT_JSON, {"report": report, "issue_closure_rows": closure_rows, "provider_id_backfill_rows": backfill_rows}, indent=2)
    write_markdown(out_md, report, closure_rows, backfill_rows)
    print(json.dumps({
        "version": report["version"],
        "status": report["status"],
        "closure_rows": report["closure_rows"],
        "backfill_rows": report["backfill_rows"],
        "closure_template_csv": report["closure_template_csv"],
        "provider_id_backfill_template_csv": report["provider_id_backfill_template_csv"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
