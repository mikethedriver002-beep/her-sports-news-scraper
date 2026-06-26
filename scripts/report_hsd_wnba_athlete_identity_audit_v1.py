from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, write_csv as write_run_csv, write_json

ROOT = Path("data/asset_registry/wnba")
ATHLETES = ROOT / "athletes.csv"
ATHLETE_IMAGES = ROOT / "athlete_images.csv"
APPROVED_ASSETS = ROOT / "athlete_image_approved_assets.csv"
MATCH_REVIEW = ROOT / "athlete_image_match_review.csv"
APPROVAL_DECISIONS = Path("outputs/latest/review_files/athlete_image_approval_pack/approval_decisions.csv")

OUT_CSV = "data/asset_registry/wnba/athlete_identity_audit.csv"
OUT_JSON = "data/asset_registry/wnba/athlete_identity_audit.json"
OUT_MD = "data/asset_registry/wnba/athlete_identity_audit.md"

VERSION = "hsd-wnba-athlete-identity-audit-v1-review-only"
REVIEW_ONLY_POLICY = "audit_only_no_auto_approval_no_file_movement_no_publish_ready_lane"
ISSUE_FIELDS = [
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
    "review_only_policy",
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


def by_key(rows: Iterable[Mapping[str, str]], *fields: str) -> Dict[Tuple[str, ...], Mapping[str, str]]:
    out: Dict[Tuple[str, ...], Mapping[str, str]] = {}
    for row in rows:
        key = tuple(clean(row.get(field)) for field in fields)
        if all(key):
            out[key] = row
    return out


def rows_by_key(rows: Iterable[Mapping[str, str]], *fields: str) -> Dict[Tuple[str, ...], List[Mapping[str, str]]]:
    out: Dict[Tuple[str, ...], List[Mapping[str, str]]] = {}
    for row in rows:
        key = tuple(clean(row.get(field)) for field in fields)
        if all(key):
            out.setdefault(key, []).append(row)
    return out


def boolish(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y", "approved"}


def issue(
    severity: str,
    issue_code: str,
    *,
    athlete_id: str = "",
    display_name: str = "",
    team_id: str = "",
    provider_player_id: str = "",
    asset_path: str = "",
    approved_marker_path: str = "",
    evidence: str = "",
    recommendation: str = "",
) -> Dict[str, str]:
    return {
        "severity": severity,
        "issue_code": issue_code,
        "athlete_id": athlete_id,
        "display_name": display_name,
        "team_id": team_id,
        "provider_player_id": provider_player_id,
        "asset_path": asset_path,
        "approved_marker_path": approved_marker_path,
        "evidence": evidence,
        "recommendation": recommendation,
        "review_only_policy": REVIEW_ONLY_POLICY,
    }


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def approval_decision_for(
    approved: Mapping[str, str],
    decisions_by_athlete: Mapping[Tuple[str, ...], List[Mapping[str, str]]],
) -> Mapping[str, str]:
    rows = decisions_by_athlete.get((clean(approved.get("athlete_id")),), [])
    if not rows:
        return {}
    approved_file = clean(approved.get("approved_file"))
    for row in rows:
        if clean(row.get("approval_target_path")) == approved_file:
            return row
    return rows[0]


def marker_issues(approved: Mapping[str, str], marker_payload: Mapping[str, Any]) -> List[Dict[str, str]]:
    athlete_id = clean(approved.get("athlete_id"))
    display_name = clean(approved.get("display_name"))
    team_id = clean(approved.get("team_id"))
    provider_player_id = clean(approved.get("provider_player_id"))
    asset_path = clean(approved.get("approved_file"))
    marker_path = clean(approved.get("approved_marker"))
    problems: List[Dict[str, str]] = []
    comparisons = [
        ("athlete_id", athlete_id),
        ("display_name", display_name),
        ("team_id", team_id),
        ("provider_player_id", provider_player_id),
    ]
    for field, expected in comparisons:
        observed = clean(marker_payload.get(field))
        if expected and observed and observed != expected:
            problems.append(issue(
                "critical",
                "approved_marker_identity_mismatch",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id,
                asset_path=asset_path,
                approved_marker_path=marker_path,
                evidence=f"{field}: registry={expected}; marker={observed}",
                recommendation="Hold this approved marker for manual identity review before renderer use.",
            ))
    return problems


def audit_approved_assets(
    athlete_rows: List[Mapping[str, str]],
    image_rows: List[Mapping[str, str]],
    approved_rows: List[Mapping[str, str]],
    review_rows: List[Mapping[str, str]],
    decision_rows: List[Mapping[str, str]],
) -> List[Dict[str, str]]:
    athletes = by_key(athlete_rows, "athlete_id")
    images_by_athlete_kind = by_key(image_rows, "athlete_id", "image_type")
    review_by_athlete = by_key(review_rows, "athlete_id")
    decisions_by_athlete = rows_by_key(decision_rows, "athlete_id")
    issues: List[Dict[str, str]] = []

    for approved in sorted(approved_rows, key=lambda row: clean(row.get("athlete_id"))):
        athlete_id = clean(approved.get("athlete_id"))
        athlete = athletes.get((athlete_id,), {})
        display_name = clean(approved.get("display_name")) or clean(athlete.get("display_name"))
        team_id = clean(approved.get("team_id")) or clean(athlete.get("team_id"))
        provider_player_id = clean(approved.get("provider_player_id")) or clean(athlete.get("provider_player_id"))
        asset_path = clean(approved.get("approved_file"))
        marker_path = clean(approved.get("approved_marker")) or f"{asset_path}.approved"
        asset = Path(asset_path)
        marker = Path(marker_path)
        image = images_by_athlete_kind.get((athlete_id, "headshot"), {})
        review = review_by_athlete.get((athlete_id,), {})
        decision = approval_decision_for(approved, decisions_by_athlete)
        decision_source = clean(approved.get("decision_source"))

        if not asset.exists():
            issues.append(issue(
                "critical",
                "approved_asset_file_missing",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id,
                asset_path=asset_path,
                approved_marker_path=marker_path,
                evidence="approved registry row points to a missing file",
                recommendation="Remove renderer eligibility until the reviewed file is restored and rechecked.",
            ))
        if not marker.exists():
            issues.append(issue(
                "critical",
                "approved_marker_missing",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id,
                asset_path=asset_path,
                approved_marker_path=marker_path,
                evidence="approved registry row points to a missing sibling marker",
                recommendation="Keep this asset out of approved render slots until a human-reviewed marker exists.",
            ))
        else:
            marker_payload = read_json(marker)
            if not marker_payload:
                issues.append(issue(
                    "high",
                    "approved_marker_json_unreadable",
                    athlete_id=athlete_id,
                    display_name=display_name,
                    team_id=team_id,
                    provider_player_id=provider_player_id,
                    asset_path=asset_path,
                    approved_marker_path=marker_path,
                    evidence="marker exists but could not be parsed as JSON",
                    recommendation="Recheck the marker contents and identity evidence manually.",
                ))
            else:
                issues.extend(marker_issues(approved, marker_payload))
                marker_source = clean(marker_payload.get("decision_source"))
                if marker_source == "default":
                    issues.append(issue(
                        "high",
                        "default_approval_requires_identity_recheck",
                        athlete_id=athlete_id,
                        display_name=display_name,
                        team_id=team_id,
                        provider_player_id=provider_player_id,
                        asset_path=asset_path,
                        approved_marker_path=marker_path,
                        evidence="approved marker decision_source=default",
                        recommendation="Replace wildcard/default provenance with an explicit per-athlete human decision before trusting identity.",
                    ))

        if decision_source == "default":
            issues.append(issue(
                "high",
                "default_approval_requires_identity_recheck",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id,
                asset_path=asset_path,
                approved_marker_path=marker_path,
                evidence="approved assets registry decision_source=default",
                recommendation="Replace wildcard/default provenance with an explicit per-athlete human decision before trusting identity.",
            ))

        if review and clean(review.get("status")) == "needs_human_approval":
            issues.append(issue(
                "high",
                "approved_asset_still_has_pending_match_review",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id or clean(review.get("provider_player_id")),
                asset_path=asset_path,
                approved_marker_path=marker_path,
                evidence=f"match_review status=needs_human_approval; confidence={clean(review.get('confidence')) or 'unknown'}",
                recommendation="Keep a per-athlete review note or decision row that closes the pending match-review state.",
            ))

        if decision and not clean(decision.get("decision")):
            issues.append(issue(
                "medium",
                "blank_per_row_approval_decision",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id or clean(decision.get("provider_player_id")),
                asset_path=asset_path,
                approved_marker_path=marker_path,
                evidence="approval_decisions.csv row has a blank decision and was approved by fallback/default logic",
                recommendation="Record explicit approve/hold/reject decisions per athlete for identity-sensitive headshots.",
            ))

        if image:
            image_provider = clean(image.get("provider_player_id"))
            if not image_provider and provider_player_id:
                issues.append(issue(
                    "medium",
                    "missing_provider_player_id_in_image_registry",
                    athlete_id=athlete_id,
                    display_name=display_name,
                    team_id=team_id,
                    provider_player_id=provider_player_id,
                    asset_path=asset_path,
                    approved_marker_path=marker_path,
                    evidence=f"athlete_images.csv provider_player_id is blank; approved registry has {provider_player_id}",
                    recommendation="Backfill the canonical image registry with the exact provider ID used to fetch the headshot.",
                ))
            if clean(image.get("file_path")) != asset_path:
                issues.append(issue(
                    "high",
                    "approved_file_differs_from_image_registry",
                    athlete_id=athlete_id,
                    display_name=display_name,
                    team_id=team_id,
                    provider_player_id=provider_player_id,
                    asset_path=asset_path,
                    approved_marker_path=marker_path,
                    evidence=f"athlete_images file_path={clean(image.get('file_path'))}",
                    recommendation="Reconcile the canonical image row and approved assets row before renderer use.",
                ))
            if not boolish(image.get("approved")):
                issues.append(issue(
                    "high",
                    "approved_asset_registry_disagrees_with_image_registry",
                    athlete_id=athlete_id,
                    display_name=display_name,
                    team_id=team_id,
                    provider_player_id=provider_player_id,
                    asset_path=asset_path,
                    approved_marker_path=marker_path,
                    evidence=f"athlete_images approved={clean(image.get('approved')) or 'blank'}",
                    recommendation="Reconcile approval status across WNBA athlete registries.",
                ))
        else:
            issues.append(issue(
                "high",
                "approved_asset_missing_from_image_registry",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id,
                asset_path=asset_path,
                approved_marker_path=marker_path,
                evidence="no athlete_images.csv headshot row for this approved asset",
                recommendation="Add or repair the canonical headshot row before renderer use.",
            ))

    issues.extend(duplicate_provider_issues(approved_rows))
    issues.extend(duplicate_image_hash_issues(approved_rows))
    issues.extend(duplicate_display_name_issues(athlete_rows))
    return sorted(issues, key=lambda row: (
        {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(row["severity"], 9),
        row["issue_code"],
        row["team_id"],
        row["display_name"],
    ))


def duplicate_provider_issues(approved_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    by_provider = rows_by_key(
        [row for row in approved_rows if clean(row.get("provider_player_id"))],
        "provider_player_id",
    )
    issues: List[Dict[str, str]] = []
    for (provider_player_id,), rows in by_provider.items():
        athlete_ids = sorted({clean(row.get("athlete_id")) for row in rows})
        if len(athlete_ids) <= 1:
            continue
        for row in rows:
            issues.append(issue(
                "critical",
                "provider_player_id_reused_across_athletes",
                athlete_id=clean(row.get("athlete_id")),
                display_name=clean(row.get("display_name")),
                team_id=clean(row.get("team_id")),
                provider_player_id=provider_player_id,
                asset_path=clean(row.get("approved_file")),
                approved_marker_path=clean(row.get("approved_marker")),
                evidence="same provider_player_id appears for: " + ", ".join(athlete_ids),
                recommendation="Hold all rows sharing the provider ID until identity mapping is corrected.",
            ))
    return issues


def duplicate_image_hash_issues(approved_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    hash_rows: Dict[str, List[Mapping[str, str]]] = {}
    for row in approved_rows:
        path = Path(clean(row.get("approved_file")))
        if path.exists() and path.is_file():
            hash_rows.setdefault(sha256_file(path), []).append(row)
    issues: List[Dict[str, str]] = []
    for digest, rows in hash_rows.items():
        athlete_ids = sorted({clean(row.get("athlete_id")) for row in rows})
        if len(athlete_ids) <= 1:
            continue
        for row in rows:
            issues.append(issue(
                "critical",
                "exact_duplicate_approved_headshot_hash",
                athlete_id=clean(row.get("athlete_id")),
                display_name=clean(row.get("display_name")),
                team_id=clean(row.get("team_id")),
                provider_player_id=clean(row.get("provider_player_id")),
                asset_path=clean(row.get("approved_file")),
                approved_marker_path=clean(row.get("approved_marker")),
                evidence=f"sha256={digest}; duplicate athletes={', '.join(athlete_ids)}",
                recommendation="Hold duplicate image rows for visual identity review.",
            ))
    return issues


def duplicate_display_name_issues(athlete_rows: List[Mapping[str, str]]) -> List[Dict[str, str]]:
    by_name = rows_by_key(athlete_rows, "display_name")
    issues: List[Dict[str, str]] = []
    for (display_name,), rows in by_name.items():
        athlete_ids = sorted({clean(row.get("athlete_id")) for row in rows})
        team_ids = sorted({clean(row.get("team_id")) for row in rows})
        if len(athlete_ids) <= 1:
            continue
        for row in rows:
            issues.append(issue(
                "medium",
                "duplicate_display_name_across_athlete_registry",
                athlete_id=clean(row.get("athlete_id")),
                display_name=display_name,
                team_id=clean(row.get("team_id")),
                provider_player_id=clean(row.get("provider_player_id")),
                evidence=f"display_name appears for athlete_ids={', '.join(athlete_ids)}; teams={', '.join(team_ids)}",
                recommendation="Confirm whether this is a transfer/stale roster duplicate before using name-only matching.",
            ))
    return issues


def summarize(issues: List[Mapping[str, str]], out_csv: Path, out_json: Path, out_md: Path) -> Dict[str, Any]:
    by_severity: Dict[str, int] = {}
    by_code: Dict[str, int] = {}
    for item in issues:
        by_severity[item["severity"]] = by_severity.get(item["severity"], 0) + 1
        by_code[item["issue_code"]] = by_code.get(item["issue_code"], 0) + 1
    status = "pass"
    if by_severity.get("critical"):
        status = "critical_identity_review"
    elif by_severity.get("high"):
        status = "needs_identity_review"
    elif issues:
        status = "review_recommended"
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "review_only": True,
        "status": status,
        "issue_rows": len(issues),
        "severity_counts": dict(sorted(by_severity.items())),
        "issue_code_counts": dict(sorted(by_code.items())),
        "audit_csv": out_csv.as_posix(),
        "audit_json": out_json.as_posix(),
        "audit_md": out_md.as_posix(),
        "policy": "This audit reports WNBA athlete identity provenance risks only. It does not approve, reject, move, fetch, publish, or create a publish-ready lane for athlete photos.",
    }


def write_markdown(path: Path, report: Mapping[str, Any], issues: List[Mapping[str, str]]) -> None:
    lines = [
        "# HSD WNBA Athlete Identity Audit v1",
        "",
        f"Generated: {report.get('generated_at_utc')}",
        f"Status: **{report.get('status')}**",
        "",
        "## Policy",
        "",
        "- Review-only identity provenance audit.",
        "- No athlete photo was approved, rejected, copied, moved, fetched, published, or marked publish-ready by this report.",
        "- A high or critical issue means the asset should receive explicit human identity QA before renderer trust is increased.",
        "",
        "## Counts",
        "",
        f"- issue rows: {report.get('issue_rows')}",
    ]
    for severity, count in (report.get("severity_counts") or {}).items():
        lines.append(f"- {severity}: {count}")
    lines += ["", "## Issue Codes", ""]
    for code, count in (report.get("issue_code_counts") or {}).items():
        lines.append(f"- {code}: {count}")
    lines += ["", "## Priority Review Sample", ""]
    if issues:
        for row in issues[:50]:
            lines.append(
                f"- {row.get('severity')} | {row.get('issue_code')} | "
                f"{row.get('display_name')} | {row.get('team_id')} | `{row.get('asset_path')}` | {row.get('evidence')}"
            )
        if len(issues) > 50:
            lines.append(f"- ...and {len(issues) - 50} more issue rows in the CSV.")
    else:
        lines.append("- None")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    out_csv = output_path(OUT_CSV)
    out_json = output_path(OUT_JSON)
    out_md = output_path(OUT_MD)
    issues = audit_approved_assets(
        read_csv(ATHLETES),
        read_csv(ATHLETE_IMAGES),
        read_csv(APPROVED_ASSETS),
        read_csv(MATCH_REVIEW),
        read_csv(APPROVAL_DECISIONS),
    )
    report = summarize(issues, out_csv, out_json, out_md)
    write_run_csv(OUT_CSV, issues, ISSUE_FIELDS)
    write_json(OUT_JSON, {"report": report, "issues": issues}, indent=2)
    write_markdown(out_md, report, issues)
    print(json.dumps({
        "version": report["version"],
        "status": report["status"],
        "issue_rows": report["issue_rows"],
        "severity_counts": report["severity_counts"],
        "audit_csv": report["audit_csv"],
        "audit_md": report["audit_md"],
    }, indent=2))


if __name__ == "__main__":
    main()
