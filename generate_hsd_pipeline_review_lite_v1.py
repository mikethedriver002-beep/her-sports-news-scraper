from __future__ import annotations
import csv, json, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path

VERSION = "hsd-pipeline-review-lite-v3.1"
OUT_DIR = Path("hsd_pipeline_lite_review")
OUT_ZIP = Path("hsd_pipeline_lite_review.zip")
KEY_FILES = [
    "operator_status.md","operator_status.json","operator_status.csv",
    "publish_guard_report.md","publish_guard_report.json",
    "install_report.md","contract_validation_report.md","pipeline_outcome.md","pipeline_stop_reason.md",
    "results_contract_report.md","results_contract_v2.csv","manual_story_inbox_report.md","story_candidates_manual.csv",
    "discovery_sources_report.md","story_candidates_discovery.csv","daily_slate_plan.md","daily_slate_plan.csv",
    "latest_results_run_summary.md","news_fact_packets.csv","latest_news_sync_run_summary.md",
    "studio_bundle_queue.csv","studio_bundle_packets.md","studio_bundle_prompts.md","studio_fresh_packet_report.md",
    "graphics_upload_pack_status.csv","graphics_chat_direct_handoff.md","graphics_qa_report.md",
    "player_image_sourcing_report.md","player_image_requirements.csv","player_image_fit_report.md",
    "asset_candidates_review.md","approved_graphics_assets.csv","graphics_chat_upload_manifest.csv"
]

def row_count(path: str) -> int:
    p = Path(path)
    if not p.exists(): return 0
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return sum(1 for _ in csv.DictReader(f))
    except Exception:
        return 0

def copy_if_exists(name: str, files_dir: Path, manifest: list[dict]):
    p = Path(name)
    if not p.exists():
        return
    dest = files_dir / p.name
    shutil.copy2(p, dest)
    manifest.append({"path": name, "included_as": dest.as_posix(), "size": p.stat().st_size})

def main() -> None:
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    if OUT_ZIP.exists():
        OUT_ZIP.unlink()
    files_dir = OUT_DIR / "files"
    ready_dir = OUT_DIR / "ready_upload_packs"
    files_dir.mkdir(parents=True)
    ready_dir.mkdir(parents=True)
    manifest = []
    for name in KEY_FILES:
        copy_if_exists(name, files_dir, manifest)
    ready_packs = []
    status = Path("graphics_upload_pack_status.csv")
    if status.exists():
        with status.open(newline="", encoding="utf-8", errors="replace") as f:
            for r in csv.DictReader(f):
                if r.get("upload_pack_status") in {"ready","ready_with_review"}:
                    p = Path(r.get("zip_path",""))
                    if p.exists() and p.stat().st_size < 10_000_000:
                        dest = ready_dir / p.name
                        shutil.copy2(p, dest)
                        ready_packs.append({"bundle_name": r.get("bundle_name"), "zip": dest.as_posix(), "size": p.stat().st_size})
    counts = {
        "results_contract_rows": row_count("results_contract_v2.csv"),
        "manual_story_candidates": row_count("story_candidates_manual.csv"),
        "discovery_candidates": row_count("story_candidates_discovery.csv"),
        "slate_items": row_count("daily_slate_plan.csv"),
        "upload_pack_rows": row_count("graphics_upload_pack_status.csv"),
        "ready_packs_included": len(ready_packs),
    }
    status_json = {"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "counts": counts, "ready_packs": ready_packs}
    (OUT_DIR / "pipeline_status.json").write_text(json.dumps(status_json, indent=2), encoding="utf-8")
    (OUT_DIR / "lite_manifest.csv").write_text("path,included_as,size\n" + "\n".join(f"{m['path']},{m['included_as']},{m['size']}" for m in manifest) + "\n", encoding="utf-8")
    (OUT_DIR / "README.md").write_text("# HSD Pipeline Lite Review\n\n" + json.dumps(status_json, indent=2) + "\n", encoding="utf-8")
    with zipfile.ZipFile(OUT_ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for p in OUT_DIR.rglob("*"):
            if p.is_file():
                z.write(p, p.relative_to(OUT_DIR.parent))
    print(json.dumps({"zip": OUT_ZIP.as_posix(), **counts}, indent=2))

if __name__ == "__main__":
    main()
