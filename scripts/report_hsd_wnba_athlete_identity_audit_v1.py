from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple
from urllib.parse import urlparse

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
    "source_url",
    "source_provenance",
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
    source_url: str = "",
    source_provenance: str = "",
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
        "source_url": source_url,
        "source_provenance": source_provenance,
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


def official_free_source_url(value: Any) -> bool:
    url = clean(value)
    if not url:
        return False
    host = urlparse(url).netloc.lower()
    return host == "wnba.com" or host.endswith(".wnba.com")


def source_provenance(athlete: Mapping[str, str], review: Mapping[str, str]) -> str:
    parts: List[str] = []
    athlete_source = clean(athlete.get("source_url"))
    if athlete_source:
        source_label = "official_wnba_roster_source" if official_free_source_url(athlete_source) else "non_official_or_unverified_athlete_source"
        parts.append(f"{source_label}:{athlete_source}")
    method = clean(review.get("match_method"))
    confidence = clean(review.get("confidence"))
    status = clean(review.get("status"))
    if method or confidence or status:
        parts.append(f"match_review method={method or 'blank'} confidence={confidence or 'blank'} status={status or 'blank'}")
    return " | ".join(parts)


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
        athlete_source_url = clean(athlete.get("source_url"))
        provenance = source_provenance(athlete, review)
        marker_payload: Mapping[str, Any] = {}

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
                source_url=athlete_source_url,
                source_provenance=provenance,
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
                source_url=athlete_source_url,
                source_provenance=provenance,
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
                    source_url=athlete_source_url,
                    source_provenance=provenance,
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
                        source_url=athlete_source_url,
                        source_provenance=provenance,
                        evidence="approved marker decision_source=default",
                        recommendation="Replace wildcard/default provenance with an explicit per-athlete human decision before trusting identity.",
                    ))

        if not athlete_source_url or not official_free_source_url(athlete_source_url):
            issues.append(issue(
                "medium",
                "approved_asset_lacks_official_roster_source",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id,
                asset_path=asset_path,
                approved_marker_path=marker_path,
                source_url=athlete_source_url,
                source_provenance=provenance,
                evidence=f"athletes.csv source_url={athlete_source_url or 'blank'}",
                recommendation="Add a free official WNBA/team roster source before raising trust in this athlete photo.",
            ))

        parsed_provider_sources = {
            "approved_assets.source_file": parse_provider_id_from_text(approved.get("source_file")),
            "approved_marker.source_file": parse_provider_id_from_text(marker_payload.get("source_file")) if marker_payload else "",
            "match_review.image_url": parse_provider_id_from_text(review.get("image_url")),
        }
        for source_name, parsed_provider_id in parsed_provider_sources.items():
            if provider_player_id and parsed_provider_id and parsed_provider_id != provider_player_id:
                issues.append(issue(
                    "critical",
                    "provider_player_id_disagrees_with_source_artifact",
                    athlete_id=athlete_id,
                    display_name=display_name,
                    team_id=team_id,
                    provider_player_id=provider_player_id,
                    asset_path=asset_path,
                    approved_marker_path=marker_path,
                    source_url=athlete_source_url,
                    source_provenance=provenance,
                    evidence=f"{source_name} implies provider_player_id={parsed_provider_id}; approved registry has {provider_player_id}",
                    recommendation="Hold this asset until provider ID evidence is reconciled against a trusted player/source page.",
                ))

        canonical_provider_sources = {
            clean(athlete.get("provider_player_id")): "athletes.csv",
            clean(image.get("provider_player_id")): "athlete_images.csv",
            clean(review.get("provider_player_id")): "athlete_image_match_review.csv",
        }
        canonical_provider_sources.pop("", None)
        if provider_player_id and provider_player_id not in canonical_provider_sources:
            issues.append(issue(
                "high",
                "approved_provider_id_not_backed_by_canonical_registry",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id,
                asset_path=asset_path,
                approved_marker_path=marker_path,
                source_url=athlete_source_url,
                source_provenance=provenance,
                evidence="approved provider_player_id is absent from athletes.csv, athlete_images.csv, and match_review.csv",
                recommendation="Backfill only after a manual source-backed identity check confirms the athlete and provider ID.",
            ))

        review_method = clean(review.get("match_method"))
        try:
            confidence = float(clean(review.get("confidence")) or "0")
        except ValueError:
            confidence = 0.0
        if "order" in review_method.lower() and confidence < 0.9:
            issues.append(issue(
                "high",
                "order_matched_headshot_requires_source_backed_identity_review",
                athlete_id=athlete_id,
                display_name=display_name,
                team_id=team_id,
                provider_player_id=provider_player_id or clean(review.get("provider_player_id")),
                asset_path=asset_path,
                approved_marker_path=marker_path,
                source_url=athlete_source_url,
                source_provenance=provenance,
                evidence=f"match_method={review_method}; confidence={clean(review.get('confidence')) or 'blank'}; image_url={clean(review.get('image_url')) or 'blank'}",
                recommendation="Verify the exact player page/headshot source by eye; roster-order matching alone is not strong enough for trusted athlete photos.",
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
                source_url=athlete_source_url,
                source_provenance=provenance,
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
                source_url=athlete_source_url,
                source_provenance=provenance,
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
                source_url=athlete_source_url,
                source_provenance=provenance,
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
                    source_url=athlete_source_url,
                    source_provenance=provenance,
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
                    source_url=athlete_source_url,
                    source_provenance=provenance,
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
                    source_url=athlete_source_url,
                    source_provenance=provenance,
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
                source_url=athlete_source_url,
                source_provenance=provenance,
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


def coverage_summary(
    athlete_rows: List[Mapping[str, str]],
    image_rows: List[Mapping[str, str]],
    approved_rows: List[Mapping[str, str]],
    review_rows: List[Mapping[str, str]],
) -> Dict[str, int]:
    athletes = by_key(athlete_rows, "athlete_id")
    images_by_athlete_kind = by_key(image_rows, "athlete_id", "image_type")
    review_by_athlete = by_key(review_rows, "athlete_id")
    approved_athlete_ids = {clean(row.get("athlete_id")) for row in approved_rows if clean(row.get("athlete_id"))}
    headshot_rows = [row for row in image_rows if clean(row.get("image_type")) == "headshot"]

    summary = {
        "athlete_rows": len(athlete_rows),
        "headshot_registry_rows": len(headshot_rows),
        "approved_asset_rows": len(approved_rows),
        "approved_unique_athletes": len(approved_athlete_ids),
        "approved_with_official_roster_source_url": 0,
        "approved_missing_athlete_provider_player_id": 0,
        "approved_missing_image_provider_player_id": 0,
        "approved_with_match_review_provider_player_id": 0,
        "approved_with_order_match_review": 0,
        "approved_with_pending_match_review": 0,
        "approved_with_default_decision_source": 0,
    }

    for approved in approved_rows:
        athlete_id = clean(approved.get("athlete_id"))
        athlete = athletes.get((athlete_id,), {})
        image = images_by_athlete_kind.get((athlete_id, "headshot"), {})
        review = review_by_athlete.get((athlete_id,), {})
        if official_free_source_url(athlete.get("source_url")):
            summary["approved_with_official_roster_source_url"] += 1
        if not clean(athlete.get("provider_player_id")):
            summary["approved_missing_athlete_provider_player_id"] += 1
        if not clean(image.get("provider_player_id")):
            summary["approved_missing_image_provider_player_id"] += 1
        if clean(review.get("provider_player_id")):
            summary["approved_with_match_review_provider_player_id"] += 1
        if "order" in clean(review.get("match_method")).lower():
            summary["approved_with_order_match_review"] += 1
        if clean(review.get("status")) == "needs_human_approval":
            summary["approved_with_pending_match_review"] += 1
        if clean(approved.get("decision_source")) == "default":
            summary["approved_with_default_decision_source"] += 1
    return summary


def summarize(
    issues: List[Mapping[str, str]],
    out_csv: Path,
    out_json: Path,
    out_md: Path,
    coverage: Mapping[str, int] | None = None,
) -> Dict[str, Any]:
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
        "coverage_summary": dict(sorted((coverage or {}).items())),
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
    lines += ["", "## Coverage Summary", ""]
    coverage = report.get("coverage_summary") or {}
    if coverage:
        for key, count in coverage.items():
            lines.append(f"- {key}: {count}")
    else:
        lines.append("- Not available")
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
    athlete_rows = read_csv(ATHLETES)
    image_rows = read_csv(ATHLETE_IMAGES)
    approved_rows = read_csv(APPROVED_ASSETS)
    review_rows = read_csv(MATCH_REVIEW)
    decision_rows = read_csv(APPROVAL_DECISIONS)
    issues = audit_approved_assets(
        athlete_rows,
        image_rows,
        approved_rows,
        review_rows,
        decision_rows,
    )
    report = summarize(issues, out_csv, out_json, out_md, coverage_summary(athlete_rows, image_rows, approved_rows, review_rows))
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
