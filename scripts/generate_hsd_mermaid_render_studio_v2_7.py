from __future__ import annotations

import base64, csv, io, json, math, re, shutil, zipfile
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageFont

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
WATERMARK_PNGS = [Path("assets/branding/official_hsd_watermark.png"), Path("data/assets/brand/hsd_watermark.png"), Path("data/assets/brand/hsd_official_watermark.png")]
WATERMARK_B64 = Path("data/assets/brand/hsd_watermark_base64.txt")
CANVAS = {"IG Feed": (1080, 1350), "Threads": (1080, 1350), "IG Stories": (1080, 1920)}
BG=(8,12,22); PANEL=(15,22,38); PANEL2=(24,34,58); TEXT=(248,250,255); MUTED=(176,187,205); ACCENT=(88,156,255); PINK=(244,83,154); GOLD=(245,196,68); LINE=(58,74,106); GREEN=(74,190,132)
STATUS_FIELDS=["packet_id","platform","headline","status","reason","rendered_files","used_watermark","used_logos","template_family","visual_decision"]
MANIFEST_FIELDS=["packet_id","platform","headline","output_path","width","height","used_watermark","used_logos","template_family"]
QA_FIELDS=["packet_id","platform","headline","template_family","dimensions","watermark_status","used_logos","used_score_context","internal_text_found","decision","reason"]
INTERNAL_WORDS=["review before publish","control rules","do not render","artifact_only","manual_workflow","assignment_handoff"]
TEAM_ALIASES={"la sparks":"los angeles sparks","ny liberty":"new york liberty","connecticut":"connecticut sun","indiana":"indiana fever","vegas aces":"las vegas aces"}


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"


def read_csv(path: Path) -> List[Dict[str,str]]:
    if not path.exists(): return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f: return list(csv.DictReader(f))
    except Exception: return []


def write_csv(path: Path, data: List[Dict[str,Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows([{k:r.get(k,"") for k in fields} for r in data])


def font(size:int,bold:bool=False,condensed:bool=False):
    names=[]
    if condensed: names += ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf"]
    names += ["/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf"]
    for p in names:
        if p and Path(p).exists(): return ImageFont.truetype(p,size)
    return ImageFont.load_default()


def wrap(draw,text,fnt,max_w):
    words=clean(text).split(); lines=[]
    if not words: return [""]
    cur=words[0]
    for word in words[1:]:
        test=cur+" "+word
        if draw.textbbox((0,0),test,font=fnt)[2] <= max_w: cur=test
        else: lines.append(cur); cur=word
    lines.append(cur); return lines


def block(draw,x,y,text,fnt,fill,max_w,gap=8,max_lines=6):
    for line in wrap(draw,text,fnt,max_w)[:max_lines]:
        draw.text((x,y),line,font=fnt,fill=fill); y=draw.textbbox((x,y),line,font=fnt)[3]+gap
    return y


def load_watermark()->Tuple[Optional[Image.Image],str]:
    for p in WATERMARK_PNGS:
        if p.exists():
            try: return Image.open(p).convert("RGBA"), p.as_posix()
            except Exception: pass
    if WATERMARK_B64.exists():
        try: return Image.open(io.BytesIO(base64.b64decode(WATERMARK_B64.read_text().strip()))).convert("RGBA"), WATERMARK_B64.as_posix()
        except Exception as e: return None, f"base64 failed {type(e).__name__}"
    return None,"missing"


def open_asset(path:Path)->Optional[Image.Image]:
    try:
        if path.suffix.lower()==".svg":
            import cairosvg
            return Image.open(io.BytesIO(cairosvg.svg2png(url=str(path)))).convert("RGBA")
        return Image.open(path).convert("RGBA")
    except Exception: return None


def find_file_by_slug(name:str)->Optional[Path]:
    s=slug(name); tokens=[s, s.replace("-","_")]
    roots=[Path("data/assets/approved"),Path("assets"),Path("graphics_chat_upload_pack"),Path("ig_story_results_upload_pack"),Path("hsd_pipeline_lite_review")]
    for root in roots:
        if not root.exists(): continue
        for p in root.rglob("*"):
            if p.is_file() and p.suffix.lower() in {".png",".jpg",".jpeg",".webp",".svg"}:
                low=p.as_posix().lower()
                if any(t in low for t in tokens): return p
    return None


def logo_registry()->Dict[str,Path]:
    reg:Dict[str,Path]={}
    for csv_path in [Path("approved_graphics_assets.csv"),Path("hsd_pipeline_lite_review/files/approved_graphics_assets.csv")]:
        for r in read_csv(csv_path):
            if clean(r.get("entity_type")).lower()!="team": continue
            name=clean(r.get("entity_name"))
            if not name: continue
            p=None
            for key in ["master_path","web_path"]:
                val=clean(r.get(key))
                if val and Path(val).exists(): p=Path(val); break
            if not p: p=find_file_by_slug(name)
            if p: reg[name.lower()]=p
    return reg


def team_norm(t:str)->str:
    t=clean(t).strip(" .:-")
    return TEAM_ALIASES.get(t.lower(),t)


def teams_from_headline(h:str)->List[str]:
    h=clean(h)
    for sep in [" at "," vs "," vs. "]:
        if sep in h.lower():
            parts=re.split(sep,h,flags=re.I); return [team_norm(parts[0]),team_norm(parts[1])] if len(parts)>=2 else []
    m=re.match(r"(.+?)\s+beat\s+(.+)$",h,flags=re.I)
    if m: return [team_norm(m.group(1)),team_norm(m.group(2))]
    return []


def template_family(packet:Dict[str,Any])->str:
    h=packet["headline"].lower(); ct=packet.get("content_type","").lower()
    if "last night in the w" in h: return "last_night_scoreboard"
    if "preview" in ct or " at " in h or " vs " in h: return "preview_matchup"
    if " beat " in h or "result" in ct or "recap" in ct: return "result_final"
    return "storyline_feature"


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
        return {"packet_id":data.get("packet_id") or zp.stem,"platform":clean(slot.get("platform") or pub.get("platform") or "IG Feed"),"headline":clean(pub.get("headline") or slot.get("headline") or zp.stem),"league":clean(pub.get("league") or slot.get("league")),"content_type":clean(pub.get("content_type") or slot.get("content_type")),"hook":clean(pub.get("hook") or slot.get("copy_hook")),"first":clean(pub.get("first") or slot.get("first_comment"))}
    except Exception: return None


def score_rows()->List[Tuple[str,str,str,str]]:
    txt="\n".join([p.read_text(encoding="utf-8",errors="replace") for p in [Path("ig_story_results_frames.md"),Path("final_score_story_guard_report.md"),Path("manual_workflow_render_plans.json")] if p.exists()])
    rows=[]
    pat=r"([A-Z][A-Za-z .&'-]{2,34})\s+(\d{2,3})\s*[—\-·|]\s*([A-Z][A-Za-z .&'-]{2,34})\s+(\d{2,3})"
    for a,sa,b,sb in re.findall(pat,txt):
        item=(clean(a),sa,clean(b),sb)
        if item not in rows: rows.append(item)
    return rows[:6]


def score_for(teams:List[str], scores):
    lows=[t.lower() for t in teams]
    for a,sa,b,sb in scores:
        if len(lows)>=2 and lows[0] in a.lower() and lows[1] in b.lower(): return (a,sa,b,sb)
        if len(lows)>=2 and lows[0] in b.lower() and lows[1] in a.lower(): return (b,sb,a,sa)
    return None


def base_canvas(size):
    W,H=size; im=Image.new("RGBA",size,BG); d=ImageDraw.Draw(im)
    for i in range(0,W,18): d.line((i,0,i-H//2,H),fill=(13,20,36,80),width=2)
    for x in range(70,W,38):
        for y in range(170,H-120,38):
            if (x+y)//38%3==0: d.ellipse((x,y,x+3,y+3),fill=(255,255,255,22))
    glow=Image.new("RGBA",size,(0,0,0,0)); gd=ImageDraw.Draw(glow)
    gd.ellipse((-260,-240,690,650),fill=(30,70,140,160)); gd.ellipse((W-420,H-520,W+320,H+260),fill=(100,25,75,130))
    im.alpha_composite(glow.filter(ImageFilter.GaussianBlur(26)))
    d.rounded_rectangle((44,138,W-44,H-68),radius=38,fill=PANEL,outline=LINE,width=2)
    return im


def paste_wm(im,wm):
    mark=wm.copy(); mark.thumbnail((86,86),Image.LANCZOS); im.alpha_composite(mark,(58,44))


def badge(d,x,y,text,fill=ACCENT):
    f=font(24,True); box=d.textbbox((0,0),text,font=f); w=box[2]-box[0]+34
    d.rounded_rectangle((x,y,x+w,y+34),radius=16,fill=fill); d.text((x+17,y+4),text,font=f,fill=TEXT); return x+w


def draw_logo(im,logo,x,y,box=150):
    lg=logo.copy(); lg.thumbnail((box,box),Image.LANCZOS); im.alpha_composite(lg,(int(x+(box-lg.width)/2),int(y+(box-lg.height)/2)))


def resolve_logos(team_names:List[str], reg:Dict[str,Path])->Tuple[Dict[str,Image.Image],List[str]]:
    logos={}; missing=[]
    for team in team_names:
        path=reg.get(team.lower()) or find_file_by_slug(team)
        img=open_asset(path) if path else None
        if img: logos[team]=img
        else: missing.append(team)
    return logos,missing


def internal_found(packet):
    text=" ".join([packet.get(k,"") for k in ["headline","hook","first","content_type"]]).lower()
    return any(w in text for w in INTERNAL_WORDS)


def render_preview(packet,wm,logos,teams):
    size=CANVAS.get(packet["platform"],(1080,1350)); W,H=size; im=base_canvas(size); d=ImageDraw.Draw(im); paste_wm(im,wm)
    badge(d,170,55,"TONIGHT",PINK); badge(d,W-250,55,packet.get("league") or "HSD",PANEL2)
    y=240 if H<1500 else 330; left,right=teams[:2]
    draw_logo(im,logos[left],120,y,210); draw_logo(im,logos[right],W-330,y,210)
    d.text((W//2,y+92),"AT",font=font(42,True,True),fill=MUTED,anchor="mm")
    tf=font(44,True,True); d.text((225,y+245),left.upper(),font=tf,fill=TEXT,anchor="mm"); d.text((W-225,y+245),right.upper(),font=tf,fill=TEXT,anchor="mm")
    d.line((90,y+325,W-90,y+325),fill=LINE,width=3)
    hf=font(78 if H<1500 else 92,True,True); sub=packet.get("first") or "Who controls the game first?"
    block(d,90,y+370,packet.get("hook") or packet["headline"],hf,TEXT,W-180,10,3)
    d.rounded_rectangle((90,H-230,W-90,H-115),radius=30,fill=PANEL2,outline=LINE,width=2); block(d,120,H-202,sub,font(32,True),TEXT,W-240,6,2)
    return im


def render_result(packet,wm,logos,teams,scores):
    size=CANVAS.get(packet["platform"],(1080,1350)); W,H=size; im=base_canvas(size); d=ImageDraw.Draw(im); paste_wm(im,wm)
    badge(d,170,55,"FINAL",GREEN); badge(d,W-230,55,packet.get("league") or "HSD",PANEL2)
    score=score_for(teams,scores); a,sa,b,sb=(score if score else (teams[0],"",teams[1],"")); y=245 if H<1500 else 360
    for i,(team,sc) in enumerate([(a,sa),(b,sb)]):
        top=y+i*245; fill=(22,34,58) if i==0 else (16,25,42)
        d.rounded_rectangle((90,top,W-90,top+190),radius=34,fill=fill,outline=LINE,width=2)
        if team in logos: draw_logo(im,logos[team],120,top+28,125)
        d.text((265,top+52),team.upper(),font=font(44,True,True),fill=TEXT)
        if sc: d.text((W-160,top+95),sc,font=font(92,True,True),fill=GOLD if i==0 else TEXT,anchor="mm")
    y2=y+515; d.text((90,y2),"WHAT CHANGED",font=font(30,True),fill=ACCENT); block(d,90,y2+48,packet.get("hook") or packet["headline"],font(54 if H<1500 else 64,True,True),TEXT,W-180,10,3)
    d.rounded_rectangle((90,H-220,W-90,H-110),radius=30,fill=PANEL2,outline=LINE,width=2); block(d,120,H-192,packet.get("first") or "What was the swing moment?",font(32,True),TEXT,W-240,6,2)
    return im, bool(score)


def render_last_night(packet,wm,reg,scores):
    size=CANVAS.get(packet["platform"],(1080,1350)); W,H=size; im=base_canvas(size); d=ImageDraw.Draw(im); paste_wm(im,wm)
    badge(d,170,55,"SCOREBOARD",ACCENT); badge(d,W-230,55,"WNBA",PANEL2)
    y=220 if H<1500 else 285; d.text((90,y),"LAST NIGHT",font=font(82 if H<1500 else 98,True,True),fill=TEXT); d.text((90,y+86),"IN THE W",font=font(82 if H<1500 else 98,True,True),fill=GOLD)
    y+=210 if H<1500 else 255; used=[]
    for a,sa,b,sb in scores[:4]:
        d.rounded_rectangle((90,y,W-90,y+96),radius=24,fill=PANEL2,outline=LINE,width=2)
        d.text((120,y+31),a.upper(),font=font(27,True,True),fill=TEXT); d.text((W//2-40,y+31),sa,font=font(36,True),fill=GOLD)
        d.text((W//2+40,y+31),b.upper(),font=font(27,True,True),fill=MUTED); d.text((W-135,y+31),sb,font=font(36,True),fill=TEXT)
        y+=112; used += [a,b]
    d.rounded_rectangle((90,H-220,W-90,H-110),radius=30,fill=(38,26,56),outline=LINE,width=2); block(d,120,H-192,packet.get("first") or "Which result mattered most?",font(32,True),TEXT,W-240,6,2)
    return im, bool(scores), used


def render_story(packet,wm):
    size=CANVAS.get(packet["platform"],(1080,1350)); W,H=size; im=base_canvas(size); d=ImageDraw.Draw(im); paste_wm(im,wm)
    badge(d,170,55,packet.get("league") or "HSD",GREEN if packet.get("league").upper()=="LPGA" else ACCENT)
    y=245 if H<1500 else 360
    d.text((90,y),"THE LANE",font=font(34,True),fill=ACCENT); y+=58
    block(d,90,y,packet["headline"],font(74 if H<1500 else 88,True,True),TEXT,W-180,8,5)
    d.line((90,H-335,W-90,H-335),fill=LINE,width=3); block(d,90,H-300,packet.get("hook") or "This belongs on the board.",font(40,False),MUTED,W-180,8,4)
    d.rounded_rectangle((90,H-205,W-90,H-100),radius=30,fill=PANEL2,outline=LINE,width=2); block(d,120,H-178,packet.get("first") or "Are we paying enough attention?",font(31,True),TEXT,W-240,6,2)
    return im


def save_packet(packet,im,template):
    folder=OUT_DIR/packet["packet_id"]; folder.mkdir(parents=True,exist_ok=True); out=folder/(slug(packet["headline"])[:82]+".png"); im.convert("RGB").save(out,quality=95); return out


def contact_sheet(paths:List[Path]):
    if not paths: return
    thumbs=[]
    for p in paths[:12]:
        im=Image.open(p).convert("RGB"); im.thumbnail((290,330),Image.LANCZOS); cell=Image.new("RGB",(330,390),(8,12,24)); cell.paste(im,((330-im.width)//2,15)); ImageDraw.Draw(cell).text((18,352),p.parent.name[:34],font=font(15,True),fill=TEXT); thumbs.append(cell)
    cols=3; sheet=Image.new("RGB",(cols*330+28,math.ceil(len(thumbs)/cols)*390+28),(5,8,16))
    for i,t in enumerate(thumbs): sheet.paste(t,(14+(i%cols)*330,14+(i//cols)*390))
    sheet.save(CONTACT,quality=92)


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
    OUT_DIR.mkdir(parents=True,exist_ok=True)
    wm,wm_source=load_watermark(); reg=logo_registry(); scores=score_rows(); packets=[p for p in (parse_packet(z) for z in discover_packets()) if p]
    status=[]; manifest=[]; qa=[]; files=[]
    for p in packets:
        fam=template_family(p); teams=teams_from_headline(p["headline"]); used_score=False; used_logos="no"; reason="ok"; decision="pass"
        if not wm:
            st="blocked"; reason=f"watermark missing: {wm_source}"; decision="fail"; outs=[]
        elif fam in {"result_final","preview_matchup"}:
            logos,missing=resolve_logos(teams,reg)
            if missing or len(logos)<len(teams): st="blocked"; reason="missing exact team logo(s): "+", ".join(missing); decision="fail"; outs=[]; used_logos="missing"
            else:
                if fam=="preview_matchup": im=render_preview(p,wm,logos,teams); used_score=False
                else: im,used_score=render_result(p,wm,logos,teams,scores)
                out=save_packet(p,im,fam); outs=[out]; files.append(out); st="rendered"; used_logos="yes"
        elif fam=="last_night_scoreboard":
            if not scores: st="blocked"; reason="missing score context for Last Night scoreboard"; decision="fail"; outs=[]; used_logos="n/a"
            else:
                all_teams=[]
                for a,_,b,_ in scores[:4]: all_teams += [a,b]
                _,missing=resolve_logos(all_teams,reg)
                if missing: st="blocked"; reason="missing exact team logo(s): "+", ".join(sorted(set(missing))); decision="fail"; outs=[]; used_logos="missing"
                else:
                    im,used_score,_=render_last_night(p,wm,reg,scores); out=save_packet(p,im,fam); outs=[out]; files.append(out); st="rendered"; used_logos="yes"
        else:
            im=render_story(p,wm); out=save_packet(p,im,fam); outs=[out]; files.append(out); st="rendered"; used_logos="n/a"
        internal="yes" if internal_found(p) else "no"
        if internal=="yes": st="blocked"; reason="internal/control text detected"; decision="fail"; outs=[]
        status.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"status":st,"reason":reason,"rendered_files":len(outs),"used_watermark":"yes" if wm else "no","used_logos":used_logos,"template_family":fam,"visual_decision":decision})
        qa.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"template_family":fam,"dimensions":str(CANVAS.get(p["platform"],(1080,1350))),"watermark_status":"pass" if wm else "fail","used_logos":used_logos,"used_score_context":"yes" if used_score else "no","internal_text_found":internal,"decision":decision,"reason":reason})
        for out in outs:
            with Image.open(out) as im2: W,H=im2.size
            manifest.append({"packet_id":p["packet_id"],"platform":p["platform"],"headline":p["headline"],"output_path":out.as_posix(),"width":W,"height":H,"used_watermark":"yes","used_logos":used_logos,"template_family":fam})
    write_csv(STATUS,status,STATUS_FIELDS); write_csv(MANIFEST,manifest,MANIFEST_FIELDS); write_csv(VISUAL_QA,qa,QA_FIELDS); contact_sheet(files); zip_outputs()
    rendered=sum(1 for r in status if r["status"]=="rendered"); blocked=sum(1 for r in status if r["status"]=="blocked")
    lines=["# Mermaid Render Studio v2.9 Visual QA Report","",f"- version: {VERSION}",f"- rendered packets: {rendered}",f"- blocked packets: {blocked}",f"- watermark source: {wm_source}","","## Packet Status",""]
    lines += [f"- {r['packet_id']} | {r['platform']} | {r['template_family']} | {r['status']} | {r['reason']}" for r in status]
    REPORT.write_text("\n".join(lines)+"\n",encoding="utf-8")
    META.write_text(json.dumps({"version":VERSION,"rendered":rendered,"blocked":blocked,"watermark_source":wm_source,"strict_team_logos":True},indent=2),encoding="utf-8")
    print(json.dumps({"rendered":rendered,"blocked":blocked,"version":VERSION},indent=2))

if __name__=="__main__": main()
