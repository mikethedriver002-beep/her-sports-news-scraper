from __future__ import annotations

import csv, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-studio-visual-upgrade-v2.5"
INPUT_BUNDLE_QUEUE = os.environ.get("HSD_STUDIO_BUNDLE_QUEUE", "studio_bundle_queue.csv")
INPUT_BUNDLE_PACKETS = os.environ.get("HSD_STUDIO_BUNDLE_PACKETS", "studio_bundle_packets.md")
INPUT_LAUNCH_GRAPHICS_BRIEF = os.environ.get("HSD_LAUNCH_GRAPHICS_BRIEF", "launch_graphics_chat_brief.md")
INPUT_APPROVED_ASSETS = os.environ.get("HSD_APPROVED_GRAPHICS_ASSETS", "approved_graphics_assets.csv")
INPUT_FACT_WARNINGS = os.environ.get("HSD_FACT_WARNING_QUEUE", "fact_warning_queue.csv")

MAIN_RESULT_REQUIRED_PLAYERS = {
    "Jessica Shepard", "Arike Ogunbowale", "Paige Bueckers",
    "Kelsey Plum", "Ariel Atkins", "Dearica Hamby", "Nneka Ogwumike", "Cameron Brink",
}

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
    bundle_name = clean(bundle.get("bundle_name")).lower()
    matched = []
    for a in assets:
        name = clean(a.get("entity_name"))
        if not name:
            continue
        name_l = name.lower()
        if name_l in blob:
            matched.append(a)
            continue
        # Main result requires player/person assets even when the original source packet only names one side.
        if "main wnba result" in bundle_name and name in MAIN_RESULT_REQUIRED_PLAYERS:
            matched.append(a)
    seen = set(); out=[]
    for a in matched:
        key = a.get("approved_asset_id") or a.get("source_url") or a.get("entity_name")
        if key in seen:
            continue
        seen.add(key); out.append(a)
    return out

def warnings_for_bundle(bundle, warnings):
    """Attach warnings by bundle_id when possible, otherwise by subject/detail text.

    v1.2 found warnings but sometimes the warning bundle_id and the later visual
    bundle_id did not match because the bundle source was parsed from a different
    file. This fallback makes sure high-risk warnings still reach prompts and QA.
    """
    bundle_id = bundle.get("bundle_id")
    blob = " ".join(str(v).lower() for v in bundle.values())
    out = []
    for w in warnings:
        if w.get("bundle_id") and w.get("bundle_id") == bundle_id:
            out.append(w)
            continue
        subject = clean(w.get("subject")).lower()
        details = clean(w.get("details")).lower()
        if subject and subject in blob:
            out.append(w)
            continue
        # For player/team mismatch warnings, also match if the named teams appear.
        if w.get("warning_type") == "player_team_mismatch":
            for token in re.findall(r"(?:expected team|says) ([A-Z][A-Za-z .'-]+)", w.get("details", "")):
                if clean(token).lower() in blob:
                    out.append(w)
                    break
    # Dedupe by warning_id/details.
    seen = set()
    deduped = []
    for w in out:
        key = w.get("warning_id") or w.get("details")
        if key in seen:
            continue
        seen.add(key)
        deduped.append(w)
    return deduped

def prompt(bundle, assets, warnings):
    m=matched_assets(bundle,assets)
    bundle_warnings = warnings_for_bundle(bundle, warnings)
    player_assets = [a for a in m if a.get("entity_type") == "player"]
    approved_asset_block="\n".join([f"- {a.get('entity_name')} | {a.get('approved_variant')} | {a.get('source_url')}" for a in m]) or "No approved exact assets matched. Use premium text-forward design. Do not invent logos or players."
    warning_block="\n".join([f"- {w.get('warning_type')}: {w.get('details')}" for w in bundle_warnings]) or "No fact warnings."
    safe_mode = "logos_and_text_only" if not player_assets else "player_images_allowed"
    safe_instruction = "Do not show any player photo. Use team logos, typography, score treatment, textures, and editorial design only." if safe_mode == "logos_and_text_only" else "Player photos are allowed only for approved exact player assets listed below. Never invent or substitute."

    return f"""HSD VISUAL UPGRADE v2.5 PROMPT
Bundle: {clean(bundle.get('bundle_name'))}
Template: {template_for(bundle)}
Canvas: 1080x1350 carousel
Source facts: {clean(bundle.get('source_headlines'))}
Caption/context: {clean(bundle.get('caption_seed'))}
Accuracy lock: {clean(bundle.get('accuracy_lock'))}

Safe graphics mode: {safe_mode}
Critical instruction: {safe_instruction}

Approved exact assets:
{approved_asset_block}

Fact warnings:
{warning_block}

Art direction:
Create a premium women’s sports media carousel, not a dashboard card. Use bold hierarchy, huge result typography, sport-specific atmosphere, diagonal panels, depth, glow accents, and a polished CTA/end slide.
If no approved exact player asset is listed, do not use player photography. Use text-forward design with logos, flags, sport texture, court or field lines, and scoreboard energy.
Never invent player bodies, fake jerseys, fake jersey numbers, fake logos, fake headshots, unsupported stats, rankings, injuries, quotes, or records.
If a fact warning exists, require manual human verification before posting.
Accuracy beats aesthetics, but aesthetics must be premium.
""".strip()

def main():
    Path("brand_system").mkdir(exist_ok=True)
    Path("studio_templates_v2").mkdir(exist_ok=True)
    Path("visual_upgrade_dashboard").mkdir(exist_ok=True)
    bundles=load_bundles()
    assets=read_csv_any(INPUT_APPROVED_ASSETS)
    warnings=read_csv_any(INPUT_FACT_WARNINGS)
    Path("brand_system/hsd_tokens.json").write_text(json.dumps(tokens(),indent=2),encoding="utf-8")
    rules={"version":VERSION,"rules":["one dominant thesis per slide","never use boxed tables as full design","use exact assets only","text-forward when player assets missing","CTA/end slide required","manual review on fact warnings"]}
    Path("brand_system/hsd_template_rules.json").write_text(json.dumps(rules,indent=2),encoding="utf-8")
    for t in ["carousel_cover_v2","result_slide_v2","roundup_v2","radar_v2","cta_v2"]:
        Path(f"studio_templates_v2/{t}.json").write_text(json.dumps({"template":t,"tokens":"brand_system/hsd_tokens.json"},indent=2),encoding="utf-8")
    lines=["# HSD Bundle Prompts v2.2","",f"Generated: {now()}",""]
    render={"version":VERSION,"generated_at_utc":now(),"bundles":[]}
    for i,b in enumerate(bundles,1):
        slug=slugify(b.get("bundle_name") or f"bundle-{i}")
        m=matched_assets(b,assets)
        bw=warnings_for_bundle(b, warnings)
        player_assets = [a.get("approved_asset_id") for a in m if a.get("entity_type") == "player" and a.get("approved_asset_id")]
        safe_mode = "logos_and_text_only" if not player_assets else "player_images_allowed"
        lines += [f"## {clean(b.get('bundle_name'))}","","```text",prompt(b,assets,warnings),"```",""]
        render["bundles"].append({
            "bundle_id":b.get("bundle_id") or f"bundle_{i}",
            "post_slug":slug,
            "bundle_name":b.get("bundle_name"),
            "template_name":template_for(b),
            "asset_ids":[a.get("approved_asset_id") for a in m if a.get("approved_asset_id")],
            "safe_graphics_mode": safe_mode,
            "fact_warning_count": len(bw),
            "source_facts":{"source_headlines":b.get("source_headlines"),"caption_seed":b.get("caption_seed"),"accuracy_lock":b.get("accuracy_lock")},
            "text_layers":[{"layer_id":slug+"_headline","text":b.get("bundle_name"),"font_size_px":72,"font_weight":800,"color_hex":"#F4F7FB","background_hex":"#071226","essential":True}],
            "all_layers":[{"layer_id":slug+"_watermark","bbox":[48,48,76,76]},{"layer_id":slug+"_headline","bbox":[96,160,850,220]},{"layer_id":slug+"_cta","bbox":[96,1150,888,110]}],
            "render_path":f"generated_graphics/{slug}.png"
        })
    Path("studio_bundle_prompts_v2.md").write_text("\n".join(lines),encoding="utf-8")
    Path("studio_render_manifest_v2.json").write_text(json.dumps(render,indent=2),encoding="utf-8")
    Path("studio_visual_upgrade_v2.md").write_text(f"# HSD Studio Visual Upgrade v2.2\n\nGenerated: {now()}\n\nBundles: {len(bundles)}\nApproved exact assets: {len(assets)}\nFact warnings: {len(warnings)}\n",encoding="utf-8")
    Path("visual_upgrade_manifest.json").write_text(json.dumps({"version":VERSION,"generated_at_utc":now(),"counts":{"bundles":len(bundles),"approved_assets":len(assets),"fact_warnings":len(warnings),"warnings_propagated_to_prompts":sum(1 for b in bundles if warnings_for_bundle(b, warnings))}},indent=2),encoding="utf-8")
    Path("visual_upgrade_dashboard/index.html").write_text(f"<html><body><h1>HSD Visual Upgrade v2.2</h1><p>Bundles: {len(bundles)}</p><p>Assets: {len(assets)}</p><p>Fact warnings: {len(warnings)}</p></body></html>",encoding="utf-8")
    print("Created HSD Visual Upgrade v2.2 outputs")

if __name__=="__main__":
    main()
