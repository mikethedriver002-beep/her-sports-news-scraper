from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from hsd_asset_assurance_core import (
    VERSION as CORE_VERSION,
    clean,
    generate_individual_nameplate,
    generate_team_badge,
    image_decodable,
    read_csv,
    read_json,
    resolve_team_asset,
    slug,
    write_csv,
)

VERSION = "v1.0-phase6m-asset-assurance-preflight"
CATALOG = Path("config/graphics/v4/asset_assurance/sports_catalog_v1.json")
POLICY = Path("config/graphics/v4/asset_assurance/asset_assurance_policy_v1.json")
OUT_ROOT = Path("outputs/latest/HSD_ASSET_ASSURANCE")
REPORT_JSON = Path("asset_assurance_preflight_v1_report.json")
REPORT_MD = Path("asset_assurance_preflight_v1_report.md")
ROWS_CSV = OUT_ROOT / "asset_assurance_preflight_v1_rows.csv"
ROW_FIELDS = [
    "sport_id",
    "sport_display_name",
    "integration_status",
    "entity_id",
    "display_name",
    "entity_type",
    "resolution_mode",
    "resolved_path",
    "render_safe",
    "live_ready_pre_human",
    "requires_asset_visual_approval",
    "reason",
]
ENTITY_TEMPLATE_FIELDS = [
    "entity_id",
    "display_name",
    "entity_type",
    "active",
    "primary_hex",
    "secondary_hex",
    "asset_path",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _bool_text(value: bool) -> str:
    return "true" if value else "false"


def _entity_id(row: Dict[str, Any]) -> str:
    return clean(row.get("team_id") or row.get("entity_id") or row.get("player_id") or row.get("athlete_id"))


def _display_name(row: Dict[str, Any]) -> str:
    return clean(row.get("team_name") or row.get("display_name") or row.get("player_name") or row.get("athlete_name") or row.get("name"))


def _active(row: Dict[str, Any]) -> bool:
    raw = clean(row.get("active"))
    return not raw or raw.lower() in {"true", "1", "yes", "y"}


def _logo_map(path: Path) -> Dict[str, Dict[str, str]]:
    return {
        clean(row.get("team_id") or row.get("entity_id")): row
        for row in read_csv(path)
        if clean(row.get("team_id") or row.get("entity_id"))
    }


def _write_entity_template(sport_id: str, display_name: str, entity_model: str) -> Path:
    output = OUT_ROOT / "bootstrap" / sport_id / "entities_template.csv"
    if not output.exists():
        write_csv(output, [], ENTITY_TEMPLATE_FIELDS)
    if "individual" in entity_model:
        generate_individual_nameplate(
            OUT_ROOT / sport_id / "sport_fallback_template.png",
            f"{display_name} Athlete",
            sport_label=display_name,
        )
    else:
        generate_team_badge(
            OUT_ROOT / sport_id / "sport_fallback_template.png",
            f"{display_name} Team",
            sport_label=display_name,
        )
    return output


def process_sport(root: Path, sport: Dict[str, Any]) -> Dict[str, Any]:
    sport_id = clean(sport.get("sport_id"))
    display_name = clean(sport.get("display_name")) or sport_id.upper()
    integration_status = clean(sport.get("integration_status")) or "bootstrap_ready"
    entity_model = clean(sport.get("entity_model")) or "team"
    entity_registry = root / clean(sport.get("entity_registry"))
    logo_registry = root / clean(sport.get("logo_registry")) if clean(sport.get("logo_registry")) else None
    primary_default = clean(sport.get("fallback_primary_hex")) or "#DFA126"
    secondary_default = clean(sport.get("fallback_secondary_hex")) or "#080A10"
    template_path = _write_entity_template(sport_id, display_name, entity_model)

    entities = [row for row in read_csv(entity_registry) if _active(row)]
    logos = _logo_map(logo_registry) if logo_registry is not None and logo_registry.is_file() else {}
    rows: List[Dict[str, Any]] = []
    blockers: List[str] = []

    for entity in entities:
        entity_id = _entity_id(entity) or slug(_display_name(entity))
        entity_name = _display_name(entity)
        entity_type = clean(entity.get("entity_type")) or ("athlete" if "individual" in entity_model else "team")
        if not entity_name:
            blockers.append(f"missing_display_name:{sport_id}:{entity_id}")
            continue
        logo_row = logos.get(entity_id, {})
        raw_path = clean(logo_row.get("file_path") or logo_row.get("asset_path") or entity.get("asset_path"))
        approval_raw = clean(logo_row.get("approved") or entity.get("asset_approved"))
        approved = not approval_raw or approval_raw.lower() in {"true", "1", "yes", "y"}
        exact_path = root / raw_path if raw_path and approved else None
        if entity_type in {"athlete", "player", "individual"}:
            if exact_path and image_decodable(exact_path):
                resolution = {
                    "resolution_mode": "approved_player_asset",
                    "resolved_path": exact_path.relative_to(root).as_posix() if exact_path.is_relative_to(root) else exact_path.as_posix(),
                    "render_safe": True,
                    "live_ready_pre_human": True,
                    "requires_asset_visual_approval": False,
                    "reason": "verified_decodable_individual_asset",
                }
            else:
                fallback = OUT_ROOT / sport_id / "individual_nameplates" / f"{slug(entity_id)}.png"
                generate_individual_nameplate(
                    fallback,
                    entity_name,
                    sport_label=display_name,
                    primary_hex=clean(entity.get("primary_hex")) or primary_default,
                    secondary_hex=clean(entity.get("secondary_hex")) or secondary_default,
                )
                resolution = {
                    "resolution_mode": "hsd_individual_nameplate",
                    "resolved_path": fallback.as_posix(),
                    "render_safe": image_decodable(fallback),
                    "live_ready_pre_human": False,
                    "requires_asset_visual_approval": True,
                    "reason": "verified_individual_image_unavailable_hsd_no_photo_nameplate_generated",
                }
        else:
            resolution = resolve_team_asset(
                sport_id=sport_id,
                entity_id=entity_id,
                display_name=entity_name,
                exact_path=exact_path,
                output_root=OUT_ROOT,
                primary_hex=clean(entity.get("primary_hex")) or primary_default,
                secondary_hex=clean(entity.get("secondary_hex")) or secondary_default,
            )
        row = {
            "sport_id": sport_id,
            "sport_display_name": display_name,
            "integration_status": integration_status,
            "entity_id": entity_id,
            "display_name": entity_name,
            "entity_type": entity_type,
            **resolution,
        }
        row["render_safe"] = _bool_text(bool(resolution.get("render_safe")))
        row["live_ready_pre_human"] = _bool_text(bool(resolution.get("live_ready_pre_human")))
        row["requires_asset_visual_approval"] = _bool_text(bool(resolution.get("requires_asset_visual_approval")))
        rows.append(row)
        if not resolution.get("render_safe"):
            blockers.append(f"entity_not_render_safe:{sport_id}:{entity_id}")

    return {
        "sport_id": sport_id,
        "display_name": display_name,
        "integration_status": integration_status,
        "entity_model": entity_model,
        "entity_registry": entity_registry.as_posix(),
        "entity_registry_exists": entity_registry.is_file(),
        "logo_registry": logo_registry.as_posix() if logo_registry is not None else "",
        "bootstrap_template": template_path.as_posix(),
        "entity_count": len(entities),
        "resolved_count": len(rows),
        "render_safe_count": sum(row["render_safe"] == "true" for row in rows),
        "fallback_count": sum(str(row.get("resolution_mode", "")).startswith("hsd_") for row in rows),
        "blockers": sorted(set(blockers)),
        "rows": rows,
    }


def build_report(root: Path) -> Dict[str, Any]:
    catalog = read_json(root / CATALOG)
    policy = read_json(root / POLICY)
    sports = [dict(row) for row in catalog.get("sports") or [] if isinstance(row, dict)]
    blockers: List[str] = []
    if not catalog:
        blockers.append("sports_catalog_missing")
    if not policy:
        blockers.append("asset_assurance_policy_missing")
    required_ids = {"wnba", "nwsl", "uswnt", "tennis", "lpga", "ncaa_softball", "volleyball"}
    catalog_ids = {clean(row.get("sport_id")) for row in sports}
    for sport_id in sorted(required_ids - catalog_ids):
        blockers.append(f"required_sport_missing:{sport_id}")

    original = Path.cwd()
    try:
        import os

        os.chdir(root)
        results = [process_sport(root, sport) for sport in sports]
    finally:
        import os

        os.chdir(original)

    rows = [row for result in results for row in result["rows"]]
    for result in results:
        blockers.extend(result.get("blockers") or [])
    active = [result for result in results if result.get("integration_status") == "active_renderer"]
    if not active:
        blockers.append("no_active_renderer_sport")
    for result in active:
        if not result.get("entity_registry_exists") or result.get("entity_count", 0) == 0:
            blockers.append(f"active_sport_entity_registry_missing_or_empty:{result['sport_id']}")
        elif result.get("render_safe_count") != result.get("entity_count"):
            blockers.append(f"active_sport_not_fully_render_safe:{result['sport_id']}")
    status = "passed_asset_assurance_preflight" if not blockers else "blocked_asset_assurance_preflight"
    return {
        "version": VERSION,
        "core_version": CORE_VERSION,
        "generated_at_utc": now_iso(),
        "status": status,
        "strict_exit_code": 0 if not blockers else 2,
        "sport_count": len(results),
        "active_renderer_sports": [result["sport_id"] for result in active],
        "bootstrap_ready_sports": [result["sport_id"] for result in results if result.get("integration_status") == "bootstrap_ready"],
        "entity_count": sum(result.get("entity_count", 0) for result in results),
        "render_safe_count": sum(result.get("render_safe_count", 0) for result in results),
        "fallback_count": sum(result.get("fallback_count", 0) for result in results),
        "blockers": sorted(set(blockers)),
        "warnings": [],
        "production_cutover_allowed": False,
        "auto_publish_allowed": False,
        "human_visual_approval_required": True,
        "sports": results,
        "rows": rows,
    }


def write_report(root: Path, report: Dict[str, Any]) -> None:
    (root / REPORT_JSON).write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    write_csv(root / ROWS_CSV, report.get("rows") or [], ROW_FIELDS)
    lines = [
        "# HSD Phase 6M Asset Assurance Preflight",
        "",
        f"Status: `{report['status']}`",
        f"Sports catalogued: `{report['sport_count']}`",
        f"Entities resolved: `{report['entity_count']}`",
        f"Render-safe entities: `{report['render_safe_count']}`",
        f"Fallback assets generated: `{report['fallback_count']}`",
        "Production cutover allowed: `false`",
        "Auto-publish allowed: `false`",
        "",
        "## Sports",
        "",
    ]
    for sport in report.get("sports") or []:
        lines.append(
            f"- `{sport['sport_id']}` — `{sport['integration_status']}` — entities `{sport['entity_count']}` — render-safe `{sport['render_safe_count']}` — fallbacks `{sport['fallback_count']}`"
        )
    lines += ["", "## Blockers", ""]
    lines += [f"- `{value}`" for value in report.get("blockers") or []] or ["- None"]
    lines += [
        "",
        "## Contract",
        "",
        "- Missing logos generate clearly labelled HSD team badges.",
        "- Missing verified player images route to non-player team spotlight layouts.",
        "- Other sports receive generic registry templates and fallback templates from the same core.",
        "- Render-safe does not bypass hash-bound human visual approval.",
    ]
    (root / REPORT_MD).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Phase 6M multi-sport asset assurance preflight.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()
    report = build_report(root)
    write_report(root, report)
    print(json.dumps({key: report[key] for key in ["version", "status", "sport_count", "entity_count", "render_safe_count", "fallback_count", "blockers"]}, indent=2))
    return report["strict_exit_code"] if args.strict else 0


if __name__ == "__main__":
    raise SystemExit(main())
