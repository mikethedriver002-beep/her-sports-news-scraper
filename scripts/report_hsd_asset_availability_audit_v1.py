from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from hsd_run_io import output_path, write_csv as write_run_csv, write_json
import report_hsd_athlete_photo_catalog_v1 as athlete_catalog
import report_hsd_logo_asset_catalog_v1 as logo_catalog
import report_hsd_template_renderer_logo_status_v1 as renderer_logo_status


VERSION = "hsd-asset-availability-audit-v1-review-only"

DEFAULT_REGISTRY_ROOT = Path("data/asset_registry")
DEFAULT_WNBA_REGISTRY = DEFAULT_REGISTRY_ROOT / "wnba"
DEFAULT_TEMPLATE_MAPPING = Path("config/graphics/template_render_mapping_v1.json")
DEFAULT_VERIFIED_LOGO_REGISTRY = Path("config/hsd_verified_logo_registry_v1.json")
DEFAULT_RENDERER_LOGO_AUDIT = Path(renderer_logo_status.DEFAULT_LOGO_AUDIT_JSON)
DEFAULT_RENDERER_MANIFEST = Path(renderer_logo_status.DEFAULT_MANIFEST_JSON)
DEFAULT_ASSET_ASSURANCE_ROWS = Path("outputs/latest/HSD_ASSET_ASSURANCE/asset_assurance_preflight_v1_rows.csv")

DEFAULT_OUT_CSV = "data/asset_registry/asset_availability_audit.csv"
DEFAULT_OUT_JSON = "data/asset_registry/asset_availability_audit.json"
DEFAULT_OUT_MD = "data/asset_registry/asset_availability_audit.md"

AUDIT_FIELDS = [
    "review_packet_id",
    "decision_lane",
    "default_operator_decision",
    "decision_packet_title",
    "allowed_operator_decisions",
    "decision_primary_action",
    "decision_hold_cue",
    "decision_revise_cue",
    "asset_domain",
    "league",
    "entity_type",
    "entity_id",
    "entity_name",
    "asset_kind",
    "asset_path",
    "finding",
    "severity",
    "approval_status",
    "format_status",
    "dimension_status",
    "renderer_coverage",
    "source_confidence",
    "identity_confidence",
    "manual_approval_status",
    "asset_readiness",
    "logo_readiness_status",
    "renderer_fallback_cue",
    "operator_copy_target",
    "manual_review_packet",
    "publish_ready",
    "auto_approval",
    "auto_publish",
    "move_files",
    "paid_apis",
    "recommended_next_step",
    "blocker_summary",
    "evidence",
]

SUPPORTED_RASTER = {".png", ".jpg", ".jpeg", ".webp"}
SUPPORTED_LOGO = SUPPORTED_RASTER | {".svg"}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def boolish(value: Any) -> bool:
    return clean(value).lower() in {"1", "true", "yes", "y", "approved"}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists() or not path.is_file():
        return []
    import csv

    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def count_by(rows: Iterable[Mapping[str, str]], field: str) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for row in rows:
        key = clean(row.get(field)) or "unknown"
        counts[key] = counts.get(key, 0) + 1
    return dict(sorted(counts.items()))


def image_probe(path: Path, *, asset_domain: str) -> Dict[str, str]:
    suffix = path.suffix.lower()
    if not path.exists():
        return {
            "format_status": "missing_file",
            "dimension_status": "not_available",
            "evidence": "path_missing",
        }
    if suffix not in (SUPPORTED_LOGO if asset_domain != "player_photo" else SUPPORTED_RASTER):
        return {
            "format_status": "unsupported_extension",
            "dimension_status": "not_available",
            "evidence": f"extension={suffix or 'none'}",
        }
    if suffix == ".svg":
        text = path.read_text(encoding="utf-8", errors="ignore")
        has_svg = "<svg" in text.lower()
        has_size_hint = any(token in text.lower() for token in ["viewbox", "width=", "height="])
        return {
            "format_status": "valid_svg" if has_svg else "invalid_svg",
            "dimension_status": "svg_size_hint_present" if has_size_hint else "svg_size_hint_missing_review",
            "evidence": f"bytes={path.stat().st_size}; svg_tag={str(has_svg).lower()}; size_hint={str(has_size_hint).lower()}",
        }
    try:
        from PIL import Image  # type: ignore

        with Image.open(path) as image:
            width, height = image.size
            image.verify()
        if asset_domain == "player_photo":
            dimension_status = "meets_player_photo_floor" if width >= 260 and height >= 190 else "below_player_photo_floor"
        else:
            dimension_status = "meets_logo_floor" if width >= 128 and height >= 128 else "below_logo_floor"
        return {
            "format_status": "valid_raster",
            "dimension_status": dimension_status,
            "evidence": f"bytes={path.stat().st_size}; image_size={width}x{height}",
        }
    except Exception as exc:
        return {
            "format_status": "decode_failed",
            "dimension_status": "unverified",
            "evidence": f"bytes={path.stat().st_size}; decode_error={type(exc).__name__}",
        }


def row(
    *,
    asset_domain: str,
    league: str,
    entity_type: str,
    entity_id: str,
    entity_name: str,
    asset_kind: str,
    asset_path: str,
    finding: str,
    severity: str,
    approval_status: str,
    format_status: str = "",
    dimension_status: str = "",
    renderer_coverage: str = "",
    logo_readiness_status: str = "",
    renderer_fallback_cue: str = "",
    recommended_next_step: str = "",
    evidence: str = "",
) -> Dict[str, str]:
    return {
        "asset_domain": asset_domain,
        "league": league,
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "asset_kind": asset_kind,
        "asset_path": asset_path,
        "finding": finding,
        "severity": severity,
        "approval_status": approval_status,
        "format_status": format_status,
        "dimension_status": dimension_status,
        "renderer_coverage": renderer_coverage,
        "logo_readiness_status": logo_readiness_status,
        "renderer_fallback_cue": renderer_fallback_cue,
        "recommended_next_step": recommended_next_step,
        "evidence": evidence,
    }


def review_packet_path(asset_domain: str, finding: str) -> str:
    if asset_domain == "player_photo" and finding == "suspicious_or_default_player_approval":
        return "data/asset_registry/wnba/athlete_identity_resolution_workflow.md"
    if asset_domain == "player_photo":
        return "data/asset_registry/wnba/athlete_photo_catalog.md"
    if asset_domain in {"team_logo", "league_logo"}:
        return "data/asset_registry/wnba/logo_review_catalog_report.md"
    return "data/asset_registry/asset_availability_audit.md"


def review_packet_lane(asset_domain: str, finding: str) -> str:
    if asset_domain == "player_photo" and finding == "suspicious_or_default_player_approval":
        return "wnba_athlete_identity_resolution"
    if asset_domain == "player_photo":
        return "wnba_athlete_photo_onboarding"
    if asset_domain in {"team_logo", "league_logo"}:
        return "wnba_logo_review"
    return "renderer_fallback_review"


def review_packet_decision(asset_domain: str, finding: str, severity: str) -> str:
    if asset_domain == "player_photo" and finding == "suspicious_or_default_player_approval":
        return "hold_identity"
    if asset_domain == "player_photo":
        return "hold_photo_slot"
    if asset_domain == "league_logo":
        return "hold_league_mark"
    if asset_domain == "team_logo":
        return "hold_or_verify_logo"
    if asset_domain == "renderer":
        return "verify_renderer_fallback"
    return "review_required" if severity in {"error", "warning"} else "monitor"


def review_packet_allowed_decisions(asset_domain: str, finding: str) -> str:
    if asset_domain == "player_photo" and finding == "suspicious_or_default_player_approval":
        return "verify_identity_for_review_renders|hold_identity|revise_asset"
    if asset_domain == "player_photo":
        return "verify_photo_for_review_renders|hold_photo_slot|revise_photo_asset"
    if asset_domain in {"team_logo", "league_logo"}:
        return "verify_logo_for_review_renders|hold_logo_slot|revise_logo_source_metadata"
    if asset_domain == "renderer":
        return "confirm_no_active_fallback|hold_render|revise_asset_registry"
    return "verify_for_review_renders|hold|revise_asset"


def review_packet_title(asset_domain: str, finding: str, entity: str) -> str:
    if asset_domain == "player_photo":
        return f"Player photo blocker: {entity}"
    if asset_domain == "team_logo":
        return f"WNBA team logo blocker: {entity}"
    if asset_domain == "league_logo":
        return f"WNBA league mark blocker: {entity}"
    if asset_domain == "renderer":
        return f"Renderer fallback review: {entity}"
    return f"Asset blocker: {entity} ({finding.replace('_', ' ')})"


def review_packet_hold_cue(asset_domain: str, finding: str) -> str:
    if asset_domain == "player_photo":
        return "Hold if identity, source, approval marker, crop, format, or dimensions are incomplete."
    if asset_domain in {"team_logo", "league_logo"}:
        return "Hold if exact local logo evidence, source provenance, approval, format, or dimensions are incomplete."
    if asset_domain == "renderer":
        return "Hold if a text badge or generated fallback is standing in for an exact required logo."
    return "Hold if source, approval, identity, format, or renderer evidence is incomplete."


def review_packet_revise_cue(asset_domain: str, finding: str) -> str:
    if asset_domain == "player_photo":
        return "Revise through the review-only athlete-photo workflow before any renderer photo use."
    if asset_domain in {"team_logo", "league_logo"}:
        return "Revise local/source registry metadata only after human evidence review; do not download, invent, or substitute a logo."
    if asset_domain == "renderer":
        return "Revise upstream asset registry or template inputs after manual evidence review; do not change renderer trust automatically."
    return "Revise through review-only asset workflows before renderer trust."


def review_packet_source_confidence(finding: str, evidence: str, approval_status: str) -> str:
    text = f"{finding} {evidence} {approval_status}".lower()
    if "missing" in text or "empty_" in text:
        return "source_missing_or_unregistered"
    if "default" in text or "blocked" in text or "unknown" in text:
        return "source_recheck_required"
    if "approved" in text and "valid_" in text:
        return "local_source_present_manual_crosscheck_required"
    return "manual_source_review_required"


def review_packet_identity_confidence(asset_domain: str, finding: str, evidence: str) -> str:
    if asset_domain != "player_photo":
        return "not_applicable"
    text = f"{finding} {evidence}".lower()
    if "default" in text or "suspicious" in text:
        return "identity_hold_default_or_suspicious_approval"
    if "missing" in text:
        return "identity_unverified_asset_missing"
    return "identity_manual_review_required"


def review_packet_asset_readiness(asset_domain: str, finding: str, severity: str, approval_status: str, format_status: str) -> str:
    if severity == "error":
        return "blocked_until_asset_or_format_fixed"
    if asset_domain == "player_photo" and finding == "suspicious_or_default_player_approval":
        return "blocked_until_identity_resolution"
    if asset_domain in {"team_logo", "league_logo"} and approval_status != "approved":
        return "blocked_until_logo_review"
    if asset_domain == "renderer":
        return "review_renderer_fallback_before_trust"
    if format_status and not format_status.startswith("valid_"):
        return "review_format_before_renderer_use"
    return "manual_review_required"


def review_packet_target(asset_domain: str, finding: str) -> str:
    if asset_domain == "player_photo" and finding == "suspicious_or_default_player_approval":
        return "operator/inbox/wnba_athlete_identity_resolution.csv"
    if asset_domain == "player_photo":
        return "operator/inbox/athlete_photo_onboarding_decisions.csv"
    if asset_domain in {"team_logo", "league_logo"}:
        return "operator/assets/brand_logos/README.md"
    return "data/asset_registry/asset_availability_audit.csv"


def enrich_review_packet_fields(item: Dict[str, str], rank: int) -> Dict[str, str]:
    asset_domain = clean(item.get("asset_domain"))
    finding = clean(item.get("finding"))
    severity = clean(item.get("severity"))
    evidence = clean(item.get("evidence"))
    approval_status = clean(item.get("approval_status"))
    format_status = clean(item.get("format_status"))
    entity = clean(item.get("entity_name")) or clean(item.get("entity_id")) or "unknown_asset"
    logo_readiness = clean(item.get("logo_readiness_status"))
    fallback_cue = clean(item.get("renderer_fallback_cue"))
    decision = review_packet_decision(asset_domain, finding, severity)
    enriched = dict(item)
    enriched.update(
        {
            "review_packet_id": f"asset_review_{rank:04d}_{asset_domain or 'asset'}_{clean(item.get('entity_id')) or 'unknown'}",
            "decision_lane": review_packet_lane(asset_domain, finding),
            "default_operator_decision": decision,
            "decision_packet_title": review_packet_title(asset_domain, finding, entity),
            "allowed_operator_decisions": review_packet_allowed_decisions(asset_domain, finding),
            "decision_primary_action": clean(item.get("recommended_next_step")) or "manual_review_required_before_renderer_trust",
            "decision_hold_cue": review_packet_hold_cue(asset_domain, finding),
            "decision_revise_cue": review_packet_revise_cue(asset_domain, finding),
            "source_confidence": review_packet_source_confidence(finding, evidence, approval_status),
            "identity_confidence": review_packet_identity_confidence(asset_domain, finding, evidence),
            "manual_approval_status": "manual_review_required" if severity in {"error", "warning"} else "manual_monitoring",
            "asset_readiness": logo_readiness or review_packet_asset_readiness(asset_domain, finding, severity, approval_status, format_status),
            "logo_readiness_status": logo_readiness,
            "renderer_fallback_cue": fallback_cue or (clean(item.get("renderer_coverage")) if asset_domain == "renderer" else ""),
            "operator_copy_target": review_packet_target(asset_domain, finding),
            "manual_review_packet": review_packet_path(asset_domain, finding),
            "publish_ready": "false",
            "auto_approval": "false",
            "auto_publish": "false",
            "move_files": "false",
            "paid_apis": "false",
            "blocker_summary": f"{entity}: {finding.replace('_', ' ')}; default decision={decision}; readiness={logo_readiness or review_packet_asset_readiness(asset_domain, finding, severity, approval_status, format_status)}",
        }
    )
    return enriched


def audit_player_photos(root: Path) -> List[Dict[str, str]]:
    template_uses = athlete_catalog.discover_render_template_uses(root / athlete_catalog.TEMPLATE_DOC_ROOT)
    rows = athlete_catalog.build_catalog(
        athlete_catalog.read_csv(root / athlete_catalog.ATHLETES),
        athlete_catalog.read_csv(root / athlete_catalog.ATHLETE_IMAGES),
        athlete_catalog.read_csv(root / athlete_catalog.APPROVED_ASSETS),
        athlete_catalog.read_csv(root / athlete_catalog.MATCH_REVIEW),
        template_uses,
    )
    findings: List[Dict[str, str]] = []
    for item in rows:
        asset_path = clean(item.get("local_asset_path"))
        status = clean(item.get("status"))
        probe = image_probe(root / asset_path, asset_domain="player_photo") if asset_path else {
            "format_status": "missing_path",
            "dimension_status": "not_available",
            "evidence": "empty_local_asset_path",
        }
        common = {
            "asset_domain": "player_photo",
            "league": clean(item.get("league")) or "WNBA",
            "entity_type": "athlete",
            "entity_id": clean(item.get("athlete_id")),
            "entity_name": clean(item.get("athlete_name")),
            "asset_kind": clean(item.get("asset_kind")),
            "asset_path": asset_path,
            "approval_status": status,
            "format_status": probe["format_status"],
            "dimension_status": probe["dimension_status"],
            "renderer_coverage": clean(item.get("render_template_uses")),
            "evidence": "; ".join(part for part in [clean(item.get("source_evidence")), clean(item.get("crop_readiness_notes")), probe["evidence"]] if part),
        }
        if status == "missing":
            findings.append(row(**common, finding="missing_local_player_asset", severity="error", recommended_next_step="keep_photo_slot_disabled_until_asset_and_marker_are_reviewed"))
        elif status == "unapproved":
            findings.append(row(**common, finding="player_asset_present_without_complete_approval", severity="warning", recommended_next_step="human_review_required_before_renderer_photo_use"))
        if status == "approved" and clean(item.get("render_template_uses")).startswith("review_only_manual_source_recheck_required"):
            findings.append(row(**common, finding="suspicious_or_default_player_approval", severity="warning", recommended_next_step="recheck_decision_source_source_file_and_approval_timestamp"))
        if probe["format_status"] not in {"valid_raster"}:
            findings.append(row(**common, finding="player_photo_format_problem", severity="error" if status == "approved" else "warning", recommended_next_step="replace_with_decodable_png_jpg_or_webp_before_renderer_use"))
        elif probe["dimension_status"] == "below_player_photo_floor":
            findings.append(row(**common, finding="player_photo_dimension_problem", severity="warning", recommended_next_step="review_crop_or_replace_with_headshot_at_least_260x190"))
    return findings


def audit_logos(root: Path, registry_root: Path, template_mapping: Path, verified_logo_registry: Path) -> List[Dict[str, str]]:
    report = logo_catalog.build_catalog(root / registry_root, root / template_mapping, root / verified_logo_registry)
    findings: List[Dict[str, str]] = []
    for item in report.get("rows") or []:
        asset_path = clean(item.get("local_logo_path"))
        status = clean(item.get("approval_status"))
        probe = image_probe(root / asset_path, asset_domain="logo") if asset_path else {
            "format_status": "missing_path",
            "dimension_status": "not_available",
            "evidence": "empty_local_logo_path",
        }
        common = {
            "asset_domain": "league_logo" if item.get("entity_type") == "league_logo" else "team_logo",
            "league": clean(item.get("league")),
            "entity_type": clean(item.get("entity_type")),
            "entity_id": clean(item.get("team_id")) or clean(item.get("league")),
            "entity_name": clean(item.get("team_name")) or clean(item.get("league")),
            "asset_kind": clean(item.get("asset_type")),
            "asset_path": asset_path,
            "approval_status": status,
            "format_status": probe["format_status"],
            "dimension_status": probe["dimension_status"],
            "renderer_coverage": clean(item.get("fallback_status")),
            "logo_readiness_status": clean(item.get("logo_readiness_status")),
            "renderer_fallback_cue": clean(item.get("renderer_fallback_cue")),
            "evidence": "; ".join(part for part in [clean(item.get("evidence")), clean(item.get("source_trust_status")), probe["evidence"]] if part),
        }
        if status in {"missing", "not_registered"}:
            findings.append(row(**common, finding="missing_or_unregistered_logo_asset", severity="error", recommended_next_step="supply_exact_local_logo_and_manual_registry_review"))
        elif status == "unapproved_review_required":
            findings.append(row(**common, finding="logo_present_without_complete_approval", severity="warning", recommended_next_step="human_review_required_before_renderer_logo_use"))
        if clean(item.get("blocked_url_match")) or clean(item.get("operator_action")) in {
            "replace_or_reverify_blocked_source_before_manual_approval",
            "manual_source_recheck_required_before_operator_trust",
        }:
            findings.append(row(**common, finding="suspicious_logo_source_or_approval", severity="warning", recommended_next_step=clean(item.get("operator_action")) or "manual_source_recheck_required"))
        if probe["format_status"] not in {"valid_raster", "valid_svg", "missing_file"}:
            findings.append(row(**common, finding="logo_format_problem", severity="error" if status == "approved" else "warning", recommended_next_step="replace_with_decodable_png_svg_jpg_or_webp"))
        elif probe["dimension_status"] in {"below_logo_floor", "svg_size_hint_missing_review"}:
            findings.append(row(**common, finding="logo_dimension_or_size_hint_problem", severity="warning", recommended_next_step="review_logo_dimensions_or_svg_viewbox_before_renderer_use"))
    return findings


def audit_renderer_fallbacks(root: Path, logo_audit_path: Path, manifest_path: Path, assurance_rows_path: Path) -> List[Dict[str, str]]:
    findings: List[Dict[str, str]] = []
    if (root / logo_audit_path).exists() or (root / manifest_path).exists():
        report = renderer_logo_status.build_report(root / logo_audit_path, root / manifest_path)
        for item in report.get("active_fallback_rows") or []:
            findings.append(row(
                asset_domain="renderer",
                league=clean(item.get("league")),
                entity_type="team_logo",
                entity_id=clean(item.get("team_id") or item.get("team")),
                entity_name=clean(item.get("team")),
                asset_kind="renderer_logo_fallback",
                asset_path=clean(item.get("path_or_url")),
                finding="renderer_active_logo_fallback",
                severity="warning",
                approval_status="fallback_review_only",
                renderer_coverage="active_renderer_text_badge_fallback",
                renderer_fallback_cue="active_text_badge_fallback_review_only_hold_exact_logo_required",
                recommended_next_step="verify exact approved logo coverage before live handoff",
                evidence=json.dumps(item, sort_keys=True),
            ))
    else:
        findings.append(row(
            asset_domain="renderer",
            league="",
            entity_type="renderer_manifest",
            entity_id="template_renderer_logo_status",
            entity_name="Template renderer logo status",
            asset_kind="renderer_logo_audit",
            asset_path=(root / logo_audit_path).as_posix(),
            finding="renderer_logo_audit_missing",
            severity="info",
            approval_status="not_applicable",
            renderer_coverage="not_observed",
            renderer_fallback_cue="renderer_logo_audit_missing_run_status_before_trusting_logo_fallbacks",
            recommended_next_step="run renderer logo status after the next local render to confirm fallback coverage",
            evidence=f"missing={logo_audit_path.as_posix()}",
        ))

    assurance_rows = read_csv(root / assurance_rows_path)
    for item in assurance_rows:
        mode = clean(item.get("resolution_mode"))
        if mode.startswith("hsd_"):
            findings.append(row(
                asset_domain="renderer",
                league=clean(item.get("sport_id")).upper(),
                entity_type=clean(item.get("entity_type")),
                entity_id=clean(item.get("entity_id")),
                entity_name=clean(item.get("display_name")),
                asset_kind="asset_assurance_fallback",
                asset_path=clean(item.get("resolved_path")),
                finding="asset_assurance_hsd_fallback_generated",
                severity="info",
                approval_status="fallback_review_only",
                format_status="generated_local_fallback",
                renderer_coverage=mode,
                renderer_fallback_cue="generated_hsd_fallback_review_only_not_publish_ready",
                recommended_next_step="keep fallback in review lane until exact asset or human visual approval is available",
                evidence=f"render_safe={clean(item.get('render_safe'))}; live_ready_pre_human={clean(item.get('live_ready_pre_human'))}; reason={clean(item.get('reason'))}",
            ))
    return findings


def build_audit(
    root: Path,
    *,
    registry_root: Path = DEFAULT_REGISTRY_ROOT,
    template_mapping: Path = DEFAULT_TEMPLATE_MAPPING,
    verified_logo_registry: Path = DEFAULT_VERIFIED_LOGO_REGISTRY,
    renderer_logo_audit: Path = DEFAULT_RENDERER_LOGO_AUDIT,
    renderer_manifest: Path = DEFAULT_RENDERER_MANIFEST,
    asset_assurance_rows: Path = DEFAULT_ASSET_ASSURANCE_ROWS,
) -> Dict[str, Any]:
    root = root.resolve()
    findings: List[Dict[str, str]] = []
    original = Path.cwd()
    try:
        import os

        os.chdir(root)
        findings.extend(audit_player_photos(root))
        findings.extend(audit_logos(root, registry_root, template_mapping, verified_logo_registry))
        findings.extend(audit_renderer_fallbacks(root, renderer_logo_audit, renderer_manifest, asset_assurance_rows))
    finally:
        import os

        os.chdir(original)
    findings = [enrich_review_packet_fields(item, index + 1) for index, item in enumerate(findings)]
    status = "review_required" if any(row["severity"] in {"error", "warning"} for row in findings) else "pass"
    return {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "review_only": True,
        "status": status,
        "strict_exit_code": 2 if any(row["severity"] == "error" for row in findings) else 0,
        "finding_count": len(findings),
        "severity_counts": count_by(findings, "severity"),
        "finding_counts": count_by(findings, "finding"),
        "asset_domain_counts": count_by(findings, "asset_domain"),
        "policy": {
            "no_paid_apis": True,
            "no_auto_approval": True,
            "no_asset_downloads": True,
            "no_file_movement_into_publish_ready_lanes": True,
            "no_publishing": True,
            "does_not_change_renderer_behavior": True,
        },
        "inputs": {
            "registry_root": (root / registry_root).as_posix(),
            "template_mapping": (root / template_mapping).as_posix(),
            "verified_logo_registry": (root / verified_logo_registry).as_posix(),
            "renderer_logo_audit": (root / renderer_logo_audit).as_posix(),
            "renderer_manifest": (root / renderer_manifest).as_posix(),
            "asset_assurance_rows": (root / asset_assurance_rows).as_posix(),
        },
        "findings": findings,
    }


def write_markdown(report: Mapping[str, Any], path: Path) -> None:
    findings = list(report.get("findings") or [])
    lines = [
        "# HSD Asset Availability Audit v1",
        "",
        f"Generated: `{report.get('generated_at_utc')}`",
        f"Status: `{report.get('status')}`",
        "",
        "Review-only audit. This report does not approve assets, fetch files, move files into publish-ready lanes, publish, or change renderer behavior.",
        "",
        "## Counts",
        "",
        f"- findings: `{report.get('finding_count')}`",
    ]
    for key, value in (report.get("severity_counts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines += ["", "## Finding Types", ""]
    for key, value in (report.get("finding_counts") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines += ["", "## Error And Warning Sample", ""]
    sample = [item for item in findings if item.get("severity") in {"error", "warning"}]
    if sample:
        for item in sample[:80]:
            lines.append(
                f"- `{item.get('severity')}` `{item.get('finding')}` | {item.get('asset_domain')} | "
                f"{item.get('entity_name') or item.get('entity_id')} | `{item.get('asset_path')}` | "
                f"{item.get('recommended_next_step')}"
            )
        if len(sample) > 80:
            lines.append(f"- ...and {len(sample) - 80} more error/warning findings in the CSV.")
    else:
        lines.append("- None")
    lines += ["", "## Focused Decision Packets", ""]
    packet_sample = [item for item in findings if item.get("severity") in {"error", "warning"}]
    if packet_sample:
        for item in packet_sample[:80]:
            lines.append(
                f"- `{item.get('default_operator_decision')}` | `{item.get('decision_lane')}` | "
                f"{item.get('decision_packet_title') or item.get('entity_name') or item.get('entity_id')} | readiness=`{item.get('asset_readiness')}` | "
                f"source=`{item.get('source_confidence')}` | identity=`{item.get('identity_confidence')}` | "
                f"copy=`{item.get('operator_copy_target')}` | action=`{item.get('decision_primary_action')}`"
            )
        if len(packet_sample) > 80:
            lines.append(f"- ...and {len(packet_sample) - 80} more decision packet rows in the CSV.")
    else:
        lines.append("- None")
    lines += ["", "## Renderer Availability Notes", ""]
    renderer = [item for item in findings if item.get("asset_domain") == "renderer"]
    if renderer:
        for item in renderer[:40]:
            lines.append(
                f"- `{item.get('severity')}` `{item.get('finding')}` | `{item.get('renderer_coverage')}` | "
                f"{item.get('entity_name') or item.get('entity_id')} | cue `{item.get('renderer_fallback_cue')}`"
            )
    else:
        lines.append("- No renderer fallback findings observed.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Build a review-only HSD asset availability audit.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--registry-root", default=str(DEFAULT_REGISTRY_ROOT))
    parser.add_argument("--template-mapping", default=str(DEFAULT_TEMPLATE_MAPPING))
    parser.add_argument("--verified-logo-registry", default=str(DEFAULT_VERIFIED_LOGO_REGISTRY))
    parser.add_argument("--renderer-logo-audit", default=str(DEFAULT_RENDERER_LOGO_AUDIT))
    parser.add_argument("--renderer-manifest", default=str(DEFAULT_RENDERER_MANIFEST))
    parser.add_argument("--asset-assurance-rows", default=str(DEFAULT_ASSET_ASSURANCE_ROWS))
    parser.add_argument("--csv", default=DEFAULT_OUT_CSV)
    parser.add_argument("--json", default=DEFAULT_OUT_JSON)
    parser.add_argument("--md", default=DEFAULT_OUT_MD)
    parser.add_argument("--strict", action="store_true", help="Exit nonzero when error findings are present.")
    args = parser.parse_args(argv)

    report = build_audit(
        Path(args.root),
        registry_root=Path(args.registry_root),
        template_mapping=Path(args.template_mapping),
        verified_logo_registry=Path(args.verified_logo_registry),
        renderer_logo_audit=Path(args.renderer_logo_audit),
        renderer_manifest=Path(args.renderer_manifest),
        asset_assurance_rows=Path(args.asset_assurance_rows),
    )
    csv_path = output_path(args.csv)
    json_path = output_path(args.json)
    md_path = output_path(args.md)
    write_run_csv(args.csv, report["findings"], AUDIT_FIELDS)
    write_json(args.json, report, indent=2, sort_keys=True)
    write_markdown(report, md_path)
    print(json.dumps({
        "version": VERSION,
        "review_only": True,
        "status": report["status"],
        "finding_count": report["finding_count"],
        "severity_counts": report["severity_counts"],
        "csv": csv_path.as_posix(),
        "json": json_path.as_posix(),
        "md": md_path.as_posix(),
    }, indent=2, sort_keys=True))
    if args.strict:
        return int(report["strict_exit_code"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
