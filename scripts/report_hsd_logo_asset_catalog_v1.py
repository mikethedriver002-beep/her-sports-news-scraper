from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, write_csv as write_run_csv, write_json


VERSION = "hsd-logo-asset-catalog-v1"
DEFAULT_REGISTRY_ROOT = Path("data/asset_registry")
DEFAULT_TEMPLATE_MAPPING = Path("config/graphics/template_render_mapping_v1.json")
DEFAULT_VERIFIED_LOGO_REGISTRY = Path("config/hsd_verified_logo_registry_v1.json")
DEFAULT_SCHEMA = Path("contracts/logo_asset_catalog_v1.schema.json")
DEFAULT_OUT_CSV = "data/asset_registry/logo_asset_catalog.csv"
DEFAULT_OUT_JSON = "data/asset_registry/logo_asset_catalog.json"
DEFAULT_OUT_MD = "data/asset_registry/logo_asset_catalog.md"

CATALOG_FIELDS = [
    "league",
    "entity_type",
    "team_id",
    "team_name",
    "asset_type",
    "local_logo_path",
    "png_path",
    "png_exists",
    "svg_path",
    "svg_exists",
    "preferred_format",
    "file_exists",
    "approval_status",
    "required",
    "missing_status",
    "fallback_status",
    "source_url",
    "source_note",
    "source_trust_status",
    "verified_registry_status",
    "blocked_url_match",
    "evidence",
    "render_template_ids",
    "template_scope",
    "review_only",
    "operator_action",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def bool_text(value: bool) -> str:
    return "true" if value else "false"


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def write_csv(path: Path, rows: Iterable[Mapping[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def league_code(value: str) -> str:
    return clean(value).lower()


def league_label(value: str) -> str:
    return clean(value).upper()


def template_ids_for_league(mapping: Mapping[str, Any], league: str) -> List[str]:
    league_upper = league_label(league)
    ids: List[str] = []

    for item in mapping.get("event_mappings") or []:
        if not isinstance(item, dict):
            continue
        if league_label(clean(item.get("league"))) == league_upper:
            template_id = clean(item.get("template_id"))
            if template_id:
                ids.append(template_id)

    for item in mapping.get("batch_mappings") or []:
        if not isinstance(item, dict):
            continue
        haystack = " ".join(clean(item.get(key)) for key in ["name", "family", "source", "mode"]).lower()
        normalized = haystack.replace("_", " ").replace("-", " ")
        if league_code(league) in haystack or "in the w" in normalized:
            template_id = clean(item.get("template_id"))
            if template_id:
                ids.append(template_id)

    return sorted(dict.fromkeys(ids))


def primary_paths(league: str, team_id: str, registered_path: str) -> Dict[str, str]:
    base = Path(registered_path).parent if registered_path else Path("assets") / "leagues" / league_code(league) / "teams" / team_id
    return {
        "png_path": (base / "logo.png").as_posix(),
        "svg_path": (base / "logo.svg").as_posix(),
    }


def file_exists(path_text: str) -> bool:
    return bool(path_text) and Path(path_text).exists()


def source_for_team(sources: List[Dict[str, str]], team_id: str) -> Dict[str, str]:
    for row in sources:
        if clean(row.get("team_id")) == team_id:
            return row
    return {}


def verified_policy_for_team(verified_registry: Mapping[str, Any], team_name: str) -> Mapping[str, Any]:
    teams = verified_registry.get("teams") if isinstance(verified_registry, Mapping) else {}
    if not isinstance(teams, Mapping):
        return {}
    policy = teams.get(team_name)
    return policy if isinstance(policy, Mapping) else {}


def blocked_url_match(source_url: str, policy: Mapping[str, Any]) -> str:
    haystack = source_url.lower()
    for item in policy.get("blocked_url_substrings") or []:
        needle = clean(item).lower()
        if needle and needle in haystack:
            return clean(item)
    return ""


def verified_registry_status(policy: Mapping[str, Any], blocked_match: str) -> str:
    if not policy:
        return "no_verified_policy"
    if blocked_match:
        return "blocked_source_url_match"
    return "verified_policy_present"


def source_trust_status(source_url: str, policy: Mapping[str, Any], blocked_match: str) -> str:
    if blocked_match:
        return "blocked_stale_source_review_required"
    if not source_url:
        return "missing_source_url_review_required"
    if policy:
        return "registered_source_policy_no_block_match"
    return "source_policy_not_registered_review_required"


def approval_status(logo_row: Mapping[str, str], local_exists: bool) -> str:
    if not logo_row:
        return "not_registered"
    if clean(logo_row.get("approved")).lower() == "true" and local_exists:
        return "approved"
    if local_exists:
        return "unapproved_review_required"
    return "missing"


def missing_status(status: str) -> str:
    if status == "approved":
        return "ready_exact_logo_registered"
    if status == "unapproved_review_required":
        return "local_file_exists_manual_review_required"
    if status == "not_registered":
        return "missing_registry_row"
    return "missing_local_logo_file"


def fallback_status(status: str) -> str:
    if status == "approved":
        return "no_fallback_needed"
    return "fallback_review_only_human_hold"


def operator_action(status: str, blocked_match: str = "") -> str:
    if blocked_match:
        return "replace_or_reverify_blocked_source_before_manual_approval"
    if status == "approved":
        return "catalog_only_no_action"
    if status == "unapproved_review_required":
        return "human_review_required_do_not_auto_enable"
    if status == "not_registered":
        return "add_manual_registry_row_after_evidence_review"
    return "supply_exact_logo_file_then_manual_review"


def build_team_row(
    league: str,
    team: Mapping[str, str],
    logo_row: Mapping[str, str],
    source_row: Mapping[str, str],
    verified_registry: Mapping[str, Any],
    template_ids: List[str],
) -> Dict[str, str]:
    team_id = clean(team.get("team_id") or logo_row.get("team_id"))
    team_name = clean(team.get("team_name") or source_row.get("team_name") or team_id)
    registered_path = clean(logo_row.get("file_path")) or f"assets/leagues/{league_code(league)}/teams/{team_id}/logo.png"
    paths = primary_paths(league, team_id, registered_path)
    local_exists = file_exists(registered_path)
    png_exists = file_exists(paths["png_path"])
    svg_exists = file_exists(paths["svg_path"])
    status = approval_status(logo_row, local_exists)
    preferred_format = Path(registered_path).suffix.lower().lstrip(".") if local_exists else ("png" if png_exists else ("svg" if svg_exists else ""))
    source_url = clean(source_row.get("source_url"))
    source_note = clean(logo_row.get("source_note") or source_row.get("source_note"))
    verified_policy = verified_policy_for_team(verified_registry, team_name)
    blocked_match = blocked_url_match(source_url, verified_policy)
    verified_status = verified_registry_status(verified_policy, blocked_match)
    trust_status = source_trust_status(source_url, verified_policy, blocked_match)
    evidence = "; ".join(
        part
        for part in [
            f"registry_path={registered_path}" if registered_path else "",
            f"source_url={source_url}" if source_url else "",
            f"source_note={source_note}" if source_note else "",
            f"blocked_url_match={blocked_match}" if blocked_match else "",
            f"verified_registry_status={verified_status}",
            f"png_exists={bool_text(png_exists)}",
            f"svg_exists={bool_text(svg_exists)}",
        ]
        if part
    )
    return {
        "league": league_label(league),
        "entity_type": "team_logo",
        "team_id": team_id,
        "team_name": team_name,
        "asset_type": clean(logo_row.get("asset_type")) or "primary_logo",
        "local_logo_path": registered_path,
        "png_path": paths["png_path"],
        "png_exists": bool_text(png_exists),
        "svg_path": paths["svg_path"],
        "svg_exists": bool_text(svg_exists),
        "preferred_format": preferred_format,
        "file_exists": bool_text(local_exists),
        "approval_status": status,
        "required": clean(logo_row.get("required")) or "true",
        "missing_status": missing_status(status),
        "fallback_status": fallback_status(status),
        "source_url": source_url,
        "source_note": source_note,
        "source_trust_status": trust_status,
        "verified_registry_status": verified_status,
        "blocked_url_match": blocked_match,
        "evidence": evidence,
        "render_template_ids": ";".join(template_ids),
        "template_scope": "current_review_mapping",
        "review_only": "true",
        "operator_action": operator_action(status, blocked_match),
    }


def build_league_row(league: str, template_ids: List[str]) -> Dict[str, str]:
    png_path = f"assets/leagues/{league_code(league)}/logo.png"
    svg_path = f"assets/leagues/{league_code(league)}/logo.svg"
    png_exists = file_exists(png_path)
    svg_exists = file_exists(svg_path)
    local_path = png_path if png_exists else (svg_path if svg_exists else png_path)
    status = "unapproved_review_required" if png_exists or svg_exists else "missing"
    return {
        "league": league_label(league),
        "entity_type": "league_logo",
        "team_id": "",
        "team_name": "",
        "asset_type": "league_logo",
        "local_logo_path": local_path,
        "png_path": png_path,
        "png_exists": bool_text(png_exists),
        "svg_path": svg_path,
        "svg_exists": bool_text(svg_exists),
        "preferred_format": "png" if png_exists else ("svg" if svg_exists else ""),
        "file_exists": bool_text(png_exists or svg_exists),
        "approval_status": status,
        "required": "false",
        "missing_status": "local_file_exists_manual_review_required" if status.startswith("unapproved") else "missing_local_league_logo_file",
        "fallback_status": "fallback_review_only_human_hold",
        "source_url": "",
        "source_note": "league_logo_catalog_probe_no_auto_approval",
        "source_trust_status": "league_logo_source_not_registered_review_required",
        "verified_registry_status": "not_applicable",
        "blocked_url_match": "",
        "evidence": f"png_exists={bool_text(png_exists)}; svg_exists={bool_text(svg_exists)}",
        "render_template_ids": ";".join(template_ids),
        "template_scope": "current_review_mapping",
        "review_only": "true",
        "operator_action": "human_review_required_do_not_auto_enable" if png_exists or svg_exists else "optional_supply_league_logo_then_manual_review",
    }


def build_catalog(
    registry_root: Path = DEFAULT_REGISTRY_ROOT,
    template_mapping: Path = DEFAULT_TEMPLATE_MAPPING,
    verified_logo_registry: Path = DEFAULT_VERIFIED_LOGO_REGISTRY,
) -> Dict[str, Any]:
    mapping = read_json(template_mapping)
    verified_registry = read_json(verified_logo_registry)
    rows: List[Dict[str, str]] = []
    league_dirs = sorted(path for path in registry_root.iterdir() if path.is_dir()) if registry_root.exists() else []

    for league_dir in league_dirs:
        league = league_dir.name
        teams = read_csv(league_dir / "teams.csv")
        logos = read_csv(league_dir / "team_logos.csv")
        sources = read_csv(league_dir / "logo_sources.csv")
        by_logo = {clean(row.get("team_id")): row for row in logos}
        template_ids = template_ids_for_league(mapping, league)

        rows.append(build_league_row(league, template_ids))
        for team in teams:
            team_id = clean(team.get("team_id"))
            rows.append(build_team_row(league, team, by_logo.get(team_id, {}), source_for_team(sources, team_id), verified_registry, template_ids))

    by_status: Dict[str, int] = {}
    by_trust_status: Dict[str, int] = {}
    for row in rows:
        by_status[row["approval_status"]] = by_status.get(row["approval_status"], 0) + 1
        trust_status = row.get("source_trust_status") or ""
        by_trust_status[trust_status] = by_trust_status.get(trust_status, 0) + 1

    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "review_only": True,
        "catalog_csv": output_path(DEFAULT_OUT_CSV).as_posix(),
        "schema": DEFAULT_SCHEMA.as_posix(),
        "template_mapping": template_mapping.as_posix(),
        "verified_logo_registry": verified_logo_registry.as_posix(),
        "row_count": len(rows),
        "team_logo_rows": sum(row["entity_type"] == "team_logo" for row in rows),
        "league_logo_rows": sum(row["entity_type"] == "league_logo" for row in rows),
        "approval_status_counts": by_status,
        "source_trust_status_counts": by_trust_status,
        "rows": rows,
        "policy": {
            "no_auto_approval": True,
            "no_asset_downloads": True,
            "fallbacks_are_review_only": True,
            "catalog_does_not_change_renderer_behavior": True,
        },
    }


def write_markdown(report: Mapping[str, Any], path: Path) -> None:
    rows = list(report.get("rows") or [])
    status_counts = report.get("approval_status_counts") or {}
    lines = [
        "# HSD Logo Asset Catalog",
        "",
        f"Generated: `{report.get('generated_at_utc')}`",
        f"Version: `{report.get('version')}`",
        "",
        "Review-only catalog. This report does not approve logos, enable fallbacks, download assets, or change renderer behavior.",
        "",
        "## Summary",
        "",
        f"- Rows: `{report.get('row_count')}`",
        f"- Team logo rows: `{report.get('team_logo_rows')}`",
        f"- League logo rows: `{report.get('league_logo_rows')}`",
    ]
    for key in sorted(status_counts):
        lines.append(f"- {key}: `{status_counts[key]}`")

    trust_counts = report.get("source_trust_status_counts") or {}
    lines += ["", "## Source trust status", ""]
    for key in sorted(trust_counts):
        lines.append(f"- {key}: `{trust_counts[key]}`")

    lines += ["", "## Needs operator review", ""]
    review_rows = [row for row in rows if row.get("approval_status") != "approved"]
    if review_rows:
        for row in review_rows:
            label = row.get("team_name") or row.get("league")
            lines.append(
                f"- `{row.get('league')}` {row.get('entity_type')} `{label}`: "
                f"`{row.get('approval_status')}`; path `{row.get('local_logo_path')}`; action `{row.get('operator_action')}`"
            )
    else:
        lines.append("- None")

    lines += ["", "## Source policy warnings", ""]
    warning_rows = [row for row in rows if row.get("blocked_url_match")]
    if warning_rows:
        for row in warning_rows:
            lines.append(
                f"- `{row.get('league')}` team_logo `{row.get('team_name')}`: "
                f"blocked source substring `{row.get('blocked_url_match')}`; source `{row.get('source_url')}`; "
                f"action `{row.get('operator_action')}`"
            )
    else:
        lines.append("- None")

    lines += ["", "## Template scope", ""]
    by_league: Dict[str, str] = {}
    for row in rows:
        by_league.setdefault(clean(row.get("league")), clean(row.get("render_template_ids")))
    for league, template_ids in sorted(by_league.items()):
        lines.append(f"- `{league}`: `{template_ids or 'none'}`")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build a review-only HSD team/league logo asset catalog.")
    parser.add_argument("--registry-root", default=str(DEFAULT_REGISTRY_ROOT))
    parser.add_argument("--template-mapping", default=str(DEFAULT_TEMPLATE_MAPPING))
    parser.add_argument("--verified-logo-registry", default=str(DEFAULT_VERIFIED_LOGO_REGISTRY))
    parser.add_argument("--csv", default=DEFAULT_OUT_CSV)
    parser.add_argument("--json", default=DEFAULT_OUT_JSON)
    parser.add_argument("--md", default=DEFAULT_OUT_MD)
    args = parser.parse_args(argv)

    report = build_catalog(Path(args.registry_root), Path(args.template_mapping), Path(args.verified_logo_registry))
    csv_path = output_path(args.csv)
    json_path = output_path(args.json)
    md_path = output_path(args.md)
    report["catalog_csv"] = csv_path.as_posix()

    write_run_csv(args.csv, report["rows"], CATALOG_FIELDS)
    write_json(args.json, report, indent=2, sort_keys=True)
    write_markdown(report, md_path)

    print(
        json.dumps(
            {
                "version": VERSION,
                "review_only": True,
                "row_count": report["row_count"],
                "approval_status_counts": report["approval_status_counts"],
                "source_trust_status_counts": report["source_trust_status_counts"],
                "csv": csv_path.as_posix(),
                "json": json_path.as_posix(),
                "md": md_path.as_posix(),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
