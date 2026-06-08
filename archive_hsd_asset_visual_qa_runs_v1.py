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
"graphics_qa_dashboard/index.html","data/assets"
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

def main():
    now=datetime.now(timezone.utc); date=now.strftime("%Y-%m-%d"); tm=now.strftime("%H%M_UTC"); stamp=now.strftime("%Y-%m-%d %H:%M:%S UTC")
    run=Path("asset_run_history")/date/tm; latest=Path("asset_run_history")/"latest"
    run.mkdir(parents=True,exist_ok=True); latest.mkdir(parents=True,exist_ok=True)
    copied=[]; missing=[]
    for name in FILES:
        src=Path(name)
        if copy(src,run) and copy(src,latest): copied.append(name)
        else: missing.append(name)
    counts={n:rows(Path(n)) for n in copied if n.endswith(".csv")}
    summary=["# HSD Asset Visual QA v1.2 Run Summary","",f"Run timestamp UTC: `{stamp}`",f"Archive folder: `{run.as_posix()}`","","## Row counts",""]
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
