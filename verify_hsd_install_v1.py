from __future__ import annotations

import hashlib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-install-verifier-v3.2.4-bebe-ops-v2.3"
EXPECTED_PIPELINE_VERSION = "v3.2.4-bebe-ops-v2.3"
MIN_SAFE_PIPELINE_PREFIXES = ("v3.2", "v3.3")

REQUIRED_FILES = [
    ".github/workflows/hsd-pipeline-control-v1.yml",
    "build_hsd_run_manifest_v1.py",
    "generate_hsd_results_contract_v1.py",
    "normalize_hsd_manual_story_inbox_v1.py",
    "ingest_hsd_discovery_sources_v1.py",
    "build_hsd_daily_slate_v1.py",
    "publish_hsd_guard_v1.py",
    "generate_hsd_operator_status_v1.py",
    "generate_hsd_pipeline_review_lite_v1.py",
    "generate_hsd_tonight_preview_bridge_v1.py",
    "generate_hsd_preview_quality_gate_v1.py",
    "generate_hsd_player_image_assets_v1.py",
    "generate_hsd_graphics_upload_pack_v1.py",
    "generate_hsd_graphics_qa_v1.py",
    "generate_hsd_rendered_slide_qa_v1.py",
    "generate_hsd_bebe_daily_ops_plan_v2.py",
    "generate_hsd_source_registry_audit_v2.py",
    "generate_hsd_operator_command_center_v2.py",
    "validate_hsd_contracts_v1.py",
    "config/pipeline_version.json",
    "config/daily_slate.json",
    "config/source_registry.json",
    "config/hsd_daily_cadence_v2.json",
    "config/hsd_priority_sports_14d_v2.json",
    "config/hsd_platform_policy_v2.json",
    "config/graphics_rendered_qa_policy_v2.json",
    "config/preview_focus_map.json",
]

OPTIONAL_TEMPLATE_FILES = [
    "operator/inbox/story_inbox_template_v2.csv",
    "config/hsd_release_version.json",
    ".github/workflows/hsd-production-controller-v3-2-4-bebe-v2-3.yml",
]

MANUAL_ONLY_WORKFLOW_MARKERS = ["workflow_dispatch"]
UNSAFE_WORKFLOW_MARKERS = ["workflow_run", "\npush:", "\nschedule:", "pull_request:"]

STALE_FILES = [
    "pipeline_stop_reason.md", "pipeline_outcome.md", "pipeline_publish_warning.md",
    "operator_status.md", "operator_status.json", "operator_status.csv",
    "publish_guard_report.md", "publish_guard_report.json",
    "contract_validation_report.md", "contract_validation_manifest.json",
    "results_contract_v2.csv", "results_contract_v2.jsonl", "results_contract_report.md",
    "story_candidates_manual.csv", "story_candidates_manual.jsonl", "manual_story_inbox_report.md",
    "story_candidates_discovery.csv", "story_candidates_discovery.jsonl", "discovery_sources_report.md",
    "daily_slate_plan.csv", "daily_slate_plan.md",
    "latest_results_run_summary.md", "latest_news_sync_run_summary.md", "news_fact_packets.csv",
    "studio_bundle_queue.csv", "studio_graphics_queue.csv", "studio_bundle_packets.md", "studio_bundle_prompts.md",
    "studio_fresh_packet_report.md", "studio_freshness_gate.csv", "studio_freshness_report.md", "studio_stale_packet_queue.csv",
    "studio_preview_build_v2_report.md", "studio_preview_build_v2.json", "preview_player_focus.csv",
    "preview_bundle_quality.csv", "preview_bundle_quality.md", "preview_bundle_quality_summary.csv",
    "source_registry_audit.csv", "source_registry_audit.md", "source_registry_audit.json",
    "bebe_daily_ops_plan.md", "bebe_daily_ops_plan.csv", "bebe_daily_ops_status.json", "bebe_priority_board.md", "bebe_posting_schedule_today.md",
    "operator_command_center.html", "operator_command_center.md", "operator_command_center.json",
    "approved_graphics_assets.csv", "approved_graphics_assets.json", "asset_candidates_review.md",
    "player_assets.csv", "player_assets.json", "player_image_candidates.csv", "player_image_sourcing_report.md", "player_image_requirements.csv", "player_image_fit_report.md", "player_image_fit_gate.csv",
    "graphics_upload_pack_status.csv", "graphics_upload_pack_status.json", "graphics_chat_direct_handoff.md", "graphics_chat_upload_instructions.md", "graphics_chat_upload_manifest.csv", "graphics_chat_upload_manifest.json",
    "graphics_qa_report.md", "graphics_qa_results.csv", "graphics_qa_manifest.json",
    "graphics_prompt_clean_report.md", "graphics_prompt_clean_manifest.json", "graphics_banned_language.csv", "graphics_copy_style_guide.md", "graphics_display_copy.csv", "graphics_asset_usage_map.csv", "graphics_layout_blueprint.csv",
    "rendered_slide_qa.csv", "rendered_slide_qa_report.md", "rendered_slide_qa_manifest.json", "rendered_graphics_manual_review_template.csv",
    "hsd_current_run.json", "hsd_pipeline_lite_review.zip",
]

STALE_DIRS = [
    "hsd_pipeline_lite_review", "graphics_chat_upload_pack", "graphics_chat_upload_pack_zips", "graphics_clean_prompts", "graphics_qa_dashboard", "generated_graphics",
]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes())
        return h.hexdigest()
    except Exception:
        return ""


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def remove_stale_generated_state() -> Dict[str, int]:
    removed_files = 0
    removed_dirs = 0
    for name in STALE_FILES:
        p = Path(name)
        try:
            if p.exists() and p.is_file():
                p.unlink()
                removed_files += 1
        except Exception:
            pass
    for name in STALE_DIRS:
        p = Path(name)
        try:
            if p.exists() and p.is_dir():
                shutil.rmtree(p)
                removed_dirs += 1
        except Exception:
            pass
    return {"files": removed_files, "dirs": removed_dirs}


def validate_registry(issues: List[str], warnings: List[str]) -> None:
    registry = read_json("config/source_registry.json")
    sources = registry.get("sources", [])
    if not isinstance(sources, list) or not sources:
        issues.append("config/source_registry.json has no sources list")
        return
    source_ids = set()
    green = 0
    for idx, src in enumerate(sources):
        if not isinstance(src, dict):
            issues.append(f"source_registry source index {idx} is not an object")
            continue
        sid = clean(src.get("source_id"))
        band = clean(src.get("trust_band") or src.get("tier")).lower()
        if not sid:
            issues.append(f"source_registry source index {idx} missing source_id")
        elif sid in source_ids:
            issues.append(f"source_registry duplicate source_id: {sid}")
        source_ids.add(sid)
        if band in {"green", "official", "primary", "operator"}:
            green += 1
        if band == "red" and src.get("enabled"):
            issues.append(f"red/prohibited source is enabled: {sid}")
    if green < 3:
        warnings.append("source registry has fewer than 3 green/official sources; discovery may be thin")


def inspect_workflow(path: Path, issues: List[str], warnings: List[str], hashes: Dict[str, str]) -> None:
    if not path.exists():
        return
    hashes[path.as_posix()] = sha(path)
    txt = path.read_text(encoding="utf-8", errors="replace")
    for marker in MANUAL_ONLY_WORKFLOW_MARKERS:
        if marker not in txt:
            issues.append(f"{path}: missing manual trigger marker: {marker}")
    for marker in UNSAFE_WORKFLOW_MARKERS:
        if marker in txt:
            issues.append(f"{path}: has unsafe auto trigger marker: {marker.strip()}")
    if "HSD_PUBLISH_OUTPUTS" not in txt or "artifact_only" not in txt:
        warnings.append(f"{path}: may not be locked to artifact-first publish mode")
    if "HSD_ALLOW_PREVIEW_PLAYER_IMAGES" not in txt:
        warnings.append(f"{path}: preview player-image mode env is missing")
    if "generate_hsd_bebe_daily_ops_plan_v2.py" not in txt:
        issues.append(f"{path}: does not run BeBe daily ops plan")
    if "STRICT FRESHNESS GATE" not in txt:
        warnings.append(f"{path}: GitHub UI still has old strict_freshness label. Safe to run, but copy the hidden .github workflow to fix the display.")
    if EXPECTED_PIPELINE_VERSION not in txt and "v3.2.4" not in txt:
        warnings.append(f"{path}: visible workflow name/artifact name does not show {EXPECTED_PIPELINE_VERSION}; copy the hidden .github workflow to fix GitHub display.")
    if "${{ github.run_number }}" not in txt:
        warnings.append(f"{path}: artifact/run name does not include github.run_number; GitHub artifact names may remain confusing")


def main() -> None:
    cleanup = remove_stale_generated_state()
    issues: List[str] = []
    warnings: List[str] = []
    hashes: Dict[str, str] = {}

    for name in REQUIRED_FILES:
        p = Path(name)
        if not p.exists():
            issues.append(f"missing required file: {name}")
        else:
            hashes[name] = sha(p)

    for name in OPTIONAL_TEMPLATE_FILES:
        p = Path(name)
        if not p.exists():
            warnings.append(f"optional/version helper missing: {name}")
        else:
            hashes[name] = sha(p)

    pv = read_json("config/pipeline_version.json")
    pipeline_version = clean(pv.get("pipeline_version"))
    version_status = "pass" if pipeline_version == EXPECTED_PIPELINE_VERSION else "warning"
    if pipeline_version != EXPECTED_PIPELINE_VERSION:
        if not pipeline_version.startswith(MIN_SAFE_PIPELINE_PREFIXES):
            issues.append(f"pipeline_version too old or missing: {pipeline_version!r}; expected {EXPECTED_PIPELINE_VERSION!r}")
        else:
            warnings.append(f"pipeline_version mismatch: {pipeline_version!r}; expected {EXPECTED_PIPELINE_VERSION!r}. This no longer blocks the run; update config/pipeline_version.json for cleaner GitHub/operator display.")

    inspect_workflow(Path(".github/workflows/hsd-pipeline-control-v1.yml"), issues, warnings, hashes)
    inspect_workflow(Path(".github/workflows/hsd-production-controller-v3-2-4-bebe-v2-3.yml"), issues, warnings, hashes)

    review_gen = Path("generate_hsd_pipeline_review_lite_v1.py")
    if review_gen.exists():
        rt = review_gen.read_text(encoding="utf-8", errors="replace")
        if "include_ready_upload_packs" not in rt or "graphics_chat_upload_pack_zips" not in rt:
            issues.append("lite review generator does not include graphics upload pack ZIP safety net")

    validate_registry(issues, warnings)

    report = {
        "version": VERSION,
        "expected_pipeline_version": EXPECTED_PIPELINE_VERSION,
        "installed_pipeline_version": pipeline_version,
        "version_status": version_status,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "preflight_cleanup": cleanup,
        "issues": issues,
        "warnings": warnings,
        "hashes": hashes,
    }
    Path("install_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# HSD Install Verification",
        "",
        f"Verifier: {VERSION}",
        f"Expected pipeline version: `{EXPECTED_PIPELINE_VERSION}`",
        f"Installed pipeline version: `{pipeline_version or 'missing'}`",
        f"Generated: {report['generated_at_utc']}",
        "",
        f"- issues: {len(issues)}",
        f"- warnings: {len(warnings)}",
        f"- version status: {version_status}",
        f"- stale files removed before run: {cleanup['files']}",
        f"- stale directories removed before run: {cleanup['dirs']}",
        "",
    ]
    if issues:
        lines += ["## Issues", "", *[f"- {x}" for x in issues], ""]
    if warnings:
        lines += ["## Warnings", "", *[f"- {x}" for x in warnings], ""]
    if not issues:
        lines.append("Install verification passed for safe execution. Version/display mismatches are warnings, not blockers, in BeBe Ops v2.3.")
    Path("install_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"issues": len(issues), "warnings": len(warnings), "version_status": version_status, "preflight_cleanup": cleanup}, indent=2))
    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
