from __future__ import annotations

import csv
import json
import os
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-pipeline-review-lite-v3.2.10-bebe-ops-v2.9"
OUT_DIR = Path("hsd_pipeline_lite_review")
OUT_ZIP = Path("hsd_pipeline_lite_review.zip")
MAX_UPLOAD_PACK_BYTES = int(os.environ.get("HSD_LITE_REVIEW_MAX_UPLOAD_PACK_BYTES", "100000000"))

KEY_FILES = [
    "operator_status.md", "operator_status.json", "operator_status.csv",
    "publish_guard_report.md", "publish_guard_report.json",
    "install_report.md", "install_report.json", "config/hsd_release_version.json", "config/pipeline_version.json", "contract_validation_report.md", "pipeline_outcome.md", "pipeline_stop_reason.md",
    "results_contract_report.md", "results_contract_v2.csv", "manual_story_inbox_report.md", "story_candidates_manual.csv",
    "discovery_sources_report.md", "story_candidates_discovery.csv", "daily_slate_plan.md", "daily_slate_plan.csv", "daily_slate_guard_report.md",
    "latest_results_run_summary.md", "news_fact_packets.csv", "latest_news_sync_run_summary.md",
    "studio_bundle_queue.csv", "studio_bundle_packets.md", "studio_bundle_prompts.md", "studio_fresh_packet_report.md",
    "studio_preview_build_v2_report.md", "studio_preview_build_v2.json", "preview_player_focus.csv",
    "preview_bundle_quality.csv", "preview_bundle_quality.md", "preview_bundle_quality_summary.csv",
    "source_registry_audit.csv", "source_registry_audit.md", "source_registry_audit.json",
    "bebe_daily_ops_plan.md", "bebe_daily_ops_plan.csv", "bebe_daily_ops_status.json", "bebe_priority_board.md", "bebe_posting_schedule_today.md",
    "operator_command_center.html", "operator_command_center.md", "operator_command_center.json",
    "graphics_upload_pack_status.csv", "graphics_upload_pack_status.json", "graphics_chat_direct_handoff.md", "graphics_chat_upload_instructions.md",
    "graphics_qa_report.md", "graphics_qa_results.csv", "graphics_qa_manifest.json",
    "graphics_prompt_clean_report.md", "graphics_prompt_clean_manifest.json", "graphics_banned_language.csv",
    "exact_asset_audit.csv", "exact_asset_audit_report.md", "exact_asset_audit_manifest.json",
    "graphics_copy_style_guide.md", "graphics_display_copy.csv", "graphics_asset_usage_map.csv", "graphics_layout_blueprint.csv",
    "player_image_sourcing_report.md", "player_image_requirements.csv", "player_image_fit_report.md", "player_image_fit_gate.csv",
    "asset_candidates_review.md", "approved_graphics_assets.csv", "graphics_chat_upload_manifest.csv", "graphics_chat_upload_manifest.json",
    "config/hsd_exact_asset_policy_v1.json", "config/hsd_verified_logo_registry_v1.json",
    "rendered_slide_qa.csv", "rendered_slide_qa_report.md", "rendered_slide_qa_manifest.json", "rendered_graphics_manual_review_template.csv",
]


def row_count(path: str) -> int:
    p = Path(path)
    if not p.exists():
        return 0
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in csv.DictReader(f))
    except Exception:
        return 0


def copy_if_exists(name: str, files_dir: Path, manifest: List[Dict[str, Any]]) -> None:
    p = Path(name)
    if not p.exists() or not p.is_file():
        return
    dest = files_dir / p.name
    shutil.copy2(p, dest)
    manifest.append({"path": name, "included_as": dest.as_posix(), "size": p.stat().st_size})


def safe_copy_tree_files(src_dir: Path, dest_dir: Path, manifest: List[Dict[str, Any]], max_file_bytes: int = MAX_UPLOAD_PACK_BYTES) -> int:
    if not src_dir.exists():
        return 0
    count = 0
    for p in src_dir.rglob("*"):
        if not p.is_file():
            continue
        if p.stat().st_size > max_file_bytes:
            continue
        rel = p.relative_to(src_dir)
        dest = dest_dir / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        manifest.append({"path": p.as_posix(), "included_as": dest.as_posix(), "size": p.stat().st_size})
        count += 1
    return count


def include_ready_upload_packs(ready_dir: Path, manifest: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    ready_dir.mkdir(parents=True, exist_ok=True)
    ready_packs: List[Dict[str, Any]] = []
    seen: set[str] = set()
    status = Path("graphics_upload_pack_status.csv")
    if status.exists():
        with status.open(newline="", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                if r.get("upload_pack_status") not in {"ready", "ready_with_review"}:
                    continue
                p = Path(r.get("zip_path", ""))
                if not p.exists():
                    ready_packs.append({
                        "bundle_name": r.get("bundle_name"),
                        "zip": p.as_posix(),
                        "status": r.get("upload_pack_status"),
                        "included": False,
                        "reason": "zip path not found at review artifact time",
                    })
                    continue
                size = p.stat().st_size
                if size > MAX_UPLOAD_PACK_BYTES:
                    ready_packs.append({
                        "bundle_name": r.get("bundle_name"),
                        "zip": p.as_posix(),
                        "status": r.get("upload_pack_status"),
                        "included": False,
                        "size": size,
                        "reason": f"zip larger than {MAX_UPLOAD_PACK_BYTES} bytes",
                    })
                    continue
                dest = ready_dir / p.name
                shutil.copy2(p, dest)
                seen.add(p.resolve().as_posix())
                manifest.append({"path": p.as_posix(), "included_as": dest.as_posix(), "size": size})
                ready_packs.append({
                    "bundle_name": r.get("bundle_name"),
                    "zip": dest.as_posix(),
                    "status": r.get("upload_pack_status"),
                    "included": True,
                    "size": size,
                })
    # Safety net: include any zip files even if status CSV path had a mismatch.
    zip_dir = Path("graphics_chat_upload_pack_zips")
    if zip_dir.exists():
        for p in zip_dir.glob("*.zip"):
            if p.resolve().as_posix() in seen:
                continue
            size = p.stat().st_size
            if size > MAX_UPLOAD_PACK_BYTES:
                continue
            dest = ready_dir / p.name
            shutil.copy2(p, dest)
            manifest.append({"path": p.as_posix(), "included_as": dest.as_posix(), "size": size})
            ready_packs.append({"bundle_name": p.stem, "zip": dest.as_posix(), "status": "found_zip", "included": True, "size": size})
    return ready_packs


def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()

    files_dir = OUT_DIR / "files"
    ready_dir = OUT_DIR / "ready_upload_packs"
    pack_dir = OUT_DIR / "graphics_chat_upload_pack"
    files_dir.mkdir(parents=True)
    ready_dir.mkdir(parents=True)

    manifest: List[Dict[str, Any]] = []
    for name in KEY_FILES:
        copy_if_exists(name, files_dir, manifest)

    ready_packs = include_ready_upload_packs(ready_dir, manifest)
    pack_file_count = safe_copy_tree_files(Path("graphics_chat_upload_pack"), pack_dir, manifest, max_file_bytes=MAX_UPLOAD_PACK_BYTES)

    counts = {
        "results_contract_rows": row_count("results_contract_v2.csv"),
        "manual_story_candidates": row_count("story_candidates_manual.csv"),
        "discovery_candidates": row_count("story_candidates_discovery.csv"),
        "slate_items": row_count("daily_slate_plan.csv"),
        "upload_pack_rows": row_count("graphics_upload_pack_status.csv"),
        "ready_packs_included": sum(1 for p in ready_packs if p.get("included")),
        "graphics_upload_pack_files_included": pack_file_count,
    }
    status_json = {
        "version": VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "counts": counts,
        "ready_packs": ready_packs,
        "max_upload_pack_bytes": MAX_UPLOAD_PACK_BYTES,
    }
    (OUT_DIR / "pipeline_status.json").write_text(json.dumps(status_json, indent=2), encoding="utf-8")
    (OUT_DIR / "lite_manifest.csv").write_text(
        "path,included_as,size\n" + "\n".join(f"{m['path']},{m['included_as']},{m['size']}" for m in manifest) + "\n",
        encoding="utf-8",
    )
    (OUT_DIR / "README.md").write_text(
        "# HSD Pipeline Lite Review\n\n"
        "This lite review includes BeBe status files plus ready graphics upload packs when available.\n\n"
        + json.dumps(status_json, indent=2)
        + "\n",
        encoding="utf-8",
    )
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in OUT_DIR.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(OUT_DIR.parent))
    print(json.dumps({"zip": OUT_ZIP.as_posix(), **counts}, indent=2))


if __name__ == "__main__":
    main()
