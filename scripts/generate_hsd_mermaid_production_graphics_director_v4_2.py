from __future__ import annotations

import csv
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "v4.2-evidence-context-engine"
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
RESULT_FILES = [Path("results_contract_v2.csv")]
STORY_RESULTS_QUEUE = Path("ig_story_results_queue.csv")
TEAMS = Path("data/asset_registry/wnba/teams.csv")
ATHLETES = Path("data/asset_registry/wnba/athletes.csv")
ATHLETE_IMAGES = Path("data/asset_registry/wnba/athlete_images.csv")
ATHLETE_NEEDS_FIX = Path("data/asset_registry/wnba/athlete_image_needs_fix.csv")

EXPORT_FIELDS = ["packet_id", "platform", "headline", "source_png", "export_png", "review_status", "reason"]
COPY_FIELDS = ["package_id", "packet_id", "platform", "headline", "content_family", "caption", "threads_post", "first_comment", "story_frame_text", "poll_question", "hashtags", "evidence"]
CAROUSEL_FIELDS = ["package_id", "packet_id", "platform", "headline", "content_family", "slides", "carousel_plan_path", "prompt_dossier_path", "status"]
CONTEXT_FIELDS = ["package_id", "packet_id", "platform", "headline", "league", "content_type", "content_family", "teams", "approved_players", "needs_fix_players", "context_quality", "evidence"]
QA_FIELDS = ["package_id", "headline", "render_status", "visual_decision", "reason", "export_path"]


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
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({field: row.get(field, "") for field in fields})


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


def packet_index() -> Dict[str, Dict[str, Any]]:
    packets: Dict[str, Dict[str, Any]] = {}
    for folder in PACKET_DIRS:
        if not folder.exists():
            continue
        for zp in sorted(folder.glob("*.zip")):
            try:
                with zipfile.ZipFile(zp) as z:
                    data = json.loads(z.read("content_packet.json").decode("utf-8"))
                slot = data.get("slot", {}) if isinstance(data, dict) else {}
                pub = data.get("public_copy", {}) if isinstance(data, dict) else {}
                pid = clean(data.get("packet_id") or zp.stem)
                packets[pid] = {
                    "package_id": pid,
                    "packet_id": pid,
                    "platform": clean(slot.get("platform") or pub.get("platform")),
                    "headline": clean(pub.get("headline") or slot.get("headline") or zp.stem),
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
            pid = clean(row.get("packet_id") or row.get("id") or row.get("slot_id") or row.get("bundle_name"))
            if not pid:
                continue
            item = packets.setdefault(pid, {"package_id": pid, "packet_id": pid, "source_kind": "slot_csv"})
            for k, v in row.items():
                if clean(v) and k not in item:
                    item[k] = clean(v)
            item["raw_text"] = clean(item.get("raw_text", "") + " | " + " | ".join(clean(v) for v in row.values() if clean(v)))
    return packets


def upload_pack_items() -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for root in GRAPHICS_PACK_DIRS:
        if not root.exists():
            continue
        for pack in sorted([p for p in root.iterdir() if p.is_dir()]):
            specs = read_json(pack / "graphics_production_specs.json")
            prompt = read_text(pack / "00_PROMPT_TO_PASTE.md")
            freshness = read_text(pack / "studio_freshness_report.md")
            display_rows = read_csv(pack / "graphics_display_copy.csv")
            headline = clean(display_rows[0].get("display_headline")) if display_rows else clean(specs.get("posts", [{}])[0].get("bundle_name", pack.name) if specs else pack.name.replace("-", " ").title())
            source_facts_match = re.search(r"Source facts:\s*(.+)", prompt)
            source_facts = clean(source_facts_match.group(1)) if source_facts_match else ""
            players = []
            for m in re.finditer(r"- ([A-Z][A-Za-zÀ-ÿ' .-]+) \| primary_player_photo", prompt):
                players.append(clean(m.group(1)))
            blocked = "Decision: **block**" in freshness or "blocked_stale_event" in freshness
            package_id = f"upload-pack_{pack.name}"
            out[package_id] = {
                "package_id": package_id,
                "packet_id": package_id,
                "platform": "Manual Graphics Pack",
                "headline": headline,
                "league": "WNBA" if " W" in headline or "WNBA" in prompt or "Sparks" in prompt or "Valkyries" in prompt else "",
                "content_type": "graphics_upload_pack",
                "hook": source_facts,
                "caption_seed": source_facts,
                "story_text": clean(display_rows[0].get("display_subhead")) if display_rows else "",
                "first_comment": clean(display_rows[0].get("cta_copy")) if display_rows else "",
                "raw_text": " | ".join([headline, source_facts, prompt[:6000], freshness[:1000], "; ".join(players)]),
                "source_kind": "graphics_upload_pack",
                "pack_dir": pack.as_posix(),
                "graphics_specs": specs,
                "freshness_blocked": blocked,
                "listed_players": players,
            }
    return out


def render_rows() -> List[Dict[str, str]]:
    for path in RENDER_MANIFESTS:
        rows = read_csv(path)
        if rows:
            return rows
    out = []
    for p in Path("outputs/latest/rendered_graphics").rglob("*.png"):
        out.append({"packet_id": p.parent.name, "platform": "review", "headline": p.stem.replace("-", " ").title(), "output_path": p.as_posix()})
    return out


def team_registry() -> Dict[str, Dict[str, str]]:
    return {r.get("team_id", ""): r for r in read_csv(TEAMS) if r.get("team_id")}


def team_name(tid: str, teams: Dict[str, Dict[str, str]]) -> str:
    return clean(teams.get(tid, {}).get("team_name") or tid.replace("_", " ").title())


def approved_athletes() -> Tuple[Dict[str, Dict[str, str]], set[str]]:
    rows = {r.get("athlete_id", ""): r for r in read_csv(ATHLETES) if r.get("athlete_id")}
    approved = {}
    for row in read_csv(ATHLETE_IMAGES):
        aid = row.get("athlete_id", "")
        path = clean(row.get("file_path"))
        if row.get("image_type") == "headshot" and row.get("approved") == "true" and Path(path).exists() and Path(path + ".approved").exists() and aid in rows:
            item = dict(rows[aid])
            item["headshot_path"] = path
            approved[norm(item.get("display_name", ""))] = item
    needs_fix = {r.get("athlete_id", "") for r in read_csv(ATHLETE_NEEDS_FIX) if r.get("athlete_id")}
    return approved, needs_fix


def detect_teams(text: str, teams: Dict[str, Dict[str, str]]) -> List[str]:
    blob = norm(text)
    found: List[str] = []
    for tid, row in teams.items():
        for c in [row.get("team_name", ""), row.get("city", ""), row.get("nickname", "")]:
            cn = norm(c)
            if cn and len(cn) > 2 and cn in blob and tid not in found:
                found.append(tid)
    return found[:4]


def detect_players(text: str, athletes_by_name: Dict[str, Dict[str, str]], needs_fix: set[str]) -> Tuple[List[Dict[str, str]], List[str]]:
    blob = norm(text)
    found: List[Dict[str, str]] = []
    missing: List[str] = []
    seen: set[str] = set()
    for key, row in sorted(athletes_by_name.items(), key=lambda kv: len(kv[0]), reverse=True):
        aid = row.get("athlete_id", "")
        if key and key in blob and aid not in seen:
            if aid in needs_fix:
                missing.append(aid)
            else:
                found.append(row)
                seen.add(aid)
    return found[:6], missing[:10]


def results_evidence() -> Dict[str, Any]:
    evidence: Dict[str, Any] = {"score_summaries": [], "eligible_previews": [], "live_reviews": [], "blocked": []}
    for row in read_csv(STORY_RESULTS_QUEUE):
        if clean(row.get("score_summary")):
            evidence["score_summaries"].append(clean(row.get("score_summary")))
    for path in RESULT_FILES:
        for row in read_csv(path):
            record = {"headline": clean(row.get("headline")), "summary": clean(row.get("summary")), "score_display": clean(row.get("score_display")), "status": clean(row.get("status")), "eligibility": clean(row.get("content_eligibility")), "reason": clean(row.get("freshness_reason"))}
            if row.get("content_eligibility") == "eligible":
                evidence["eligible_previews"].append(record)
            elif row.get("content_eligibility") == "review":
                evidence["live_reviews"].append(record)
            else:
                evidence["blocked"].append(record)
    return evidence


def classify(ctx: Dict[str, Any]) -> str:
    h = ctx["headline"].lower()
    if ctx.get("source_kind") == "graphics_upload_pack":
        return "manual_graphics_pack"
    if "last night in the w" in h:
        return "wnba_results_roundup"
    if ctx["league"].upper() == "WNBA" and len(ctx.get("teams", [])) >= 2 and (" at " in h or " vs " in h or "preview" in ctx.get("content_type", "").lower()):
        return "wnba_game_preview"
    if ctx["league"].upper() == "WNBA" and ("beat" in h or "result" in ctx.get("content_type", "").lower() or "recap" in ctx.get("content_type", "").lower()):
        return "wnba_result_recap"
    if ctx["league"].upper() == "LPGA" or "championship" in h or "lpga" in ctx.get("raw_text", "").lower():
        return "feature_story"
    return "feature_story"


def context_for(item: Dict[str, Any], teams: Dict[str, Dict[str, str]], athletes_by_name: Dict[str, Dict[str, str]], needs_fix: set[str]) -> Dict[str, Any]:
    raw = " | ".join(clean(item.get(k, "")) for k in ["headline", "league", "content_type", "hook", "caption_seed", "story_text", "first_comment", "raw_text"] if clean(item.get(k, "")))
    headline = clean(item.get("headline") or item.get("package_id"))
    team_ids = detect_teams(raw + " | " + headline, teams)
    players, missing = detect_players(raw + " | " + headline, athletes_by_name, needs_fix)
    league = clean(item.get("league")) or ("WNBA" if team_ids or "last night in the w" in headline.lower() else "")
    ctx = dict(item)
    ctx.update({"headline": headline, "league": league, "teams": team_ids, "approved_players": players, "needs_fix_players": missing, "context_quality": "rich" if len(raw) > 250 or players or team_ids else "thin", "evidence": raw[:850]})
    ctx["content_family"] = classify(ctx)
    return ctx


def score_lines(ev: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    for summary in ev.get("score_summaries", []):
        parts = [clean(p) for p in summary.split("|") if clean(p)]
        lines.extend(parts)
    return lines[:4]


def hashtags(ctx: Dict[str, Any], teams: Dict[str, Dict[str, str]]) -> str:
    tags = ["#HerSportsDaily", "#WomensSports"]
    if ctx["league"].upper() == "WNBA" or ctx["content_family"].startswith("wnba") or ctx["content_family"] == "manual_graphics_pack":
        tags += ["#WNBA", "#Basketball"]
    if ctx["league"].upper() == "LPGA" or "golf" in ctx.get("evidence", "").lower():
        tags += ["#LPGA", "#Golf"]
    for tid in ctx.get("teams", [])[:2]:
        tags.append("#" + team_name(tid, teams).replace(" ", ""))
    return " ".join(dict.fromkeys(tags))


def player_names(players: List[Dict[str, str]], fallback: List[str] | None = None) -> str:
    names = [clean(p.get("display_name")) for p in players if clean(p.get("display_name"))]
    if not names and fallback:
        names = [clean(x) for x in fallback if clean(x)]
    if not names:
        return "the players who tilt the matchup"
    return ", ".join(names[:-1]) + " and " + names[-1] if len(names) > 1 else names[0]


def copy_package(ctx: Dict[str, Any], teams: Dict[str, Dict[str, str]], ev: Dict[str, Any]) -> Tuple[str, str, str, str, str]:
    headline = ctx["headline"]
    fam = ctx["content_family"]
    team_ids = ctx.get("teams", [])
    if fam == "manual_graphics_pack":
        facts = clean(ctx.get("hook")) or headline
        people = player_names(ctx.get("approved_players", []), ctx.get("listed_players", []))
        caption = f"{facts}.\n\nStill to come in the W. 👀\n\nThis is the late-window kind of game that can give the night a real pulse. {people} give the matchup star power, but the bigger question is simple: who sets the terms first?\n\nThe Sparks need the road edge. Golden State gets the building. And in a California matchup with real rivalry potential, the first clean run can change the whole feel.\n\nWho needs this one more? 🏀\n\n{hashtags(ctx, teams)}"
        return caption, f"{facts}. Who needs this one more?", "Road edge or home hold? Drop your pick.", f"{facts}. Who owns the first run?", "Who needs it more?"
    if fam == "wnba_results_roundup":
        lines = score_lines(ev)
        score_text = "\n".join(f"• {x}" for x in lines) if lines else "• Final scores are in."
        caption = f"Last Night in the W.\n\n{score_text}\n\nThe scoreboard gives us the finals. The bigger story is what travels: who found rhythm, who left with questions, and which result changes the next conversation.\n\nThis is the kind of recap that should feel bigger than a score dump.\n\nWhich result mattered most? 🏀\n\n{hashtags(ctx, teams)}"
        return caption, "Last Night in the W. Which result actually moved the night?", "Best win of the night?", "Last Night in the W: which result mattered most?", "Best win?"
    if fam == "feature_story" and ctx["league"].upper() == "LPGA":
        caption = f"Gina Kim and Yana Wilson are officially in the LPGA winner’s circle together.\n\nFrom the Epson Tour to a title moment at the Dow Championship, this is the kind of women’s golf story that deserves more than a line in the ticker. It is about a team format, a breakthrough, and two players turning a shared opportunity into a career marker.\n\nWomen’s golf has stories with texture. This is one of them.\n\nAre we talking about this enough?\n\n{hashtags(ctx, teams)}"
        return caption, "Gina Kim and Yana Wilson in the LPGA winner’s circle together. This deserves more attention.", "Are we talking about this enough?", "LPGA breakthrough: Kim + Wilson win together.", "Enough attention?"
    caption = f"{headline}.\n\nThis is a women’s sports story with more context than the headline can hold. The names, the moment, and what comes next all matter.\n\nWhat are you watching closest?\n\n{hashtags(ctx, teams)}"
    return caption, headline[:250], "What are you watching here?", headline[:110], "What stood out?"


def carousel_slides(ctx: Dict[str, Any], teams: Dict[str, Dict[str, str]], ev: Dict[str, Any]) -> List[Dict[str, str]]:
    fam = ctx["content_family"]
    if fam == "manual_graphics_pack":
        facts = clean(ctx.get("hook")) or ctx["headline"]
        return [
            {"slide": "1", "title": "Cover", "copy": facts, "visual": "Use attached style reference: premium dark HSD cover, both team logos, approved player photos, no white cards."},
            {"slide": "2", "title": "Matchup", "copy": "Road edge vs home hold", "visual": "Two-column matchup card with Sparks left, Valkyries right, player-photo cutouts and logo lockups."},
            {"slide": "3", "title": "Players to watch", "copy": player_names(ctx.get("approved_players", []), ctx.get("listed_players", [])), "visual": "Approved or attached exact player photos only, names clearly labeled."},
            {"slide": "4", "title": "Keys", "copy": "Pace. Glass. Shot quality. Late-clock answers.", "visual": "Four bold key tiles, big type, no tiny body text."},
            {"slide": "5", "title": "CTA", "copy": "Who needs this one more?", "visual": "Poll-style end slide with both logos and HSD watermark."},
        ]
    if fam == "wnba_results_roundup":
        lines = score_lines(ev)
        return [
            {"slide": "1", "title": "Cover", "copy": "Last Night in the W", "visual": "Premium dark scoreboard cover."},
            {"slide": "2", "title": "Scores", "copy": " | ".join(lines) if lines else "Every final, clean and readable.", "visual": "Large final-score rows with exact team logos."},
            {"slide": "3", "title": "Biggest win", "copy": "Which result moved the night?", "visual": "Spotlight one result with bigger type and team logos."},
            {"slide": "4", "title": "What changed", "copy": "Momentum, pressure, and the next matchup.", "visual": "Editorial analysis slide, no invented stats."},
            {"slide": "5", "title": "CTA", "copy": "Best win of the night?", "visual": "Engagement slide."},
        ]
    if fam == "feature_story" and ctx["league"].upper() == "LPGA":
        return [
            {"slide": "1", "title": "Cover", "copy": "Kim + Wilson win together", "visual": "Premium LPGA editorial cover, trophy/winner-circle energy, no fake player imagery."},
            {"slide": "2", "title": "Why it matters", "copy": "From Epson Tour to LPGA winner’s circle", "visual": "Timeline-style context card."},
            {"slide": "3", "title": "The story", "copy": "A team-format breakthrough at the Dow Championship", "visual": "Clean explainer card with event lockup."},
            {"slide": "4", "title": "CTA", "copy": "Are we talking about this enough?", "visual": "Question-first HSD slide."},
        ]
    return [{"slide": "1", "title": "Cover", "copy": ctx["headline"], "visual": "Premium editorial cover."}, {"slide": "2", "title": "Context", "copy": "Why it matters.", "visual": "Clean explainer."}, {"slide": "3", "title": "CTA", "copy": "What stood out?", "visual": "Question-first end slide."}]


def prompt_dossier(ctx: Dict[str, Any], caption: str, slides: List[Dict[str, str]]) -> str:
    assets = "\n".join([f"- {p.get('display_name')} -> {p.get('headshot_path')}" for p in ctx.get("approved_players", [])]) or "- Use only attached exact assets or approved registry assets. If not available, use text/logos only."
    slide_text = "\n".join([f"### Slide {s['slide']}: {s['title']}\nOn-image copy: {s['copy']}\nVisual direction: {s['visual']}\n" for s in slides])
    return f"# HSD Manual Prompt Dossier — {ctx['headline']}\n\nPacket: `{ctx['package_id']}`\nPlatform: `{ctx['platform']}`\nFamily: `{ctx['content_family']}`\nQuality: `{ctx['context_quality']}`\n\n## Brand Style\n\nPremium women’s sports editorial. Dark high-contrast background. Bold condensed sports typography. Cinematic lighting. Clean hierarchy. No white dashboard cards. No tiny text. Use the HSD watermark.\n\n## Approved / Exact Assets\n\n{assets}\n\n## Evidence\n\n{ctx.get('evidence','')[:1100]}\n\n## Carousel Plan\n\n{slide_text}\n## Caption\n\n{caption}\n\n## Negative Prompt\n\nNo fake players. No invented stats. No unapproved headshots. No generic blank headshots. No cut-off names. No low-contrast text. No extra teams. No white panels.\n"


def render_exports() -> List[Dict[str, Any]]:
    for p in RENDER_MANIFESTS:
        rows = read_csv(p)
        if rows:
            return [dict(r, package_id=r.get("packet_id", ""), source_kind="rendered_export") for r in rows]
    return []


def copy_rendered(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if POSTABLE.exists():
        shutil.rmtree(POSTABLE)
    POSTABLE.mkdir(parents=True, exist_ok=True)
    out = []
    for r in rows:
        src = Path(r.get("output_path", ""))
        if not src.exists():
            continue
        plat = clean(r.get("platform"))
        folder = "ig_stories" if "story" in plat.lower() else "threads" if "thread" in plat.lower() else "ig_feed" if "feed" in plat.lower() else "review_only"
        dest = POSTABLE / folder / f"{slug(r.get('packet_id') or r.get('headline') or src.stem)}.png"
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)
        r["export_png"] = dest.as_posix()
        out.append(r)
    return out


def update_summary(fields: Dict[str, Any]) -> None:
    s = read_json(SUMMARY)
    s.update(fields)
    if SUMMARY.parent.exists():
        SUMMARY.write_text(json.dumps(s, indent=2), encoding="utf-8")


def main() -> None:
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    for d in [COPY_DIR, CAROUSEL_DIR, PROMPT_DIR, QA_DIR, CONTEXT_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    packets = packet_index()
    packs = upload_pack_items()
    teams = team_registry()
    athlete_map, needs_fix = approved_athletes()
    ev = results_evidence()
    rendered = copy_rendered(render_exports())
    items: Dict[str, Dict[str, Any]] = {}
    for r in rendered:
        pid = r.get("packet_id") or r.get("package_id")
        base = dict(packets.get(pid, {}))
        base.update({"package_id": pid, "packet_id": pid, "platform": r.get("platform"), "headline": r.get("headline"), "source_kind": "rendered_export", "export_png": r.get("export_png", "")})
        items[pid] = base
    items.update(packs)
    copy_rows: List[Dict[str, Any]] = []
    carousel_rows: List[Dict[str, Any]] = []
    context_rows: List[Dict[str, Any]] = []
    qa_rows: List[Dict[str, Any]] = []
    for pid, raw_item in items.items():
        ctx = context_for(raw_item, teams, athlete_map, needs_fix)
        caption, threads, first, story, poll = copy_package(ctx, teams, ev)
        slides = carousel_slides(ctx, teams, ev)
        prompt = prompt_dossier(ctx, caption, slides)
        ppath = PROMPT_DIR / f"{slug(pid)}.md"
        ppath.write_text(prompt, encoding="utf-8")
        cpath = CAROUSEL_DIR / f"{slug(pid)}_carousel_plan.md"
        cpath.write_text("# Carousel Plan\n\n" + "\n".join([f"## Slide {s['slide']}: {s['title']}\n{s['copy']}\n\n{s['visual']}\n" for s in slides]), encoding="utf-8")
        copy_rows.append({"package_id": pid, "packet_id": ctx.get("packet_id"), "platform": ctx.get("platform"), "headline": ctx.get("headline"), "content_family": ctx.get("content_family"), "caption": caption, "threads_post": threads, "first_comment": first, "story_frame_text": story, "poll_question": poll, "hashtags": hashtags(ctx, teams), "evidence": ctx.get("evidence", "")[:700]})
        carousel_rows.append({"package_id": pid, "packet_id": ctx.get("packet_id"), "platform": ctx.get("platform"), "headline": ctx.get("headline"), "content_family": ctx.get("content_family"), "slides": len(slides), "carousel_plan_path": cpath.as_posix(), "prompt_dossier_path": ppath.as_posix(), "status": "ready_for_manual_or_renderer_build"})
        context_rows.append({"package_id": pid, "packet_id": ctx.get("packet_id"), "platform": ctx.get("platform"), "headline": ctx.get("headline"), "league": ctx.get("league"), "content_type": ctx.get("content_type"), "content_family": ctx.get("content_family"), "teams": ";".join(ctx.get("teams", [])), "approved_players": ";".join([p.get("athlete_id", "") for p in ctx.get("approved_players", [])]), "needs_fix_players": ";".join(ctx.get("needs_fix_players", [])), "context_quality": ctx.get("context_quality"), "evidence": ctx.get("evidence", "")[:700]})
        qa_rows.append({"package_id": pid, "headline": ctx.get("headline"), "render_status": "exported" if ctx.get("export_png") else "manual_prompt_only", "visual_decision": "human_review_required", "reason": "do not auto-post; review visual and copy", "export_path": ctx.get("export_png", "")})
    write_csv(COPY_DIR / "copy_bank.csv", copy_rows, COPY_FIELDS)
    write_csv(CAROUSEL_DIR / "carousel_manifest.csv", carousel_rows, CAROUSEL_FIELDS)
    write_csv(CONTEXT_DIR / "context_bank.csv", context_rows, CONTEXT_FIELDS)
    write_csv(QA_DIR / "visual_qa_hard_gate.csv", qa_rows, QA_FIELDS)
    (COPY_DIR / "copy_bank.md").write_text("# HSD Copy Bank\n\n" + "\n\n---\n\n".join([f"## {r['headline']}\n\nFamily: `{r['content_family']}`\n\n### IG Caption\n{r['caption']}\n\n### Threads\n{r['threads_post']}\n\n### First comment\n{r['first_comment']}" for r in copy_rows]) + "\n", encoding="utf-8")
    report = {"version": VERSION, "generated_at_utc": now_iso(), "packages": len(items), "rendered_exports": len(rendered), "copy_items": len(copy_rows), "carousel_plans": len(carousel_rows), "prompt_dossiers": len(list(PROMPT_DIR.glob("*.md"))), "context_rows": len(context_rows), "rich_context_rows": len([r for r in context_rows if r.get("context_quality") == "rich"]), "manual_graphics_packs": len(packs), "postable_graphics_dir": POSTABLE.as_posix()}
    (OUT_ROOT / "production_graphics_director_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT_ROOT / "production_graphics_director_report.md").write_text("# Mermaid Production Graphics Director v4.2 Evidence Context Engine\n\n" + f"Generated: {report['generated_at_utc']}\n\n" + "## Counts\n\n" + "\n".join([f"- {k}: {v}" for k, v in report.items() if k not in {"version", "generated_at_utc"}]) + "\n\n## Policy\n\n- Auto-renders remain human-review only.\n- Manual graphics packs are now included as production packages.\n- Evidence from result queues and graphics packs is used before fallback copy.\n", encoding="utf-8")
    update_summary({"production_director_version": VERSION, "production_director_packages": len(items), "production_director_rendered_exports": len(rendered), "production_director_copy_items": len(copy_rows), "production_director_carousel_plans": len(carousel_rows), "production_director_prompt_dossiers": report["prompt_dossiers"], "production_director_manual_graphics_packs": len(packs)})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
