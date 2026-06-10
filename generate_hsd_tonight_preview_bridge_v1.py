from __future__ import annotations

import csv, hashlib, json, os, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-tonight-preview-bridge-v1.4"
MAX_HOURS_AHEAD = float(os.environ.get("HSD_PREVIEW_LOOKAHEAD_HOURS", "30"))
TIMEZONE_LABEL = os.environ.get("HSD_TIMEZONE_LABEL", "ET")

BUNDLE_FIELDS = [
    "bundle_rank","bundle_id","bundle_name","bundle_type","production_priority","asset_type","asset_shape","slide_count",
    "content_family","sports_mix","source_items_count","source_headlines","caption_seed","bundle_prompt","accuracy_lock",
    "watermark_rule","source_packet_ids_json","event_date","event_datetime","result_date","freshness_label","freshness_source",
    "source_run_timestamp","event_age_hours","freshness_status","freshness_decision","source_event_dates_json"
]
GRAPHICS_FIELDS = ["post_rank","post_slug","post_title","content_family","asset_type","asset_shape","priority","source_headline","caption_seed","event_date","event_datetime","freshness_status"]


def now() -> str: return datetime.now(timezone.utc).isoformat()
def clean(v: Any) -> str: return re.sub(r"\s+", " ", str(v or "")).strip()
def slugify(v: str) -> str: return re.sub(r"[^a-zA-Z0-9]+", "-", clean(v).lower()).strip("-") or "post"
def stable_id(*parts: Any) -> str: return "bundle_"+hashlib.sha1("|".join(clean(p) for p in parts).encode()).hexdigest()[:14]

def read_csv(path: str) -> List[Dict[str,str]]:
    p=Path(path)
    if not p.exists(): return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f: return list(csv.DictReader(f))

def write_csv(path: str, rows: List[Dict[str,Any]], fields: List[str]) -> None:
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields, extrasaction="ignore"); w.writeheader(); w.writerows(rows)

def parse_dt(s: str):
    s=clean(s).replace("Z","+00:00")
    if not s: return None
    try:
        dt=datetime.fromisoformat(s)
        return dt if dt.tzinfo else dt.replace(tzinfo=timezone.utc)
    except Exception: pass
    m=re.search(r"\b(20\d{2})-(\d{1,2})-(\d{1,2})\b", s)
    if m: return datetime(int(m.group(1)), int(m.group(2)), int(m.group(3)), 12, tzinfo=timezone.utc)
    return None

def is_existing_bundle_empty() -> bool:
    p=Path("studio_bundle_queue.csv")
    if not p.exists(): return True
    try: return sum(1 for _ in csv.DictReader(p.open(newline='',encoding='utf-8',errors='replace'))) == 0
    except Exception: return True

def row_is_upcoming(row: Dict[str,str], now_dt) -> bool:
    status=clean(row.get("status_norm") or row.get("game_state")).lower()
    if "final" in status or clean(row.get("winner")) or clean(row.get("loser")):
        return False
    dt=parse_dt(row.get("scheduled_start_utc") or row.get("event_datetime") or row.get("scheduled_datetime_local") or row.get("scheduled_date_local"))
    if not dt: return False
    hours=(dt-now_dt).total_seconds()/3600.0
    return -2 <= hours <= MAX_HOURS_AHEAD

def matchup(row: Dict[str,str]) -> str:
    away=clean(row.get("away_team_display") or row.get("away_team_norm"))
    home=clean(row.get("home_team_display") or row.get("home_team_norm"))
    return f"{away} at {home}" if away and home else clean(row.get("graphics_headline") or row.get("headline") or row.get("canonical_key"))

def time_label(row: Dict[str,str]) -> str:
    # Keep source-provided label if present. Do not overpromise conversion.
    status=clean(row.get("game_state") or row.get("status_norm"))
    if status and "pm" in status.lower() or "am" in status.lower(): return status
    dt=parse_dt(row.get("scheduled_start_utc"))
    if not dt: return "Time TBA"
    # Approx ET by UTC-4 for HSD social copy. This is only display support.
    hour=(dt.hour-4)%24; minute=dt.minute
    suffix="AM" if hour<12 else "PM"; h=hour%12 or 12
    return f"{h}:{minute:02d} {suffix} {TIMEZONE_LABEL}"

def main() -> None:
    if not is_existing_bundle_empty():
        print("Studio bundle queue already has rows. Preview fallback not needed.")
        return
    now_dt=datetime.now(timezone.utc)
    all_rows=[]
    for fname in ["top_womens_results.csv","today_womens_results.csv","reconciled_events.csv"]:
        for r in read_csv(fname):
            r["_source_file"]=fname
            all_rows.append(r)
    upcoming=[]; seen=set()
    for r in all_rows:
        if not row_is_upcoming(r, now_dt): continue
        key=clean(r.get("canonical_key") or matchup(r)).lower()
        if key in seen: continue
        seen.add(key); upcoming.append(r)
    upcoming=upcoming[:4]
    if not upcoming:
        Path("studio_preview_fallback_report.md").write_text(f"# HSD Tonight Preview Fallback v1.4\n\nGenerated: {now()}\n\nNo upcoming rows found.\n", encoding="utf-8")
        print("No upcoming rows found for preview fallback.")
        return
    first_dt=parse_dt(upcoming[0].get("scheduled_start_utc") or upcoming[0].get("scheduled_date_local")) or now_dt
    event_date=first_dt.date().isoformat()
    source_headlines=" | ".join(matchup(r) for r in upcoming)
    schedule_lines=[f"{matchup(r)} - {time_label(r)}" for r in upcoming]
    bundle_name="Tonight in the W Preview" if any(clean(r.get("league_norm")).upper()=="WNBA" for r in upcoming) else "Tonight in Women’s Sports Preview"
    prompt=(
        "Create a 4-slide 1080x1350 Her Sports Daily carousel previewing tonight's women's sports slate.\n"
        "Use only exact approved team/logo assets. Do not invent player photos.\n"
        "Slide 1: strong Tonight in the W cover with the full slate.\n"
        "Slide 2: schedule board with game times.\n"
        "Slide 3: what to watch, using only matchup context, no invented stats.\n"
        "Slide 4: CTA asking which game people are watching.\n"
        "Games: " + " | ".join(schedule_lines)
    )
    row={
        "bundle_rank":"1","bundle_id":stable_id(VERSION,bundle_name,source_headlines),"bundle_name":bundle_name,
        "bundle_type":"wnba_preview","production_priority":"POST FIRST","asset_type":"4-slide carousel","asset_shape":"1080x1350","slide_count":"4",
        "content_family":"Tonight in the W","sports_mix":", ".join(sorted(set(clean(r.get('sport_norm')) for r in upcoming if clean(r.get('sport_norm'))))),
        "source_items_count":str(len(upcoming)),"source_headlines":source_headlines,
        "caption_seed":"Tonight in the W: " + " | ".join(schedule_lines),"bundle_prompt":prompt,
        "accuracy_lock":"Preview schedule only. Do not invent final scores, player stats, injuries, records, or quotes.",
        "watermark_rule":"Use one compact HSD watermark/logo bug in the top-left safe zone.",
        "source_packet_ids_json":json.dumps([clean(r.get('event_uid') or r.get('canonical_key')) for r in upcoming]),
        "event_date":event_date,"event_datetime":first_dt.isoformat(),"result_date":"","freshness_label":"upcoming_schedule",
        "freshness_source":"results_desk_upcoming_fallback","source_run_timestamp":now(),"event_age_hours":"0.0",
        "freshness_status":"fresh_upcoming_schedule","freshness_decision":"allow","source_event_dates_json":json.dumps([clean(r.get('scheduled_date_local')) for r in upcoming])
    }
    write_csv("studio_bundle_queue.csv", [row], BUNDLE_FIELDS)
    write_csv("studio_graphics_queue.csv", [{"post_rank":"1","post_slug":slugify(bundle_name),"post_title":bundle_name,"content_family":"Tonight in the W","asset_type":"4-slide carousel","asset_shape":"1080x1350","priority":"POST FIRST","source_headline":source_headlines,"caption_seed":row['caption_seed'],"event_date":event_date,"event_datetime":row['event_datetime'],"freshness_status":"fresh_upcoming_schedule"}], GRAPHICS_FIELDS)
    Path("studio_bundle_packets.md").write_text(f"# HSD Studio Bundle Packets\n\n## BUNDLE 1: {bundle_name}\n\nSource items: {source_headlines}\n\n### Caption seed\n{row['caption_seed']}\n\n### Accuracy lock\n{row['accuracy_lock']}\n", encoding="utf-8")
    Path("studio_bundle_prompts.md").write_text(f"# HSD Studio Bundle Prompts\n\n## {bundle_name}\n\n```text\n{prompt}\n```\n", encoding="utf-8")
    Path("studio_preview_fallback_report.md").write_text("# HSD Tonight Preview Fallback v1.4\n\nGenerated: "+now()+"\n\nCreated preview bundle from fresh upcoming schedule rows.\n\n"+"\n".join([f"- {x}" for x in schedule_lines])+"\n", encoding="utf-8")
    print(f"Created {bundle_name} preview bundle with {len(upcoming)} games.")

if __name__ == "__main__": main()
