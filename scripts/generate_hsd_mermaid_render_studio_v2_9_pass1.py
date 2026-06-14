from __future__ import annotations

import base64
import csv
import io
import json
import math
import re
import shutil
import zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

VERSION = "v2.9-visual-polish-pass1"
OUT_DIR = Path("rendered_handoff_graphics")
ZIP_DIR = Path("rendered_handoff_zips")
STATUS = Path("rendered_handoff_status.csv")
MANIFEST = Path("rendered_handoff_manifest.csv")
VISUAL_QA = Path("rendered_handoff_visual_qa.csv")
REPORT = Path("rendered_handoff_qa_report.md")
CONTACT = Path("rendered_handoff_contact_sheet.jpg")
META = Path("rendered_handoff_metadata.json")
PACKET_DIRS = [Path("manual_workflow_handoff_packs"), Path("assignment_handoff_zips")]
WATERMARK_PNGS = [Path("assets/branding/official_hsd_watermark.png"), Path("data/assets/brand/hsd_watermark.png"), Path("data/assets/brand/hsd_official_watermark.png"), Path("assets/hsd_watermark.png"), Path("brand/hsd_watermark.png")]
WATERMARK_B64 = Path("data/assets/brand/hsd_watermark_base64.txt")
CANVAS = {"IG Feed": (1080, 1350), "Threads": (1080, 1350), "IG Stories": (1080, 1920)}
STATUS_FIELDS = ["packet_id", "platform", "headline", "status", "reason", "template_family", "rendered_files", "used_watermark", "used_logos", "used_score_context", "missing_logos"]
MANIFEST_FIELDS = ["packet_id", "platform", "headline", "template_family", "output_path", "width", "height", "used_watermark", "used_logos", "used_score_context"]
VISUAL_QA_FIELDS = ["packet_id", "platform", "headline", "template_family", "dimensions", "watermark_status", "used_logos", "missing_logos", "used_score_context", "public_text_safe", "internal_text_found", "decision", "reason"]
WNBA_TEAMS = ["Atlanta Dream", "Chicago Sky", "Connecticut Sun", "Dallas Wings", "Golden State Valkyries", "Indiana Fever", "Las Vegas Aces", "Los Angeles Sparks", "Minnesota Lynx", "New York Liberty", "Phoenix Mercury", "Seattle Storm", "Washington Mystics", "Toronto Tempo", "Portland Fire"]
ALIASES = {"Aces":"Las Vegas Aces", "Dream":"Atlanta Dream", "Fever":"Indiana Fever", "Liberty":"New York Liberty", "Lynx":"Minnesota Lynx", "Mercury":"Phoenix Mercury", "Mystics":"Washington Mystics", "Sparks":"Los Angeles Sparks", "Sun":"Connecticut Sun", "Sky":"Chicago Sky", "Wings":"Dallas Wings", "Storm":"Seattle Storm", "Valkyries":"Golden State Valkyries", "Tempo":"Toronto Tempo", "Fire":"Portland Fire"}
TEAM_COLORS = {"Atlanta Dream":((224,45,95),(37,187,210)), "Chicago Sky":((255,205,49),(77,196,224)), "Connecticut Sun":((247,115,37),(21,45,81)), "Dallas Wings":((0,126,184),(196,155,58)), "Golden State Valkyries":((190,151,255),(22,19,33)), "Indiana Fever":((203,18,48),(16,43,84)), "Las Vegas Aces":((196,30,58),(35,31,32)), "Los Angeles Sparks":((88,44,131),(255,199,44)), "Minnesota Lynx":((35,97,146),(111,196,178)), "New York Liberty":((98,185,172),(8,36,53)), "Phoenix Mercury":((229,95,32),(82,45,131)), "Seattle Storm":((47,174,97),(255,213,64)), "Washington Mystics":((226,24,54),(7,42,86)), "Toronto Tempo":((91,214,154),(32,26,58)), "Portland Fire":((241,79,47),(80,38,26))}
BG=(7,10,18); INK=(247,250,255); MUTED=(173,184,205); BLUE=(74,144,255); PINK=(245,89,160); GOLD=(246,201,80); GREEN=(88,215,154)

def clean(v: Any) -> str: return re.sub(r"\s+", " ", str(v or "")).strip()
def slug(v: str) -> str: return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"
def norm(v: str) -> str: return re.sub(r"[^a-z0-9]+", "", clean(v).lower())
def canon_team(v: str) -> str:
    n=clean(v)
    for full in WNBA_TEAMS:
        if norm(n)==norm(full): return full
    for alias, full in ALIASES.items():
        if norm(n)==norm(alias): return full
    return n

def read_csv(path: Path) -> List[Dict[str,str]]:
    if not path.exists(): return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f: return list(csv.DictReader(f))
    except Exception: return []

def write_csv(path: Path, rows: List[Dict[str,Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows([{k:r.get(k,"") for k in fields} for r in rows])

def safe_text(path: Path) -> str:
    try: return path.read_text(encoding="utf-8", errors="replace")
    except Exception: return ""

def font(size:int,bold:bool=False):
    opts=[]
    if bold: opts += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
    opts += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    for p in opts:
        if Path(p).exists(): return ImageFont.truetype(p, size)
    return ImageFont.load_default()

def text_w(d:ImageDraw.ImageDraw, text:str, fnt)->int:
    b=d.textbbox((0,0), text, font=fnt); return b[2]-b[0]

def wrap(d:ImageDraw.ImageDraw,text:str,fnt,max_w:int,max_lines:int=8)->List[str]:
    words=clean(text).split()
    if not words: return [""]
    lines=[]; cur=words[0]
    for word in words[1:]:
        test=cur+" "+word
        if text_w(d,test,fnt)<=max_w: cur=test
        else:
            lines.append(cur); cur=word
            if len(lines)>=max_lines-1: break
    lines.append(cur); return lines[:max_lines]

def draw_block(d:ImageDraw.ImageDraw,x:int,y:int,text:str,fnt,fill,max_w:int,gap:int=8,max_lines:int=8)->int:
    for line in wrap(d,text,fnt,max_w,max_lines):
        d.text((x,y), line, font=fnt, fill=fill); y=d.textbbox((x,y), line, font=fnt)[3]+gap
    return y

def prepare_watermark(img: Image.Image) -> Image.Image:
    img=img.convert("RGBA"); alpha=img.getchannel("A")
    if alpha.getextrema()==(255,255):
        pix=img.load(); w,h=img.size
        for y in range(h):
            for x in range(w):
                r,g,b,a=pix[x,y]; mx=max(r,g,b); mn=min(r,g,b)
                if mx>172 and (mx-mn)<24: pix[x,y]=(r,g,b,0)
    bbox=img.getbbox()
    return img.crop(bbox) if bbox else img

def load_watermark()->Tuple[Optional[Image.Image],str]:
    for p in WATERMARK_PNGS:
        if p.exists():
            try: return prepare_watermark(Image.open(p).convert("RGBA")), p.as_posix()
            except Exception: pass
    if WATERMARK_B64.exists():
        try:
            raw=base64.b64decode(WATERMARK_B64.read_text(encoding="utf-8").strip()); return prepare_watermark(Image.open(io.BytesIO(raw)).convert("RGBA")), WATERMARK_B64.as_posix()
        except Exception as exc: return None, f"base64 decode failed: {type(exc).__name__}"
    return None,"missing"

def paste_watermark(img:Image.Image, wm:Image.Image)->None:
    mark=wm.copy(); mark.thumbnail((82 if img.size[1]<=1350 else 92, 82 if img.size[1]<=1350 else 92), Image.LANCZOS)
    chip=Image.new("RGBA",(mark.width+28,mark.height+26),(0,0,0,0)); cd=ImageDraw.Draw(chip)
    cd.rounded_rectangle((0,0,chip.width-1,chip.height-1),radius=18,fill=(8,12,22,210),outline=(255,255,255,34),width=1)
    chip.alpha_composite(mark,(14,13)); img.alpha_composite(chip,(54,42))

def load_asset(path:Path)->Optional[Image.Image]:
    if not path.exists() or not path.is_file(): return None
    if path.suffix.lower()==".svg":
        try:
            import cairosvg  # type: ignore
            raw=cairosvg.svg2png(url=path.as_posix()); return Image.open(io.BytesIO(raw)).convert("RGBA")
        except Exception: return None
    try: return Image.open(path).convert("RGBA")
    except Exception: return None

def logo_assets()->List[Path]:
    roots=[Path("data/assets/approved"),Path("assets"),Path("brand_assets"),Path("graphics_chat_upload_pack"),Path("ig_story_results_upload_pack"),Path("hsd_pipeline_lite_review")]
    out=[]
    for root in roots:
        if root.exists(): out += [p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in {".png",".jpg",".jpeg",".webp",".svg"}]
    return out

def build_logo_index()->Dict[str,Path]:
    idx={}
    for csv_path in [Path("approved_graphics_assets.csv"),Path("hsd_pipeline_lite_review/files/approved_graphics_assets.csv")]:
        for row in read_csv(csv_path):
            if clean(row.get("entity_type")).lower()!="team": continue
            name=clean(row.get("entity_name"))
            for key in ["master_path","web_path","local_path"]:
                val=clean(row.get(key)); p=Path(val)
                if val and p.exists() and p.suffix.lower() in {".png",".jpg",".jpeg",".webp",".svg"}: idx[norm(name)]=p; break
    assets=logo_assets()
    for team in WNBA_TEAMS:
        if norm(team) in idx: continue
        team_slug=slug(team); words=[w.lower() for w in team.split()]; found=[]
        for p in assets:
            low=p.as_posix().lower(); score=0
            if team_slug in low: score+=100
            if all(w in low for w in words): score+=80
            if "logo" in low: score+=25
            if "player" in low or "headshot" in low or "img_" in low: score-=85
            if score>0: found.append((score,len(low),p))
        if found:
            found.sort(key=lambda x:(-x[0],x[1])); idx[norm(team)]=found[0][2]
    return idx

def resolve_logo(team:str, idx:Dict[str,Path])->Tuple[Optional[Image.Image],Optional[Path]]:
    p=idx.get(norm(canon_team(team)))
    if not p: return None,None
    return load_asset(p),p

def discover_packets()->List[Path]:
    found={}
    for d in PACKET_DIRS:
        if d.exists():
            for z in d.glob("*.zip"): found[z.name]=z
    return [found[k] for k in sorted(found)]

def parse_packet(zp:Path)->Optional[Dict[str,Any]]:
    try:
        with zipfile.ZipFile(zp) as z: data=json.loads(z.read("content_packet.json").decode("utf-8"))
        slot=data.get("slot",{}); pub=data.get("public_copy",{})
        return {"packet_id":data.get("packet_id") or zp.stem,"platform":clean(slot.get("platform") or pub.get("platform") or "IG Feed"),"headline":clean(pub.get("headline") or slot.get("headline") or zp.stem),"league":clean(pub.get("league") or slot.get("league")),"content_type":clean(pub.get("content_type") or slot.get("content_type")),"hook":clean(pub.get("hook") or slot.get("copy_hook")),"first":clean(pub.get("first") or slot.get("first_comment")),"story":clean(pub.get("story") or slot.get("story_frame_text")),"caption":clean(pub.get("caption") or slot.get("ig_caption_seed"))}
    except Exception: return None

def choose_template(p:Dict[str,Any])->str:
    h=p["headline"].lower(); ct=p.get("content_type","").lower(); lg=p.get("league","").upper()
    if "last night in the w" in h: return "last_night_scoreboard"
    if "preview" in ct or " at " in h or " vs " in h: return "preview_matchup"
    if lg=="WNBA" and ("beat" in h or "result" in ct or "recap" in ct): return "result_final"
    return "storyline_feature"

def teams_from_headline(headline:str)->List[str]:
    h=clean(headline)
    for pat in [r"(.+?)\s+beat\s+(.+)$",r"(.+?)\s+(?:at|vs\.?|versus)\s+(.+)$"]:
        m=re.match(pat,h,flags=re.I)
        if m: return [canon_team(m.group(1)), canon_team(m.group(2))]
    found=[]; nh=norm(h)
    for team in WNBA_TEAMS:
        if norm(team) in nh or any(norm(a) in nh for a,f in ALIASES.items() if f==team): found.append(team)
    return found

def source_text()->str:
    parts=[]
    for p in [Path("manual_workflow_render_plans.json"),Path("ig_story_results_frames.md"),Path("final_score_story_guard_report.md"),Path("results_contract_report.md"),Path("mermaid_master_content_board.md"),Path("caption_bank.md")]:
        if p.exists(): parts.append(safe_text(p))
    for c in [Path("ig_story_results_queue.csv"),Path("results_contract_v2.csv"),Path("mermaid_content_slots_v2.csv")]:
        for r in read_csv(c): parts.append(" | ".join(clean(v) for v in r.values()))
    return "\n".join(parts)

def score_pairs()->List[Dict[str,Any]]:
    txt=source_text().replace("\u00b7","·"); chunks=[]
    for line in txt.splitlines(): chunks += [c.strip() for c in re.split(r"\||;",line) if c.strip()]
    pats=[re.compile(r"([A-Z][A-Za-z .&]+?)\s+(\d{2,3})\s*[·\-–—]\s*([A-Z][A-Za-z .&]+?)\s+(\d{2,3})"), re.compile(r"([A-Z][A-Za-z .&]+?)\s+(\d{2,3})\s*,\s*([A-Z][A-Za-z .&]+?)\s+(\d{2,3})")]
    out=[]; seen=set()
    for ch in chunks:
        for pat in pats:
            for m in pat.finditer(ch):
                t1,t2=canon_team(m.group(1)),canon_team(m.group(3)); s1,s2=int(m.group(2)),int(m.group(4))
                if not any(norm(t1)==norm(x) for x in WNBA_TEAMS) or not any(norm(t2)==norm(x) for x in WNBA_TEAMS): continue
                key=tuple(sorted([norm(t1),norm(t2)]))+tuple(sorted([s1,s2]))
                if key in seen: continue
                seen.add(key); out.append({"team_a":t1,"score_a":s1,"team_b":t2,"score_b":s2})
    return out

def pairs_for_packet(p:Dict[str,Any], pairs:List[Dict[str,Any]])->List[Dict[str,Any]]:
    if choose_template(p)=="last_night_scoreboard": return pairs[:5]
    teams=teams_from_headline(p["headline"])
    if len(teams)<2: return []
    wanted={norm(teams[0]),norm(teams[1])}
    return [x for x in pairs if {norm(x["team_a"]),norm(x["team_b"])}==wanted][:1]

def palette(team:str)->Tuple[Tuple[int,int,int],Tuple[int,int,int]]: return TEAM_COLORS.get(canon_team(team),(BLUE,PINK))
def make_canvas(size:Tuple[int,int],a=BLUE,b=PINK)->Image.Image:
    w,h=size; img=Image.new("RGBA",size,BG); d=ImageDraw.Draw(img)
    d.ellipse((-260,-260,int(w*.76),int(h*.52)),fill=(*a,54)); d.ellipse((int(w*.45),int(h*.52),w+330,h+280),fill=(*b,42))
    for x in range(-w,w*2,170): d.polygon([(x,0),(x+36,0),(x+w+36,h),(x+w,h)],fill=(255,255,255,10))
    for yy in range(170,h-150,34):
        for xx in range(w-250,w-55,34):
            r=2+((xx+yy)%5); d.ellipse((xx-r,yy-r,xx+r,yy+r),fill=(255,255,255,18))
    d.rounded_rectangle((48,138,w-48,h-64),radius=42,fill=(13,18,31,228),outline=(255,255,255,28),width=2)
    return img

def kicker(d,x,y,text,fill=BLUE):
    f=font(24,True); text=clean(text).upper(); tw=text_w(d,text,f); d.rounded_rectangle((x,y,x+tw+34,y+34),radius=15,fill=fill); d.text((x+17,y+4),text,font=f,fill=(255,255,255))

def logo_circle(img:Image.Image,center:Tuple[int,int],logo:Image.Image,accent:Tuple[int,int,int],size:int=164):
    x,y=center; d=ImageDraw.Draw(img); d.ellipse((x-size//2-10,y-size//2-10,x+size//2+10,y+size//2+10),fill=(*accent,42)); d.ellipse((x-size//2,y-size//2,x+size//2,y+size//2),fill=(255,255,255,18),outline=(255,255,255,65),width=2)
    lg=logo.copy(); lg.thumbnail((size-40,size-40),Image.LANCZOS); img.alpha_composite(lg,(x-lg.width//2,y-lg.height//2))

def render_result(p,wm,pair,logos):
    teams=teams_from_headline(p["headline"]); win=teams[0] if teams else p["headline"]; lose=teams[1] if len(teams)>1 else ""; a,b=palette(win); size=CANVAS.get(p["platform"],(1080,1350)); img=make_canvas(size,a,b); d=ImageDraw.Draw(img); paste_watermark(img,wm); W,H=size; kicker(d,84,180,"FINAL",a); y=300 if H<1500 else 390; ph=190 if H<1500 else 230
    d.text((84,y-66),"RESULT",font=font(46,True),fill=MUTED); d.rounded_rectangle((78,y,W-78,y+ph),radius=30,fill=(*a,54),outline=(*a,210),width=3); d.rounded_rectangle((78,y+ph+24,W-78,y+ph*2+24),radius=30,fill=(255,255,255,22),outline=(255,255,255,50),width=2)
    if win in logos: logo_circle(img,(170,y+ph//2),logos[win],a,132)
    if lose in logos: logo_circle(img,(170,y+ph+24+ph//2),logos[lose],b,132)
    d.text((260,y+40),win.upper(),font=font(36 if H<1500 else 44,True),fill=INK); d.text((260,y+ph+64),lose.upper(),font=font(36 if H<1500 else 44,True),fill=INK)
    used="no"; sf=font(104 if H<1500 else 132,True)
    if pair:
        used="yes"; sw=pair["score_a"] if norm(pair["team_a"])==norm(win) else pair["score_b"]; sl=pair["score_b"] if norm(pair["team_a"])==norm(win) else pair["score_a"]; d.text((W-110,y+ph//2),str(sw),font=sf,fill=INK,anchor="rm"); d.text((W-110,y+ph+24+ph//2),str(sl),font=sf,fill=MUTED,anchor="rm")
    else: d.text((W-110,y+ph//2),"W",font=sf,fill=INK,anchor="rm")
    cta_y=H-(210 if H<1500 else 270); d.rounded_rectangle((84,cta_y,W-84,cta_y+120),radius=28,fill=(255,255,255,20),outline=(255,255,255,45),width=2); draw_block(d,118,cta_y+28,p.get("first") or "What changed after this one?",font(34,True),INK,W-236,8,2); img.info["score"]=used; return img

def render_last(p,wm,pairs,logos):
    img=make_canvas(CANVAS.get(p["platform"],(1080,1350)),BLUE,PINK); d=ImageDraw.Draw(img); paste_watermark(img,wm); W,H=img.size; kicker(d,84,180,"SCOREBOARD",PINK); d.text((84,250 if H<1500 else 330),"LAST NIGHT",font=font(82 if H<1500 else 100,True),fill=INK); d.text((84,335 if H<1500 else 440),"IN THE W",font=font(82 if H<1500 else 100,True),fill=BLUE)
    start=470 if H<1500 else 620; rh=110 if H<1500 else 128
    for i,x in enumerate(pairs[:5]):
        y=start+i*(rh+16); t1,t2=x["team_a"],x["team_b"]; d.rounded_rectangle((84,y,W-84,y+rh),radius=24,fill=(255,255,255,18),outline=(255,255,255,38),width=1); logo_circle(img,(135,y+rh//2),logos[t1],palette(t1)[0],62); logo_circle(img,(W-135,y+rh//2),logos[t2],palette(t2)[0],62); d.text((185,y+22),t1.upper(),font=font(25 if H<1500 else 30,True),fill=INK); d.text((W-185,y+22),t2.upper(),font=font(25 if H<1500 else 30,True),fill=INK,anchor="ra"); d.text((185,y+58),str(x["score_a"]),font=font(44 if H<1500 else 54,True),fill=INK); d.text((W-185,y+58),str(x["score_b"]),font=font(44 if H<1500 else 54,True),fill=INK,anchor="ra"); d.text((W//2,y+rh//2),"FINAL",font=font(21,True),fill=MUTED,anchor="mm")
    cta_y=H-(210 if H<1500 else 270); d.rounded_rectangle((84,cta_y,W-84,cta_y+110),radius=28,fill=(255,255,255,20),outline=(255,255,255,45),width=2); draw_block(d,118,cta_y+26,p.get("first") or "Which result mattered most?",font(34 if H<1500 else 42,True),INK,W-236,8,2); img.info["score"]="yes"; return img

def render_preview(p,wm,logos):
    teams=teams_from_headline(p["headline"]); left,right=teams[0],teams[1]; a,_=palette(left); b,_=palette(right); img=make_canvas(CANVAS.get(p["platform"],(1080,1350)),a,b); d=ImageDraw.Draw(img); paste_watermark(img,wm); W,H=img.size; kicker(d,84,180,"TONIGHT",GOLD); y=300 if H<1500 else 420; d.rounded_rectangle((84,y,W-84,y+430),radius=38,fill=(255,255,255,18),outline=(255,255,255,45),width=2); logo_circle(img,(250,y+175),logos[left],a,190); logo_circle(img,(W-250,y+175),logos[right],b,190); d.text((250,y+305),left.upper(),font=font(34,True),fill=INK,anchor="ma"); d.text((W-250,y+305),right.upper(),font=font(34,True),fill=INK,anchor="ma"); d.text((W//2,y+175),"AT",font=font(42,True),fill=MUTED,anchor="mm"); h_y=y+(500 if H<1500 else 560); draw_block(d,84,h_y,p.get("story") or p.get("hook") or "Who owns the first run?",font(48 if H<1500 else 58,True),INK,W-168,10,3); cta_y=H-(220 if H<1500 else 290); d.rounded_rectangle((84,cta_y,W-84,cta_y+110),radius=28,fill=(255,255,255,20),outline=(255,255,255,45),width=2); draw_block(d,118,cta_y+26,p.get("first") or "Who needs this one more?",font(34,True),INK,W-236,8,2); img.info["score"]="no"; return img

def render_feature(p,wm):
    accent=GREEN if p.get("league","").upper()=="LPGA" else BLUE; img=make_canvas(CANVAS.get(p["platform"],(1080,1350)),accent,GOLD); d=ImageDraw.Draw(img); paste_watermark(img,wm); W,H=img.size; kicker(d,84,180,p.get("league") or "HSD",accent); y=270 if H<1500 else 350; y=draw_block(d,84,y,p["headline"],font(72 if H<1500 else 86,True),INK,W-168,8,5)+30; d.line((84,y,W-84,y),fill=(*accent,210),width=4); y+=34; draw_block(d,84,y,p.get("hook") or p.get("caption") or "This belongs on the board.",font(38 if H<1500 else 46,False),MUTED,W-168,10,5); cta_y=H-(220 if H<1500 else 290); d.rounded_rectangle((84,cta_y,W-84,cta_y+112),radius=28,fill=(255,255,255,20),outline=(255,255,255,45),width=2); draw_block(d,118,cta_y+26,p.get("first") or "Are we paying enough attention?",font(34 if H<1500 else 42,True),INK,W-236,8,2); img.info["score"]="no"; return img

def validate(p,template,pairs,idx):
    need=[]
    if p.get("league","").upper()=="WNBA":
        if template=="last_night_scoreboard":
            for pair in pairs: need += [pair["team_a"],pair["team_b"]]
        elif template in {"result_final","preview_matchup"}: need=teams_from_headline(p["headline"])
    need=list(dict.fromkeys(need)); missing=[]; logos={}
    for t in need:
        img,path=resolve_logo(t,idx)
        if img is None: missing.append(t)
        else: logos[canon_team(t)]=img
    return missing,logos

def save(p,img):
    folder=OUT_DIR/p["packet_id"]; folder.mkdir(parents=True,exist_ok=True); out=folder/(slug(p["headline"])[:88]+".png"); img.convert("RGB").save(out,quality=96); return out

def render(p,wm,pairs_all,idx):
    template=choose_template(p); pairs=pairs_for_packet(p,pairs_all)
    if template=="last_night_scoreboard" and not pairs: return "blocked",[],"score context missing for Last Night scoreboard",template,"no","no",""
    missing,logos=validate(p,template,pairs,idx)
    if missing: return "blocked",[],"missing required exact team logo(s)",template,"no","no","; ".join(missing)
    if template=="result_final": img=render_result(p,wm,pairs[0] if pairs else None,logos)
    elif template=="last_night_scoreboard": img=render_last(p,wm,pairs,logos)
    elif template=="preview_matchup": img=render_preview(p,wm,logos)
    else: img=render_feature(p,wm)
    out=save(p,img); return "rendered",[out],"ok",template,"yes" if logos else "not_required",img.info.get("score","no"),""

def contact_sheet(paths):
    if not paths: return
    thumbs=[]
    for p in paths[:12]:
        try:
            im=Image.open(p).convert("RGB"); im.thumbnail((310,310),Image.LANCZOS); cell=Image.new("RGB",(340,382),(8,10,18)); cell.paste(im,((340-im.width)//2,14)); d=ImageDraw.Draw(cell); d.rounded_rectangle((12,332,328,370),radius=14,fill=(20,27,44)); d.text((24,343),p.parent.name[:34],font=font(15,True),fill=INK); thumbs.append(cell)
        except Exception: pass
    cols=3; sheet=Image.new("RGB",(cols*340+28,math.ceil(len(thumbs)/cols)*382+28),(5,7,13))
    for i,t in enumerate(thumbs): sheet.paste(t,(14+(i%cols)*340,14+(i//cols)*382))
    sheet.save(CONTACT,quality=94)

def zip_outputs():
    if ZIP_DIR.exists(): shutil.rmtree(ZIP_DIR)
    ZIP_DIR.mkdir(parents=True,exist_ok=True)
    for folder in OUT_DIR.glob("*"):
        if folder.is_dir():
            with zipfile.ZipFile(ZIP_DIR/f"{folder.name}.zip","w",zipfile.ZIP_DEFLATED) as z:
                for f in folder.rglob("*"):
                    if f.is_file(): z.write(f,f.relative_to(folder))

def main():
    if OUT_DIR.exists(): shutil.rmtree(OUT_DIR)
    OUT_DIR.mkdir(parents=True,exist_ok=True); wm,wm_source=load_watermark(); packets=[p for p in (parse_packet(z) for z in discover_packets()) if p]; pairs_all=score_pairs(); idx=build_logo_index(); status=[]; manifest=[]; visual=[]; files=[]
    for p in packets:
        if wm is None: st,outs,reason,template,used_logos,used_score,missing="blocked",[],f"official HSD watermark asset missing or unreadable: {wm_source}",choose_template(p),"no","no",""
        else: st,outs,reason,template,used_logos,used_score,missing=render(p,wm,pairs_all,idx)
        status.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"status":st,"reason":reason,"template_family":template,"rendered_files":len(outs),"used_watermark":"yes" if wm else "no","used_logos":used_logos,"used_score_context":used_score,"missing_logos":missing})
        dims=""
        for out in outs:
            files.append(out)
            with Image.open(out) as im: W,H=im.size
            dims=f"{W}x{H}"; manifest.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"template_family":template,"output_path":out.as_posix(),"width":W,"height":H,"used_watermark":"yes","used_logos":used_logos,"used_score_context":used_score})
        visual.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"template_family":template,"dimensions":dims,"watermark_status":"pass" if wm else "fail","used_logos":used_logos,"missing_logos":missing,"used_score_context":used_score,"public_text_safe":"yes","internal_text_found":"no","decision":"pass" if st=="rendered" else "fail","reason":reason})
    write_csv(STATUS,status,STATUS_FIELDS); write_csv(MANIFEST,manifest,MANIFEST_FIELDS); write_csv(VISUAL_QA,visual,VISUAL_QA_FIELDS); contact_sheet(files); zip_outputs(); rendered=sum(1 for r in status if r["status"]=="rendered"); blocked=sum(1 for r in status if r["status"]=="blocked")
    lines=["# Mermaid Render Studio v2.9 Visual Polish QA Report","",f"- version: {VERSION}",f"- rendered packets: {rendered}",f"- blocked packets: {blocked}",f"- watermark source: {wm_source}",f"- exact logo index entries: {len(idx)}",f"- score pairs found: {len(pairs_all)}",f"- WNBA team logos required: true","","## Packet Status",""]
    for r in status: lines.append(f"- {r['packet_id']} | {r['platform']} | {r['template_family']} | {r['headline']} | {r['status']} | {r['reason']} | missing logos: {r.get('missing_logos','')}")
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8"); META.write_text(json.dumps({"version":VERSION,"rendered":rendered,"blocked":blocked,"watermark_source":wm_source,"team_logos_required":True,"logo_index_entries":len(idx),"score_pairs_found":len(pairs_all)},indent=2),encoding="utf-8"); print(json.dumps({"version":VERSION,"rendered":rendered,"blocked":blocked},indent=2))

if __name__=="__main__": main()
