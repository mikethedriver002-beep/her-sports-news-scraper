from __future__ import annotations

import csv, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-studio-visual-upgrade-v2.1"
INPUT_BUNDLE_QUEUE = os.environ.get("HSD_STUDIO_BUNDLE_QUEUE", "studio_bundle_queue.csv")
INPUT_BUNDLE_PACKETS = os.environ.get("HSD_STUDIO_BUNDLE_PACKETS", "studio_bundle_packets.md")
INPUT_LAUNCH_GRAPHICS_BRIEF = os.environ.get("HSD_LAUNCH_GRAPHICS_BRIEF", "launch_graphics_chat_brief.md")
INPUT_APPROVED_ASSETS = os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS", "approved_graphics_assets.csv")


def now(): return datetime.now(timezone.utc).isoformat()
def clean(v): return re.sub(r"\s+", " ", str(v or "")).strip()
def slugify(v): return re.sub(r"[^a-zA-Z0-9]+","-",clean(v).lower()).strip("-")
def sid(prefix,*parts): import hashlib; return prefix+"_"+hashlib.sha1("|".join(clean(p) for p in parts).encode()).hexdigest()[:14]

def find_file(filename: str) -> Path:
    candidates = [Path(filename)]
    for root in ["studio_run_history","launch_run_history","asset_run_history"]:
        r = Path(root)
        if r.exists():
            candidates += sorted(r.rglob(Path(filename).name), key=lambda p:p.stat().st_mtime, reverse=True)
    for p in candidates:
        if p.exists() and p.is_file() and p.stat().st_size > 0:
            return p
    return Path(filename)

def read_csv_any(filename: str) -> List[Dict[str,str]]:
    p = find_file(filename)
    if not p.exists(): return []
    with p.open(newline="",encoding="utf-8",errors="replace") as f:
        return list(csv.DictReader(f))

def read_text_any(filename: str) -> str:
    p = find_file(filename)
    return p.read_text(encoding="utf-8",errors="replace") if p.exists() else ""

def parse_bundle_text(text: str) -> List[Dict[str,str]]:
    bundles=[]
    for block in re.split(r"\n(?=##\s+BUNDLE\s+\d+:)", text):
        m=re.search(r"##\s+BUNDLE\s+(\d+):\s*(.+)", block)
        if not m: continue
        rank,name=m.group(1),clean(m.group(2))
        cap=re.search(r"### Caption seed\s+(.+?)(?:\n###|\n---|\Z)", block, re.S)
        lock=re.search(r"### Accuracy lock\s+(.+?)(?:\n---|\Z)", block, re.S)
        sm=re.search(r"Source items:\s*(.+)", block)
        btype="main_wnba_lead" if "Main WNBA" in name else "wnba_mini_roundup" if "WNBA" in name or "Tonight in the W" in name else "volleyball_roundup" if "Volleyball" in name else "soccer_radar" if "Soccer" in name else "bundle"
        bundles.append({"bundle_rank":rank,"bundle_id":sid("bundle",name),"bundle_name":name,"bundle_type":btype,"production_priority":"POST FIRST" if rank=="1" else "POST NEXT","source_headlines":clean(sm.group(1)) if sm else "", "caption_seed":clean(cap.group(1)) if cap else "", "accuracy_lock":clean(lock.group(1)) if lock else ""})
    return bundles

def load_bundles():
    rows=read_csv_any(INPUT_BUNDLE_QUEUE)
    if rows: return rows
    return parse_bundle_text(read_text_any(INPUT_BUNDLE_PACKETS)+"\n"+read_text_any(INPUT_LAUNCH_GRAPHICS_BRIEF))

def tokens():
    return {
        "canvas":{"width":1080,"height":1350},
        "colors":{"dark":"#071226","panel":"#101D3A","cyan":"#62E8FF","magenta":"#FF4FD8","white":"#F4F7FB","muted":"#AEB9CE"},
        "type":{"headline":"bold condensed, 72-96px","body":"Inter-style, 28-36px","score":"oversized 96px+"},
        "watermark":{"file":"brand_assets/hsd_watermark_bug.svg","position":"top-left","size_px":76}
    }

def template_for(b):
    blob=(clean(b.get("bundle_type"))+" "+clean(b.get("bundle_name"))).lower()
    if "soccer" in blob: return "radar_v2"
    if "volleyball" in blob: return "roundup_v2"
    if "main" in blob and "wnba" in blob: return "result_slide_v2"
    if "wnba" in blob: return "roundup_v2"
    return "carousel_cover_v2"

def matched_assets(bundle, assets):
    blob=" ".join(str(v).lower() for v in bundle.values())
    return [a for a in assets if clean(a.get("entity_name")).lower() and clean(a.get("entity_name")).lower() in blob]

def prompt(bundle, assets):
    m=matched_assets(bundle,assets)
    asset_block="\n".join([f"- {a.get('entity_name')} | {a.get('approved_variant')} | {a.get('source_url')}" for a in m]) or "No approved exact assets matched. Use premium text-forward design. Do not invent logos or players."
    return f"""HSD VISUAL UPGRADE v2.1 PROMPT
Bundle: {clean(bundle.get('bundle_name'))}
Template: {template_for(bundle)}
Canvas: 1080x1350 carousel
Source facts: {clean(bundle.get('source_headlines'))}
Caption/context: {clean(bundle.get('caption_seed'))}
Accuracy lock: {clean(bundle.get('accuracy_lock'))}

Approved exact assets:
{asset_block}

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact asset is listed, use text, sport texture, court/field/pitch lines, scoreboard energy, and HSD branding only.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
Accuracy beats aesthetics, but aesthetics must be premium.
""".strip()

def main():
    Path("brand_system").mkdir(exist_ok=True)
    Path("studio_templates_v2").mkdir(exist_ok=True)
    Path("visual_upgrade_dashboard").mkdir(exist_ok=True)
    bundles=load_bundles()
    assets=read_csv_any(INPUT_APPROVED_ASSETS)
    Path("brand_system/hsd_tokens.json").write_text(json.dumps(tokens(),indent=2),encoding="utf-8")
    rules={"version":VERSION,"rules":["one dominant thesis per slide","never use boxed tables as full design","use exact assets only","text-forward when assets missing","CTA/end slide required"]}
    Path("brand_system/hsd_template_rules.json").write_text(json.dumps(rules,indent=2),encoding="utf-8")
    for t in ["carousel_cover_v2","result_slide_v2","roundup_v2","radar_v2","cta_v2"]:
        Path(f"studio_templates_v2/{t}.json").write_text(json.dumps({"template":t,"tokens":"brand_system/hsd_tokens.json"},indent=2),encoding="utf-8")
    lines=["# HSD Bundle Prompts v2.1","",f"Generated: {now()}",""]
    render={"version":VERSION,"generated_at_utc":now(),"bundles":[]}
    for i,b in enumerate(bundles,1):
        slug=slugify(b.get("bundle_name") or f"bundle-{i}")
        m=matched_assets(b,assets)
        lines += [f"## {clean(b.get('bundle_name'))}","","```text",prompt(b,assets),"```",""]
        render["bundles"].append({
            "bundle_id":b.get("bundle_id") or f"bundle_{i}",
            "post_slug":slug,
            "bundle_name":b.get("bundle_name"),
            "template_name":template_for(b),
            "asset_ids":[a.get("approved_asset_id") for a in m if a.get("approved_asset_id")],
            "source_facts":{"source_headlines":b.get("source_headlines"),"caption_seed":b.get("caption_seed"),"accuracy_lock":b.get("accuracy_lock")},
            "text_layers":[{"layer_id":slug+"_headline","text":b.get("bundle_name"),"font_size_px":72,"font_weight":800,"color_hex":"#F4F7FB","background_hex":"#071226","essential":True}],
            "all_layers":[{"layer_id":slug+"_watermark","bbox":[48,48,76,76]},{"layer_id":slug+"_headline","bbox":[96,160,850,220]},{"layer_id":slug+"_cta","bbox":[96,1150,888,110]}],
            "render_path":f"generated_graphics/{slug}.png"
        })
    Path("studio_bundle_prompts_v2.md").write_text("\n".join(lines),encoding="utf-8")
    Path("studio_render_manifest_v2.json").write_text(json.dumps(render,indent=2),encoding="utf-8")
    Path("studio_visual_upgrade_v2.md").write_text(f"# HSD Studio Visual Upgrade v2.1\n\nGenerated: {now()}\n\nBundles: {len(bundles)}\nApproved exact assets: {len(assets)}\n",encoding="utf-8")
    Path("visual_upgrade_manifest.json").write_text(json.dumps({"version":VERSION,"generated_at_utc":now(),"counts":{"bundles":len(bundles),"approved_assets":len(assets)}},indent=2),encoding="utf-8")
    Path("visual_upgrade_dashboard/index.html").write_text(f"<html><body><h1>HSD Visual Upgrade v2.1</h1><p>Bundles: {len(bundles)}</p><p>Assets: {len(assets)}</p></body></html>",encoding="utf-8")
    print("Created HSD Visual Upgrade v2.1 outputs")

if __name__=="__main__":
    main()
