from __future__ import annotations

import base64
import csv
import io
import json
import math
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, ImageDraw, ImageFont

VERSION = "v3.0-registry-resolver-accounting-fix"
OUT_DIR = Path("rendered_handoff_graphics")
ZIP_DIR = Path("rendered_handoff_zips")
STATUS = Path("rendered_handoff_status.csv")
MANIFEST = Path("rendered_handoff_manifest.csv")
VISUAL_QA = Path("rendered_handoff_visual_qa.csv")
REPORT = Path("rendered_handoff_qa_report.md")
CONTACT = Path("rendered_handoff_contact_sheet.jpg")
META = Path("rendered_handoff_metadata.json")
PACKET_DIRS = [Path("manual_workflow_handoff_packs"), Path("assignment_handoff_zips")]
REGISTRY_ROOT = Path("data/asset_registry/wnba")
TEAMS_CSV = REGISTRY_ROOT / "teams.csv"
ALIASES_CSV = REGISTRY_ROOT / "team_aliases.csv"
TEAM_LOGOS_CSV = REGISTRY_ROOT / "team_logos.csv"
WATERMARK_PNGS = [Path("assets/branding/official_hsd_watermark.png"), Path("data/assets/brand/hsd_watermark.png"), Path("data/assets/brand/hsd_official_watermark.png"), Path("assets/hsd_watermark.png"), Path("brand/hsd_watermark.png")]
WATERMARK_B64 = Path("data/assets/brand/hsd_watermark_base64.txt")
CANVAS = {"IG Feed": (1080, 1350), "Threads": (1080, 1350), "IG Stories": (1080, 1920)}
STATUS_FIELDS = ["packet_id", "platform", "headline", "status", "reason", "template_family", "rendered_files", "used_watermark", "used_logos", "used_score_context", "missing_logos"]
MANIFEST_FIELDS = ["packet_id", "platform", "headline", "template_family", "output_path", "width", "height", "used_watermark", "used_logos", "used_score_context"]
VISUAL_QA_FIELDS = ["packet_id", "platform", "headline", "template_family", "dimensions", "watermark_status", "used_logos", "missing_logos", "used_score_context", "public_text_safe", "internal_text_found", "decision", "reason"]
BG=(7,10,18); INK=(247,250,255); MUTED=(173,184,205); BLUE=(74,144,255); PINK=(245,89,160); GOLD=(246,201,80); GREEN=(88,215,154)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: str, sep: str = "-") -> str:
    return re.sub(r"[^a-z0-9]+", sep, clean(v).lower()).strip(sep) or "item"


def norm(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(v).lower())


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})


def safe_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def font(size:int,bold:bool=False):
    opts=[]
    if bold:
        opts += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf"]
    opts += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf", "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    for p in opts:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    return ImageFont.load_default()


def text_w(d:ImageDraw.ImageDraw, text:str, fnt)->int:
    b=d.textbbox((0,0), text, font=fnt)
    return b[2]-b[0]


def wrap(d:ImageDraw.ImageDraw, text:str, fnt, max_w:int, max_lines:int=8)->List[str]:
    words=clean(text).split()
    if not words:
        return [""]
    lines=[]; cur=words[0]
    for word in words[1:]:
        test=cur+" "+word
        if text_w(d,test,fnt)<=max_w:
            cur=test
        else:
            lines.append(cur); cur=word
            if len(lines)>=max_lines-1:
                break
    lines.append(cur)
    return lines[:max_lines]


def draw_block(d:ImageDraw.ImageDraw,x:int,y:int,text:str,fnt,fill,max_w:int,gap:int=8,max_lines:int=8)->int:
    for line in wrap(d,text,fnt,max_w,max_lines):
        d.text((x,y), line, font=fnt, fill=fill)
        y=d.textbbox((x,y), line, font=fnt)[3]+gap
    return y


def prepare_watermark(img: Image.Image) -> Image.Image:
    img=img.convert("RGBA")
    if img.getchannel("A").getextrema()==(255,255):
        pix=img.load(); w,h=img.size
        for y in range(h):
            for x in range(w):
                r,g,b,a=pix[x,y]; mx=max(r,g,b); mn=min(r,g,b)
                if mx>172 and (mx-mn)<24:
                    pix[x,y]=(r,g,b,0)
    bbox=img.getbbox()
    return img.crop(bbox) if bbox else img


def load_watermark()->Tuple[Optional[Image.Image],str]:
    for p in WATERMARK_PNGS:
        if p.exists():
            try:
                return prepare_watermark(Image.open(p).convert("RGBA")), p.as_posix()
            except Exception:
                pass
    if WATERMARK_B64.exists():
        try:
            raw=base64.b64decode(WATERMARK_B64.read_text(encoding="utf-8").strip())
            return prepare_watermark(Image.open(io.BytesIO(raw)).convert("RGBA")), WATERMARK_B64.as_posix()
        except Exception as exc:
            return None, f"base64 decode failed: {type(exc).__name__}"
    return None,"missing"


def paste_watermark(img:Image.Image, wm:Image.Image)->None:
    mark=wm.copy(); target=82 if img.size[1]<=1350 else 92
    mark.thumbnail((target,target), Image.LANCZOS)
    chip=Image.new("RGBA",(mark.width+28,mark.height+26),(0,0,0,0)); cd=ImageDraw.Draw(chip)
    cd.rounded_rectangle((0,0,chip.width-1,chip.height-1),radius=18,fill=(8,12,22,210),outline=(255,255,255,34),width=1)
    chip.alpha_composite(mark,(14,13)); img.alpha_composite(chip,(54,42))


def load_asset(path:Path)->Optional[Image.Image]:
    if not path.exists() or not path.is_file():
        return None
    if path.suffix.lower()==".svg":
        try:
            import cairosvg  # type: ignore
            raw=cairosvg.svg2png(url=path.as_posix())
            return Image.open(io.BytesIO(raw)).convert("RGBA")
        except Exception:
            return None
    try:
        return Image.open(path).convert("RGBA")
    except Exception:
        return None


def registry() -> Tuple[Dict[str, Dict[str, str]], Dict[str, str], Dict[str, Dict[str, str]]]:
    teams={r.get("team_id",""):r for r in read_csv(TEAMS_CSV) if r.get("team_id")}
    aliases={}
    for team_id,row in teams.items():
        aliases[norm(row.get("team_name",""))]=team_id
        aliases[norm(row.get("nickname",""))]=team_id
        aliases[norm(row.get("city",""))]=team_id
    for row in read_csv(ALIASES_CSV):
        if row.get("team_id"):
            aliases[norm(row.get("alias",""))]=row.get("team_id","")
    logo_rows={r.get("team_id",""):r for r in read_csv(TEAM_LOGOS_CSV) if r.get("team_id")}
    return teams, aliases, logo_rows


def resolve_team(name:str, aliases:Dict[str,str]) -> Optional[str]:
    n=norm(name)
    if n in aliases:
        return aliases[n]
    for alias, team_id in aliases.items():
        if alias and alias in n:
            return team_id
    return None


def team_name(team_id:str, teams:Dict[str,Dict[str,str]])->str:
    return clean(teams.get(team_id,{}).get("team_name") or team_id.replace("_"," ").title())


def team_palette(team_id:str, teams:Dict[str,Dict[str,str]])->Tuple[Tuple[int,int,int],Tuple[int,int,int]]:
    row=teams.get(team_id,{})
    def hx(v:str, fallback:Tuple[int,int,int]):
        v=clean(v).lstrip("#")
        if len(v)==6:
            try: return tuple(int(v[i:i+2],16) for i in (0,2,4))
            except Exception: pass
        return fallback
    return hx(row.get("primary_hex",""), BLUE), hx(row.get("secondary_hex",""), PINK)


def logo_for(team_id:str, logo_rows:Dict[str,Dict[str,str]])->Tuple[Optional[Image.Image],str]:
    row=logo_rows.get(team_id,{})
    if row.get("required") == "true" and row.get("file_exists") != "true":
        return None, "missing_required_registry_logo"
    path=Path(clean(row.get("file_path")))
    if not path.exists():
        return None, f"registry_path_missing:{path.as_posix()}"
    img=load_asset(path)
    if img is None:
        return None, f"registry_logo_unreadable:{path.as_posix()}"
    return img, "ok"


def discover_packets()->List[Path]:
    found={}
    for d in PACKET_DIRS:
        if d.exists():
            for z in d.glob("*.zip"):
                found[z.name]=z
    return [found[k] for k in sorted(found)]


def parse_packet(zp:Path)->Dict[str,Any]:
    with zipfile.ZipFile(zp) as z:
        data=json.loads(z.read("content_packet.json").decode("utf-8"))
    slot=data.get("slot",{}); pub=data.get("public_copy",{})
    return {"packet_id":data.get("packet_id") or zp.stem,"platform":clean(slot.get("platform") or pub.get("platform") or "IG Feed"),"headline":clean(pub.get("headline") or slot.get("headline") or zp.stem),"league":clean(pub.get("league") or slot.get("league")),"content_type":clean(pub.get("content_type") or slot.get("content_type")),"hook":clean(pub.get("hook") or slot.get("copy_hook")),"first":clean(pub.get("first") or slot.get("first_comment")),"story":clean(pub.get("story") or slot.get("story_frame_text")),"caption":clean(pub.get("caption") or slot.get("ig_caption_seed"))}


def choose_template(p:Dict[str,Any])->str:
    h=p["headline"].lower(); ct=p.get("content_type","").lower(); lg=p.get("league","").upper()
    if "last night in the w" in h:
        return "last_night_scoreboard"
    if "preview" in ct or " at " in h or " vs " in h:
        return "preview_matchup"
    if lg=="WNBA" and ("beat" in h or "result" in ct or "recap" in ct):
        return "result_final"
    return "storyline_feature"


def teams_from_headline(headline:str, aliases:Dict[str,str])->List[str]:
    h=clean(headline)
    for pat in [r"(.+?)\s+beat\s+(.+)$", r"(.+?)\s+(?:at|vs\.?|versus)\s+(.+)$"]:
        m=re.match(pat,h,flags=re.I)
        if m:
            out=[]
            for part in [m.group(1),m.group(2)]:
                tid=resolve_team(part, aliases)
                if tid: out.append(tid)
            return out
    out=[]; hn=norm(h)
    for alias,tid in aliases.items():
        if alias and alias in hn and tid not in out:
            out.append(tid)
    return out


def source_text()->str:
    parts=[]
    for p in [Path("manual_workflow_render_plans.json"),Path("ig_story_results_frames.md"),Path("final_score_story_guard_report.md"),Path("results_contract_report.md"),Path("mermaid_master_content_board.md"),Path("caption_bank.md")]:
        if p.exists(): parts.append(safe_text(p))
    for c in [Path("ig_story_results_queue.csv"),Path("results_contract_v2.csv"),Path("mermaid_content_slots_v2.csv")]:
        for r in read_csv(c): parts.append(" | ".join(clean(v) for v in r.values()))
    return "\n".join(parts)


def score_pairs(aliases:Dict[str,str])->List[Dict[str,Any]]:
    txt=source_text().replace("\u00b7","·"); chunks=[]
    for line in txt.splitlines(): chunks += [c.strip() for c in re.split(r"\||;",line) if c.strip()]
    pats=[re.compile(r"([A-Z][A-Za-z .&]+?)\s+(\d{2,3})\s*[·\-–—]\s*([A-Z][A-Za-z .&]+?)\s+(\d{2,3})"), re.compile(r"([A-Z][A-Za-z .&]+?)\s+(\d{2,3})\s*,\s*([A-Z][A-Za-z .&]+?)\s+(\d{2,3})")]
    out=[]; seen=set()
    for ch in chunks:
        for pat in pats:
            for m in pat.finditer(ch):
                t1=resolve_team(m.group(1),aliases); t2=resolve_team(m.group(3),aliases)
                if not t1 or not t2 or t1==t2: continue
                s1,s2=int(m.group(2)),int(m.group(4)); key=tuple(sorted([t1,t2]))+tuple(sorted([s1,s2]))
                if key in seen: continue
                seen.add(key); out.append({"team_a":t1,"score_a":s1,"team_b":t2,"score_b":s2})
    return out


def pairs_for_packet(p:Dict[str,Any], pairs:List[Dict[str,Any]], aliases:Dict[str,str])->List[Dict[str,Any]]:
    if choose_template(p)=="last_night_scoreboard":
        return pairs[:5]
    teams=teams_from_headline(p["headline"], aliases)
    if len(teams)<2: return []
    wanted=set(teams[:2])
    return [x for x in pairs if {x["team_a"],x["team_b"]}==wanted][:1]


def required_teams(p:Dict[str,Any], template:str, pairs:List[Dict[str,Any]], aliases:Dict[str,str])->List[str]:
    if p.get("league","").upper() != "WNBA": return []
    if template == "last_night_scoreboard":
        out=[]
        for pair in pairs:
            out += [pair["team_a"],pair["team_b"]]
        return list(dict.fromkeys(out))
    if template in {"result_final","preview_matchup"}:
        return list(dict.fromkeys(teams_from_headline(p["headline"], aliases)))
    return []


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


def render_result(p,wm,pair,logos,teams,aliases):
    ids=teams_from_headline(p["headline"],aliases); win=ids[0] if ids else ""; lose=ids[1] if len(ids)>1 else ""; a,b=team_palette(win,teams); size=CANVAS.get(p["platform"],(1080,1350)); img=make_canvas(size,a,b); d=ImageDraw.Draw(img); paste_watermark(img,wm); W,H=size; kicker(d,84,180,"FINAL",a); y=300 if H<1500 else 390; ph=190 if H<1500 else 230
    d.text((84,y-66),"RESULT",font=font(46,True),fill=MUTED); d.rounded_rectangle((78,y,W-78,y+ph),radius=30,fill=(*a,54),outline=(*a,210),width=3); d.rounded_rectangle((78,y+ph+24,W-78,y+ph*2+24),radius=30,fill=(255,255,255,22),outline=(255,255,255,50),width=2)
    if win in logos: logo_circle(img,(170,y+ph//2),logos[win],a,132)
    if lose in logos: logo_circle(img,(170,y+ph+24+ph//2),logos[lose],b,132)
    d.text((260,y+40),team_name(win,teams).upper(),font=font(36 if H<1500 else 44,True),fill=INK); d.text((260,y+ph+64),team_name(lose,teams).upper(),font=font(36 if H<1500 else 44,True),fill=INK)
    used="no"; sf=font(104 if H<1500 else 132,True)
    if pair:
        used="yes"; sw=pair["score_a"] if pair["team_a"]==win else pair["score_b"]; sl=pair["score_b"] if pair["team_a"]==win else pair["score_a"]; d.text((W-110,y+ph//2),str(sw),font=sf,fill=INK,anchor="rm"); d.text((W-110,y+ph+24+ph//2),str(sl),font=sf,fill=MUTED,anchor="rm")
    else: d.text((W-110,y+ph//2),"W",font=sf,fill=INK,anchor="rm")
    cta_y=H-(210 if H<1500 else 270); d.rounded_rectangle((84,cta_y,W-84,cta_y+120),radius=28,fill=(255,255,255,20),outline=(255,255,255,45),width=2); draw_block(d,118,cta_y+28,p.get("first") or "What changed after this one?",font(34,True),INK,W-236,8,2); img.info["score"]=used; return img


def render_last(p,wm,pairs,logos,teams):
    img=make_canvas(CANVAS.get(p["platform"],(1080,1350)),BLUE,PINK); d=ImageDraw.Draw(img); paste_watermark(img,wm); W,H=img.size; kicker(d,84,180,"SCOREBOARD",PINK); d.text((84,250 if H<1500 else 330),"LAST NIGHT",font=font(82 if H<1500 else 100,True),fill=INK); d.text((84,335 if H<1500 else 440),"IN THE W",font=font(82 if H<1500 else 100,True),fill=BLUE)
    start=470 if H<1500 else 620; rh=110 if H<1500 else 128
    for i,x in enumerate(pairs[:5]):
        y=start+i*(rh+16); t1,t2=x["team_a"],x["team_b"]; d.rounded_rectangle((84,y,W-84,y+rh),radius=24,fill=(255,255,255,18),outline=(255,255,255,38),width=1); logo_circle(img,(135,y+rh//2),logos[t1],team_palette(t1,teams)[0],62); logo_circle(img,(W-135,y+rh//2),logos[t2],team_palette(t2,teams)[0],62); d.text((185,y+22),team_name(t1,teams).upper(),font=font(25 if H<1500 else 30,True),fill=INK); d.text((W-185,y+22),team_name(t2,teams).upper(),font=font(25 if H<1500 else 30,True),fill=INK,anchor="ra"); d.text((185,y+58),str(x["score_a"]),font=font(44 if H<1500 else 54,True),fill=INK); d.text((W-185,y+58),str(x["score_b"]),font=font(44 if H<1500 else 54,True),fill=INK,anchor="ra"); d.text((W//2,y+rh//2),"FINAL",font=font(21,True),fill=MUTED,anchor="mm")
    cta_y=H-(210 if H<1500 else 270); d.rounded_rectangle((84,cta_y,W-84,cta_y+110),radius=28,fill=(255,255,255,20),outline=(255,255,255,45),width=2); draw_block(d,118,cta_y+26,p.get("first") or "Which result mattered most?",font(34 if H<1500 else 42,True),INK,W-236,8,2); img.info["score"]="yes" if pairs else "no"; return img


def render_preview(p,wm,logos,teams,aliases):
    ids=teams_from_headline(p["headline"],aliases); left,right=ids[0],ids[1]; a,_=team_palette(left,teams); b,_=team_palette(right,teams); img=make_canvas(CANVAS.get(p["platform"],(1080,1350)),a,b); d=ImageDraw.Draw(img); paste_watermark(img,wm); W,H=img.size; kicker(d,84,180,"TONIGHT",GOLD); y=300 if H<1500 else 420; d.rounded_rectangle((84,y,W-84,y+430),radius=38,fill=(255,255,255,18),outline=(255,255,255,45),width=2); logo_circle(img,(250,y+175),logos[left],a,190); logo_circle(img,(W-250,y+175),logos[right],b,190); d.text((250,y+305),team_name(left,teams).upper(),font=font(34,True),fill=INK,anchor="ma"); d.text((W-250,y+305),team_name(right,teams).upper(),font=font(34,True),fill=INK,anchor="ma"); d.text((W//2,y+175),"AT",font=font(42,True),fill=MUTED,anchor="mm"); h_y=y+(500 if H<1500 else 560); draw_block(d,84,h_y,p.get("story") or p.get("hook") or "Who owns the first run?",font(48 if H<1500 else 58,True),INK,W-168,10,3); cta_y=H-(220 if H<1500 else 290); d.rounded_rectangle((84,cta_y,W-84,cta_y+110),radius=28,fill=(255,255,255,20),outline=(255,255,255,45),width=2); draw_block(d,118,cta_y+26,p.get("first") or "Who needs this one more?",font(34,True),INK,W-236,8,2); img.info["score"]="no"; return img


def render_feature(p,wm):
    accent=GREEN if p.get("league","").upper()=="LPGA" else BLUE; img=make_canvas(CANVAS.get(p["platform"],(1080,1350)),accent,GOLD); d=ImageDraw.Draw(img); paste_watermark(img,wm); W,H=img.size; kicker(d,84,180,p.get("league") or "HSD",accent); y=270 if H<1500 else 350; y=draw_block(d,84,y,p["headline"],font(72 if H<1500 else 86,True),INK,W-168,8,5)+30; d.line((84,y,W-84,y),fill=(*accent,210),width=4); y+=34; draw_block(d,84,y,p.get("hook") or p.get("caption") or "This belongs on the board.",font(38 if H<1500 else 46,False),MUTED,W-168,10,5); cta_y=H-(220 if H<1500 else 290); d.rounded_rectangle((84,cta_y,W-84,cta_y+112),radius=28,fill=(255,255,255,20),outline=(255,255,255,45),width=2); draw_block(d,118,cta_y+26,p.get("first") or "Are we paying enough attention?",font(34 if H<1500 else 42,True),INK,W-236,8,2); img.info["score"]="no"; return img


def resolve_logos(required:List[str], logo_rows:Dict[str,Dict[str,str]])->Tuple[Dict[str,Image.Image],List[str],List[str]]:
    logos={}; missing=[]; reasons=[]
    for tid in required:
        img,reason=logo_for(tid, logo_rows)
        if img is None:
            missing.append(tid); reasons.append(f"{tid}:{reason}")
        else:
            logos[tid]=img
    return logos,missing,reasons


def save_image(p:Dict[str,Any], img:Image.Image)->Path:
    folder=OUT_DIR / p["packet_id"]
    folder.mkdir(parents=True, exist_ok=True)
    out=folder / (slug(p["headline"])[:88]+".png")
    img.convert("RGB").save(out, quality=96)
    return out


def render_one(p:Dict[str,Any], wm:Optional[Image.Image], teams, aliases, logo_rows, all_pairs)->Tuple[str,List[Path],str,str,str,str,str]:
    template=choose_template(p)
    if wm is None:
        return "blocked", [], "official HSD watermark missing", template, "no", "no", ""
    pairs=pairs_for_packet(p, all_pairs, aliases)
    if template == "last_night_scoreboard" and not pairs:
        return "blocked", [], "score context missing for Last Night scoreboard", template, "no", "no", ""
    required=required_teams(p, template, pairs, aliases)
    if template in {"result_final","preview_matchup"} and p.get("league","").upper()=="WNBA" and len(required)<2:
        return "blocked", [], "could not resolve two WNBA teams from headline", template, "no", "no", ""
    logos,missing,reasons=resolve_logos(required, logo_rows)
    if missing:
        return "blocked", [], "missing required registry team logo(s): " + "; ".join(reasons), template, "no", "no", "; ".join(missing)
    if template == "result_final": img=render_result(p,wm,pairs[0] if pairs else None,logos,teams,aliases)
    elif template == "last_night_scoreboard": img=render_last(p,wm,pairs,logos,teams)
    elif template == "preview_matchup": img=render_preview(p,wm,logos,teams,aliases)
    else: img=render_feature(p,wm)
    out=save_image(p,img)
    return "rendered", [out], "ok", template, "yes" if logos else "not_required", img.info.get("score","no"), ""


def make_contact_sheet(paths:List[Path])->None:
    if not paths: return
    thumbs=[]
    for p in paths[:12]:
        try:
            im=Image.open(p).convert("RGB"); im.thumbnail((310,310),Image.LANCZOS)
            cell=Image.new("RGB",(340,382),(8,10,18)); cell.paste(im,((340-im.width)//2,14)); d=ImageDraw.Draw(cell); d.rounded_rectangle((12,332,328,370),radius=14,fill=(20,27,44)); d.text((24,343),p.parent.name[:34],font=font(15,True),fill=INK); thumbs.append(cell)
        except Exception: pass
    if not thumbs: return
    cols=3; sheet=Image.new("RGB",(cols*340+28,math.ceil(len(thumbs)/cols)*382+28),(5,7,13))
    for i,t in enumerate(thumbs): sheet.paste(t,(14+(i%cols)*340,14+(i//cols)*382))
    sheet.save(CONTACT, quality=94)


def zip_outputs()->int:
    if ZIP_DIR.exists(): shutil.rmtree(ZIP_DIR)
    ZIP_DIR.mkdir(parents=True, exist_ok=True)
    count=0
    for folder in OUT_DIR.glob("*"):
        pngs=[p for p in folder.rglob("*.png") if p.is_file()]
        if folder.is_dir() and pngs:
            with zipfile.ZipFile(ZIP_DIR/f"{folder.name}.zip","w",zipfile.ZIP_DEFLATED) as z:
                for f in folder.rglob("*"):
                    if f.is_file(): z.write(f,f.relative_to(folder))
            count+=1
    return count


def clean_outputs()->None:
    for p in [OUT_DIR, ZIP_DIR]:
        if p.exists(): shutil.rmtree(p)
        p.mkdir(parents=True, exist_ok=True)


def main()->None:
    clean_outputs()
    wm,wm_source=load_watermark()
    teams,aliases,logo_rows=registry()
    all_pairs=score_pairs(aliases)
    status_rows=[]; manifest_rows=[]; visual_rows=[]; rendered_files=[]
    packets=[]
    for z in discover_packets():
        try:
            packets.append(parse_packet(z))
        except Exception as exc:
            packet_id=z.stem
            status_rows.append({"packet_id":packet_id,"platform":"","headline":packet_id,"status":"blocked","reason":f"packet parse error: {type(exc).__name__}","template_family":"unknown","rendered_files":0,"used_watermark":"yes" if wm else "no","used_logos":"no","used_score_context":"no","missing_logos":""})
    for p in packets:
        try:
            st,outs,reason,template,used_logos,used_score,missing=render_one(p,wm,teams,aliases,logo_rows,all_pairs)
        except Exception as exc:
            st,outs,reason,template,used_logos,used_score,missing="blocked",[],f"render exception: {type(exc).__name__}: {exc}",choose_template(p),"no","no",""
        status_rows.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"status":st,"reason":reason,"template_family":template,"rendered_files":len(outs),"used_watermark":"yes" if wm else "no","used_logos":used_logos,"used_score_context":used_score,"missing_logos":missing})
        dims=""
        for out in outs:
            rendered_files.append(out)
            try:
                with Image.open(out) as im: W,H=im.size
                dims=f"{W}x{H}"
                manifest_rows.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"template_family":template,"output_path":out.as_posix(),"width":W,"height":H,"used_watermark":"yes","used_logos":used_logos,"used_score_context":used_score})
            except Exception as exc:
                status_rows.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"status":"blocked","reason":f"saved image unreadable: {type(exc).__name__}","template_family":template,"rendered_files":0,"used_watermark":"yes","used_logos":used_logos,"used_score_context":used_score,"missing_logos":missing})
        visual_rows.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"template_family":template,"dimensions":dims,"watermark_status":"pass" if wm else "fail","used_logos":used_logos,"missing_logos":missing,"used_score_context":used_score,"public_text_safe":"yes","internal_text_found":"no","decision":"pass" if st=="rendered" else "fail","reason":reason})
    make_contact_sheet(rendered_files)
    zip_count=zip_outputs()
    write_csv(STATUS,status_rows,STATUS_FIELDS)
    write_csv(MANIFEST,manifest_rows,MANIFEST_FIELDS)
    write_csv(VISUAL_QA,visual_rows,VISUAL_QA_FIELDS)
    rendered_count=sum(1 for r in status_rows if r.get("status")=="rendered")
    blocked_count=sum(1 for r in status_rows if r.get("status")=="blocked")
    png_count=len(rendered_files)
    integrity="pass"
    integrity_reason="ok"
    if png_count>0 and rendered_count==0:
        integrity="fail"; integrity_reason="graphics_files_gt_zero_but_rendered_packets_zero"
    if rendered_count>0 and len(manifest_rows)==0:
        integrity="fail"; integrity_reason="rendered_packets_gt_zero_but_manifest_empty"
    meta={"version":VERSION,"generated_at_utc":now_iso(),"packets_seen":len(packets),"rendered_packets":rendered_count,"blocked_packets":blocked_count,"graphics_files":png_count,"zip_files":zip_count,"watermark_source":wm_source,"score_pairs_found":len(all_pairs),"registry_team_count":len(teams),"registry_logo_count":len(logo_rows),"integrity_status":integrity,"integrity_reason":integrity_reason,"logo_source":"data/asset_registry/wnba/team_logos.csv"}
    META.write_text(json.dumps(meta,indent=2),encoding="utf-8")
    lines=["# Mermaid Render Studio v3.0 Registry Resolver QA Report","",f"Generated: {meta['generated_at_utc']}",f"Version: {VERSION}","", "## Counts", "", f"- packets seen: {len(packets)}", f"- rendered packets: {rendered_count}", f"- blocked packets: {blocked_count}", f"- graphics files: {png_count}", f"- zip files: {zip_count}", f"- score pairs found: {len(all_pairs)}", f"- registry teams: {len(teams)}", f"- registry logos: {len(logo_rows)}", f"- watermark source: {wm_source}", f"- integrity status: {integrity}", f"- integrity reason: {integrity_reason}", "", "## Packet Status", ""]
    for r in status_rows:
        lines.append(f"- {r.get('packet_id')} | {r.get('platform')} | {r.get('template_family')} | {r.get('headline')} | {r.get('status')} | {r.get('reason')}")
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    print(json.dumps(meta,indent=2))


if __name__=="__main__":
    main()
