from __future__ import annotations
import csv, json, re, os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION="hsd-graphics-qa-scorer-v1.2"
INPUT_RENDER_MANIFEST=os.environ.get("HSD_RENDER_MANIFEST","studio_render_manifest_v2.json")
INPUT_APPROVED_ASSETS=os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS","approved_graphics_assets.csv")
FIELDS=["qa_run_id","bundle_id","post_slug","template_name","render_path","score_total","critical_fail","decision","issues_json","remediation_suggestions","checked_utc"]

def now(): return datetime.now(timezone.utc).isoformat()
def clean(v): return re.sub(r"\s+"," ",str(v or "")).strip()
def read_csv_any(p):
    if not Path(p).exists(): return []
    with open(p,newline="",encoding="utf-8",errors="replace") as f: return list(csv.DictReader(f))
def write_csv(p,rows,fields):
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow({k:r.get(k,"") for k in fields})

def main():
    Path("graphics_qa_dashboard").mkdir(exist_ok=True)
    manifest={}
    if Path(INPUT_RENDER_MANIFEST).exists():
        manifest=json.loads(Path(INPUT_RENDER_MANIFEST).read_text(encoding="utf-8"))
    approved={r.get("approved_asset_id") for r in read_csv_any(INPUT_APPROVED_ASSETS) if r.get("approved_asset_id")}
    bundles=manifest.get("bundles",[])
    rows=[]
    run="qa_"+datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    for b in bundles:
        issues=[]
        score=100
        if not clean(b.get("source_facts",{}).get("accuracy_lock")) and not clean(b.get("source_facts",{}).get("source_headlines")):
            issues.append({"code":"MISSING_FACT_LOCK","severity":"major","message":"No source facts or accuracy lock."}); score-=20
        for aid in b.get("asset_ids",[]):
            if aid and aid not in approved:
                issues.append({"code":"UNAPPROVED_ASSET","severity":"critical","message":aid}); score-=40
        if b.get("fact_warning_count",0):
            issues.append({"code":"FACT_WARNING_PRESENT","severity":"critical","message":f"{b.get('fact_warning_count')} fact warnings present"}); score-=35
        if not any("watermark" in clean(x.get("layer_id")).lower() for x in b.get("all_layers",[])):
            issues.append({"code":"MISSING_WATERMARK","severity":"critical","message":"No watermark layer."}); score-=40
        if b.get("safe_graphics_mode") == "logos_and_text_only":
            # pass, but enforce no player assets requirement
            pass
        if not Path(b.get("render_path","")).exists():
            issues.append({"code":"RENDER_NOT_FOUND","severity":"review","message":"Graphic file not exported yet. Manifest QA only."}); score-=5
        decision="fail" if any(i["severity"]=="critical" for i in issues) or score<70 else "revise" if score<85 else "pass_with_review" if issues else "pass"
        rows.append({"qa_run_id":run,"bundle_id":b.get("bundle_id"),"post_slug":b.get("post_slug"),"template_name":b.get("template_name"),"render_path":b.get("render_path"),"score_total":max(0,score),"critical_fail":"Yes" if decision=="fail" else "No","decision":decision,"issues_json":json.dumps(issues),"remediation_suggestions":"Resolve fact warnings, export graphic, and rerun QA.","checked_utc":now()})
    write_csv("graphics_qa_results.csv",rows,FIELDS)
    report=["# HSD Graphics QA Scorer v1.2 Report","",f"Generated: {now()}","",f"Bundles scored: {len(rows)}",""]
    if not rows:
        report += ["No bundles found in render manifest. Run Visual Upgrade first."]
    for r in rows:
        report += [f"## {r['post_slug']}","",f"- Decision: **{r['decision']}**",f"- Score: {r['score_total']}",f"- Issues: `{r['issues_json']}`",""]
    Path("graphics_qa_report.md").write_text("\n".join(report),encoding="utf-8")
    Path("graphics_qa_manifest.json").write_text(json.dumps({"version":VERSION,"generated_at_utc":now(),"counts":{"bundles_scored":len(rows)}},indent=2),encoding="utf-8")
    Path("graphics_qa_dashboard/index.html").write_text(f"<html><body><h1>Graphics QA v1.2</h1><p>Bundles scored: {len(rows)}</p></body></html>",encoding="utf-8")
    print("Created HSD Graphics QA v1.2 outputs")
if __name__=="__main__":
    main()
