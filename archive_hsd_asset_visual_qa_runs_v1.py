from __future__ import annotations
import csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

FILES = [
    "asset_manifest.csv", "asset_manifest.json", "team_assets.csv", "team_assets.json", "player_assets.csv", "player_assets.json",
    "asset_rights_review.csv", "approved_graphics_assets.csv", "approved_graphics_assets.json", "launch_integration_points.csv",
    "asset_source_seed_list.csv", "fact_warning_queue.csv", "player_image_requirements.csv", "player_image_candidates.csv",
    "player_image_sourcing_report.md", "graphics_production_specs.json", "graphics_slide_blueprints.md", "graphics_prompt_sanitizer_rules.md", "asset_candidates_review.md",
    "asset_desk_manifest.json", "brand_system", "studio_templates_v2", "studio_visual_upgrade_v2.md", "studio_bundle_prompts_v2.md",
    "studio_render_manifest_v2.json", "visual_upgrade_manifest.json", "visual_upgrade_dashboard/index.html", "graphics_qa_results.csv",
    "graphics_qa_report.md", "graphics_copy_style_guide.md", "graphics_display_copy.csv", "graphics_banned_language.csv", "graphics_language_manifest.json", "graphics_qa_manifest.json", "graphics_qa_dashboard/index.html", "graphics_clean_prompts", "graphics_prompt_clean_report.md", "studio_freshness_gate.csv", "studio_stale_packet_queue.csv", "studio_freshness_report.md", "studio_freshness_manifest.json", "player_image_fit_gate.csv", "player_image_fit_report.md", "player_image_fit_manifest.json", "rendered_slide_qa.csv", "rendered_slide_qa_report.md", "rendered_slide_qa_manifest.json", "graphics_prompt_clean_manifest.json", "graphics_chat_upload_pack",
    "graphics_chat_upload_pack_zips", "graphics_chat_upload_manifest.csv", "graphics_chat_upload_manifest.json", "graphics_upload_pack_status.csv", "graphics_upload_pack_status.json",
    "graphics_chat_upload_instructions.md", "graphics_chat_direct_handoff.md", "data/assets", "chatgpt_review_pack",
    "hsd_chatgpt_review_packet.md", "latest_asset_visual_qa_run_summary.md"
]

CHATGPT_REVIEW_FILES = [
    ("01_latest_asset_visual_qa_run_summary.md", "latest_asset_visual_qa_run_summary.md"),
    ("02_asset_desk_manifest.json", "asset_desk_manifest.json"),
    ("03_asset_candidates_review.md", "asset_candidates_review.md"),
    ("04_approved_graphics_assets.csv", "approved_graphics_assets.csv"),
    ("05_player_image_requirements.csv", "player_image_requirements.csv"),
    ("06_player_image_sourcing_report.md", "player_image_sourcing_report.md"),
    ("07_player_image_candidates.csv", "player_image_candidates.csv"),
    ("08_fact_warning_queue.csv", "fact_warning_queue.csv"),
    ("09_graphics_slide_blueprints.md", "graphics_slide_blueprints.md"),
    ("10_studio_bundle_prompts_v2.md", "studio_bundle_prompts_v2.md"),
    ("11_graphics_chat_upload_instructions.md", "graphics_chat_upload_instructions.md"),
    ("12_graphics_chat_upload_manifest.csv", "graphics_chat_upload_manifest.csv"),
    ("13_graphics_chat_direct_handoff.md", "graphics_chat_direct_handoff.md"),
    ("14_graphics_upload_pack_status.csv", "graphics_upload_pack_status.csv"),
    ("15_graphics_upload_pack_status.json", "graphics_upload_pack_status.json"),
    ("16_graphics_qa_report.md", "graphics_qa_report.md"),
    ("20_graphics_copy_style_guide.md", "graphics_copy_style_guide.md"),
    ("21_graphics_display_copy.csv", "graphics_display_copy.csv"),
    ("22_graphics_banned_language.csv", "graphics_banned_language.csv"),
    ("23_graphics_asset_usage_map.csv", "graphics_asset_usage_map.csv"),
    ("24_graphics_language_manifest.json", "graphics_language_manifest.json"),
    ("25_graphics_layout_blueprint.csv", "graphics_layout_blueprint.csv"),
    ("26_graphics_prompt_sanitizer_rules.md", "graphics_prompt_sanitizer_rules.md"),
    ("27_graphics_prompt_clean_report.md", "graphics_prompt_clean_report.md"),
    ("28_graphics_prompt_clean_manifest.json", "graphics_prompt_clean_manifest.json"),
    ("29_studio_freshness_report.md", "studio_freshness_report.md"),
    ("30_studio_freshness_gate.csv", "studio_freshness_gate.csv"),
    ("31_studio_stale_packet_queue.csv", "studio_stale_packet_queue.csv"),
    ("32_player_image_fit_report.md", "player_image_fit_report.md"),
    ("33_player_image_fit_gate.csv", "player_image_fit_gate.csv"),
    ("34_rendered_slide_qa_report.md", "rendered_slide_qa_report.md"),
    ("35_rendered_slide_qa.csv", "rendered_slide_qa.csv"),

    ("17_visual_upgrade_manifest.json", "visual_upgrade_manifest.json"),
    ("18_graphics_qa_manifest.json", "graphics_qa_manifest.json"),
]


def row_count(path: Path) -> int:
    if not path.exists() or path.suffix.lower() != ".csv":
        return 0
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return max(0, sum(1 for _ in csv.reader(f)) - 1)


def copy_any(src: Path, dstroot: Path) -> bool:
    if not src.exists():
        return False
    dst = dstroot / src
    dst.parent.mkdir(parents=True, exist_ok=True)
    if src.is_dir():
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(src, dst)
    else:
        shutil.copy2(src, dst)
    return True


def read_text_safe(path: str) -> str:
    p = Path(path)
    if not p.exists(): return ""
    return p.read_text(encoding="utf-8", errors="replace")


def create_review_pack() -> None:
    pack = Path("chatgpt_review_pack")
    if pack.exists(): shutil.rmtree(pack)
    pack.mkdir(parents=True, exist_ok=True)
    consolidated = [
        "# HSD ChatGPT Review Packet",
        "",
        "Upload this single file for review. The numbered files in `chatgpt_review_pack/` are included only for deeper debugging.",
        "",
    ]
    for out_name, src_name in CHATGPT_REVIEW_FILES:
        src = Path(src_name)
        if src.exists():
            shutil.copy2(src, pack / out_name)
        consolidated.append(f"## {src_name}")
        consolidated.append("")
        if not src.exists():
            consolidated.append("MISSING")
            consolidated.append("")
            continue
        text = read_text_safe(src_name)
        limit = 22000 if src.suffix.lower() in {".md", ".json"} else 16000
        if src.suffix.lower() == ".csv":
            consolidated.append("```csv")
            consolidated.append(text[:limit])
            if len(text) > limit: consolidated.append("...TRUNCATED...")
            consolidated.append("```")
        elif src.suffix.lower() == ".json":
            consolidated.append("```json")
            consolidated.append(text[:limit])
            if len(text) > limit: consolidated.append("...TRUNCATED...")
            consolidated.append("```")
        else:
            consolidated.append(text[:limit])
            if len(text) > limit: consolidated.append("\n...TRUNCATED...")
        consolidated.append("")
    Path("hsd_chatgpt_review_packet.md").write_text("\n".join(consolidated), encoding="utf-8")
    shutil.copy2("hsd_chatgpt_review_packet.md", pack / "00_hsd_chatgpt_review_packet.md")


def main() -> None:
    now = datetime.now(timezone.utc)
    date = now.strftime("%Y-%m-%d")
    tm = now.strftime("%H%M_UTC")
    stamp = now.strftime("%Y-%m-%d %H:%M:%S UTC")
    run = Path("asset_run_history") / date / tm
    latest = Path("asset_run_history") / "latest"
    run.mkdir(parents=True, exist_ok=True)
    latest.mkdir(parents=True, exist_ok=True)

    counts = {name: row_count(Path(name)) for name in FILES if name.endswith(".csv") and Path(name).exists()}
    summary = ["# HSD Asset Visual QA v1.8 Run Summary", "", f"Run timestamp UTC: `{stamp}`", f"Archive folder: `{run.as_posix()}`", "", "## Row counts", ""]
    for k, v in counts.items(): summary.append(f"- `{k}`: {v}")

    if Path("player_image_sourcing_report.md").exists():
        summary += ["", "## Player image sourcing", ""]
        lines = read_text_safe("player_image_sourcing_report.md").splitlines()
        for line in lines[:18]: summary.append(line)

    if Path("graphics_chat_upload_manifest.json").exists():
        try:
            obj = json.loads(read_text_safe("graphics_chat_upload_manifest.json"))
            c = obj.get("counts", {})
            summary += ["", "## Graphics chat upload pack", "", f"- bundles: {c.get('bundles', 0)}", f"- asset rows: {c.get('asset_rows', 0)}", f"- files created: {c.get('files_created', 0)}", f"- png preferred created: {c.get('png_preferred_created', 0)}", f"- upload packs ready: {c.get('upload_packs_ready', 0)}", f"- upload packs blocked: {c.get('upload_packs_blocked', 0)}"]
        except Exception:
            pass

    missing = []
    copied = []
    Path("latest_asset_visual_qa_run_summary.md").write_text("\n".join(summary) + "\n", encoding="utf-8")
    create_review_pack()

    for name in FILES:
        src = Path(name)
        if copy_any(src, run) and copy_any(src, latest): copied.append(name)
        else: missing.append(name)

    summary += ["", "## Missing optional files", ""] + [f"- `{m}`" for m in missing]
    text = "\n".join(summary) + "\n"
    Path("latest_asset_visual_qa_run_summary.md").write_text(text, encoding="utf-8")
    (run / "run_summary.md").write_text(text, encoding="utf-8")
    (latest / "run_summary.md").write_text(text, encoding="utf-8")
    manifest = {"run_timestamp_utc": stamp, "copied_files": copied, "missing_files": missing, "row_counts": counts}
    (run / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    (latest / "run_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    # Refresh review pack after the final summary includes missing files.
    create_review_pack()
    copy_any(Path("hsd_chatgpt_review_packet.md"), run)
    copy_any(Path("hsd_chatgpt_review_packet.md"), latest)
    copy_any(Path("chatgpt_review_pack"), run)
    copy_any(Path("chatgpt_review_pack"), latest)

    print("Archived HSD Asset Visual QA v1.8")


if __name__ == "__main__":
    main()
