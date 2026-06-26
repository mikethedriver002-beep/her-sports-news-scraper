from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Tuple

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import input_path, write_csv as write_run_csv, write_json, write_text

ROOT = Path("data/asset_registry/wnba")
MISSING_TEAM_LOGOS = "data/asset_registry/wnba/missing_team_logos.csv"
REPORT_MD = "data/asset_registry/wnba/asset_registry_validation_report.md"
REPORT_JSON = "data/asset_registry/wnba/asset_registry_validation.json"
VERSION = "hsd-wnba-asset-registry-validator-v1.3-review-only-logo-decision-packets"
LOGO_EXTENSIONS = {".png", ".svg", ".webp", ".jpg", ".jpeg"}
MISSING_LOGO_FIELDS = [
    "team_id",
    "team_name",
    "required_asset",
    "reason",
    "recommended_path",
    "decision_packet_id",
    "decision_packet_title",
    "decision_review_status",
    "allowed_decisions",
    "decision_primary_action",
    "decision_hold_cue",
    "decision_revise_cue",
    "renderer_fallback_cue",
    "decision_source_artifact",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: Path) -> List[Dict[str, str]]:
    resolved = input_path(path)
    if not resolved.exists():
        return []
    with resolved.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def clean(value: Any) -> str:
    return str(value or "").strip()


def boolish(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y"}


def canonical_logo_paths(team_id: str) -> set[str]:
    return {
        f"assets/leagues/wnba/teams/{team_id}/logo.png",
        f"assets/leagues/wnba/teams/{team_id}/logo.svg",
    }


def decision_slug(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() else "_" for ch in clean(value).lower())
    return "_".join(part for part in cleaned.split("_") if part) or "wnba_team_logo"


def missing_logo_decision_packet(team_id: str, team_name: str, recommended_path: str) -> Dict[str, str]:
    slug = decision_slug(team_id or team_name)
    target = clean(recommended_path) or f"assets/leagues/wnba/teams/{slug}/logo.png"
    return {
        "decision_packet_id": f"asset_logo_blocker_{slug}",
        "decision_packet_title": f"WNBA team logo blocker: {team_name or team_id}",
        "decision_review_status": "operator_asset_decision_required",
        "allowed_decisions": "supply_exact_logo_for_review|hold_logo_slot|revise_registry_metadata",
        "decision_primary_action": f"Supply the exact local team logo file at {target}, then manually review source evidence before renderer trust.",
        "decision_hold_cue": "Hold the card if an exact local logo is missing, unverified, or not source-backed.",
        "decision_revise_cue": "Revise team_logos.csv/logo_sources.csv only after human evidence review; do not invent or substitute a logo.",
        "renderer_fallback_cue": "Renderer text/logo fallback remains review-only and blocked for exact-logo WNBA templates until this asset is reviewed.",
        "decision_source_artifact": "data/asset_registry/wnba/missing_team_logos.csv",
        "publish_ready": "false",
        "auto_approval": "false",
        "auto_publish": "false",
        "move_files": "false",
        "paid_apis": "false",
    }


def duplicate_values(rows: Iterable[Mapping[str, str]], field: str) -> List[str]:
    values = [clean(row.get(field)) for row in rows if clean(row.get(field))]
    return sorted(value for value, count in Counter(values).items() if count > 1)


def first_by_field(rows: Iterable[Mapping[str, str]], field: str) -> Dict[str, Mapping[str, str]]:
    found: Dict[str, Mapping[str, str]] = {}
    for row in rows:
        key = clean(row.get(field))
        if key and key not in found:
            found[key] = row
    return found


def path_exists(path_text: str) -> bool:
    return bool(path_text) and input_path(path_text).exists()


def hash_file(path_text: str) -> str:
    path = input_path(path_text)
    if not path.exists() or not path.is_file():
        return ""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def build_validation(root: Path = ROOT) -> Tuple[Dict[str, Any], List[Dict[str, str]]]:
    teams = read_csv(root / "teams.csv")
    aliases = read_csv(root / "team_aliases.csv")
    logos = read_csv(root / "team_logos.csv")
    sources = read_csv(root / "logo_sources.csv")
    issues: List[str] = []
    warnings: List[str] = []
    operator_warnings: List[str] = []
    source_path_warnings: List[str] = []

    team_ids = {clean(row.get("team_id")) for row in teams if clean(row.get("team_id"))}
    logo_ids = {clean(row.get("team_id")) for row in logos if clean(row.get("team_id"))}
    alias_ids = {clean(row.get("team_id")) for row in aliases if clean(row.get("team_id"))}
    source_ids = {clean(row.get("team_id")) for row in sources if clean(row.get("team_id"))}
    teams_by_id = first_by_field(teams, "team_id")
    logos_by_id = first_by_field(logos, "team_id")
    sources_by_id = first_by_field(sources, "team_id")

    if not teams:
        issues.append("teams.csv is empty or missing")
    for label, rows in [("teams.csv", teams), ("team_logos.csv", logos), ("logo_sources.csv", sources)]:
        duplicates = duplicate_values(rows, "team_id")
        if duplicates:
            issues.append(f"{label} has duplicate team_id rows: " + ", ".join(duplicates))
    if team_ids - logo_ids:
        issues.append("missing logo rows for: " + ", ".join(sorted(team_ids - logo_ids)))
    if logo_ids - team_ids:
        issues.append("logo rows reference unknown teams: " + ", ".join(sorted(logo_ids - team_ids)))
    if alias_ids - team_ids:
        issues.append("aliases reference unknown teams: " + ", ".join(sorted(alias_ids - team_ids)))
    if source_ids - team_ids:
        issues.append("logo sources reference unknown teams: " + ", ".join(sorted(source_ids - team_ids)))

    duplicate_paths = duplicate_values(logos, "file_path")
    if duplicate_paths:
        issues.append("duplicate registered logo file paths: " + ", ".join(duplicate_paths))

    missing_required: List[str] = []
    unapproved_required: List[str] = []
    hashes: Dict[str, List[str]] = defaultdict(list)
    for row in logos:
        team_id = clean(row.get("team_id"))
        file_path = clean(row.get("file_path"))
        required = boolish(row.get("required"))
        approved = boolish(row.get("approved"))
        declared_exists = boolish(row.get("file_exists"))
        actual_exists = path_exists(file_path)

        if not team_id:
            issues.append("team_logos.csv contains a row without team_id")
            continue
        if clean(row.get("asset_type")) != "primary_logo":
            warnings.append(f"{team_id}: logo row asset_type is not primary_logo")
        if not file_path:
            issues.append(f"{team_id}: required logo row is missing file_path")
        elif Path(file_path).suffix.lower() not in LOGO_EXTENSIONS:
            issues.append(f"{team_id}: registered logo path has unsupported extension: {file_path}")
        elif file_path not in canonical_logo_paths(team_id):
            source_path_warnings.append(f"{team_id}: registered logo path is outside canonical WNBA team logo paths: {file_path}")

        if declared_exists and not actual_exists:
            issues.append(f"{team_id}: file_exists=true but registered logo path does not exist: {file_path}")
        if not declared_exists and actual_exists:
            source_path_warnings.append(f"{team_id}: file_exists=false but registered logo path exists: {file_path}")
        if approved and not actual_exists:
            issues.append(f"{team_id}: approved logo path does not exist: {file_path}")
        if required and not actual_exists:
            missing_required.append(team_id)
        if required and actual_exists and not approved:
            unapproved_required.append(team_id)
            operator_warnings.append(f"{team_id}: local required logo exists but is not approved; human review required before enabling")

        digest = hash_file(file_path)
        if digest:
            hashes[digest].append(team_id)

    for digest, ids in sorted(hashes.items()):
        unique_ids = sorted(set(ids))
        if len(unique_ids) > 1:
            warnings.append("duplicate logo file bytes across teams: " + ", ".join(unique_ids) + f" sha256={digest[:12]}")

    for team_id in sorted(team_ids):
        team = teams_by_id.get(team_id, {})
        logo = logos_by_id.get(team_id, {})
        source = sources_by_id.get(team_id, {})
        source_url = clean(source.get("source_url"))
        target_path = clean(source.get("target_path"))
        source_note = clean(source.get("source_note"))
        registered_path = clean(logo.get("file_path"))

        if not source:
            source_path_warnings.append(f"{team_id}: missing logo_sources.csv row")
            operator_warnings.append(f"{team_id}: source metadata missing; manual source evidence review required")
            continue
        if clean(source.get("team_name")) and clean(source.get("team_name")) != clean(team.get("team_name")):
            source_path_warnings.append(f"{team_id}: source team_name differs from teams.csv")
        if not source_url:
            source_path_warnings.append(f"{team_id}: source_url missing")
            operator_warnings.append(f"{team_id}: source_url missing; manual source evidence review required")
        if not target_path:
            source_path_warnings.append(f"{team_id}: source target_path missing")
        elif Path(target_path).suffix.lower() not in LOGO_EXTENSIONS:
            source_path_warnings.append(f"{team_id}: source target_path has unsupported extension: {target_path}")
        elif target_path not in canonical_logo_paths(team_id):
            source_path_warnings.append(f"{team_id}: source target_path is outside canonical WNBA team logo paths: {target_path}")
        if target_path and registered_path and target_path != registered_path:
            source_path_warnings.append(f"{team_id}: source target_path differs from registered local logo path: source={target_path} registry={registered_path}")
        if not source_note:
            source_path_warnings.append(f"{team_id}: source_note missing")
        if boolish(logo.get("approved")) and (not source_url or not source_note):
            operator_warnings.append(f"{team_id}: approved logo lacks complete source metadata; manual source recheck required")

    missing_rows = [
        {
            "team_id": tid,
            "team_name": clean(teams_by_id.get(tid, {}).get("team_name")) or tid,
            "required_asset": "primary_logo",
            "reason": "required exact team logo file not found",
            "recommended_path": f"assets/leagues/wnba/teams/{tid}/logo.png",
            **missing_logo_decision_packet(
                tid,
                clean(teams_by_id.get(tid, {}).get("team_name")) or tid,
                f"assets/leagues/wnba/teams/{tid}/logo.png",
            ),
        }
        for tid in sorted(set(missing_required))
    ]

    status = "pass" if not issues else "fail"
    if missing_required:
        status = "needs_assets"
    elif operator_warnings:
        status = "operator_review"
    result = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "status": status,
        "review_only": True,
        "teams": len(teams),
        "aliases": len(aliases),
        "logo_rows": len(logos),
        "source_rows": len(sources),
        "missing_required_team_logos": len(set(missing_required)),
        "unapproved_required_team_logos": len(set(unapproved_required)),
        "missing_logo_decision_packets": len(missing_rows),
        "decision_packet_fields": MISSING_LOGO_FIELDS,
        "duplicate_logo_paths": duplicate_paths,
        "source_path_metadata_warnings": source_path_warnings,
        "operator_warnings": operator_warnings,
        "issues": issues,
        "warnings": warnings,
        "policy": {
            "review_only_validation": True,
            "no_auto_approval": True,
            "no_asset_downloads": True,
            "operator_must_review_unapproved_or_incomplete_source_metadata": True,
        },
    }
    return result, missing_rows


def write_reports(result: Mapping[str, Any], missing_rows: List[Dict[str, str]]) -> None:
    write_run_csv(MISSING_TEAM_LOGOS, missing_rows, MISSING_LOGO_FIELDS)
    write_json(REPORT_JSON, result)
    lines = [
        "# HSD WNBA Asset Registry Validation",
        "",
        f"Generated: {result['generated_at_utc']}",
        f"Status: **{result['status']}**",
        "",
        "Review-only validation. This report does not approve logos, download assets, enable fallbacks, or change renderer behavior.",
        "",
        "## Counts",
        "",
        f"- teams: {result['teams']}",
        f"- aliases: {result['aliases']}",
        f"- logo rows: {result['logo_rows']}",
        f"- source rows: {result['source_rows']}",
        f"- missing required team logos: {result['missing_required_team_logos']}",
        f"- unapproved required team logos: {result['unapproved_required_team_logos']}",
        f"- missing logo decision packets: {result['missing_logo_decision_packets']}",
        "",
        "## Issues",
        "",
    ]
    issues = list(result.get("issues") or [])
    lines += [f"- {item}" for item in issues] if issues else ["- None"]
    lines += ["", "## Operator warnings", ""]
    operator_warnings = list(result.get("operator_warnings") or [])
    lines += [f"- {item}" for item in operator_warnings] if operator_warnings else ["- None"]
    lines += ["", "## Source/path metadata warnings", ""]
    source_path_warnings = list(result.get("source_path_metadata_warnings") or [])
    lines += [f"- {item}" for item in source_path_warnings] if source_path_warnings else ["- None"]
    lines += ["", "## Duplicate/logo warnings", ""]
    warnings = list(result.get("warnings") or [])
    duplicate_paths = list(result.get("duplicate_logo_paths") or [])
    duplicate_lines = [f"duplicate registered logo path: {item}" for item in duplicate_paths] + warnings
    lines += [f"- {item}" for item in duplicate_lines] if duplicate_lines else ["- None"]
    lines += ["", "## Missing required logos", ""]
    lines += [
        f"- {row['team_name']} -> `{row['recommended_path']}` | packet `{row['decision_packet_id']}` | "
        f"decisions `{row['allowed_decisions']}` | fallback cue `{row['renderer_fallback_cue']}`"
        for row in missing_rows
    ] if missing_rows else ["- None"]
    write_text(REPORT_MD, "\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    result, missing_rows = build_validation(ROOT)
    write_reports(result, missing_rows)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
