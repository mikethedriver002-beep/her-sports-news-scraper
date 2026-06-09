from __future__ import annotations
import csv, json, shutil
from datetime import datetime, timezone
from pathlib import Path

FILES=[
"asset_manifest.csv","asset_manifest.json","team_assets.csv","team_assets.json","player_assets.csv","player_assets.json",
"asset_rights_review.csv","approved_graphics_assets.csv","approved_graphics_assets.json","launch_integration_points.csv",
"asset_source_seed_list.csv","fact_warning_queue.csv","asset_candidates_review.md","asset_desk_manifest.json","brand_system","studio_templates_v2",
"studio_visual_upgrade_v2.md","studio_bundle_prompts_v2.md","studio_render_manifest_v2.json","visual_upgrade_manifest.json",
"visual_upgrade_dashboard/index.html","graphics_qa_results.csv","graphics_qa_report.md","graphics_qa_manifest.json",
"graphics_qa_dashboard/index.html","data/assets","chatgpt_review_pack","hsd_chatgpt_review_packet.md"
]

CHATGPT_REVIEW_FILES = [
    ("01_latest_asset_visual_qa_run_summary.md", "latest_asset_visual_qa_run_summary.md"),
    ("02_asset_desk_manifest.json", "asset_desk_manifest.json"),
    ("03_asset_candidates_review.md", "asset_candidates_review.md"),
    ("04_approved_graphics_assets.csv", "approved_graphics_assets.csv"),
    ("05_fact_warning_queue.csv", "fact_warning_queue.csv"),
    ("06_studio_bundle_prompts_v2.md", "studio_bundle_prompts_v2.md"),
    ("07_graphics_qa_report.md", "graphics_qa_report.md"),
    ("08_visual_upgrade_manifest.json", "visual_upgrade_manifest.json"),
    ("09_graphics_qa_manifest.json", "graphics_qa_manifest.json"),
]


def rows(p):
    if not p.exists() or p.suffix!=".csv": return 0
    with p.open(newline="",encoding="utf-8",errors="replace") as f: return max(0,sum(1 for _ in csv.reader(f))-1)

def copy(src,dstroot):
    if not src.exists(): return False
    dst=dstroot/src
    dst.parent.mkdir(parents=True,exist_ok=True)
    if src.is_dir():
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(src,dst)
    else:
        shutil.copy2(src,dst)
    return True


def read_text_safe(path):
    p = Path(path)
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def create_chatgpt_review_pack():
    pack = Path("chatgpt_review_pack")
    if pack.exists():
        shutil.rmtree(pack)
    pack.mkdir(parents=True, exist_ok=True)

    # Copy the exact small set the user needs to upload back into ChatGPT.
    for out_name, src_name in CHATGPT_REVIEW_FILES:
        src = Path(src_name)
        if src.exists():
            shutil.copy2(src, pack / out_name)

    consolidated = [
        "# HSD ChatGPT Review Packet",
        "",
        "Upload this single file if you want the fastest possible review. Upload the individual files in `chatgpt_review_pack/` only if deeper debugging is needed.",
        "",
    ]

    for out_name, src_name in CHATGPT_REVIEW_FILES:
        src = Path(src_name)
        consolidated.append(f"## {src_name}")
        consolidated.append("")
        if not src.exists():
            consolidated.append("MISSING")
            consolidated.append("")
            continue
        text = read_text_safe(src_name)
        if src.suffix.lower() == ".csv":
            # Include CSV as text, but cap very large files.
            consolidated.append("```csv")
            consolidated.append(text[:12000])
            if len(text) > 12000:
                consolidated.append("...TRUNCATED...")
            consolidated.append("```")
        elif src.suffix.lower() == ".json":
            consolidated.append("```json")
            consolidated.append(text[:12000])
            if len(text) > 12000:
                consolidated.append("...TRUNCATED...")
            consolidated.append("```")
        else:
            consolidated.append(text[:18000])
            if len(text) > 18000:
                consolidated.append("\\n...TRUNCATED...")
        consolidated.append("")

    packet_text = "\\n".join(consolidated)
    Path("hsd_chatgpt_review_packet.md").write_text(packet_text, encoding="utf-8")
    shutil.copy2("hsd_chatgpt_review_packet.md", pack / "00_hsd_chatgpt_review_packet.md")


def main():
    now=datetime.now(timezone.utc); date=now.strftime("%Y-%m-%d"); tm=now.strftime("%H%M_UTC"); stamp=now.strftime("%Y-%m-%d %H:%M:%S UTC")
    run=Path("asset_run_history")/date/tm; latest=Path("asset_run_history")/"latest"
    run.mkdir(parents=True,exist_ok=True); latest.mkdir(parents=True,exist_ok=True)
    create_chatgpt_review_pack()
    copied=[]; missing=[]
    for name in FILES:
        src=Path(name)
        if copy(src,run) and copy(src,latest): copied.append(name)
        else: missing.append(name)
    counts={n:rows(Path(n)) for n in copied if n.endswith(".csv")}
    summary=["# HSD Asset Visual QA v1.2.1 Run Summary","",f"Run timestamp UTC: `{stamp}`",f"Archive folder: `{run.as_posix()}`","","## Row counts",""]
    for k,v in counts.items(): summary.append(f"- `{k}`: {v}")
    summary += ["","## Missing optional files",""] + [f"- `{m}`" for m in missing]
    text="\n".join(summary)+"\n"
    (run/"run_summary.md").write_text(text,encoding="utf-8"); (latest/"run_summary.md").write_text(text,encoding="utf-8")
    (run/"run_manifest.json").write_text(json.dumps({"run_timestamp_utc":stamp,"copied_files":copied,"missing_files":missing,"row_counts":counts},indent=2),encoding="utf-8")
    (latest/"run_manifest.json").write_text(json.dumps({"run_timestamp_utc":stamp,"copied_files":copied,"missing_files":missing,"row_counts":counts},indent=2),encoding="utf-8")
    Path("latest_asset_visual_qa_run_summary.md").write_text(text,encoding="utf-8")
    print("Archived asset visual QA v1.2")
if __name__=="__main__":
    main()
