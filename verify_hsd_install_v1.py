from __future__ import annotations

import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-install-verifier-v3.2.2-bebe-ops-v2.1"
EXPECTED_PIPELINE_VERSION = "v3.2.2-bebe-ops-v2.1"

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
]

MANUAL_ONLY_WORKFLOW_MARKERS = ["workflow_dispatch"]
UNSAFE_WORKFLOW_MARKERS = ["workflow_run", "\npush:", "\nschedule:", "pull_request:"]


def sha(path: Path) -> str:
    h = hashlib.sha256()
    try:
        h.update(path.read_bytes())
        return h.hexdigest()
    except Exception:
        return ""


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def issue_if(condition: bool, issues: List[str], message: str) -> None:
    if condition:
        issues.append(message)


def validate_registry(issues: List[str]) -> None:
    registry = read_json("config/source_registry.json")
    sources = registry.get("sources", [])
    issue_if(not isinstance(sources, list) or not sources, issues, "config/source_registry.json has no sources list")
    source_ids = set()
    for idx, src in enumerate(sources):
        if not isinstance(src, dict):
            issues.append(f"source_registry source index {idx} is not an object")
            continue
        sid = str(src.get("source_id") or "").strip()
        if not sid:
            issues.append(f"source_registry source index {idx} missing source_id")
        elif sid in source_ids:
            issues.append(f"source_registry duplicate source_id: {sid}")
        source_ids.add(sid)
        if str(src.get("trust_band") or src.get("tier") or "").strip().lower() == "red" and src.get("enabled"):
            issues.append(f"red/prohibited source is enabled: {sid}")


def main() -> None:
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
            warnings.append(f"optional template missing: {name}")
        else:
            hashes[name] = sha(p)

    pv = read_json("config/pipeline_version.json")
    version = pv.get("pipeline_version")
    if version != EXPECTED_PIPELINE_VERSION:
        issues.append(f"pipeline_version mismatch: {version!r}; expected {EXPECTED_PIPELINE_VERSION!r}")

    wf = Path(".github/workflows/hsd-pipeline-control-v1.yml")
    if wf.exists():
        txt = wf.read_text(encoding="utf-8", errors="replace")
        for marker in MANUAL_ONLY_WORKFLOW_MARKERS:
            if marker not in txt:
                issues.append(f"controller workflow missing manual trigger marker: {marker}")
        for marker in UNSAFE_WORKFLOW_MARKERS:
            if marker in txt:
                issues.append(f"controller workflow has unsafe auto trigger marker: {marker.strip()}")
        if "HSD_PUBLISH_OUTPUTS" not in txt or "artifact_only" not in txt:
            warnings.append("controller workflow may not be locked to artifact-first publish mode")
        if "HSD_ALLOW_PREVIEW_PLAYER_IMAGES" not in txt:
            warnings.append("preview player-image mode env is missing")
        if "generate_hsd_bebe_daily_ops_plan_v2.py" not in txt:
            issues.append("controller workflow does not run BeBe daily ops plan")
        if "STRICT FRESHNESS GATE" not in txt:
            warnings.append("strict_freshness input exists but is not labeled with the BeBe v2.1 wording")
        if "graphics_chat_upload_pack_zips/**/*.zip" not in txt:
            issues.append("controller workflow does not upload graphics pack ZIPs in lite artifact")

    validate_registry(issues)

    report = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "issues": issues,
        "warnings": warnings,
        "hashes": hashes,
    }
    Path("install_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")

    lines = [
        "# HSD Install Verification",
        "",
        f"Version: {VERSION}",
        f"Generated: {report['generated_at_utc']}",
        "",
        f"- issues: {len(issues)}",
        f"- warnings: {len(warnings)}",
        "",
    ]
    if issues:
        lines += ["## Issues", "", *[f"- {x}" for x in issues], ""]
    if warnings:
        lines += ["## Warnings", "", *[f"- {x}" for x in warnings], ""]
    if not issues:
        lines.append("Install verification passed for BeBe Ops v2.1 / v3.2.2.")
    Path("install_report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps({"issues": len(issues), "warnings": len(warnings)}, indent=2))
    if issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
