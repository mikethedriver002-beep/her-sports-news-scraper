from __future__ import annotations
import csv,json,shutil
from pathlib import Path
from datetime import datetime, timezone
FILES=["asset_manifest.csv","asset_manifest.json","team_assets.csv","team_assets.json","player_assets.csv","player_assets.json","asset_rights_review.csv","approved_graphics_assets.csv","approved_graphics_assets.json","launch_integration_points.csv","asset_source_seed_list.csv","asset_candidates_review.md","asset_desk_manifest.json","asset_desk_dashboard/index.html","brand_system","studio_templates_v2","studio_visual_upgrade_v2.md","studio_bundle_prompts_v2.md","studio_render_manifest_v2.json","visual_upgrade_manifest.json","visual_upgrade_dashboard/index.html","graphics_qa_results.csv","graphics_qa_report.md","graphics_qa_manifest.json","graphics_qa_dashboard/index.html","data/assets"]
def rowcount(p):
    if not p.exists() or p.suffix!=".csv": return 0
    with p.open(newline="",encoding="utf-8",errors="replace") as f: return max(0,sum(1 for _ in csv.reader(f))-1)
def cp(src,root):
    if not src.exists(): return False
    dst=root/src; dst.parent.mkdir(parents=True,exist_ok=True)
    if src.is_dir():
        if dst.exists(): shutil.rmtree(dst)
        shutil.copytree(src,dst)
    else: shutil.copy2(src,dst)
    return True
def main():
    now=datetime.now(timezone.utc); run=Path("asset_run_history")/now.strftime("%Y-%m-%d")/now.strftime("%H%M_UTC"); latest=Path("asset_run_history/latest")
    for d in [run,latest]: d.mkdir(parents=True,exist_ok=True)
    copied=[]; missing=[]
    for name in FILES:
        s=Path(name)
        if cp(s,run) and cp(s,latest): copied.append(name)
        else: missing.append(name)
    counts={f:rowcount(Path(f)) for f in copied if f.endswith(".csv")}
    summary=["# HSD Asset + Visual + QA Run Summary","",f"Run timestamp UTC: `{now.strftime('%Y-%m-%d %H:%M:%S UTC')}`",f"Archive folder: `{run.as_posix()}`","","## Row counts"]+[f"- `{k}`: {v}" for k,v in counts.items()]+["","## Archived files"]+[f"- `{f}`" for f in copied]
    if missing: summary+=["","## Missing optional files"]+[f"- `{f}`" for f in missing]
    (run/"run_summary.md").write_text("\n".join(summary)+"\n",encoding="utf-8"); (latest/"run_summary.md").write_text("\n".join(summary)+"\n",encoding="utf-8")
    man={"run_timestamp_utc":now.isoformat(),"archive_folder":run.as_posix(),"latest_folder":latest.as_posix(),"copied_files":copied,"missing_files":missing,"row_counts":counts}
    (run/"run_manifest.json").write_text(json.dumps(man,indent=2),encoding="utf-8"); (latest/"run_manifest.json").write_text(json.dumps(man,indent=2),encoding="utf-8"); Path("latest_asset_visual_qa_run_summary.md").write_text("\n".join(summary)+"\n",encoding="utf-8")
    idx=Path("asset_run_history/_index.md"); old=idx.read_text(encoding="utf-8") if idx.exists() else "# HSD Asset + Visual + QA Run History\n\n| Run UTC | Archive Folder | Files |\n|---|---:|---:|\n"
    idx.write_text("\n".join(old.splitlines()[:4])+"\n"+f"| {now.strftime('%Y-%m-%d %H:%M:%S UTC')} | [Open archive]({run.as_posix()}) | {len(copied)} files |\n"+"\n".join(old.splitlines()[4:])+"\n",encoding="utf-8")
    print(f"Archived {len(copied)} files to {run}")
if __name__=="__main__": main()
