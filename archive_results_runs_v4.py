from __future__ import annotations
import csv, json, os, shutil
from datetime import datetime, timezone
from pathlib import Path
FILES=['source_observations.csv','reconciled_events.csv','today_results_board.csv','today_womens_results.csv','today_final_results.csv','top_womens_results.csv','manual_review_queue.csv','source_health_report.csv','results_graphics_queue.md','results_system_hub.md','run_manifest.json','results_dashboard/index.html']
def row_count(path):
    p=Path(path)
    if not p.exists() or p.suffix.lower()!='.csv': return 0
    try:
        with p.open(newline='', encoding='utf-8') as f: return max(0, sum(1 for _ in csv.reader(f))-1)
    except Exception: return 0
def main():
    now=datetime.now(timezone.utc); run_date=now.strftime('%Y-%m-%d'); run_time=now.strftime('%H%M_UTC'); stamp=now.strftime('%Y-%m-%d %H:%M:%S UTC')
    run_dir=Path('results_run_history')/run_date/run_time; latest=Path('results_run_history')/'latest'
    run_dir.mkdir(parents=True, exist_ok=True); latest.mkdir(parents=True, exist_ok=True)
    copied=[]; missing=[]
    for name in FILES:
        src=Path(name)
        if not src.exists(): missing.append(name); continue
        for root in [run_dir, latest]:
            dst=root/name; dst.parent.mkdir(parents=True, exist_ok=True); shutil.copy2(src,dst)
        copied.append(name)
    counts={name: row_count(name) for name in copied if name.endswith('.csv')}
    manifest={'run_timestamp_utc':stamp,'archive_folder':run_dir.as_posix(),'latest_folder':latest.as_posix(),'copied_files':copied,'missing_files':missing,'row_counts':counts,'github_run_id':os.environ.get('GITHUB_RUN_ID',''),'github_sha':os.environ.get('GITHUB_SHA','')}
    summary=['# Her Sports Daily Results Desk v4 Run Summary','',f'Run timestamp UTC: `{stamp}`',f'Archive folder: `{run_dir.as_posix()}`','','## Row counts','']
    for k,v in counts.items(): summary.append(f'- `{k}`: {v}')
    summary+=['','## Archived files','']+[f'- `{x}`' for x in copied]
    if missing: summary+=['','## Missing files','']+[f'- `{x}`' for x in missing]
    for root in [run_dir, latest]:
        (root/'run_summary.md').write_text('\n'.join(summary)+'\n', encoding='utf-8')
        (root/'run_manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    Path('latest_results_run_summary.md').write_text('\n'.join(summary)+'\n', encoding='utf-8')
    index=Path('results_run_history')/'_index.md'
    existing=index.read_text(encoding='utf-8') if index.exists() else '# Her Sports Daily Results Run History\n\n| Run UTC | Archive Folder | Files |\n|---|---:|---:|\n'
    lines=existing.splitlines(keepends=True); entry=f'| {stamp} | [Open archive]({run_dir.as_posix()}) | {len(copied)} files |\n'
    index.write_text(''.join(lines[:4])+entry+''.join(lines[4:]) if len(lines)>=4 else existing+entry, encoding='utf-8')
    print(f'Archived {len(copied)} files to {run_dir}')
if __name__=='__main__': main()
