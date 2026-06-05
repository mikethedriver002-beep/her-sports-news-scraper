"""
Her Sports Daily Studio Generator
---------------------------------

Reads:
    daily_content_brief.csv

Creates:
    daily_content_command_center.csv
    tonight_in_the_w_package.csv
    must_post_carousels.csv
    story_poll_package.csv
    caption_bank_v2.csv
    reel_script_package.md
    graphics_copy_package.md
    hsd_daily_content_hub.md
"""

from __future__ import annotations
import csv, re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

INPUT_FILE = "daily_content_brief.csv"
COMMAND_CENTER_FILE = "daily_content_command_center.csv"
TONIGHT_W_FILE = "tonight_in_the_w_package.csv"
MUST_POST_FILE = "must_post_carousels.csv"
STORY_POLL_FILE = "story_poll_package.csv"
CAPTION_BANK_FILE = "caption_bank_v2.csv"
REEL_SCRIPT_FILE = "reel_script_package.md"
GRAPHICS_COPY_FILE = "graphics_copy_package.md"
CONTENT_HUB_FILE = "hsd_daily_content_hub.md"
BRAND_NAME = "Her Sports Daily"

def clean(value: str) -> str:
    value = value or ""
    value = re.sub(r"\s+", " ", str(value)).strip()
    return value

def rank_value(row: Dict[str, str]) -> int:
    try: return int(clean(row.get("rank", "999")))
    except: return 999

def decision_priority(decision: str) -> int:
    return {"Must Post":1,"Maybe Post":2,"Save for Weekend":3,"Verify First":4,"Review Before Posting":5,"Skip":6}.get(clean(decision), 9)

def load_rows() -> List[Dict[str, str]]:
    with open(INPUT_FILE, newline="", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    rows.sort(key=lambda r: rank_value(r))
    return rows

def format_family(row: Dict[str, str]) -> str:
    decision = clean(row.get("editorial_decision", ""))
    story_type = clean(row.get("story_type", ""))
    sport = clean(row.get("sport", ""))
    if sport == "WNBA" and story_type in {"Game Preview","Game Recap / Result","Tournament Update"}:
        return "Tonight in the W"
    if decision == "Must Post":
        return "Breaking / Must Post Carousel"
    if story_type in {"Business / Growth","League Expansion","Record / Milestone"}:
        return "Context Carousel"
    if story_type in {"Recruiting / Roster News","Player Feature","Culture / Advocacy"}:
        return "Story + Feed Combo"
    if story_type in {"Opinion / Analysis","Soft Viral / Social"}:
        return "Stories / Poll"
    return "Feed Post"

def recommended_asset(row: Dict[str, str]) -> str:
    story_type = clean(row.get("story_type", ""))
    decision = clean(row.get("editorial_decision", ""))
    family = format_family(row)
    if family == "Tonight in the W": return "4-slide matchup/pregame graphic"
    if decision == "Must Post": return "4-slide news carousel"
    if story_type == "Business / Growth": return "4-slide data carousel"
    if story_type == "Record / Milestone": return "3 to 4-slide milestone graphic"
    if story_type == "Recruiting / Roster News": return "single graphic + Story follow-up"
    if story_type == "Game Recap / Result": return "single recap card or quick carousel"
    if story_type == "Opinion / Analysis": return "Story poll + debate card"
    return "single feed card"

def production_status(row: Dict[str, str]) -> str:
    decision = clean(row.get("editorial_decision", ""))
    if decision == "Must Post": return "Make first"
    if decision == "Maybe Post": return "Make today if time"
    if decision == "Save for Weekend": return "Backlog"
    if decision in {"Verify First","Review Before Posting"}: return "Hold"
    return "Skip"

def story_poll_question(row: Dict[str, str]) -> str:
    sport = clean(row.get("sport", "women's sports"))
    story_type = clean(row.get("story_type", ""))
    if story_type == "Game Preview": return f"Who are you backing in this {sport} matchup?"
    if story_type == "Game Recap / Result": return f"What was the biggest takeaway from this {sport} result?"
    if story_type == "Record / Milestone": return "How impressive is this milestone?"
    if story_type == "Business / Growth": return "What growth story in women's sports matters most to you?"
    if story_type == "Recruiting / Roster News": return "How big is this move for the program or team?"
    if story_type == "Opinion / Analysis": return "Do you agree or disagree?"
    return f"Should {BRAND_NAME} cover this story in more detail?"

def story_poll_options(row: Dict[str, str]) -> str:
    story_type = clean(row.get("story_type", ""))
    if story_type == "Game Preview": return "Team A / Team B"
    if story_type == "Game Recap / Result": return "Big statement / Need more proof"
    if story_type == "Record / Milestone": return "Historic / Solid but overhyped"
    if story_type == "Business / Growth": return "Media rights / Attendance / Investment / Sponsorship"
    if story_type == "Recruiting / Roster News": return "Huge move / Good move / Not sold yet"
    if story_type == "Opinion / Analysis": return "Agree / Disagree"
    return "Yes / No"

def caption_text(row: Dict[str, str], variant: str) -> str:
    headline = clean(row.get("headline", ""))
    why = clean(row.get("why_it_matters", ""))
    angle = clean(row.get("instagram_angle", ""))
    hashtags = clean(row.get("hashtags", ""))
    hook = clean(row.get("hook", ""))
    if variant == "feed":
        body = f"{headline}\n\n{angle}\n\nWhy it matters: {why}\n\nFollow {BRAND_NAME} for daily women's sports coverage."
    elif variant == "carousel":
        body = f"{headline}\n\n{hook}\n\nWhy it matters: {why}\n\nSwipe through for the quick breakdown."
    else:
        body = f"{headline}\n\nQuick hit: {why}\n\nWant more? Follow {BRAND_NAME}."
    return f"{body}\n\n{hashtags}".strip()

def write_command_center(rows):
    fieldnames = ["rank","editorial_decision","production_status","content_family","recommended_asset","recommended_timing","sport","story_type","headline","hook","source","link","visual_brief"]
    with open(COMMAND_CENTER_FILE,"w",newline="",encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for row in rows:
            w.writerow({
                "rank": clean(row.get("rank","")),
                "editorial_decision": clean(row.get("editorial_decision","")),
                "production_status": production_status(row),
                "content_family": format_family(row),
                "recommended_asset": recommended_asset(row),
                "recommended_timing": clean(row.get("recommended_timing","")),
                "sport": clean(row.get("sport","")),
                "story_type": clean(row.get("story_type","")),
                "headline": clean(row.get("headline","")),
                "hook": clean(row.get("hook","")),
                "source": clean(row.get("source","")),
                "link": clean(row.get("link","")),
                "visual_brief": clean(row.get("visual_brief","")),
            })

def tonight_card_type(row):
    story_type = clean(row.get("story_type",""))
    if story_type == "Game Preview": return "Pregame"
    if story_type == "Game Recap / Result": return "Postgame"
    if story_type == "Tournament Update": return "Standings/Update"
    if story_type == "Record / Milestone": return "Stat Watch"
    return "League Watch"

def tonight_headline(row):
    story_type = clean(row.get("story_type","")); headline = clean(row.get("headline",""))
    if story_type == "Game Preview": return f"Tonight in the W: {headline}"
    if story_type == "Game Recap / Result": return f"Tonight in the W Recap: {headline}"
    return f"Tonight in the W Watch: {headline}"

def tonight_key_stat(row):
    story_type = clean(row.get("story_type",""))
    if story_type == "Record / Milestone": return clean(row.get("why_it_matters",""))
    if story_type == "Game Preview": return "Key watch item: one player and one matchup to know."
    if story_type == "Game Recap / Result": return "Key takeaway: what changed and who stood out."
    return clean(row.get("instagram_angle",""))

def build_tonight_rows(rows):
    candidates = [r for r in rows if clean(r.get("sport",""))=="WNBA" and clean(r.get("editorial_decision","")) in {"Must Post","Maybe Post","Save for Weekend"}]
    candidates.sort(key=lambda r: (decision_priority(r.get("editorial_decision","")), rank_value(r)))
    out = []
    for idx, row in enumerate(candidates[:6], start=1):
        out.append({
            "card_order": str(idx),
            "card_type": tonight_card_type(row),
            "headline": tonight_headline(row),
            "subhead": clean(row.get("hook","")),
            "key_stat_or_angle": tonight_key_stat(row),
            "graphic_copy": clean(row.get("first_slide","")) or clean(row.get("headline","")),
            "cta": "What are you watching in the W tonight?",
            "source": clean(row.get("source","")),
            "link": clean(row.get("link","")),
        })
    return out

def write_tonight_package(rows):
    fieldnames = ["card_order","card_type","headline","subhead","key_stat_or_angle","graphic_copy","cta","source","link"]
    with open(TONIGHT_W_FILE,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for row in build_tonight_rows(rows): w.writerow(row)

def make_carousel_copy(row):
    headline = clean(row.get("headline","")); first_slide = clean(row.get("first_slide","")) or headline
    why = clean(row.get("why_it_matters","")); angle = clean(row.get("instagram_angle","")); story_type = clean(row.get("story_type","")); sport = clean(row.get("sport",""))
    slide2_title, slide2_body = "What happened", headline
    if story_type == "Business / Growth": slide2_title, slide2_body = "The number to know", why
    elif story_type == "Record / Milestone": slide2_title, slide2_body = "The milestone", why
    elif story_type == "Recruiting / Roster News": slide2_title, slide2_body = "Why this move matters", why
    elif story_type == "Game Recap / Result": slide2_title, slide2_body = "Quick takeaway", why
    elif story_type == "Game Preview": slide2_title, slide2_body = "What to watch", angle
    slides = [("1",first_slide,"Top story alert."),("2",slide2_title,slide2_body),("3","The Her Sports Daily angle",angle or why),("4",f"Your take on this {sport} story?","Comment below and follow Her Sports Daily.")]
    return [{"rank": clean(row.get("rank","")),"editorial_decision": clean(row.get("editorial_decision","")),"sport": sport,"headline": headline,"slide_number": n,"slide_title": t,"slide_body": b} for n,t,b in slides]

def write_must_post(rows):
    fieldnames = ["rank","editorial_decision","sport","headline","slide_number","slide_title","slide_body"]
    with open(MUST_POST_FILE,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for row in [r for r in rows if clean(r.get("editorial_decision","")) in {"Must Post","Maybe Post"}]:
            for slide in make_carousel_copy(row): w.writerow(slide)

def write_story_polls(rows):
    fieldnames = ["rank","headline","sport","story_type","poll_question","poll_options","story_frame_1","story_frame_2"]
    with open(STORY_POLL_FILE,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for row in [r for r in rows if clean(r.get("editorial_decision","")) in {"Must Post","Maybe Post","Save for Weekend"}]:
            w.writerow({
                "rank": clean(row.get("rank","")),
                "headline": clean(row.get("headline","")),
                "sport": clean(row.get("sport","")),
                "story_type": clean(row.get("story_type","")),
                "poll_question": story_poll_question(row),
                "poll_options": story_poll_options(row),
                "story_frame_1": clean(row.get("first_slide","")) or clean(row.get("headline","")),
                "story_frame_2": "Vote in the poll, then send us your take.",
            })

def write_caption_bank(rows):
    fieldnames = ["rank","headline","editorial_decision","caption_variant","caption"]
    with open(CAPTION_BANK_FILE,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fieldnames); w.writeheader()
        for row in rows:
            for variant in ["feed","carousel","story"]:
                w.writerow({"rank": clean(row.get("rank","")),"headline": clean(row.get("headline","")),"editorial_decision": clean(row.get("editorial_decision","")),"caption_variant": variant,"caption": caption_text(row, variant)})

def reel_script(row):
    headline=clean(row.get("headline","")); hook=clean(row.get("hook","")) or headline; why=clean(row.get("why_it_matters","")); angle=clean(row.get("instagram_angle","")); sport=clean(row.get("sport","Women's sports")); decision=clean(row.get("editorial_decision",""))
    return f"""## Rank {clean(row.get("rank",""))}: {headline}

**Priority:** {decision}  
**Sport:** {sport}  
**Recommended format:** 20 to 30 second talking-head or voiceover Reel

**Voiceover**
{hook}

Here is the quick context: {headline}

{angle}

Why it matters: {why}

Follow Her Sports Daily for daily women's sports coverage.

**On-screen text**
1. {headline}
2. Why it matters
3. What comes next?

"""

def write_reel_scripts(rows):
    lines=["# Her Sports Daily Reel Script Package","",f"Generated: {datetime.now(timezone.utc).isoformat()}",""]
    for row in [r for r in rows if clean(r.get("editorial_decision","")) in {"Must Post","Maybe Post"}]:
        lines.append(reel_script(row))
    Path(REEL_SCRIPT_FILE).write_text("\n".join(lines), encoding="utf-8")

def write_graphics_copy(rows):
    lines=["# Her Sports Daily Graphics Copy Package","",f"Generated: {datetime.now(timezone.utc).isoformat()}","","## Daily Content Command Center",""]
    for row in rows:
        lines.extend([f"### Rank {clean(row.get('rank',''))}: {clean(row.get('headline',''))}","",f"- Decision: {clean(row.get('editorial_decision',''))}",f"- Content family: {format_family(row)}",f"- Recommended asset: {recommended_asset(row)}",f"- Hook: {clean(row.get('hook',''))}",f"- First slide / main text: {clean(row.get('first_slide',''))}",f"- Carousel outline: {clean(row.get('carousel_outline',''))}",f"- Visual brief: {clean(row.get('visual_brief',''))}",""])
    lines.extend(["## Tonight in the W",""])
    for row in build_tonight_rows(rows):
        lines.extend([f"### Card {clean(row.get('card_order',''))}: {clean(row.get('headline',''))}","",f"- Card type: {clean(row.get('card_type',''))}",f"- Subhead: {clean(row.get('subhead',''))}",f"- Key stat or angle: {clean(row.get('key_stat_or_angle',''))}",f"- CTA: {clean(row.get('cta',''))}",""])
    Path(GRAPHICS_COPY_FILE).write_text("\n".join(lines), encoding="utf-8")

def write_content_hub(rows):
    must=[r for r in rows if clean(r.get("editorial_decision",""))=="Must Post"]; maybe=[r for r in rows if clean(r.get("editorial_decision",""))=="Maybe Post"]; weekend=[r for r in rows if clean(r.get("editorial_decision",""))=="Save for Weekend"]
    lines=["# Her Sports Daily Daily Content Hub","",f"Generated: {datetime.now(timezone.utc).isoformat()}","","## What this package includes","",f"- `{COMMAND_CENTER_FILE}`",f"- `{TONIGHT_W_FILE}`",f"- `{MUST_POST_FILE}`",f"- `{STORY_POLL_FILE}`",f"- `{CAPTION_BANK_FILE}`",f"- `{REEL_SCRIPT_FILE}`",f"- `{GRAPHICS_COPY_FILE}`",""]
    for group_name, items in [("Must Post", must),("Maybe Post", maybe),("Save for Weekend", weekend)]:
        lines.append(f"## {group_name}"); lines.append("")
        if not items: lines.extend(["No items in this bucket.",""]); continue
        for row in items:
            lines.extend([f"### Rank {clean(row.get('rank',''))}: {clean(row.get('headline',''))}","",f"- Sport: {clean(row.get('sport',''))}",f"- Story type: {clean(row.get('story_type',''))}",f"- Content family: {format_family(row)}",f"- Recommended asset: {recommended_asset(row)}",f"- Hook: {clean(row.get('hook',''))}",f"- Caption starter: {clean(row.get('caption_starter',''))}",f"- Visual brief: {clean(row.get('visual_brief',''))}",""])
    Path(CONTENT_HUB_FILE).write_text("\n".join(lines), encoding="utf-8")

def main():
    rows=load_rows()
    write_command_center(rows)
    write_tonight_package(rows)
    write_must_post(rows)
    write_story_polls(rows)
    write_caption_bank(rows)
    write_reel_scripts(rows)
    write_graphics_copy(rows)
    write_content_hub(rows)
    print("done")

if __name__=="__main__":
    main()
