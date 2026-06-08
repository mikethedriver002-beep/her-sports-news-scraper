from __future__ import annotations
import csv,json,os,re,html
from pathlib import Path
from datetime import datetime, timezone
from typing import Any,Dict,List

VERSION="hsd-studio-visual-upgrade-v2"
IN_BUNDLE=os.getenv("HSD_STUDIO_BUNDLE_QUEUE","studio_bundle_queue.csv")
IN_ASSETS=os.getenv("HSD_APPROVED_GRAPHICS_ASSETS","approved_graphics_assets.csv")
OUT_TOKENS="brand_system/hsd_tokens.json"; OUT_RULES="brand_system/hsd_template_rules.json"; OUT_MD="studio_visual_upgrade_v2.md"; OUT_PROMPTS="studio_bundle_prompts_v2.md"; OUT_RENDER="studio_render_manifest_v2.json"; OUT_DASH="visual_upgrade_dashboard/index.html"; OUT_MANIFEST="visual_upgrade_manifest.json"

def now(): return datetime.now(timezone.utc).isoformat()
def clean(x): return re.sub(r"\s+"," ",str(x or "")).strip()
def slug(x): return re.sub(r"[^a-z0-9]+","-",clean(x).lower()).strip("-")
def find(path):
    fname=Path(path).name; cand=[Path(path),Path("studio_run_history/latest")/fname,Path("launch_run_history/latest")/fname,Path("asset_run_history/latest")/fname]
    for r in [Path("studio_run_history"),Path("asset_run_history"),Path("launch_run_history")]:
        if r.exists(): cand+=sorted(r.rglob(fname),key=lambda p:p.stat().st_mtime,reverse=True)
    for p in cand:
        if p.exists() and p.stat().st_size>0: return p
    return Path(path)
def read_csv(path):
    p=find(path)
    if not p.exists(): return []
    with p.open(newline="",encoding="utf-8",errors="replace") as f: return list(csv.DictReader(f))
def wjson(path,data): Path(path).parent.mkdir(parents=True,exist_ok=True); Path(path).write_text(json.dumps(data,indent=2),encoding="utf-8")
def tokens():
    return {"version":VERSION,"canvas":{"feed":{"width":1080,"height":1350}},"grid":{"columns":12,"gutter":24,"safe_left":96,"safe_right":984,"safe_top":84,"safe_bottom":1254},"colors":{"bg_900":"#071226","bg_800":"#0C1730","surface_1":"#101D3A","surface_2":"#142447","text_strong":"#F4F7FB","text_muted":"#AEB9CE","accent_cyan":"#62E8FF","accent_magenta":"#FF4FD8","accent_lime":"#C6FF4D"},"type":{"display_headline":{"family":"Sora or Anton fallback","weight":700,"size":88},"slide_headline":{"family":"Sora or Anton fallback","weight":700,"size":64},"score_digits":{"family":"Sora or Anton fallback","weight":700,"size":96},"body":{"family":"Inter fallback","weight":500,"size":28}},"watermark":{"file":"brand_assets/hsd_watermark_bug.svg","position":"top-left","size":[76,76]}}
def rules():
    return {"version":VERSION,"non_negotiables":["One dominant visual thesis per slide.","Use approved assets when available. Do not invent players, jerseys, logos, or numbers.","Scoreboard accuracy outranks art direction.","Every carousel has a premium CTA/end slide."],"templates":{"carousel_cover_v2":{"purpose":"Premium cover with hero visual/logo cluster."},"result_slide_v2":{"purpose":"One game with huge score slab."},"top_performers_v2":{"purpose":"Top performer context with approved player/logo assets."},"roundup_v2":{"purpose":"Multi-result editorial grid. Max six rows per slide."},"radar_v2":{"purpose":"Soccer/multi-sport radar with matchday feel."},"cta_v2":{"purpose":"Minimal HSD close slide."}}}
def template(b):
    blob=(b.get("bundle_type","")+" "+b.get("bundle_name","")).lower()
    if "soccer" in blob: return "radar_v2"
    if "volleyball" in blob or "roundup" in blob: return "roundup_v2"
    if "main" in blob and "wnba" in blob: return "result_slide_v2"
    if "wnba" in blob: return "roundup_v2"
    return "carousel_cover_v2"
def matched_assets(bundle,assets):
    blob=" ".join(str(v).lower() for v in bundle.values())
    return [a for a in assets if clean(a.get("entity_name")).lower() and clean(a.get("entity_name")).lower() in blob]
def prompt(bundle,assets):
    aset="\n".join(f"- {a.get('entity_name')} | {a.get('approved_variant')} | {a.get('source_url') or a.get('master_path')}" for a in assets) or "No approved assets matched. Use sport-specific abstract texture. Do not invent logos or players."
    return f"""HSD VISUAL UPGRADE v2 PROMPT
Bundle: {clean(bundle.get('bundle_name'))}
Template: {template(bundle)}
Canvas: 1080x1350 carousel
Source facts: {clean(bundle.get('source_headlines'))}
Caption/context: {clean(bundle.get('caption_seed'))}

Approved assets:
{aset}

Create a premium Her Sports Daily editorial sports carousel, not a dashboard card.
Use huge readable hierarchy, layered diagonal panels, sport atmosphere, and neon cyan/magenta energy.
Use approved logos/player images when listed. If not listed, do not invent them.
No fake jerseys, fake jersey numbers, fake official logos, fake player bodies, fake quotes, or unsupported stats.
Every slide must look designed, not auto-filled. Reject flat tables, tiny text, weak hierarchy, and generic dark boxes."""
def render_manifest(bundles,assets):
    tk=tokens(); out=[]
    for i,b in enumerate(bundles,1):
        a=matched_assets(b,assets); s=slug(b.get("bundle_name") or f"bundle_{i}")
        out.append({"bundle_rank":b.get("bundle_rank",i),"bundle_id":b.get("bundle_id",f"bundle_{i:02d}"),"bundle_name":b.get("bundle_name",""),"post_slug":s,"template_name":template(b),"canvas":tk["canvas"]["feed"],"safe_area":{"left":96,"top":84,"right":984,"bottom":1254},"asset_ids":[x.get("approved_asset_id") for x in a if x.get("approved_asset_id")],"asset_entities":[{"entity_name":x.get("entity_name"),"source_url":x.get("source_url"),"asset_id":x.get("approved_asset_id")} for x in a],"source_facts":{"source_headlines":b.get("source_headlines"),"caption_seed":b.get("caption_seed"),"accuracy_lock":b.get("accuracy_lock")},"text_layers":[{"layer_id":s+"_headline","text":b.get("bundle_name",""),"font_size_px":64,"font_weight":700,"color_hex":tk["colors"]["text_strong"],"background_hex":tk["colors"]["bg_900"],"essential":True},{"layer_id":s+"_caption","text":b.get("caption_seed",""),"font_size_px":28,"font_weight":500,"color_hex":tk["colors"]["text_muted"],"background_hex":tk["colors"]["surface_1"],"essential":False}],"all_layers":[{"layer_id":s+"_watermark","bbox":[48,48,76,76]},{"layer_id":s+"_headline","bbox":[96,180,760,190]},{"layer_id":s+"_primary_visual","bbox":[540,330,444,600]}],"logo_layers":[],"portrait_layers":[{"layer_id":x.get("approved_asset_id"),"source_status":"approved","watermark_flag":False,"face_count":None} for x in a if x.get("entity_type")=="player"],"render_path":f"generated_graphics/{s}.png"})
    return {"version":VERSION,"generated_at_utc":now(),"bundles":out}
def main():
    Path("brand_system").mkdir(exist_ok=True); Path("studio_templates_v2").mkdir(exist_ok=True); Path("visual_upgrade_dashboard").mkdir(exist_ok=True)
    bundles=read_csv(IN_BUNDLE); assets=read_csv(IN_ASSETS)
    wjson(OUT_TOKENS,tokens()); rr=rules(); wjson(OUT_RULES,rr)
    for k,v in rr["templates"].items(): wjson(f"studio_templates_v2/{k}.json",{"template_name":k,**v,"tokens_ref":OUT_TOKENS})
    rm=render_manifest(bundles,assets); wjson(OUT_RENDER,rm)
    Path(OUT_MD).write_text("# HSD Studio Visual Upgrade v2\n\nGenerated: "+now()+"\n\nUse approved assets when available. If unavailable, use premium sport-specific abstraction, not fake visuals.\n",encoding="utf-8")
    Path(OUT_PROMPTS).write_text("# HSD Bundle Prompts v2\n\n"+"\n\n".join("## "+clean(b.get("bundle_name"))+"\n\n```text\n"+prompt(b,matched_assets(b,assets))+"\n```" for b in bundles),encoding="utf-8")
    cards="".join(f"<div class='card'><h3>{html.escape(clean(b.get('bundle_name')))}</h3><p>{template(b)}</p><p>Assets: {len(matched_assets(b,assets))}</p></div>" for b in bundles)
    Path(OUT_DASH).write_text(f"<html><head><style>body{{background:#071226;color:#F4F7FB;font-family:Inter,Arial}}.card{{background:#101D3A;margin:12px;padding:16px;border-radius:18px}}</style></head><body><h1>Visual Upgrade v2</h1>{cards}</body></html>",encoding="utf-8")
    manifest={"version":VERSION,"generated_at_utc":now(),"outputs":[OUT_TOKENS,OUT_RULES,OUT_MD,OUT_PROMPTS,OUT_RENDER,OUT_DASH],"counts":{"bundles":len(bundles),"approved_assets":len(assets),"render_manifests":len(rm["bundles"])}}
    Path(OUT_MANIFEST).write_text(json.dumps(manifest,indent=2),encoding="utf-8"); print(json.dumps(manifest["counts"],indent=2))
if __name__=="__main__": main()
