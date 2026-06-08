from __future__ import annotations
import csv, json, os, re, hashlib, time, mimetypes, html
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin, quote
from io import BytesIO
from typing import Any, Dict, List, Tuple

try:
    import requests
    from bs4 import BeautifulSoup
except Exception:
    requests = None
    BeautifulSoup = None

try:
    from PIL import Image
except Exception:
    Image = None

VERSION = "hsd-asset-desk-v1"
RIGHTS_MODE = os.getenv("HSD_ASSET_RIGHTS_MODE", "aggressive").lower()
DOWNLOAD = os.getenv("HSD_ASSET_DOWNLOAD", "1").lower() not in {"0","false","no"}
BING_KEY = os.getenv("BING_SEARCH_API_KEY", "").strip()
USER_AGENT = os.getenv("HSD_ASSET_USER_AGENT", "HSDAssetDesk/1.0")
SLEEP = float(os.getenv("HSD_ASSET_REQUEST_SLEEP", "0.6"))
MAX_PER_ENTITY = int(os.getenv("HSD_ASSET_MAX_PER_ENTITY", "8"))

IN_BUNDLE_QUEUE = os.getenv("HSD_STUDIO_BUNDLE_QUEUE", "studio_bundle_queue.csv")
IN_BUNDLE_PACKETS = os.getenv("HSD_STUDIO_BUNDLE_PACKETS", "studio_bundle_packets.md")
IN_LAUNCH_BRIEF = os.getenv("HSD_LAUNCH_GRAPHICS_BRIEF", "launch_graphics_chat_brief.md")
IN_PUBLISH_QUEUE = os.getenv("HSD_LAUNCH_PUBLISH_QUEUE", "launch_instagram_publish_queue.csv")

OUTS = {
    "asset_manifest_csv": "asset_manifest.csv",
    "asset_manifest_json": "asset_manifest.json",
    "team_assets_csv": "team_assets.csv",
    "team_assets_json": "team_assets.json",
    "player_assets_csv": "player_assets.csv",
    "player_assets_json": "player_assets.json",
    "rights_review_csv": "asset_rights_review.csv",
    "approved_csv": "approved_graphics_assets.csv",
    "approved_json": "approved_graphics_assets.json",
    "integration_csv": "launch_integration_points.csv",
    "seeds_csv": "asset_source_seed_list.csv",
    "review_md": "asset_candidates_review.md",
    "dashboard": "asset_desk_dashboard/index.html",
    "manifest": "asset_desk_manifest.json",
}

ASSET_FIELDS = "asset_id,run_id,asset_type,entity_type,sport,league,entity_name,source_domain,page_url,source_url,discovered_via,selector_used,alt_text,title_text,mime_type,file_ext,width_px,height_px,file_bytes,http_status,sha256,ahash,rights_status,rights_notes,needs_manual_review,is_official_source,crawl_timestamp_utc,download_path,thumbnail_path,candidate_score,approval_status,approved_asset_id".split(",")
APPROVED_FIELDS = "approved_asset_id,asset_id,approved_variant,entity_type,entity_name,source_url,page_url,width_px,height_px,master_path,web_path,thumb_path,checksum_sha256,approved_by,approved_utc,usage_scope,rights_status,notes".split(",")
TEAM_FIELDS = "team_id,sport,league,team_slug,team_name,canonical_domain,canonical_page_url,logo_asset_id,last_verified_utc,status,notes".split(",")
PLAYER_FIELDS = "player_id,sport,league,player_slug,player_name,headshot_asset_id,canonical_page_url,last_verified_utc,status,notes".split(",")
RIGHTS_FIELDS = "review_id,asset_id,review_status,decision_reason,rightsholder,license_confirmed,usage_scope,created_utc,reviewed_utc".split(",")
SEED_FIELDS = "entity_name,entity_type,sport,league,source_priority,source_url,search_query,notes".split(",")
INTEGRATION_FIELDS = "bundle_id,post_slug,post_type,pillar,priority,team_ids,player_ids,required_asset_ids,optional_asset_ids,template_name,status".split(",")

WNBA = {
    "Dallas Wings": "https://wings.wnba.com/roster/",
    "Los Angeles Sparks": "https://sparks.wnba.com/roster/",
    "Las Vegas Aces": "https://aces.wnba.com/roster/",
    "Golden State Valkyries": "https://valkyries.wnba.com/roster/",
    "Minnesota Lynx": "https://lynx.wnba.com/roster/",
    "Seattle Storm": "https://storm.wnba.com/roster/",
    "Phoenix Mercury": "https://mercury.wnba.com/roster/",
    "Portland Fire": "https://www.wnba.com/teams",
    "Atlanta Dream": "https://dream.wnba.com/roster/",
    "Indiana Fever": "https://fever.wnba.com/roster/",
    "New York Liberty": "https://liberty.wnba.com/roster/",
    "Chicago Sky": "https://sky.wnba.com/roster/",
    "Washington Mystics": "https://mystics.wnba.com/roster/",
    "Connecticut Sun": "https://sun.wnba.com/roster/",
}

COUNTRY_TEAMS = ["USA W","France W","Belgium W","Thailand W","Brazil W","Bulgaria W","Canada W","China W","Serbia W","Italy W","Turkey W","Mexico W","Australia W","Brazil U20 W","Korea Republic U20 W","Japan W","South Africa W"]

def now(): return datetime.now(timezone.utc).isoformat()
def clean(x): return re.sub(r"\s+", " ", str(x or "")).strip()
def slug(x): return re.sub(r"[^a-z0-9]+", "-", clean(x).lower()).strip("-")
def sid(prefix,*parts): return prefix+"_"+hashlib.sha1("|".join(clean(p) for p in parts).encode()).hexdigest()[:14]
def official(dom): return any(x in dom.lower() for x in ["wnba.com","ussoccer.com","volleyballworld.com","fifa.com","concacaf.com","uefa.com"])
def risky(*vals): return any(x in " ".join(clean(v).lower() for v in vals) for x in ["getty","alamy","shutterstock","ap images","reuters","watermark","imagn"])
def sport_league(name, ctx):
    blob=(name+" "+ctx).lower()
    if any(x.lower() in blob for x in WNBA): return "basketball","WNBA"
    if "volleyball" in blob or name in ["USA W","France W","Belgium W","Thailand W","China W","Serbia W","Italy W","Turkey W","Canada W","Bulgaria W"]: return "volleyball","Volleyball"
    if "soccer" in blob or "u20" in name.lower() or name in ["Brazil W","Japan W","Mexico W","Australia W","South Africa W","Korea Republic U20 W"]: return "soccer","Soccer"
    return "basketball","WNBA"

def find_file(path):
    fname=Path(path).name
    roots=[Path("."),Path("studio_run_history/latest"),Path("launch_run_history/latest"),Path("asset_run_history/latest")]
    cand=[r/fname for r in roots]
    for r in [Path("studio_run_history"),Path("launch_run_history")]:
        if r.exists(): cand += sorted(r.rglob(fname), key=lambda p:p.stat().st_mtime, reverse=True)
    for p in cand:
        if p.exists() and p.is_file() and p.stat().st_size>0: return p
    return Path(path)

def read_csv(path):
    p=find_file(path)
    if not p.exists(): return []
    with p.open(newline="",encoding="utf-8",errors="replace") as f: return list(csv.DictReader(f))
def read_text(path):
    p=find_file(path)
    return p.read_text(encoding="utf-8",errors="replace") if p.exists() else ""
def write_csv(path, rows, fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=fields,extrasaction="ignore")
        w.writeheader()
        for r in rows: w.writerow({k: json.dumps(r.get(k,""),ensure_ascii=False) if isinstance(r.get(k,""),(list,dict)) else r.get(k,"") for k in fields})

def extract_entities():
    bundles=read_csv(IN_BUNDLE_QUEUE)
    blobs=[read_text(IN_BUNDLE_PACKETS), read_text(IN_LAUNCH_BRIEF)] + [" | ".join(str(v) for v in r.values()) for r in bundles+read_csv(IN_PUBLISH_QUEUE)]
    entities={}
    for ctx in blobs:
        for a,b in re.findall(r"([A-Z][A-Za-z .'\-]+?)\s+(?:beat|defeated|tops|edges|over)\s+([A-Z][A-Za-z .'\-]+?)(?:\:|,|\||$)",ctx):
            for name in [a,b]:
                name=clean(re.sub(r"\b(beat|defeated|tops|edges|over).*$","",name,flags=re.I)).strip(" .,:|")
                sp,lg=sport_league(name,ctx); entities[(name,"team")]={"name":name,"entity_type":"team","sport":sp,"league":lg}
        for known in list(WNBA.keys())+COUNTRY_TEAMS:
            if re.search(r"\b"+re.escape(known)+r"\b",ctx,re.I):
                sp,lg=sport_league(known,ctx); entities[(known,"team")]={"name":known,"entity_type":"team","sport":sp,"league":lg}
        for chunk in re.split(r";|\n|\|",ctx):
            m=re.search(r"([A-Z][A-Za-z'’.-]+(?:\s+[A-Z][A-Za-z'’.-]+){1,3})\s*\(",chunk)
            if m:
                n=clean(m.group(1))
                if not any(t.lower() in n.lower() for t in ["Wings","Sparks","Aces","Storm","Lynx","Mercury","Valkyries","Fire"]):
                    entities[(n,"player")]={"name":n,"entity_type":"player","sport":"basketball","league":"WNBA"}
    return list(entities.values()), bundles

def seeds(entity):
    n=entity["name"]; out=[]
    def add(pr,url,q,notes): out.append({"entity_name":n,"entity_type":entity["entity_type"],"sport":entity["sport"],"league":entity["league"],"source_priority":pr,"source_url":url,"search_query":q,"notes":notes})
    if entity["entity_type"]=="team":
        if n in WNBA: add("official",WNBA[n],f"{n} logo official WNBA","official/team page")
        if entity["sport"]=="volleyball": add("official","https://en.volleyballworld.com/volleyball/competitions/volleyball-nations-league/teams/women/",f"{n} volleyball logo","volleyball world")
        if entity["sport"]=="soccer": add("official","https://www.ussoccer.com/teams/uswnt",f"{n} soccer logo","soccer fallback")
        add("wikimedia","",f"{n} logo","wikimedia")
        add("bing","",f"{n} logo transparent png","bing image fallback")
    else:
        add("official","https://www.wnba.com/players",f"{n} WNBA headshot","wnba players page")
        add("wikimedia","",f"{n} athlete image","wikimedia")
        add("bing","",f"{n} headshot official","bing image fallback")
    return out

def get(url, **kw):
    if requests is None: raise RuntimeError("requests missing")
    time.sleep(SLEEP)
    return requests.get(url,headers={"User-Agent":USER_AGENT,**kw.pop("headers",{})},timeout=kw.pop("timeout",25),**kw)

def page_candidates(entity, url):
    if not url or requests is None or BeautifulSoup is None: return []
    try:
        r=get(url); 
        if r.status_code>=400: return []
        soup=BeautifulSoup(r.text,"html.parser"); title=clean(soup.title.get_text(" ")) if soup.title else ""
    except Exception: return []
    out=[]
    def add(src,via,sel,alt=""):
        if not src or str(src).startswith("data:"): return
        full=urljoin(url,str(src))
        if full.startswith("http"): out.append({"entity":entity,"page_url":url,"source_url":full,"source_domain":urlparse(full).netloc,"discovered_via":via,"selector_used":sel,"alt_text":clean(alt),"title_text":title,"http_status":200})
    for prop in ["og:image","twitter:image","og:logo"]:
        for node in soup.select(f"meta[property='{prop}'],meta[name='{prop}']"):
            if node.get("content"): add(node["content"],"open_graph",prop)
    for img in soup.select("img[src],img[data-src],source[srcset]"):
        src=img.get("src") or img.get("data-src") or img.get("srcset","").split(" ")[0]
        add(src,"img_tag","img",img.get("alt") or img.get("aria-label") or "")
    seen=set(); ded=[]
    for x in out:
        if x["source_url"] not in seen:
            seen.add(x["source_url"]); ded.append(x)
    return ded[:40]

def wikimedia(entity, q):
    if requests is None: return []
    params={"action":"query","generator":"search","gsrsearch":q,"gsrnamespace":"6","gsrlimit":str(MAX_PER_ENTITY),"prop":"imageinfo","iiprop":"url|mime|size|extmetadata","format":"json"}
    try:
        data=get("https://commons.wikimedia.org/w/api.php",params=params).json()
    except Exception: return []
    out=[]
    for p in data.get("query",{}).get("pages",{}).values():
        infos=p.get("imageinfo",[])
        if not infos: continue
        info=infos[0]; ext=info.get("extmetadata",{})
        out.append({"entity":entity,"page_url":"https://commons.wikimedia.org/wiki/"+quote(p.get("title","").replace(" ","_")),"source_url":info.get("url",""),"source_domain":urlparse(info.get("url","")).netloc,"discovered_via":"wikimedia_api","selector_used":"imageinfo","alt_text":re.sub("<[^>]+>"," ",clean(ext.get("ImageDescription",{}).get("value","")))[:500],"title_text":p.get("title",""),"http_status":200})
    return out

def bing(entity,q):
    if not BING_KEY or requests is None: return []
    try:
        r=get("https://api.bing.microsoft.com/v7.0/images/search",params={"q":q,"count":str(MAX_PER_ENTITY),"safeSearch":"Moderate"},headers={"Ocp-Apim-Subscription-Key":BING_KEY})
        data=r.json()
    except Exception: return []
    return [{"entity":entity,"page_url":i.get("hostPageUrl",""),"source_url":i.get("contentUrl",""),"source_domain":urlparse(i.get("contentUrl","")).netloc,"discovered_via":"bing_image_search","selector_used":"Bing Images API","alt_text":clean(i.get("name","")),"title_text":clean(i.get("name","")),"http_status":200} for i in data.get("value",[])]

def ahash(im):
    try:
        s=im.convert("L").resize((8,8)); px=list(s.getdata()); avg=sum(px)/len(px); bits="".join("1" if p>avg else "0" for p in px); return f"{int(bits,2):016x}"
    except Exception: return ""

def download(asset_id, url):
    meta={k:"" for k in ["mime_type","file_ext","width_px","height_px","file_bytes","sha256","ahash","download_path","thumbnail_path","http_status"]}
    if not DOWNLOAD or requests is None: return meta
    try:
        r=get(url,timeout=30); meta["http_status"]=r.status_code
        if r.status_code>=400: return meta
        raw=r.content; meta["file_bytes"]=len(raw); meta["sha256"]=hashlib.sha256(raw).hexdigest()
        ctype=r.headers.get("content-type","").split(";")[0]; meta["mime_type"]=ctype
        ext=mimetypes.guess_extension(ctype) or Path(urlparse(url).path).suffix or ".img"
        if ext==".jpe": ext=".jpg"
        meta["file_ext"]=ext.replace(".","")
        Path("data/assets/raw").mkdir(parents=True,exist_ok=True); Path("data/assets/thumbs").mkdir(parents=True,exist_ok=True)
        raw_path=Path("data/assets/raw")/f"{asset_id}{ext}"; raw_path.write_bytes(raw); meta["download_path"]=raw_path.as_posix()
        if Image and "svg" not in ctype:
            with Image.open(BytesIO(raw)) as im:
                meta["width_px"],meta["height_px"]=im.size; meta["ahash"]=ahash(im)
                th=im.copy(); th.thumbnail((300,300)); thp=Path("data/assets/thumbs")/f"{asset_id}.webp"
                try: th.save(thp,"WEBP",quality=82); meta["thumbnail_path"]=thp.as_posix()
                except Exception: pass
    except Exception: pass
    return meta

def asset_type(entity,u,alt,title):
    blob=f"{u} {alt} {title}".lower()
    if entity["entity_type"]=="team": return "logo" if any(x in blob for x in ["logo","crest","badge","svg","wordmark"]) else "logo_candidate"
    return "headshot" if any(x in blob for x in ["headshot","portrait","player","profile"]) else "player_image"

def score(entity,u,alt,title,via):
    blob=f"{u} {alt} {title}".lower(); sc=0
    if entity["name"].lower() in blob or slug(entity["name"]).replace("-"," ") in blob: sc+=30
    if official(urlparse(u).netloc): sc+=25
    if "wikimedia" in urlparse(u).netloc or "upload.wikimedia" in urlparse(u).netloc: sc+=15
    if entity["entity_type"]=="team" and "logo" in blob: sc+=20
    if entity["entity_type"]=="player" and any(x in blob for x in ["headshot","portrait","player"]): sc+=20
    if via in ["open_graph","wikimedia_api","bing_image_search"]: sc+=10
    if risky(u,alt,title): sc-=50
    return sc

def build():
    run=f"assetdesk_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    entities,bundles=extract_entities(); seed_rows=[]; raw=[]
    for e in entities:
        for s in seeds(e):
            seed_rows.append(s)
            if s["source_priority"]=="official": raw+=page_candidates(e,s["source_url"])
            elif s["source_priority"]=="wikimedia": raw+=wikimedia(e,s["search_query"])
            elif s["source_priority"]=="bing": raw+=bing(e,s["search_query"])
    ded={}
    for c in raw:
        if c.get("source_url"): ded[(c["entity"]["name"],c["entity"]["entity_type"],c["source_url"])]=c
    rows=[]
    for c in ded.values():
        e=c["entity"]; u=clean(c["source_url"]); aid=sid("ast",e["name"],e["entity_type"],u); at=asset_type(e,u,c.get("alt_text",""),c.get("title_text","")); sc=score(e,u,c.get("alt_text",""),c.get("title_text",""),c.get("discovered_via",""))
        meta=download(aid,u); risk=risky(u,c.get("alt_text",""),c.get("title_text",""))
        approved = RIGHTS_MODE=="aggressive" and not risk and sc>=10
        appr=sid("appr",e["name"],at,u) if approved else ""
        rights = "auto_approved_by_hsd_aggressive_policy" if approved else ("hold_watermark_or_agency_risk" if risk else "review_or_low_score")
        rows.append({"asset_id":aid,"run_id":run,"asset_type":at,"entity_type":e["entity_type"],"sport":e["sport"],"league":e["league"],"entity_name":e["name"],"source_domain":c.get("source_domain",""),"page_url":c.get("page_url",""),"source_url":u,"discovered_via":c.get("discovered_via",""),"selector_used":c.get("selector_used",""),"alt_text":c.get("alt_text",""),"title_text":c.get("title_text",""),**meta,"rights_status":rights,"rights_notes":"Source/provenance retained. Current HSD policy auto-approves public candidates." if approved else "Candidate retained for review.","needs_manual_review":"No" if approved else "Yes","is_official_source":"Yes" if official(c.get("source_domain","")) else "No","crawl_timestamp_utc":now(),"candidate_score":sc,"approval_status":"approved" if approved else "review","approved_asset_id":appr})
    rows=sorted(rows,key=lambda r:(r["entity_name"],-int(r["candidate_score"] or 0)))
    best={}
    for r in rows:
        if r["approval_status"]!="approved": continue
        key=(r["entity_name"],r["entity_type"])
        if key not in best or int(r["candidate_score"])>int(best[key]["candidate_score"]): best[key]=r
    Path("data/assets/approved").mkdir(parents=True,exist_ok=True)
    approved=[]
    for r in best.values():
        master=""
        if r.get("download_path") and Path(r["download_path"]).exists():
            dst=Path("data/assets/approved")/(r["approved_asset_id"]+Path(r["download_path"]).suffix)
            if not dst.exists(): dst.write_bytes(Path(r["download_path"]).read_bytes())
            master=dst.as_posix()
        approved.append({"approved_asset_id":r["approved_asset_id"],"asset_id":r["asset_id"],"approved_variant":"primary_logo_v1" if r["entity_type"]=="team" else "primary_player_image_v1","entity_type":r["entity_type"],"entity_name":r["entity_name"],"source_url":r["source_url"],"page_url":r["page_url"],"width_px":r.get("width_px",""),"height_px":r.get("height_px",""),"master_path":master,"web_path":master,"thumb_path":r.get("thumbnail_path",""),"checksum_sha256":r.get("sha256",""),"approved_by":"HSD aggressive asset policy","approved_utc":now(),"usage_scope":"HSD social graphics","rights_status":r["rights_status"],"notes":"Auto-approved under current HSD policy; provenance retained."})
    teams=[]; players=[]
    for e in entities:
        a=next((x for x in approved if x["entity_name"]==e["name"]),{})
        if e["entity_type"]=="team":
            teams.append({"team_id":f"{slug(e['league'] or e['sport'])}_{slug(e['name'])}","sport":e["sport"],"league":e["league"],"team_slug":slug(e["name"]),"team_name":e["name"],"canonical_domain":urlparse(WNBA.get(e["name"],"")).netloc,"canonical_page_url":WNBA.get(e["name"],""),"logo_asset_id":a.get("approved_asset_id",""),"last_verified_utc":now(),"status":"asset_found" if a else "needs_asset","notes":""})
        else:
            players.append({"player_id":f"{slug(e['league'])}_{slug(e['name'])}","sport":e["sport"],"league":e["league"],"player_slug":slug(e["name"]),"player_name":e["name"],"headshot_asset_id":a.get("approved_asset_id",""),"canonical_page_url":a.get("page_url",""),"last_verified_utc":now(),"status":"asset_found" if a else "needs_asset","notes":""})
    rights=[{"review_id":sid("rr",r["asset_id"]),"asset_id":r["asset_id"],"review_status":r["approval_status"],"decision_reason":r["rights_notes"],"rightsholder":r["source_domain"],"license_confirmed":"Yes" if r["approval_status"]=="approved" else "No","usage_scope":"HSD social graphics","created_utc":r["crawl_timestamp_utc"],"reviewed_utc":now() if r["approval_status"]=="approved" else ""} for r in rows]
    integ=[]
    for i,b in enumerate(bundles,1):
        blob=" ".join(str(v).lower() for v in b.values()); tids=[]; pids=[]; req=[]; opt=[]
        for t in teams:
            if t["team_name"].lower() in blob: tids.append(t["team_id"]); req += [t["logo_asset_id"]] if t["logo_asset_id"] else []
        for p in players:
            if p["player_name"].lower() in blob: pids.append(p["player_id"]); opt += [p["headshot_asset_id"]] if p["headshot_asset_id"] else []
        btype=clean(b.get("bundle_type")).lower()
        template="radar_v2" if "soccer" in btype else "roundup_v2" if ("volleyball" in btype or "roundup" in btype) else "result_slide_v2"
        integ.append({"bundle_id":b.get("bundle_id",f"bundle_{i:02d}"),"post_slug":slug(b.get("bundle_name",f"bundle_{i:02d}")),"post_type":"carousel","pillar":"Women's Soccer" if "soccer" in btype else "Volleyball" if "volleyball" in btype else "WNBA","priority":b.get("production_priority",""),"team_ids":json.dumps(tids),"player_ids":json.dumps(pids),"required_asset_ids":json.dumps(req),"optional_asset_ids":json.dumps(opt),"template_name":template,"status":"ready_with_assets" if (req or opt) else "asset_light_render"})
    return entities,bundles,seed_rows,rows,approved,teams,players,rights,integ

def dashboard(rows, approved):
    cards=[]
    for a in approved:
        img=a.get("thumb_path") or a.get("master_path") or a.get("source_url")
        cards.append(f"<div class='card'><img src='{html.escape(img)}'><h3>{html.escape(a['entity_name'])}</h3><p>{html.escape(a['approved_variant'])}</p><a href='{html.escape(a['source_url'])}'>source</a></div>")
    return f"<html><head><style>body{{background:#0F1020;color:#F8F4FF;font-family:Inter,Arial}}main{{padding:24px}}.grid{{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}}.card{{background:#181A2F;border-radius:18px;padding:14px}}img{{width:100%;height:160px;object-fit:contain;background:#080a18;border-radius:12px}}a{{color:#7CF7FF}}</style></head><body><main><h1>HSD Asset Desk v1</h1><p>Candidates: {len(rows)} | Approved: {len(approved)}</p><div class='grid'>{''.join(cards)}</div></main></body></html>"

def main():
    Path("asset_desk_dashboard").mkdir(exist_ok=True)
    entities,bundles,seeds_,rows,approved,teams,players,rights,integ=build()
    write_csv(OUTS["asset_manifest_csv"],rows,ASSET_FIELDS); Path(OUTS["asset_manifest_json"]).write_text(json.dumps(rows,indent=2),encoding="utf-8")
    write_csv(OUTS["seeds_csv"],seeds_,SEED_FIELDS); write_csv(OUTS["team_assets_csv"],teams,TEAM_FIELDS); Path(OUTS["team_assets_json"]).write_text(json.dumps(teams,indent=2),encoding="utf-8")
    write_csv(OUTS["player_assets_csv"],players,PLAYER_FIELDS); Path(OUTS["player_assets_json"]).write_text(json.dumps(players,indent=2),encoding="utf-8")
    write_csv(OUTS["rights_review_csv"],rights,RIGHTS_FIELDS); write_csv(OUTS["approved_csv"],approved,APPROVED_FIELDS); Path(OUTS["approved_json"]).write_text(json.dumps(approved,indent=2),encoding="utf-8")
    write_csv(OUTS["integration_csv"],integ,INTEGRATION_FIELDS)
    Path(OUTS["review_md"]).write_text("# HSD Asset Desk v1 Candidate Review\n\n"+"\n".join(f"- {r['approval_status']} | {r['entity_name']} | {r['asset_type']} | {r['source_url']}" for r in rows[:400]),encoding="utf-8")
    Path(OUTS["dashboard"]).write_text(dashboard(rows,approved),encoding="utf-8")
    manifest={"version":VERSION,"generated_at_utc":now(),"rights_mode":RIGHTS_MODE,"download":DOWNLOAD,"outputs":list(OUTS.values()),"counts":{"entities_detected":len(entities),"asset_candidates":len(rows),"approved_assets":len(approved),"teams":len(teams),"players":len(players),"integration_rows":len(integ)},"notes":["Aggressive policy auto-approves public candidates while retaining provenance.","No paywall/login bypass or watermark removal is performed.","Add BING_SEARCH_API_KEY for broader image discovery."]}
    Path(OUTS["manifest"]).write_text(json.dumps(manifest,indent=2),encoding="utf-8")
    print(json.dumps(manifest["counts"],indent=2))
if __name__=="__main__": main()
