from __future__ import annotations

import csv, importlib.util, json, random, re, runpy, shutil, zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

VERSION="v3.1-cinematic-dual-player-lanes"
BASE_SCRIPT=Path("scripts/generate_hsd_template_renderer_v2_5.py")
MAP=Path("outputs/latest/HSD_TEMPLATE_FACTORY/render_mapping/hsd_template_render_map.json")
MAP_SCRIPT=Path("scripts/generate_hsd_template_render_map_v1.py")
PLAYER_ROOT=Path("outputs/latest/production_graphics_director/graphics_variant_packs/with_players")
OUT=Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v3"); RENDERS=OUT/"renders"
MAN_CSV=OUT/"hsd_template_renderer_v3_manifest.csv"; MAN_JSON=OUT/"hsd_template_renderer_v3_manifest.json"
AUDIT_CSV=OUT/"hsd_template_renderer_v3_logo_audit.csv"; AUDIT_JSON=OUT/"hsd_template_renderer_v3_logo_audit.json"
REPORT=OUT/"hsd_template_renderer_v3_report.md"; ZIP=OUT/"hsd_template_renderer_v3_renders.zip"
CONTACT=OUT/"hsd_template_renderer_v3_contact_sheet.jpg"; CONTACT_PLAYERS=OUT/"hsd_template_renderer_v3_with_players_contact_sheet.jpg"
FIELDS=["item_id","template_id","platform","mode","headline","variant","player_mode","player_assets_used","player_names","output_path","width","height","status","review_only","notes"]
INK=(248,247,243); MUTED=(174,176,186); GOLD=(246,184,61); ORANGE=(246,81,36); PURPLE=(142,70,255); FONTS={}

def clean(v:Any)->str:return re.sub(r"\s+"," ",str(v or "")).strip()
def norm(v:Any)->str:return re.sub(r"[^a-z0-9]+"," ",clean(v).lower()).strip()
def slug(v:Any)->str:return re.sub(r"[^a-z0-9]+","-",clean(v).lower()).strip("-") or "item"
def load_json(p:Path)->Dict[str,Any]:
    try:return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    except Exception:return {}
def read_csv(p:Path)->List[Dict[str,str]]:
    if not p.exists():return []
    with p.open(newline="",encoding="utf-8",errors="replace") as f:return list(csv.DictReader(f))
def write_csv(p:Path,rows:List[Dict[str,Any]],fields:List[str])->None:
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open("w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore");w.writeheader()
        for r in rows:w.writerow({k:r.get(k,"") for k in fields})
def load_base():
    spec=importlib.util.spec_from_file_location("hsd_v25",BASE_SCRIPT)
    if not spec or not spec.loader:raise RuntimeError("renderer v2.5 missing")
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def font(size:int,bold=True):
    key=(size,bold)
    if key in FONTS:return FONTS[key]
    names=["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"] if bold else ["/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf","/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"]
    for n in names:
        if Path(n).exists():FONTS[key]=ImageFont.truetype(n,size);return FONTS[key]
    return ImageFont.load_default()
def textw(d,t,f):b=d.textbbox((0,0),clean(t),font=f);return b[2]-b[0]
def fit(d,t,w,start,floor=20,bold=True):
    for s in range(start,floor-1,-2):
        f=font(s,bold)
        if textw(d,t,f)<=w:return f
    return font(floor,bold)
def wrap(d,t,w,f,lines=2):
    out=[];cur=""
    for word in clean(t).split():
        trial=f"{cur} {word}".strip()
        if not cur or textw(d,trial,f)<=w:cur=trial
        else:out.append(cur);cur=word
    if cur:out.append(cur)
    return out[:lines]
def dominant(img:Image.Image|None,fallback):
    if img is None:return fallback
    try:
        colors=img.convert("RGB").resize((48,48)).getcolors(2304) or []
        good=[(n*(max(c)-min(c)),c) for n,c in colors if 45<sum(c)/3<225 and max(c)-min(c)>35]
        return max(good)[1] if good else fallback
    except Exception:return fallback
def bg(size:Tuple[int,int],a,b,seed):
    w,h=size;im=Image.new("RGBA",size,(4,4,8,255));d=ImageDraw.Draw(im,"RGBA")
    for y in range(h):
        v=int(4+9*y/max(h-1,1));d.line((0,y,w,y),fill=(v,v,min(21,v+7),255))
    glow=Image.new("RGBA",size,(0,0,0,0));g=ImageDraw.Draw(glow,"RGBA")
    g.ellipse((-420,-280,600,720),fill=(*a,82));g.ellipse((w-570,h-850,w+410,h+180),fill=(*b,78));im=Image.alpha_composite(im,glow.filter(ImageFilter.GaussianBlur(92)));d=ImageDraw.Draw(im,"RGBA")
    for x in range(-h,w,58):d.line((x,0,x+h,h),fill=(255,255,255,10),width=2)
    rnd=random.Random(seed)
    for _ in range(max(1,w*h//1150)):
        x=rnd.randrange(w);y=rnd.randrange(h);q=255 if rnd.random()>.5 else 0;d.point((x,y),fill=(q,q,q,rnd.randrange(3,13)))
    return im
def panel(im,box,a,fill=(5,6,12,220),radius=20):
    x,y,w,h=box;l=Image.new("RGBA",im.size,(0,0,0,0));d=ImageDraw.Draw(l,"RGBA")
    d.rounded_rectangle((x+8,y+10,x+w+8,y+h+10),radius=radius,fill=(0,0,0,120));d.rounded_rectangle((x,y,x+w,y+h),radius=radius,fill=fill,outline=(*a,150),width=2);d.rectangle((x+1,y+1,x+8,y+h-1),fill=(*a,210));im.alpha_composite(l)
def tracking(d,xy,text,size,color,space=4):
    x,y=xy;f=font(size,True)
    for c in clean(text):d.text((x,y),c,font=f,fill=color);x+=textw(d,c,f)+space
def top(im,badge,title,kicker,a,story=False):
    d=ImageDraw.Draw(im,"RGBA")
    if badge:
        b=badge.copy();b.thumbnail((88 if story else 78,88 if story else 78),Image.LANCZOS);im.alpha_composite(b,(48,50))
    tracking(d,(160,54),kicker.upper(),21,(*a,255),5);f=fit(d,title.upper(),830,88 if story else 78,48);d.text((160,88),title.upper(),font=f,fill=INK,stroke_width=3,stroke_fill=(0,0,0));d.line((160,190 if story else 180,1018,190 if story else 180),fill=(*a,175),width=2)
def logo_box(base,im,team,logo,box,a,quiet=False):
    base.logo_panel(im,ImageDraw.Draw(im),(box[0],box[1],box[2],box[3]),team,logo,a,quiet)
def load_player(p:Path):
    try:
        im=Image.open(p).convert("RGBA");bbox=im.getbbox();return im.crop(bbox) if bbox else im
    except Exception:return None
def player_card(im,player,box,a,label,mirror=False):
    x,y,w,h=box;panel(im,box,a,(5,6,12,205),20);p=load_player(Path(clean(player.get("path"))))
    if p:
        if mirror:p=ImageOps.mirror(p)
        p.thumbnail((w-24,h-88),Image.LANCZOS);px=x+(w-p.width)//2;py=y+h-82-p.height
        alpha=Image.new("L",im.size,0);alpha.paste(p.getchannel("A"),(px,py));glow=Image.new("RGBA",im.size,(*a,0));glow.putalpha(alpha.filter(ImageFilter.GaussianBlur(22)).point(lambda q:min(120,q)));im.alpha_composite(glow);im.alpha_composite(p,(px,py))
    d=ImageDraw.Draw(im,"RGBA");d.rectangle((x+1,y+h-80,x+w-1,y+h-1),fill=(4,4,8,225));d.line((x+18,y+h-80,x+w-18,y+h-80),fill=(*a,190),width=2)
    name=clean(player.get("display_name")) or label;f=fit(d,name.upper(),w-36,30,18);d.text((x+18,y+h-64),name.upper(),font=f,fill=INK);d.text((x+18,y+h-28),label.upper(),font=font(16,True),fill=a)
def packages():
    out={}
    if not PLAYER_ROOT.exists():return out
    for p in PLAYER_ROOT.glob("*/content_summary.json"):
        q=load_json(p);headline=clean(q.get("headline"));ps=q.get("players") or [];assets=q.get("player_assets") or [];en=[]
        for i,pl in enumerate(ps):
            if not isinstance(pl,dict):continue
            ap=Path(clean(assets[i])) if i<len(assets) and clean(assets[i]) else None
            if ap is not None and ap.exists():en.append({**pl,"path":ap.as_posix()})
        if headline and en:
            b={"headline":headline,"player_mode":clean(q.get("player_mode")),"players":en};out[norm(headline)]=b
            if "last night in the w" in norm(headline):out["last night in the w"]=b
    return out
def bundle_for(headline,index):
    k=norm(headline)
    if k in index:return index[k]
    if "last night in the w" in k:return index.get("last night in the w")
    for key,b in index.items():
        if key and (key in k or k in key):return b
    return None
def pick(bundle,team_id,n=0):
    ps=[p for p in (bundle or {}).get("players",[]) if clean(p.get("team_id"))==clean(team_id) and Path(clean(p.get("path"))).exists()]
    return ps[n%len(ps)] if ps else None
def team_id(base,team,aliases):
    try:return clean(base.resolve(team,aliases))
    except Exception:return ""
def final_data(base,src):
    winner,loser,score,league,date=base.final_names(src);s=base.score_parts(score);return winner,loser,s[0],s[1],league,date
def render_game(base,row,src,badge,aliases,logos,verified,variant,bundle):
    story=clean(row.get("platform"))=="stories";winner,loser,s1,s2,league,date=final_data(base,src);wl=base.logo_for(winner,aliases,logos,verified);ll=base.logo_for(loser,aliases,logos,verified);a=dominant(wl,GOLD);b=dominant(ll,PURPLE);im=bg((1080,1920) if story else (1080,1350),a,b,sum(map(ord,winner+loser+variant)));d=ImageDraw.Draw(im,"RGBA");top(im,badge,"GAME RECAP",f"FINAL SCORE • {league or 'WNBA'}",a,story)
    wp=pick(bundle,team_id(base,winner,aliases));lp=pick(bundle,team_id(base,loser,aliases))
    if variant=="with_players" and (wp or lp):
        if story:
            panel(im,(55,270,970,610),a);logo_box(base,im,winner,wl,(86,330,170,170),a);d.text((290,330),"WINNER",font=font(22,True),fill=a);f=fit(d,winner.upper(),400,58,34);d.text((290,370),winner.upper(),font=f,fill=INK);d.text((980,350),s1,font=font(160,True),fill=a,anchor="ra");d.line((86,575,980,575),fill=(*a,120),width=2);logo_box(base,im,loser,ll,(100,640,120,120),b,True);d.text((260,650),loser.upper(),font=fit(d,loser.upper(),390,38,25),fill=MUTED);d.text((970,645),s2,font=font(86,True),fill=MUTED,anchor="ra")
            if lp:player_card(im,lp,(55,930,410,560),b,"OPPONENT FEATURE",True)
            if wp:player_card(im,wp,(520,880,505,650),a,"WINNER FEATURE")
            panel(im,(55,1600,970,180),b);tracking(d,(90,1630),"THE FINAL WORD",21,b);txt=clean(src.get("summary") or f"{winner} defeated {loser}, {s1}-{s2}.").upper();f=fit(d,txt,880,36,25);yy=1674
            for line in wrap(d,txt,880,f,2):d.text((90,yy),line,font=f,fill=INK);yy+=f.size+3
        else:
            panel(im,(52,270,630,710),a);logo_box(base,im,winner,wl,(80,330,170,170),a);d.text((285,330),"WINNER",font=font(21,True),fill=a);f=fit(d,winner.upper(),330,52,32);d.text((285,370),winner.upper(),font=f,fill=INK);d.text((650,470),s1,font=font(152,True),fill=a,anchor="ra");d.line((80,610,650,610),fill=(*a,120),width=2);logo_box(base,im,loser,ll,(90,680,120,120),b,True);d.text((245,690),loser.upper(),font=fit(d,loser.upper(),270,34,23),fill=MUTED);d.text((650,680),s2,font=font(78,True),fill=MUTED,anchor="ra");d.text((82,920),f"FINAL • {clean(date).upper()}",font=font(20,True),fill=MUTED)
            if wp:player_card(im,wp,(710,270,318,710),a,"WINNER FEATURE")
            elif lp:player_card(im,lp,(710,270,318,710),b,"PLAYER FEATURE",True)
            panel(im,(52,1015,976,190),b);tracking(d,(86,1045),"THE FINAL WORD",21,b);txt=clean(src.get("summary") or f"{winner} defeated {loser}, {s1}-{s2}.").upper();f=fit(d,txt,900,38,26);yy=1090
            for line in wrap(d,txt,900,f,2):d.text((86,yy),line,font=f,fill=INK);yy+=f.size+3
    else:
        panel(im,(52,270,976,700),a);logo_box(base,im,winner,wl,(82,335,230,230),a);d.text((350,334),"WINNER",font=font(23,True),fill=a);f=fit(d,winner.upper(),390,68,38);yy=380
        for line in wrap(d,winner.upper(),390,f,2):d.text((350,yy),line,font=f,fill=INK,stroke_width=2,stroke_fill=(0,0,0));yy+=f.size+3
        d.text((986,338),s1,font=font(180,True),fill=a,anchor="ra");d.line((82,620,988,620),fill=(*a,105),width=2);logo_box(base,im,loser,ll,(100,680,160,160),b,True);d.text((305,700),loser.upper(),font=fit(d,loser.upper(),390,43,28),fill=MUTED);d.text((980,690),s2,font=font(106,True),fill=MUTED,anchor="ra");panel(im,(52,1005,976,180),b);tracking(d,(86,1036),"THE FINAL WORD",21,b);txt=clean(src.get("summary") or f"{winner} defeated {loser}, {s1}-{s2}.").upper();f=fit(d,txt,900,40,27);d.text((86,1082),txt,font=f,fill=INK)
    return im
def render_preview(base,row,src,badge,aliases,logos,verified,variant,bundle):
    home=clean(src.get("home_team_name") or "TEAM TWO");away=clean(src.get("away_team_name") or "TEAM ONE");hl=base.logo_for(home,aliases,logos,verified);al=base.logo_for(away,aliases,logos,verified);a=dominant(al,ORANGE);b=dominant(hl,PURPLE);im=bg((1080,1350),a,b,38);d=ImageDraw.Draw(im,"RGBA");top(im,badge,"TONIGHT IN THE W","MATCHUP PREVIEW • WNBA",a);panel(im,(52,270,976,730),a);ap=pick(bundle,team_id(base,away,aliases));hp=pick(bundle,team_id(base,home,aliases))
    if variant=="with_players" and (ap or hp):
        logo_box(base,im,away,al,(80,315,145,145),a);logo_box(base,im,home,hl,(855,315,145,145),b)
        if ap:player_card(im,ap,(80,390,410,545),a,away)
        else:logo_box(base,im,away,al,(115,480,320,320),a)
        if hp:player_card(im,hp,(590,390,410,545),b,home,True)
        else:logo_box(base,im,home,hl,(645,480,320,320),b)
    else:
        logo_box(base,im,away,al,(105,350,300,300),a);logo_box(base,im,home,hl,(675,350,300,300),b);d.text((255,700),away.upper(),font=fit(d,away.upper(),390,50,32),fill=INK,anchor="ma");d.text((825,700),home.upper(),font=fit(d,home.upper(),390,50,32),fill=INK,anchor="ma")
    d.ellipse((475,520,605,650),fill=(4,4,8,245),outline=(*GOLD,200),width=3);d.text((540,585),"VS",font=font(46,True),fill=GOLD,anchor="mm");panel(im,(52,1040,976,170),b);tracking(d,(86,1070),"WATCH POINT",21,b);q="WHO OWNS THE LATE-GAME EDGE?";d.text((86,1115),q,font=fit(d,q,900,48,31),fill=INK);return im
def render_last(base,row,badge,aliases,logos,verified,variant,bundle):
    story=clean(row.get("platform"))=="stories";im=bg((1080,1920) if story else (1080,1350),PURPLE,ORANGE,78);d=ImageDraw.Draw(im,"RGBA");top(im,badge,"LAST NIGHT IN THE W","WNBA RESULTS DESK",ORANGE,story);finals=base.final_rows()[:5];featured=next((p for p in (bundle or {}).get("players",[]) if Path(clean(p.get("path"))).exists()),None);listw=610 if featured else 964;y=320 if story else 300;rh=190 if story else 160
    for final in finals[:5 if story else 4]:
        w,l,s1,s2,_,_=final_data(base,final);lg=base.logo_for(w,aliases,logos,verified);a=dominant(lg,GOLD);panel(im,(58,y,listw,rh),a);logo_box(base,im,w,lg,(82,y+24,110 if not story else 128,110 if not story else 128),a);d.text((225 if not story else 240,y+34),w.upper(),font=fit(d,w.upper(),listw-350,34,22),fill=INK);d.text((58+listw-28,y+45),f"{s1}-{s2}",font=font(48 if not story else 56,True),fill=a,anchor="ra");y+=rh+18
    if variant=="with_players" and featured:player_card(im,featured,(700 if story else 735,340 if story else 300,325 if story else 293,1080 if story else 700),ORANGE,"FEATURED PLAYER")
    panel(im,(58,1540 if story else 1050,964,150 if story else 145),ORANGE);q="WHICH RESULT MATTERED MOST?";d.text((90,1585 if story else 1094),q,font=fit(d,q,890,45,28),fill=INK);return im
def render(base,row,src,badge,aliases,logos,verified,variant,bundle):
    tid=clean(row.get("template_id"))
    if tid=="tonight_in_the_w.a.v1":return render_preview(base,row,src,badge,aliases,logos,verified,variant,bundle)
    if tid in {"game_recap_final_score.a.v1","game_recap_final_score.c.story.v1"}:return render_game(base,row,src,badge,aliases,logos,verified,variant,bundle)
    if tid.startswith("last_night_in_the_w"):return render_last(base,row,badge,aliases,logos,verified,variant,bundle)
    return bg((1080,1920) if clean(row.get("platform"))=="stories" else (1080,1350),ORANGE,PURPLE,12)
def contact(items,out,title):
    if not items:return
    cols=3;cw=360;ch=510;rows=(len(items)+cols-1)//cols;sheet=Image.new("RGB",(cw*cols,74+ch*rows),(238,238,238));d=ImageDraw.Draw(sheet);d.text((24,18),title,font=font(30,True),fill=(20,20,22))
    for i,r in enumerate(items):
        p=Path(clean(r.get("output_path")))
        if not p.exists():continue
        im=Image.open(p).convert("RGB");im.thumbnail((320,430),Image.LANCZOS);x=(i%cols)*cw+(cw-im.width)//2;y=74+(i//cols)*ch+12;sheet.paste(im,(x,y));label=f"{clean(r.get('variant'))} • {clean(r.get('headline'))}";d.text(((i%cols)*cw+12,74+(i//cols)*ch+452),label,font=fit(d,label,cw-24,18,13),fill=(25,25,28))
    out.parent.mkdir(parents=True,exist_ok=True);sheet.save(out,quality=92)
def main():
    base=load_base()
    if not MAP.exists() and MAP_SCRIPT.exists():runpy.run_path(MAP_SCRIPT.as_posix(),run_name="__main__")
    mapped=load_json(MAP).get("rows",[]);OUT.mkdir(parents=True,exist_ok=True);shutil.rmtree(RENDERS,ignore_errors=True);(RENDERS/"logos_only").mkdir(parents=True);(RENDERS/"with_players").mkdir(parents=True);base.LOGO_CACHE_DIR=OUT/"logo_cache";base.LOGO_CACHE_DIR.mkdir(exist_ok=True);base.LOGO_AUDIT.clear();base.LOGO_CACHE.clear();badge=base.load_badge();aliases,logos,verified=base.registries();source=base.source_index();pindex=packages();manifest=[]
    for i,row in enumerate(mapped,1):
        if row.get("status")!="mapped":continue
        headline=clean(row.get("headline"));src=base.event_data(row,source)
        for variant in ["logos_only","with_players"]:
            bundle=bundle_for(headline,pindex) if variant=="with_players" else None
            if variant=="with_players" and not bundle:continue
            im=render(base,row,src,badge,aliases,logos,verified,variant,bundle);path=RENDERS/variant/f"{i:02d}_{slug(row.get('platform'))}_{slug(headline)}__{variant}.png";im.convert("RGB").save(path,quality=97,optimize=True);names=[clean(p.get("display_name")) for p in (bundle or {}).get("players",[]) if clean(p.get("display_name"))]
            manifest.append({"item_id":row.get("item_id"),"template_id":row.get("template_id"),"platform":row.get("platform"),"mode":row.get("mode"),"headline":headline,"variant":variant,"player_mode":(bundle or {}).get("player_mode","logos_only"),"player_assets_used":len((bundle or {}).get("players",[])),"player_names":";".join(names),"output_path":path.as_posix(),"width":im.width,"height":im.height,"status":"rendered_review","review_only":"true","notes":"Renderer v3.1 cinematic dual-lane proof; human visual approval required."})
    write_csv(MAN_CSV,manifest,FIELDS);write_csv(AUDIT_CSV,base.LOGO_AUDIT,base.LOGO_FIELDS);AUDIT_JSON.write_text(json.dumps({"version":VERSION,"rows":base.LOGO_AUDIT},indent=2),encoding="utf-8");payload={"version":VERSION,"generated_at_utc":datetime.now(timezone.utc).isoformat(),"review_only":True,"rendered_count":len(manifest),"logos_only_count":sum(r["variant"]=="logos_only" for r in manifest),"with_players_count":sum(r["variant"]=="with_players" for r in manifest),"fallback_logo_warnings":sum(r.get("status")=="warning_fallback" for r in base.LOGO_AUDIT),"policy":{"always_render_logos_only":True,"with_players_requires_packaged_player_assets":True,"no_fake_people":True,"no_invented_stats":True,"human_visual_approval_required":True},"items":manifest};MAN_JSON.write_text(json.dumps(payload,indent=2,sort_keys=True),encoding="utf-8");contact(manifest,CONTACT,"HSD Renderer v3.1 • Logos + Players");contact([r for r in manifest if r["variant"]=="with_players"],CONTACT_PLAYERS,"HSD Renderer v3.1 • Player Editions")
    with zipfile.ZipFile(ZIP,"w",zipfile.ZIP_DEFLATED) as z:
        for r in manifest:
            p=Path(r["output_path"])
            if p.exists():z.write(p,p.relative_to(OUT.parent).as_posix())
    REPORT.write_text("# HSD Template Renderer v3.1\n\n- Cinematic editorial source-of-truth direction.\n- Logos-only and approved-player editions.\n- Human visual approval required.\n",encoding="utf-8");print(json.dumps({"version":VERSION,"rendered":len(manifest),"logos_only":payload["logos_only_count"],"with_players":payload["with_players_count"]},indent=2))
if __name__=="__main__":main()
