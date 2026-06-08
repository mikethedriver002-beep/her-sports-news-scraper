from __future__ import annotations
import csv,json,os,re,html
from pathlib import Path
from datetime import datetime, timezone
from typing import Any,Tuple
try:
    from PIL import Image, ImageStat
except Exception:
    Image=None; ImageStat=None

VERSION="hsd-graphics-qa-scorer-v1"
IN_RENDER=os.getenv("HSD_RENDER_MANIFEST","studio_render_manifest_v2.json")
IN_ASSETS=os.getenv("HSD_APPROVED_GRAPHICS_ASSETS","approved_graphics_assets.csv")
OUT_CSV="graphics_qa_results.csv"; OUT_MD="graphics_qa_report.md"; OUT_JSON="graphics_qa_manifest.json"; OUT_DASH="graphics_qa_dashboard/index.html"
FIELDS="qa_run_id,bundle_id,post_slug,template_name,render_path,score_total,score_accuracy,score_rights,score_accessibility,score_layout,score_brand,score_authenticity,critical_fail,decision,issues_json,remediation_suggestions,checked_utc".split(",")
def now(): return datetime.now(timezone.utc).isoformat()
def clean(x): return re.sub(r"\s+"," ",str(x or "")).strip()
def find(p):
    fname=Path(p).name
    for x in [Path(p),Path("asset_run_history/latest")/fname,Path("studio_run_history/latest")/fname,Path("launch_run_history/latest")/fname]:
        if x.exists(): return x
    return Path(p)
def read_csv(p):
    f=find(p)
    if not f.exists(): return []
    with f.open(newline="",encoding="utf-8",errors="replace") as h: return list(csv.DictReader(h))
def write_csv(p,rows):
    with open(p,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=FIELDS,extrasaction="ignore"); w.writeheader()
        for r in rows: w.writerow({k:json.dumps(r.get(k,""),ensure_ascii=False) if isinstance(r.get(k,""),(list,dict)) else r.get(k,"") for k in FIELDS})
def rgb(h):
    h=h.strip().lstrip("#")
    return tuple(int(h[i:i+2],16) for i in (0,2,4)) if len(h)==6 else (255,255,255)
def lum(c):
    def ch(v):
        x=v/255; return x/12.92 if x<=0.03928 else ((x+0.055)/1.055)**2.4
    r,g,b=[ch(x) for x in c]; return .2126*r+.7152*g+.0722*b
def contrast(f,b):
    a,c=lum(rgb(f)),lum(rgb(b)); hi,lo=max(a,c),min(a,c); return (hi+.05)/(lo+.05)
def image_check(path):
    issues=[]; delta=0
    p=Path(path)
    if not p.exists(): return [{"code":"RENDER_NOT_FOUND","severity":"review","message":"Render not found, manifest-only QA."}],0
    if not Image: return issues,0
    try:
        with Image.open(p) as im:
            if im.size!=(1080,1350): issues.append({"code":"WRONG_SIZE","severity":"major","message":f"Expected 1080x1350 got {im.size}"}); delta-=8
            std=ImageStat.Stat(im.convert("L")).stddev[0]
            if std<18: issues.append({"code":"LOW_VISUAL_VARIANCE","severity":"major","message":"Graphic may be too flat or blank."}); delta-=6
    except Exception as e: issues.append({"code":"IMAGE_OPEN_ERROR","severity":"major","message":str(e)}); delta-=8
    return issues,delta
def score(bundle,approved_ids,qid):
    issues=[]; scores={"accuracy":35,"rights":20,"accessibility":15,"layout":15,"brand":10,"authenticity":5}; crit=False
    facts=bundle.get("source_facts",{})
    if not clean(facts.get("accuracy_lock")) and not clean(facts.get("source_headlines")): scores["accuracy"]-=12; issues.append({"code":"MISSING_SOURCE_FACTS","severity":"major","message":"Missing accuracy lock/source headlines."})
    if not bundle.get("asset_ids"): scores["rights"]-=4; issues.append({"code":"NO_ASSETS","severity":"minor","message":"No approved assets matched. Use premium abstract layout."})
    for aid in bundle.get("asset_ids",[]):
        if aid and aid not in approved_ids: scores["rights"]=0; crit=True; issues.append({"code":"UNAPPROVED_ASSET","severity":"critical","message":aid})
    for l in bundle.get("text_layers",[]):
        r=contrast(l.get("color_hex","#fff"),l.get("background_hex","#000")); need=3.0 if int(l.get("font_size_px") or 0)>=24 and int(l.get("font_weight") or 400)>=700 else 4.5
        if r<need: scores["accessibility"]-=3; issues.append({"code":"LOW_CONTRAST","severity":"major","message":f"{l.get('layer_id')} {r:.2f} below {need}"})
    safe=bundle.get("safe_area",{"left":96,"top":84,"right":984,"bottom":1254})
    for l in bundle.get("all_layers",[]):
        x,y,w,h=l.get("bbox",[0,0,0,0])
        if x<safe["left"]-60 or y<safe["top"]-60 or x+w>safe["right"]+60 or y+h>safe["bottom"]+60: scores["layout"]-=2; issues.append({"code":"SAFE_AREA_RISK","severity":"minor","message":l.get("layer_id","")})
    if not any("watermark" in clean(l.get("layer_id")).lower() for l in bundle.get("all_layers",[])): scores["brand"]-=8; crit=True; issues.append({"code":"MISSING_WATERMARK","severity":"critical","message":"Missing HSD bug layer."})
    im_issues,delta=image_check(bundle.get("render_path","")); issues+=im_issues; scores["layout"]+=min(0,delta)
    scores={k:max(0,v) for k,v in scores.items()}; total=sum(scores.values())
    decision="fail" if crit or total<70 else "revise" if total<80 else "pass_with_review" if total<90 else "pass"
    rem=[]
    for i in issues:
        if i["code"]=="NO_ASSETS": rem.append("Use approved assets if available; otherwise premium abstract template.")
        if i["code"]=="RENDER_NOT_FOUND": rem.append("Export final graphics and rerun QA.")
        if i["code"]=="LOW_CONTRAST": rem.append("Increase contrast.")
        if i["code"]=="MISSING_WATERMARK": rem.append("Add locked HSD watermark.")
    return {"qa_run_id":qid,"bundle_id":bundle.get("bundle_id"),"post_slug":bundle.get("post_slug"),"template_name":bundle.get("template_name"),"render_path":bundle.get("render_path"),"score_total":total,"score_accuracy":scores["accuracy"],"score_rights":scores["rights"],"score_accessibility":scores["accessibility"],"score_layout":scores["layout"],"score_brand":scores["brand"],"score_authenticity":scores["authenticity"],"critical_fail":"Yes" if crit else "No","decision":decision,"issues_json":issues,"remediation_suggestions":" | ".join(dict.fromkeys(rem)),"checked_utc":now()}
def main():
    Path("graphics_qa_dashboard").mkdir(exist_ok=True)
    try: manifest=json.loads(find(IN_RENDER).read_text(encoding="utf-8"))
    except Exception: manifest={"bundles":[]}
    approved={r.get("approved_asset_id") for r in read_csv(IN_ASSETS) if r.get("approved_asset_id")}
    qid="qa_"+datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    rows=[score(b,approved,qid) for b in manifest.get("bundles",[])]
    write_csv(OUT_CSV,rows)
    Path(OUT_MD).write_text("# HSD Graphics QA Scorer v1 Report\n\n"+"\n".join(f"## {r['post_slug']}\n- Decision: **{r['decision']}**\n- Score: {r['score_total']}\n- Remediation: {r['remediation_suggestions']}\n" for r in rows),encoding="utf-8")
    cards="".join(f"<div class='card {html.escape(r['decision'])}'><h3>{html.escape(clean(r['post_slug']))}</h3><div class='score'>{r['score_total']}</div><p>{html.escape(r['decision'])}</p></div>" for r in rows)
    Path(OUT_DASH).write_text(f"<html><head><style>body{{background:#0F1020;color:#F8F4FF;font-family:Inter,Arial}}.card{{background:#181A2F;margin:12px;padding:16px;border-radius:18px}}.score{{font-size:42px;color:#7CF7FF}}</style></head><body><h1>HSD Graphics QA</h1>{cards}</body></html>",encoding="utf-8")
    out={"version":VERSION,"generated_at_utc":now(),"outputs":[OUT_CSV,OUT_MD,OUT_DASH],"counts":{"bundles_scored":len(rows),"passes":sum(1 for r in rows if r["decision"]=="pass"),"review_or_revise_or_fail":sum(1 for r in rows if r["decision"]!="pass")}}
    Path(OUT_JSON).write_text(json.dumps(out,indent=2),encoding="utf-8"); print(json.dumps(out["counts"],indent=2))
if __name__=="__main__": main()
