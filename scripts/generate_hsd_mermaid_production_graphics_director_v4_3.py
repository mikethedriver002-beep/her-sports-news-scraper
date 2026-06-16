from __future__ import annotations

import csv
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "v4.3-copy-excellence-context-engine"
OUT_ROOT = Path("outputs/latest/production_graphics_director")
POSTABLE = Path("outputs/latest/POSTABLE_GRAPHICS")
COPY_DIR = OUT_ROOT / "copy_director"
CAROUSEL_DIR = OUT_ROOT / "carousel_director"
PROMPT_DIR = OUT_ROOT / "manual_prompt_dossiers"
QA_DIR = OUT_ROOT / "visual_qa_hard_gate"
CONTEXT_DIR = OUT_ROOT / "context_engine"
SUMMARY = Path("outputs/latest/summary.json")

RENDER_MANIFESTS = [Path("outputs/latest/review_files/rendered_handoff_manifest.csv"), Path("rendered_handoff_manifest.csv")]
PACKET_DIRS = [Path("manual_workflow_handoff_packs"), Path("assignment_handoff_zips")]
SLOT_FILES = [Path("manual_workflow_content_packets.csv"), Path("assignment_handoff_index.csv"), Path("mermaid_content_slots_v2.csv")]
GRAPHICS_PACK_DIRS = [Path("graphics_chat_upload_pack")]
RESULT_FILES = [Path("results_contract_v2.csv"), Path("hsd_pipeline_lite_review/files/results_contract_v2.csv")]
STORY_RESULTS_FILES = [Path("ig_story_results_queue.csv"), Path("hsd_pipeline_lite_review/files/ig_story_results_queue.csv")]
TEAMS = Path("data/asset_registry/wnba/teams.csv")
ATHLETES = Path("data/asset_registry/wnba/athletes.csv")
ATHLETE_IMAGES = Path("data/asset_registry/wnba/athlete_images.csv")
ATHLETE_NEEDS_FIX = Path("data/asset_registry/wnba/athlete_image_needs_fix.csv")

EXPORT_FIELDS = ["package_id", "packet_id", "platform", "headline", "source_png", "export_png", "review_status", "reason"]
COPY_FIELDS = ["package_id", "packet_id", "platform", "headline", "content_family", "caption", "threads_post", "first_comment", "story_frame_text", "poll_question", "hashtags", "evidence"]
CAROUSEL_FIELDS = ["package_id", "packet_id", "platform", "headline", "content_family", "slides", "carousel_plan_path", "prompt_dossier_path", "status"]
CONTEXT_FIELDS = ["package_id", "packet_id", "platform", "headline", "league", "content_type", "content_family", "teams", "approved_players", "needs_fix_players", "context_quality", "evidence"]
QA_FIELDS = ["package_id", "headline", "render_status", "visual_decision", "reason", "export_path"]

TEAM_TAGS = {
    "los_angeles_sparks": "#LASparks",
    "golden_state_valkyries": "#GoldenStateValkyries",
    "dallas_wings": "#DallasWings",
    "las_vegas_aces": "#LasVegasAces",
    "minnesota_lynx": "#MinnesotaLynx",
    "portland_fire": "#PortlandFire",
    "indiana_fever": "#IndianaFever",
    "toronto_tempo": "#TorontoTempo",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"


def norm(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(v).lower())


def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace") if path.exists() else ""
    except Exception:
        return ""


def read_json(path: Path) -> Dict[str, Any]:
    try:
        return json.loads(read_text(path)) if path.exists() else {}
    except Exception:
        return {}


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def nested_strings(value: Any) -> List[str]:
    out: List[str] = []
    if isinstance(value, str):
        out.append(value)
    elif isinstance(value, dict):
        for item in value.values():
            out.extend(nested_strings(item))
    elif isinstance(value, list):
        for item in value:
            out.extend(nested_strings(item))
    return out


def team_registry() -> Dict[str, Dict[str, str]]:
    return {row.get("team_id", ""): row for row in read_csv(TEAMS) if row.get("team_id")}


def team_name(team_id: str, teams: Dict[str, Dict[str, str]]) -> str:
    return clean(teams.get(team_id, {}).get("team_name") or team_id.replace("_", " ").title())


def detect_teams(text: str, teams: Dict[str, Dict[str, str]]) -> List[str]:
    blob = norm(text)
    found: List[str] = []
    for team_id, row in teams.items():
        for candidate in [row.get("team_name", ""), row.get("city", ""), row.get("nickname", "")]:
            value = norm(candidate)
            if value and len(value) > 2 and value in blob and team_id not in found:
                found.append(team_id)
    return found[:4]


def matchup_teams_from_headline(headline: str, teams: Dict[str, Dict[str, str]]) -> List[str]:
    h = clean(headline)
    for pattern in [r"(.+?)\s+at\s+(.+)$", r"(.+?)\s+vs\.?\s+(.+)$", r"(.+?)\s+versus\s+(.+)$", r"(.+?)\s+beat\s+(.+)$"]:
        m = re.match(pattern, h, flags=re.I)
        if not m:
            continue
        out: List[str] = []
        for piece in [m.group(1), m.group(2)]:
            candidates = detect_teams(piece, teams)
            if candidates:
                out.append(candidates[0])
        if len(out) >= 2:
            return out[:2]
    return []


def approved_athletes() -> Tuple[Dict[str, Dict[str, str]], set[str]]:
    rows = {r.get("athlete_id", ""): r for r in read_csv(ATHLETES) if r.get("athlete_id")}
    approved: Dict[str, Dict[str, str]] = {}
    for row in read_csv(ATHLETE_IMAGES):
        athlete_id = row.get("athlete_id", "")
        path = clean(row.get("file_path"))
        if row.get("image_type") == "headshot" and row.get("approved") == "true" and Path(path).exists() and Path(path + ".approved").exists() and athlete_id in rows:
            item = dict(rows[athlete_id])
            item["headshot_path"] = path
            approved[norm(item.get("display_name", ""))] = item
    needs_fix = {r.get("athlete_id", "") for r in read_csv(ATHLETE_NEEDS_FIX) if r.get("athlete_id")}
    return approved, needs_fix


def detect_players(text: str, athlete_map: Dict[str, Dict[str, str]], needs_fix: set[str]) -> Tuple[List[Dict[str, str]], List[str]]:
    blob = norm(text)
    found: List[Dict[str, str]] = []
    missing: List[str] = []
    seen: set[str] = set()
    for key, row in sorted(athlete_map.items(), key=lambda kv: len(kv[0]), reverse=True):
        athlete_id = row.get("athlete_id", "")
        if key and key in blob and athlete_id not in seen:
            if athlete_id in needs_fix:
                missing.append(athlete_id)
            else:
                found.append(row)
                seen.add(athlete_id)
    return found[:6], missing[:10]


def packet_index() -> Dict[str, Dict[str, Any]]:
    packets: Dict[str, Dict[str, Any]] = {}
    for folder in PACKET_DIRS:
        if not folder.exists():
            continue
        for path in sorted(folder.glob("*.zip")):
            try:
                with zipfile.ZipFile(path) as z:
                    data = json.loads(z.read("content_packet.json").decode("utf-8"))
                slot = data.get("slot", {}) if isinstance(data, dict) else {}
                pub = data.get("public_copy", {}) if isinstance(data, dict) else {}
                packet_id = clean(data.get("packet_id") or path.stem)
                packets[packet_id] = {
                    "package_id": packet_id,
                    "packet_id": packet_id,
                    "platform": clean(slot.get("platform") or pub.get("platform")),
                    "headline": clean(pub.get("headline") or slot.get("headline") or path.stem),
                    "league": clean(pub.get("league") or slot.get("league")),
                    "content_type": clean(pub.get("content_type") or slot.get("content_type")),
                    "hook": clean(pub.get("hook") or slot.get("copy_hook")),
                    "caption_seed": clean(pub.get("caption") or slot.get("ig_caption_seed")),
                    "story_text": clean(pub.get("story_frame_text") or slot.get("story_frame_text")),
                    "first_comment": clean(pub.get("first") or slot.get("first_comment")),
                    "raw_text": " | ".join(clean(x) for x in nested_strings(data) if clean(x)),
                    "source_kind": "content_packet",
                }
            except Exception:
                continue
    for path in SLOT_FILES:
        for row in read_csv(path):
            packet_id = clean(row.get("packet_id") or row.get("id") or row.get("slot_id") or row.get("bundle_name"))
            if not packet_id:
                continue
            item = packets.setdefault(packet_id, {"package_id": packet_id, "packet_id": packet_id, "source_kind": "slot_csv"})
            for key, value in row.items():
                if clean(value) and key not in item:
                    item[key] = clean(value)
            item["raw_text"] = clean(item.get("raw_text", "") + " | " + " | ".join(clean(v) for v in row.values() if clean(v)))
    return packets


def graphics_pack_items(teams: Dict[str, Dict[str, str]], athlete_map: Dict[str, Dict[str, str]], needs_fix: set[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for root in GRAPHICS_PACK_DIRS:
        if not root.exists():
            continue
        for pack in sorted([p for p in root.iterdir() if p.is_dir()]):
            prompt = read_text(pack / "00_PROMPT_TO_PASTE.md")
            display_rows = read_csv(pack / "graphics_display_copy.csv")
            headline = clean(display_rows[0].get("display_headline")) if display_rows else pack.name.replace("-", " ").title()
            subhead = clean(display_rows[0].get("display_subhead")) if display_rows else ""
            facts_match = re.search(r"Source facts:\s*(.+)", prompt)
            source_facts = clean(facts_match.group(1)) if facts_match else headline
            listed_players = [clean(m.group(1)) for m in re.finditer(r"- ([A-Z][A-Za-zÀ-ÿ' .-]+) \| primary_player_photo", prompt)]
            raw = " | ".join([headline, subhead, source_facts, prompt[:7000], "; ".join(listed_players)])
            team_ids = matchup_teams_from_headline(source_facts, teams) or matchup_teams_from_headline(headline, teams) or detect_teams(source_facts + " | " + headline, teams)[:2]
            players, missing = detect_players(raw, athlete_map, needs_fix)
            package_id = f"upload-pack_{pack.name}"
            out[package_id] = {
                "package_id": package_id,
                "packet_id": package_id,
                "platform": "Manual Graphics Pack",
                "headline": headline,
                "display_matchup": source_facts,
                "league": "WNBA" if team_ids else "",
                "content_type": "graphics_upload_pack",
                "hook": source_facts,
                "caption_seed": source_facts,
                "story_text": subhead,
                "first_comment": clean(display_rows[0].get("cta_copy")) if display_rows else "",
                "raw_text": raw,
                "source_kind": "graphics_upload_pack",
                "pack_dir": pack.as_posix(),
                "teams": team_ids,
                "approved_players": players,
                "needs_fix_players": missing,
                "listed_players": listed_players,
            }
    return out


def story_result_items() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for path in STORY_RESULTS_FILES:
        for row in read_csv(path):
            if clean(row.get("story_title")) and clean(row.get("score_summary")):
                package_id = f"story-results_{slug(row.get('story_slug') or row.get('story_title'))}"
                out[package_id] = {
                    "package_id": package_id,
                    "packet_id": package_id,
                    "platform": "IG Stories / Threads",
                    "headline": clean(row.get("story_title")),
                    "league": "WNBA",
                    "content_type": "results_roundup",
                    "hook": clean(row.get("score_summary")),
                    "caption_seed": clean(row.get("score_summary")),
                    "raw_text": " | ".join(clean(v) for v in row.values() if clean(v)),
                    "source_kind": "story_results_queue",
                    "score_summary": clean(row.get("score_summary")),
                    "teams_required": clean(row.get("teams_required")),
                }
    return out


def result_evidence() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for path in RESULT_FILES:
        for row in read_csv(path):
            headline = clean(row.get("headline"))
            if headline:
                out[norm(headline)] = row
    return out


def render_exports() -> List[Dict[str, Any]]:
    for path in RENDER_MANIFESTS:
        rows = read_csv(path)
        if rows:
            return [dict(row, package_id=row.get("packet_id", ""), source_kind="rendered_export") for row in rows]
    return []


def copy_rendered(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if POSTABLE.exists():
        shutil.rmtree(POSTABLE)
    POSTABLE.mkdir(parents=True, exist_ok=True)
    out: List[Dict[str, Any]] = []
    for row in rows:
        source = Path(row.get("output_path", ""))
        if not source.exists():
            continue
        platform = clean(row.get("platform"))
        folder = "ig_stories" if "story" in platform.lower() else "threads" if "thread" in platform.lower() else "ig_feed" if "feed" in platform.lower() else "review_only"
        target = POSTABLE / folder / f"{slug(row.get('packet_id') or row.get('headline') or source.stem)}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        row["export_png"] = target.as_posix()
        out.append(row)
    return out


def classify(ctx: Dict[str, Any]) -> str:
    headline = ctx.get("headline", "").lower()
    if ctx.get("source_kind") == "graphics_upload_pack":
        return "manual_graphics_pack"
    if ctx.get("source_kind") == "story_results_queue" or "last night in the w" in headline:
        return "wnba_results_roundup"
    if ctx.get("league", "").upper() == "WNBA" and len(ctx.get("teams", [])) >= 2 and (" at " in headline or " vs " in headline or "preview" in ctx.get("content_type", "").lower()):
        return "wnba_game_preview"
    if ctx.get("league", "").upper() == "WNBA" and ("beat" in headline or "result" in ctx.get("content_type", "").lower() or "recap" in ctx.get("content_type", "").lower()):
        return "wnba_result_recap"
    if ctx.get("league", "").upper() == "LPGA" or "lpga" in ctx.get("raw_text", "").lower() or "championship" in headline:
        return "feature_story"
    return "feature_story"


def build_context(item: Dict[str, Any], teams: Dict[str, Dict[str, str]], athlete_map: Dict[str, Dict[str, str]], needs_fix: set[str], result_map: Dict[str, Dict[str, str]]) -> Dict[str, Any]:
    raw = " | ".join(clean(item.get(key, "")) for key in ["headline", "league", "content_type", "hook", "caption_seed", "story_text", "first_comment", "raw_text", "score_summary"] if clean(item.get(key, "")))
    team_ids = list(item.get("teams", [])) if isinstance(item.get("teams"), list) else []
    if not team_ids:
        team_ids = matchup_teams_from_headline(clean(item.get("display_matchup") or item.get("headline")), teams) or detect_teams(raw + " | " + clean(item.get("headline")), teams)
    players = list(item.get("approved_players", [])) if isinstance(item.get("approved_players"), list) else []
    missing = list(item.get("needs_fix_players", [])) if isinstance(item.get("needs_fix_players"), list) else []
    if not players:
        players, missing = detect_players(raw, athlete_map, needs_fix)
    league = clean(item.get("league")) or ("WNBA" if team_ids or "last night in the w" in clean(item.get("headline")).lower() else "")
    headline = clean(item.get("headline") or item.get("package_id"))
    ctx = dict(item)
    ctx.update({"headline": headline, "league": league, "teams": team_ids, "approved_players": players, "needs_fix_players": missing, "result_row": result_map.get(norm(headline), {}), "context_quality": "rich" if len(raw) > 250 or players or team_ids or clean(item.get("score_summary")) else "thin", "evidence": raw[:1100]})
    ctx["content_family"] = classify(ctx)
    return ctx


def score_lines_from_summary(summary: str) -> List[str]:
    return [clean(x) for x in summary.split("|") if clean(x)]


def hashtags(ctx: Dict[str, Any], teams: Dict[str, Dict[str, str]]) -> str:
    tags = ["#HerSportsDaily", "#WomensSports"]
    if ctx.get("league", "").upper() == "WNBA" or ctx.get("content_family", "").startswith("wnba") or ctx.get("content_family") == "manual_graphics_pack":
        tags += ["#WNBA", "#Basketball"]
    if ctx.get("league", "").upper() == "LPGA" or "golf" in ctx.get("evidence", "").lower():
        tags += ["#LPGA", "#Golf"]
    for tid in ctx.get("teams", [])[:2]:
        tags.append(TEAM_TAGS.get(tid, "#" + team_name(tid, teams).replace(" ", "")))
    return " ".join(dict.fromkeys(tags))


def player_line(ctx: Dict[str, Any]) -> str:
    names = [clean(p.get("display_name")) for p in ctx.get("approved_players", []) if clean(p.get("display_name"))]
    if not names:
        names = [clean(x) for x in ctx.get("listed_players", []) if clean(x)]
    if not names:
        return "the players who tilt the night"
    return ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]


def copy_package(ctx: Dict[str, Any], teams: Dict[str, Dict[str, str]]) -> Tuple[str, str, str, str, str]:
    family = ctx.get("content_family")
    headline = ctx.get("headline", "")
    if family == "manual_graphics_pack":
        matchup = clean(ctx.get("display_matchup") or ctx.get("hook") or headline)
        names = player_line(ctx)
        caption = f"{matchup}.\n\nWho needs this one more? 👀\n\nThe Sparks come into the late window needing a road statement. {names} give this matchup real star power, and this is the kind of game that can make the California basketball conversation a little louder.\n\nGolden State gets it at home, with a chance to protect the Bay and turn the night into a statement. If the Valkyries control the pace and make LA chase the game, the building can tilt fast.\n\nOne late-night California question.\n\nDo the Sparks need the bounce more, or do the Valkyries need to hold home court? 🏀\n\n{hashtags(ctx, teams)}"
        return caption, f"{matchup}. Who needs this one more? 👀", "Road bounce or home hold? Drop your pick.", f"{matchup}. Who owns the late window?", "Who needs this one more?"
    if family == "wnba_results_roundup":
        lines = score_lines_from_summary(clean(ctx.get("score_summary") or ctx.get("hook")))
        score_block = "\n".join(f"• {line}" for line in lines[:4]) if lines else "• The finals are in."
        caption = f"Last Night in the W.\n\n{score_block}\n\nThe scores tell you who handled business. The bigger story is what each result changes: Dallas making noise, Minnesota sending a message, and another night where the W gave us a real scoreboard swing.\n\nWhich result mattered most? 🏀\n\n{hashtags(ctx, teams)}"
        return caption, "Last Night in the W. Dallas made noise. Minnesota sent a message. Which result mattered most?", "Best win of the night?", "Last Night in the W: which result mattered most?", "Best win?"
    if family == "wnba_result_recap":
        row = ctx.get("result_row", {}) if isinstance(ctx.get("result_row"), dict) else {}
        score = clean(row.get("score_display"))
        summary = clean(row.get("summary"))
        detail = summary or (f"Final: {score}." if score else "The final matters, but so does what comes next.")
        caption = f"{headline}.\n\n{detail}\n\nThis was not just a box-score result. It is the kind of win that changes the next conversation around rhythm, pressure, and who gets to carry momentum forward.\n\nWhat did this one tell you? 🏀\n\n{hashtags(ctx, teams)}"
        return caption, f"{headline}. What did this one tell you?", "What changed after this result?", headline[:110], "What stood out?"
    if family == "feature_story" and ctx.get("league", "").upper() == "LPGA":
        caption = f"Gina Kim and Yana Wilson are officially in the LPGA winner’s circle together.\n\nFrom the Epson Tour to a title moment at the Dow Championship, this is the kind of women’s golf story that deserves more than a line in the ticker. It is a team-format breakthrough, a shared win, and a reminder that the LPGA lane has real stories with texture.\n\nAre we talking about this enough?\n\n{hashtags(ctx, teams)}"
        return caption, "Gina Kim and Yana Wilson in the LPGA winner’s circle together. This deserves more attention.", "Are we talking about this enough?", "LPGA breakthrough: Kim + Wilson win together.", "Enough attention?"
    caption = f"{headline}.\n\nThis is a women’s sports story with more context than the headline can hold. The names, the moment, and what comes next all matter.\n\nWhat are you watching closest?\n\n{hashtags(ctx, teams)}"
    return caption, headline[:250], "What are you watching here?", headline[:110], "What stood out?"


def carousel_slides(ctx: Dict[str, Any], teams: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    family = ctx.get("content_family")
    if family == "manual_graphics_pack":
        matchup = clean(ctx.get("display_matchup") or ctx.get("hook") or ctx.get("headline"))
        return [
            {"slide": "1", "title": "Cover", "copy": matchup, "visual": "Premium HSD cover in the attached preferred style. Dark background. Both team logos. Approved player images. Big clean title."},
            {"slide": "2", "title": "Why it matters", "copy": "Road bounce vs Bay hold", "visual": "Two-sided stakes slide. Sparks road statement on one side, Valkyries home-court hold on the other."},
            {"slide": "3", "title": "Players to watch", "copy": player_line(ctx), "visual": "Use approved headshots only. Names large. No fake photos. No blank headshots."},
            {"slide": "4", "title": "Keys to the game", "copy": "Pace. Glass. Shot quality. Late-clock answers.", "visual": "Four bold key tiles with team-color accents."},
            {"slide": "5", "title": "CTA", "copy": "Who needs this one more?", "visual": "Poll-style end slide with both logos and HSD watermark."},
        ]
    if family == "wnba_results_roundup":
        lines = score_lines_from_summary(clean(ctx.get("score_summary") or ctx.get("hook")))
        return [
            {"slide": "1", "title": "Cover", "copy": "Last Night in the W", "visual": "Premium scoreboard cover. Dark cinematic HSD styling."},
            {"slide": "2", "title": "Scores", "copy": " | ".join(lines[:4]) if lines else "Every final, clean and readable.", "visual": "Large score rows with official team logos."},
            {"slide": "3", "title": "Dallas made noise", "copy": "Wings over Aces", "visual": "Spotlight Dallas result. Team logos only unless approved player image is contextually present."},
            {"slide": "4", "title": "Minnesota sent a message", "copy": "Lynx over Fire", "visual": "Spotlight Minnesota result. Big score, clean hierarchy."},
            {"slide": "5", "title": "CTA", "copy": "Best win of the night?", "visual": "Engagement slide."},
        ]
    if family == "feature_story" and ctx.get("league", "").upper() == "LPGA":
        return [
            {"slide": "1", "title": "Cover", "copy": "Kim + Wilson win together", "visual": "Premium LPGA editorial cover. No fake player imagery."},
            {"slide": "2", "title": "Path", "copy": "From Epson Tour to LPGA winner’s circle", "visual": "Timeline-style card."},
            {"slide": "3", "title": "Why it matters", "copy": "A shared title moment at the Dow Championship", "visual": "Clean editorial context card."},
            {"slide": "4", "title": "CTA", "copy": "Are we talking about this enough?", "visual": "Question-first end slide."},
        ]
    return [{"slide": "1", "title": "Cover", "copy": ctx.get("headline", ""), "visual": "Premium editorial cover."}, {"slide": "2", "title": "Context", "copy": "Why it matters.", "visual": "Clean explainer slide."}, {"slide": "3", "title": "CTA", "copy": "What stood out?", "visual": "Question-first end slide."}]


def prompt_dossier(ctx: Dict[str, Any], caption: str, slides: List[Dict[str, str]]) -> str:
    assets = "\n".join([f"- {p.get('display_name')} -> {p.get('headshot_path')}" for p in ctx.get("approved_players", [])]) or "- Use only exact attached assets or approved registry assets. If unavailable, use logos/text only."
    slide_text = "\n".join([f"### Slide {s['slide']}: {s['title']}\nOn-image copy: {s['copy']}\nVisual direction: {s['visual']}\n" for s in slides])
    return f"# HSD Manual Prompt Dossier — {ctx.get('headline')}\n\nPacket: `{ctx.get('package_id')}`\nPlatform: `{ctx.get('platform')}`\nFamily: `{ctx.get('content_family')}`\nQuality: `{ctx.get('context_quality')}`\n\n## Brand Style\n\nPremium women’s sports editorial. Dark high-contrast background. Bold condensed sports typography. Cinematic lighting. Clean hierarchy. No white dashboard cards. No tiny text. Use the official HSD watermark exactly.\n\n## Exact Assets\n\n{assets}\n\n## Evidence\n\n{ctx.get('evidence','')[:1200]}\n\n## Carousel Plan\n\n{slide_text}\n## Caption\n\n{caption}\n\n## Negative Prompt\n\nNo fake players. No invented stats. No unapproved headshots. No generic blank headshots. No cut-off names. No low-contrast text. No extra teams. No white panels.\n"


def copy_rendered(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if POSTABLE.exists():
        shutil.rmtree(POSTABLE)
    POSTABLE.mkdir(parents=True, exist_ok=True)
    out: List[Dict[str, Any]] = []
    for row in rows:
        source = Path(row.get("output_path", ""))
        if not source.exists():
            continue
        platform = clean(row.get("platform"))
        folder = "ig_stories" if "story" in platform.lower() else "threads" if "thread" in platform.lower() else "ig_feed" if "feed" in platform.lower() else "review_only"
        target = POSTABLE / folder / f"{slug(row.get('packet_id') or row.get('headline') or source.stem)}.png"
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        row["export_png"] = target.as_posix()
        out.append(row)
    return out


def render_exports() -> List[Dict[str, Any]]:
    for path in RENDER_MANIFESTS:
        rows = read_csv(path)
        if rows:
            return [dict(row, package_id=row.get("packet_id", ""), source_kind="rendered_export") for row in rows]
    return []


def update_summary(fields: Dict[str, Any]) -> None:
    s = read_json(SUMMARY)
    s.update(fields)
    if SUMMARY.parent.exists():
        SUMMARY.write_text(json.dumps(s, indent=2), encoding="utf-8")


def main() -> None:
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    for folder in [COPY_DIR, CAROUSEL_DIR, PROMPT_DIR, QA_DIR, CONTEXT_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
    teams = team_registry()
    athlete_map, needs_fix = approved_athletes()
    result_map = result_evidence()
    items: Dict[str, Dict[str, Any]] = {}
    packets = packet_index()
    for row in copy_rendered(render_exports()):
        package_id = row.get("packet_id") or row.get("package_id")
        base = dict(packets.get(package_id, {}))
        base.update({"package_id": package_id, "packet_id": package_id, "platform": row.get("platform"), "headline": row.get("headline"), "source_kind": "rendered_export", "export_png": row.get("export_png", "")})
        items[package_id] = base
    items.update(story_result_items())
    items.update(graphics_pack_items(teams, athlete_map, needs_fix))
    copy_rows: List[Dict[str, Any]] = []
    carousel_rows: List[Dict[str, Any]] = []
    context_rows: List[Dict[str, Any]] = []
    qa_rows: List[Dict[str, Any]] = []
    for package_id, item in items.items():
        ctx = build_context(item, teams, athlete_map, needs_fix, result_map)
        caption, threads, first, story, poll = copy_package(ctx, teams)
        slides = carousel_slides(ctx, teams)
        dossier = prompt_dossier(ctx, caption, slides)
        prompt_path = PROMPT_DIR / f"{slug(package_id)}.md"
        prompt_path.write_text(dossier, encoding="utf-8")
        carousel_path = CAROUSEL_DIR / f"{slug(package_id)}_carousel_plan.md"
        carousel_path.write_text("# Carousel Plan\n\n" + "\n".join([f"## Slide {s['slide']}: {s['title']}\n{s['copy']}\n\n{s['visual']}\n" for s in slides]), encoding="utf-8")
        copy_rows.append({"package_id": package_id, "packet_id": ctx.get("packet_id"), "platform": ctx.get("platform"), "headline": ctx.get("headline"), "content_family": ctx.get("content_family"), "caption": caption, "threads_post": threads, "first_comment": first, "story_frame_text": story, "poll_question": poll, "hashtags": hashtags(ctx, teams), "evidence": ctx.get("evidence", "")[:800]})
        carousel_rows.append({"package_id": package_id, "packet_id": ctx.get("packet_id"), "platform": ctx.get("platform"), "headline": ctx.get("headline"), "content_family": ctx.get("content_family"), "slides": len(slides), "carousel_plan_path": carousel_path.as_posix(), "prompt_dossier_path": prompt_path.as_posix(), "status": "ready_for_manual_or_renderer_build"})
        context_rows.append({"package_id": package_id, "packet_id": ctx.get("packet_id"), "platform": ctx.get("platform"), "headline": ctx.get("headline"), "league": ctx.get("league"), "content_type": ctx.get("content_type"), "content_family": ctx.get("content_family"), "teams": ";".join(ctx.get("teams", [])), "approved_players": ";".join([p.get("athlete_id", "") for p in ctx.get("approved_players", [])]), "needs_fix_players": ";".join(ctx.get("needs_fix_players", [])), "context_quality": ctx.get("context_quality"), "evidence": ctx.get("evidence", "")[:800]})
        qa_rows.append({"package_id": package_id, "headline": ctx.get("headline"), "render_status": "exported" if ctx.get("export_png") else "manual_prompt_only", "visual_decision": "human_review_required", "reason": "review visual and copy before posting", "export_path": ctx.get("export_png", "")})
    write_csv(COPY_DIR / "copy_bank.csv", copy_rows, COPY_FIELDS)
    write_csv(CAROUSEL_DIR / "carousel_manifest.csv", carousel_rows, CAROUSEL_FIELDS)
    write_csv(CONTEXT_DIR / "context_bank.csv", context_rows, CONTEXT_FIELDS)
    write_csv(QA_DIR / "visual_qa_hard_gate.csv", qa_rows, QA_FIELDS)
    (COPY_DIR / "copy_bank.md").write_text("# HSD Copy Bank\n\n" + "\n\n---\n\n".join([f"## {r['headline']}\n\nFamily: `{r['content_family']}`\n\n### IG Caption\n{r['caption']}\n\n### Threads\n{r['threads_post']}\n\n### First comment\n{r['first_comment']}" for r in copy_rows]) + "\n", encoding="utf-8")
    report = {"version": VERSION, "generated_at_utc": now_iso(), "packages": len(items), "rendered_exports": len([r for r in items.values() if r.get("export_png")]), "copy_items": len(copy_rows), "carousel_plans": len(carousel_rows), "prompt_dossiers": len(list(PROMPT_DIR.glob("*.md"))), "context_rows": len(context_rows), "rich_context_rows": len([r for r in context_rows if r.get("context_quality") == "rich"]), "manual_graphics_packs": len([r for r in items.values() if r.get("source_kind") == "graphics_upload_pack"]), "story_result_packages": len([r for r in items.values() if r.get("source_kind") == "story_results_queue"]), "postable_graphics_dir": POSTABLE.as_posix()}
    (OUT_ROOT / "production_graphics_director_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT_ROOT / "production_graphics_director_report.md").write_text("# Mermaid Production Graphics Director v4.3 Copy Excellence Engine\n\n" + f"Generated: {report['generated_at_utc']}\n\n" + "## Counts\n\n" + "\n".join([f"- {k}: {v}" for k, v in report.items() if k not in {"version", "generated_at_utc"}]) + "\n\n## Policy\n\n- Auto-renders remain human-review only.\n- Manual graphics packs and story result queues are included as production packages.\n- Evidence-first copy is preferred over headline fallback copy.\n", encoding="utf-8")
    update_summary({"production_director_version": VERSION, "production_director_packages": len(items), "production_director_copy_items": len(copy_rows), "production_director_carousel_plans": len(carousel_rows), "production_director_prompt_dossiers": report["prompt_dossiers"], "production_director_manual_graphics_packs": report["manual_graphics_packs"], "production_director_story_result_packages": report["story_result_packages"]})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
