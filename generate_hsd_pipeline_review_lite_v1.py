from __future__ import annotations

import csv
import json
import os
import shutil
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from hsd_run_io import input_path, output_path

VERSION = "hsd-pipeline-review-lite-v3.8.0-results-v5-multisport-review"
OUT_DIR = output_path("hsd_pipeline_lite_review")
OUT_ZIP = output_path("hsd_pipeline_lite_review.zip")
MAX_UPLOAD_PACK_BYTES = int(os.environ.get("HSD_LITE_REVIEW_MAX_UPLOAD_PACK_BYTES", "100000000"))

V3_PREREQ_COMMANDS = [
    ["scripts/generate_hsd_mermaid_production_graphics_director_v4_5.py"],
    ["scripts/generate_hsd_graphics_variant_packs_v1.py"],
    ["scripts/report_hsd_repo_state_v3.py"],
]

KEY_FILES = [
    "repo_state_v3.md", "repo_state_v3.json",
    "results_desk_v5_manifest.json", "results_desk_v5_report.md", "source_accuracy_v5.json", "source_accuracy_v5.md",
    "expected_games_v5_manifest.json", "expected_games_v5_report.md", "config/hsd_expected_games_v5.csv",
    "independent_schedule_verification_v5.csv", "independent_schedule_verification_v5.json", "independent_schedule_verification_v5.md",
    "multisport_results_observations_v5.csv", "multisport_results_modules_v5.json", "multisport_results_modules_v5.md",
    "operator_status.md", "operator_status.json", "operator_status.csv",
    "publish_guard_report.md", "publish_guard_report.json",
    "install_report.md", "install_report.json", "contract_validation_report.md", "pipeline_outcome.md", "pipeline_stop_reason.md",
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
    "rendered_slide_qa.csv", "rendered_slide_qa_report.md", "rendered_slide_qa_manifest.json", "rendered_graphics_manual_review_template.csv",
    "manual_workflow_content_packets.jsonl", "manual_workflow_content_packets.csv", "manual_workflow_render_plans.json",
    "manual_workflow_copy_desk.md", "manual_workflow_threads_copy.md", "manual_workflow_first_comments.md",
    "manual_workflow_priority_report.md", "manual_workflow_pack_status.csv", "manual_workflow_pack_status.json", "manual_workflow_handoff.md",
    "ig_story_results_queue.csv", "ig_story_results_frames.md", "ig_story_results_graphics_prompt.md",
    "ig_story_results_upload_pack_status.csv", "ig_story_results_upload_pack_status.json", "ig_story_results_upload_manifest.csv",
    "final_score_story_guard_report.md", "final_score_story_guard_report.json",
    "ig_story_caption_bank.md", "ig_story_poll_stickers.md", "ig_story_player_image_candidates.csv",
    "outputs/latest/review_files/athlete_image_match_review.csv",
    "outputs/latest/review_files/athlete_image_match_review_report.md",
    "outputs/latest/review_files/athlete_image_approval_pack/approval_decisions.csv",
    "outputs/latest/review_files/athlete_image_approval_pack/download_manifest.csv",
    "outputs/latest/review_files/athlete_image_approval_pack/athlete_image_approval_pack_report.md",
    "outputs/latest/review_files/athlete_image_approval_pack/athlete_image_approval_pack_manifest.json",
    "outputs/latest/production_graphics_director/production_graphics_director_report.md",
    "outputs/latest/production_graphics_director/production_graphics_director_manifest.json",
    "outputs/latest/production_graphics_director/postable_export_manifest.csv",
    "outputs/latest/production_graphics_director/copy_director/post_ready_copy.md",
    "outputs/latest/production_graphics_director/graphics_variant_packs/variant_manifest.csv",
    "outputs/latest/production_graphics_director/graphics_variant_packs/variant_pack_report.md",
    "outputs/latest/production_graphics_director/graphics_variant_packs/variant_pack_report.json",
]


def row_count(path: str) -> int:
    p = input_path(path)
    if not p.exists():
        return 0
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in csv.DictReader(f))
    except Exception:
        return 0


def file_exists(path: str) -> bool:
    return input_path(path).is_file()


def dir_exists(path: str) -> bool:
    return input_path(path).is_dir()


def count_files(path: str, pattern: str = "*") -> int:
    p = input_path(path)
    if not p.exists():
        return 0
    return sum(1 for item in p.glob(pattern) if item.is_file())


def run_optional_script(script_path: str, extra_args: Optional[List[str]] = None, timeout: int = 600) -> Dict[str, Any]:
    script = Path(script_path)
    command = [sys.executable, script.as_posix(), *(extra_args or [])]
    if not script.exists():
        return {"script": script_path, "status": "missing", "returncode": 127, "stdout_tail": "", "stderr_tail": ""}
    try:
        proc = subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout, check=False)
        return {"script": script_path, "status": "ok" if proc.returncode == 0 else "error", "returncode": proc.returncode, "stdout_tail": proc.stdout[-2000:], "stderr_tail": proc.stderr[-2000:]}
    except subprocess.TimeoutExpired as exc:
        return {"script": script_path, "status": "timeout", "returncode": None, "stdout_tail": (exc.stdout or "")[-2000:] if isinstance(exc.stdout, str) else "", "stderr_tail": (exc.stderr or "")[-2000:] if isinstance(exc.stderr, str) else ""}
    except Exception as exc:
        return {"script": script_path, "status": "exception", "returncode": None, "stdout_tail": "", "stderr_tail": f"{type(exc).__name__}: {exc}"}


def run_v3_prereqs() -> List[Dict[str, Any]]:
    return [run_optional_script(command[0], command[1:]) for command in V3_PREREQ_COMMANDS]


def copy_if_exists(name: str, files_dir: Path, manifest: List[Dict[str, Any]]) -> None:
    p = input_path(name)
    if not p.exists() or not p.is_file():
        return
    dest = files_dir / p.name
    shutil.copy2(p, dest)
    manifest.append({"path": name, "included_as": dest.as_posix(), "size": p.stat().st_size})


def safe_copy_tree_files(src_dir: Path, dest_dir: Path, manifest: List[Dict[str, Any]], max_file_bytes: int = MAX_UPLOAD_PACK_BYTES) -> int:
    src_dir = input_path(src_dir)
    if not src_dir.exists():
        return 0
    count = 0
    for p in src_dir.rglob("*"):
        if not p.is_file() or p.stat().st_size > max_file_bytes:
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
    status = input_path("graphics_upload_pack_status.csv")
    if status.exists():
        with status.open(newline="", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                if r.get("upload_pack_status") not in {"ready", "ready_with_review"}:
                    continue
                zip_path = r.get("zip_path", "")
                if not zip_path:
                    ready_packs.append({"bundle_name": r.get("bundle_name"), "zip": "", "status": r.get("upload_pack_status"), "included": False, "reason": "zip path not found"})
                    continue
                p = input_path(zip_path)
                if not p.exists():
                    ready_packs.append({"bundle_name": r.get("bundle_name"), "zip": p.as_posix(), "status": r.get("upload_pack_status"), "included": False, "reason": "zip path not found"})
                    continue
                size = p.stat().st_size
                if size > MAX_UPLOAD_PACK_BYTES:
                    ready_packs.append({"bundle_name": r.get("bundle_name"), "zip": p.as_posix(), "status": r.get("upload_pack_status"), "included": False, "size": size, "reason": "zip too large"})
                    continue
                dest = ready_dir / p.name
                shutil.copy2(p, dest)
                seen.add(p.resolve().as_posix())
                manifest.append({"path": p.as_posix(), "included_as": dest.as_posix(), "size": size})
                ready_packs.append({"bundle_name": r.get("bundle_name"), "zip": dest.as_posix(), "status": r.get("upload_pack_status"), "included": True, "size": size})
    zip_dir = input_path("graphics_chat_upload_pack_zips")
    if zip_dir.exists():
        for p in zip_dir.glob("*.zip"):
            if p.resolve().as_posix() in seen or p.stat().st_size > MAX_UPLOAD_PACK_BYTES:
                continue
            dest = ready_dir / p.name
            shutil.copy2(p, dest)
            manifest.append({"path": p.as_posix(), "included_as": dest.as_posix(), "size": p.stat().st_size})
            ready_packs.append({"bundle_name": p.stem, "zip": dest.as_posix(), "status": "found_zip", "included": True, "size": p.stat().st_size})
    return ready_packs


def main() -> None:
    v3_prereqs = run_v3_prereqs()
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
    manual_workflow_dir = OUT_DIR / "manual_workflow_handoff_packs"
    manual_workflow_pack_count = 0
    src_manual_zips = input_path("manual_workflow_handoff_packs")
    if src_manual_zips.exists():
        manual_workflow_dir.mkdir(parents=True, exist_ok=True)
        for p in src_manual_zips.glob("*.zip"):
            if p.stat().st_size <= MAX_UPLOAD_PACK_BYTES:
                dest = manual_workflow_dir / p.name
                shutil.copy2(p, dest)
                manifest.append({"path": p.as_posix(), "included_as": dest.as_posix(), "size": p.stat().st_size})
                manual_workflow_pack_count += 1
    pack_file_count = safe_copy_tree_files(Path("graphics_chat_upload_pack"), pack_dir, manifest)
    story_ready_dir = OUT_DIR / "ig_story_results_ready_upload_packs"
    story_ready_dir.mkdir(parents=True, exist_ok=True)
    story_ready_packs = []
    story_zip_dir = input_path("ig_story_results_upload_pack_zips")
    if story_zip_dir.exists():
        for p in sorted(story_zip_dir.glob("*.zip")):
            if p.stat().st_size > MAX_UPLOAD_PACK_BYTES:
                story_ready_packs.append({"zip": p.as_posix(), "included": False, "reason": "zip too large", "size": p.stat().st_size})
                continue
            dest = story_ready_dir / p.name
            shutil.copy2(p, dest)
            manifest.append({"path": p.as_posix(), "included_as": dest.as_posix(), "size": p.stat().st_size})
            story_ready_packs.append({"zip": dest.as_posix(), "included": True, "size": p.stat().st_size})
    story_pack_file_count = safe_copy_tree_files(Path("ig_story_results_upload_pack"), OUT_DIR / "ig_story_results_upload_pack", manifest)
    athlete_approval_file_count = safe_copy_tree_files(Path("outputs/latest/review_files/athlete_image_approval_pack"), OUT_DIR / "athlete_image_approval_pack", manifest)
    athlete_smoke_file_count = safe_copy_tree_files(Path("outputs/latest/review_files/athlete_smoke_test"), OUT_DIR / "athlete_smoke_test", manifest)
    production_director_file_count = safe_copy_tree_files(Path("outputs/latest/production_graphics_director"), OUT_DIR / "production_graphics_director", manifest)
    postable_graphics_file_count = safe_copy_tree_files(Path("outputs/latest/POSTABLE_GRAPHICS"), OUT_DIR / "POSTABLE_GRAPHICS", manifest)
    counts = {
        "results_contract_rows": row_count("results_contract_v2.csv"),
        "manual_story_candidates": row_count("story_candidates_manual.csv"),
        "discovery_candidates": row_count("story_candidates_discovery.csv"),
        "slate_items": row_count("daily_slate_plan.csv"),
        "multisport_observations": row_count("multisport_results_observations_v5.csv"),
        "upload_pack_rows": row_count("graphics_upload_pack_status.csv"),
        "ready_packs_included": len([p for p in ready_packs if p.get("included")]),
        "graphics_upload_pack_files_included": pack_file_count,
        "manual_workflow_packs_included": manual_workflow_pack_count,
        "ig_story_results_ready_packs_included": len([p for p in story_ready_packs if p.get("included")]),
        "ig_story_results_upload_pack_files_included": story_pack_file_count,
        "athlete_image_approval_pack_files_included": athlete_approval_file_count,
        "athlete_smoke_test_files_included": athlete_smoke_file_count,
        "production_director_files_included": production_director_file_count,
        "postable_graphics_files_included": postable_graphics_file_count,
        "repo_state_v3_md_exists": file_exists("repo_state_v3.md"),
        "repo_state_v3_json_exists": file_exists("repo_state_v3.json"),
        "post_ready_copy_exists": file_exists("outputs/latest/production_graphics_director/copy_director/post_ready_copy.md"),
        "graphics_variant_zip_dir_exists": dir_exists("outputs/latest/production_graphics_director/graphics_variant_packs/zips"),
        "graphics_variant_zip_count": count_files("outputs/latest/production_graphics_director/graphics_variant_packs/zips", "*.zip"),
        "graphics_variant_manifest_rows": row_count("outputs/latest/production_graphics_director/graphics_variant_packs/variant_manifest.csv"),
    }
    status = {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "v3_prereqs": v3_prereqs, "counts": counts, "ready_packs": ready_packs, "ig_story_results_ready_packs": story_ready_packs, "files_included": manifest}
    (OUT_DIR / "pipeline_status.json").write_text(json.dumps(status, indent=2), encoding="utf-8")
    readme = [
        "# HSD Pipeline Review Lite",
        "",
        f"Generated: {status['generated_at_utc']}",
        f"Version: {VERSION}",
        "",
        "## Included",
        "",
        "- Critical pipeline reports and contracts.",
        "- Results Desk v5 source accuracy and expected-games files.",
        "- Multi-sport v5 review-only module outputs.",
        "- Production Graphics Director outputs and variant packs.",
        "- POSTABLE_GRAPHICS as human-review-only renders.",
        "- Ready upload pack zips when available and size-safe.",
        "",
        "Auto-renders remain human-review only. Paid-source dependencies remain optional/not allowed by default.",
    ]
    (OUT_DIR / "README.md").write_text("\n".join(readme) + "\n", encoding="utf-8")
    with zipfile.ZipFile(OUT_ZIP, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in OUT_DIR.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(OUT_DIR.parent).as_posix())
    print(json.dumps({"review_zip": OUT_ZIP.as_posix(), "counts": counts}, indent=2))


if __name__ == "__main__":
    main()
