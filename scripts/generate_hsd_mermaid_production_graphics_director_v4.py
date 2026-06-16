from __future__ import annotations

import csv
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

VERSION = "v4.1-context-engine"
OUT_ROOT = Path("outputs/latest/production_graphics_director")
POSTABLE = Path("outputs/latest/POSTABLE_GRAPHICS")
COPY_DIR = OUT_ROOT / "copy_director"
CAROUSEL_DIR = OUT_ROOT / "carousel_director"
PROMPT_DIR = OUT_ROOT / "manual_prompt_dossiers"
QA_DIR = OUT_ROOT / "visual_qa_hard_gate"
CONTEXT_DIR = OUT_ROOT / "context_engine"
EXPORT_MANIFEST = OUT_ROOT / "postable_export_manifest.csv"
REPORT_MD = OUT_ROOT / "production_graphics_director_report.md"
REPORT_JSON = OUT_ROOT / "production_graphics_director_manifest.json"
SUMMARY = Path("outputs/latest/summary.json")

RENDER_MANIFESTS = [Path("outputs/latest/review_files/rendered_handoff_manifest.csv"), Path("rendered_handoff_manifest.csv")]
PACKET_DIRS = [Path("manual_workflow_handoff_packs"), Path("assignment_handoff_zips")]
SLOT_FILES = [Path("manual_workflow_content_packets.csv"), Path("assignment_handoff_index.csv"), Path("mermaid_content_slots_v2.csv")]
TEAMS = Path("data/asset_registry/wnba/teams.csv")
ATHLETES = Path("data/asset_registry/wnba/athletes.csv")
ATHLETE_IMAGES = Path("data/asset_registry/wnba/athlete_images.csv")
ATHLETE_NEEDS_FIX = Path("data/asset_registry/wnba/athlete_image_needs_fix.csv")

EXPORT_FIELDS = ["packet_id", "platform", "headline", "source_png", "export_png", "review_status", "reason"]
COPY_FIELDS = ["packet_id", "platform", "headline", "content_family", "caption", "threads_post", "first_comment", "story_frame_text", "poll_question", "hashtags", "context_sources"]
CAROUSEL_FIELDS = ["packet_id", "platform", "headline", "content_family", "slides", "carousel_plan_path", "prompt_dossier_path", "status"]
QA_FIELDS = ["packet_id", "headline", "render_status", "visual_decision", "reason", "export_path"]
CONTEXT_FIELDS = ["packet_id", "platform", "headline", "league", "content_type", "content_family", "teams", "approved_players", "needs_fix_players", "context_quality", "context_excerpt"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "item"


def norm(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())


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


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


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
                with zipfile.ZipFile(zp) as archive:
                    data = json.loads(archive.read("content_packet.json").decode("utf-8"))
                slot = data.get("slot", {}) if isinstance(data, dict) else {}
                pub = data.get("public_copy", {}) if isinstance(data, dict) else {}
                packet_id = clean(data.get("packet_id") or zp.stem)
                packets[packet_id] = {
                    "packet_id": packet_id,
                    "platform": clean(slot.get("platform") or pub.get("platform")),
                    "headline": clean(pub.get("headline") or slot.get("headline") or zp.stem),
                    "league": clean(pub.get("league") or slot.get("league")),
                    "content_type": clean(pub.get("content_type") or slot.get("content_type")),
                    "hook": clean(pub.get("hook") or slot.get("copy_hook")),
                    "caption_seed": clean(pub.get("caption") or slot.get("ig_caption_seed")),
                    "story_text": clean(pub.get("story_frame_text") or slot.get("story_frame_text")),
                    "first_comment": clean(pub.get("first") or slot.get("first_comment")),
                    "raw_text": " | ".join(clean(s) for s in nested_strings(data) if clean(s)),
                    "packet_path": zp.as_posix(),
                }
            except Exception:
                continue
    for path in SLOT_FILES:
        for row in read_csv(path):
            packet_id = clean(row.get("packet_id") or row.get("id") or row.get("slot_id") or row.get("bundle_name"))
            if not packet_id:
                continue
            item = packets.setdefault(packet_id, {"packet_id": packet_id})
            for k, v in row.items():
                if clean(v) and k not in item:
                    item[k] = clean(v)
            item["raw_text"] = clean(item.get("raw_text", "") + " | " + " | ".join(clean(v) for v in row.values() if clean(v)))
    return packets


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
    teams: Dict[str, Dict[str, str]] = {}
    for row in read_csv(TEAMS):
        tid = row.get("team_id", "")
        if tid:
            teams[tid] = row
    return teams


def approved_athlete_registry() -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]], set[str]]:
    athletes = {r.get("athlete_id", ""): r for r in read_csv(ATHLETES) if r.get("athlete_id")}
    approved_paths: Dict[str, str] = {}
    for row in read_csv(ATHLETE_IMAGES):
        aid = row.get("athlete_id", "")
        path = clean(row.get("file_path"))
        if row.get("image_type") == "headshot" and row.get("approved") == "true" and Path(path).exists() and Path(path + ".approved").exists():
            approved_paths[aid] = path
    needs_fix = {r.get("athlete_id", "") for r in read_csv(ATHLETE_NEEDS_FIX) if r.get("athlete_id")}
    approved = {}
    by_norm_name = {}
    for aid, path in approved_paths.items():
        if aid in athletes:
            row = dict(athletes[aid])
            row["headshot_path"] = path
            approved[aid] = row
            name = clean(row.get("display_name"))
            if len(name.split()) >= 2:
                by_norm_name[norm(name)] = row
    return approved, by_norm_name, needs_fix


def detect_teams(text: str, teams: Dict[str, Dict[str, str]]) -> List[str]:
    blob = norm(text)
    found: List[str] = []
    for tid, row in teams.items():
        candidates = [row.get("team_name", ""), row.get("city", ""), row.get("nickname", "")]
        for c in candidates:
            cn = norm(c)
            if cn and len(cn) > 2 and cn in blob and tid not in found:
                found.append(tid)
    return found[:4]


def team_name(tid: str, teams: Dict[str, Dict[str, str]]) -> str:
    return clean(teams.get(tid, {}).get("team_name") or tid.replace("_", " ").title())


def detect_approved_players(text: str, by_name: Dict[str, Dict[str, str]], needs_fix: set[str]) -> Tuple[List[Dict[str, str]], List[str]]:
    blob = norm(text)
    found: List[Dict[str, str]] = []
    missing: List[str] = []
    seen: set[str] = set()
    for name_key, row in sorted(by_name.items(), key=lambda kv: len(kv[0]), reverse=True):
        aid = row.get("athlete_id", "")
        if name_key and name_key in blob and aid not in seen:
            if aid in needs_fix:
                missing.append(aid)
            else:
                found.append(row)
                seen.add(aid)
    return found[:4], missing[:8]


def classify(headline: str, league: str, content_type: str, teams: List[str], text: str) -> str:
    h = headline.lower()
    ct = content_type.lower()
    if "last night in the w" in h:
        return "wnba_results_roundup"
    if league.upper() == "WNBA" and len(teams) >= 2 and (" at " in h or " vs " in h or "preview" in ct):
        return "wnba_game_preview"
    if league.upper() == "WNBA" and ("beat" in h or "result" in ct or "recap" in ct):
        return "wnba_result_recap"
    if "lpga" in league.lower() or "championship" in h or "winner" in h or "golf" in text.lower():
        return "feature_story"
    return "feature_story"


def context_excerpt(text: str, limit: int = 360) -> str:
    text = clean(text)
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "…"


def build_context(item: Dict[str, Any], teams: Dict[str, Dict[str, str]], athletes_by_name: Dict[str, Dict[str, str]], needs_fix: set[str]) -> Dict[str, Any]:
    headline = clean(item.get("headline") or item.get("packet_id"))
    raw = " | ".join(clean(item.get(k, "")) for k in ["headline", "league", "content_type", "hook", "caption_seed", "story_text", "first_comment", "raw_text"] if clean(item.get(k, "")))
    team_ids = detect_teams(raw + " | " + headline, teams)
    players, missing_players = detect_approved_players(raw + " | " + headline, athletes_by_name, needs_fix)
    league = clean(item.get("league")) or ("WNBA" if team_ids or "last night in the w" in headline.lower() else "")
    content_type = clean(item.get("content_type"))
    family = classify(headline, league, content_type, team_ids, raw)
    quality = "rich" if len(raw) > 220 or players or len(team_ids) >= 2 else "thin"
    return {
        "packet_id": clean(item.get("packet_id")),
        "platform": clean(item.get("platform")),
        "headline": headline,
        "league": league,
        "content_type": content_type,
        "content_family": family,
        "teams": team_ids,
        "approved_players": players,
        "needs_fix_players": missing_players,
        "context_quality": quality,
        "context_excerpt": context_excerpt(raw),
        "raw_text": raw,
        "hook": clean(item.get("hook")),
        "caption_seed": clean(item.get("caption_seed")),
        "story_text": clean(item.get("story_text")),
        "first_comment": clean(item.get("first_comment")),
    }


def hashtags(ctx: Dict[str, Any], teams: Dict[str, Dict[str, str]]) -> str:
    tags = ["#HerSportsDaily", "#WomensSports"]
    if ctx["league"].upper() == "WNBA" or ctx["content_family"].startswith("wnba"):
        tags += ["#WNBA", "#Basketball"]
    if ctx["content_family"] == "feature_story" and "championship" in ctx["headline"].lower():
        tags += ["#LPGA", "#Golf"]
    for tid in ctx.get("teams", [])[:2]:
        name = team_name(tid, teams).replace(" ", "")
        tags.append("#" + name)
    return " ".join(dict.fromkeys(tags))


def player_phrase(players: List[Dict[str, str]]) -> str:
    names = [clean(p.get("display_name")) for p in players if clean(p.get("display_name"))]
    if not names:
        return "the names that decide the run"
    if len(names) == 1:
        return names[0]
    return ", ".join(names[:-1]) + " and " + names[-1]


def copy_package(ctx: Dict[str, Any], teams: Dict[str, Dict[str, str]]) -> Tuple[str, str, str, str, str]:
    headline = ctx["headline"]
    family = ctx["content_family"]
    team_ids = ctx.get("teams", [])
    players = ctx.get("approved_players", [])
    if family == "wnba_game_preview" and len(team_ids) >= 2:
        away, home = team_name(team_ids[0], teams), team_name(team_ids[1], teams)
        ptext = player_phrase(players)
        caption = (
            f"{away} at {home}.\n\n"
            "Who needs this one more? 👀\n\n"
            f"{away} comes into this matchup needing a clean statement. The first stretch matters: pace, shot quality, and whether {ptext} can put pressure on the game before it settles.\n\n"
            f"{home} gets the home-floor edge and a chance to turn this into their kind of night. If they protect the ball, win the glass, and force {away} to work late in the clock, the building can tilt fast.\n\n"
            "This is why the late window matters.\n\n"
            f"Do you trust the road response, or the home hold? 🏀\n\n{hashtags(ctx, teams)}"
        )
        threads = f"{away} at {home}. Who needs this one more: road response or home hold? 🏀"
        first = "Road statement or home-court hold? Drop your pick."
        story = f"{away} at {home}: who controls the first run?"
        poll = "Who needs this one more?"
        return caption, threads, first, story, poll
    if family == "wnba_results_roundup":
        caption = (
            "Last Night in the W.\n\n"
            "The scoreboard tells you who won. The bigger story is what each result changes: who found rhythm, who left with questions, and which teams gave us something worth carrying into the next slate.\n\n"
            "This is the kind of night where one final score can shift a whole conversation.\n\n"
            f"Which result mattered most to you? 🏀\n\n{hashtags(ctx, teams)}"
        )
        return caption, "Last Night in the W. Which result mattered most?", "Best win of the night?", "Last Night in the W: which result moved you?", "Best win?"
    if family == "wnba_result_recap":
        caption = (
            f"{headline}.\n\n"
            "The final score is only part of it. The real read is what this result says about identity, pressure, and who gets to carry momentum into the next game.\n\n"
            f"What did this one tell you? 🏀\n\n{hashtags(ctx, teams)}"
        )
        return caption, f"{headline}. What did this one tell you?", "What changed after this result?", headline[:110], "What stood out?"
    caption = (
        f"{headline}.\n\n"
        "This is why women’s sports coverage needs more room. The win, the moment, and the names attached to it all deserve context, not just a headline.\n\n"
        "Stories like this are how a season builds memory.\n\n"
        f"Are we talking about this enough?\n\n{hashtags(ctx, teams)}"
    )
    return caption, f"{headline}. Are we talking about this enough?", "Are we giving this enough attention?", headline[:110], "Enough attention?"


def carousel_slides(ctx: Dict[str, Any], teams: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    family = ctx["content_family"]
    headline = ctx["headline"]
    players = player_phrase(ctx.get("approved_players", []))
    if family == "wnba_game_preview" and len(ctx.get("teams", [])) >= 2:
        away, home = team_name(ctx["teams"][0], teams), team_name(ctx["teams"][1], teams)
        return [
            {"slide": "1", "title": "Cover", "copy": f"{away} at {home}", "visual": "Premium Tonight in the W cover, dark arena lighting, both team logos large, gold/purple accents."},
            {"slide": "2", "title": "Stakes", "copy": "Road response or home hold?", "visual": "Editorial stakes slide with one sentence on each side and team-color split."},
            {"slide": "3", "title": "Players to watch", "copy": players, "visual": "Use approved headshots only. If no approved player is available, use team logos and text-only player labels."},
            {"slide": "4", "title": "Keys", "copy": "Pace. Glass. Turnovers. Shot quality.", "visual": "Four bold key tiles, no tiny body text."},
            {"slide": "5", "title": "CTA", "copy": "Who needs this one more?", "visual": "Poll-style final slide with two team logo buttons."},
        ]
    if family == "wnba_results_roundup":
        return [
            {"slide": "1", "title": "Cover", "copy": "Last Night in the W", "visual": "Bold scoreboard cover with cinematic dark background."},
            {"slide": "2", "title": "Scores", "copy": "Every final, clean and readable.", "visual": "Large score rows, team logos, no clutter."},
            {"slide": "3", "title": "Biggest win", "copy": "Which result moved the night?", "visual": "One result gets the spotlight."},
            {"slide": "4", "title": "Player standout", "copy": "Approved headshot only if verified.", "visual": "Player headshot, stat lane, short takeaway."},
            {"slide": "5", "title": "CTA", "copy": "Best win of the night?", "visual": "Engagement slide with HSD branding."},
        ]
    return [
        {"slide": "1", "title": "Cover", "copy": headline, "visual": "Premium editorial cover."},
        {"slide": "2", "title": "Context", "copy": "Why it matters.", "visual": "Clean explainer card."},
        {"slide": "3", "title": "People", "copy": "Names and stakes.", "visual": "Use real approved imagery only if available."},
        {"slide": "4", "title": "CTA", "copy": "Are we talking about this enough?", "visual": "Question-first HSD slide."},
    ]


def prompt_dossier(ctx: Dict[str, Any], caption: str, slides: List[Dict[str, str]]) -> str:
    player_lines = "\n".join([f"- {p.get('display_name')} -> {p.get('headshot_path')}" for p in ctx.get("approved_players", [])]) or "- No approved player image required for this packet."
    slide_lines = []
    for s in slides:
        slide_lines.append(f"### Slide {s['slide']}: {s['title']}\nOn-image copy: {s['copy']}\nVisual direction: {s['visual']}\n")
    return (
        f"# HSD Manual Prompt Dossier — {ctx['headline']}\n\n"
        f"Packet ID: `{ctx['packet_id']}`\nPlatform: `{ctx['platform']}`\nLeague: `{ctx['league']}`\nContent family: `{ctx['content_family']}`\nContext quality: `{ctx['context_quality']}`\n\n"
        "## Brand Style\n\nPremium women’s sports editorial. Dark cinematic background, high contrast, bold condensed sports typography, neon team-color edge lighting, gold accents, clean logo rows, no white content cards, no generic Canva look.\n\n"
        "## Approved Athlete Assets\n\n" + player_lines + "\n\n"
        "## Source Context\n\n" + ctx.get("context_excerpt", "") + "\n\n"
        "## Carousel Plan\n\n" + "\n".join(slide_lines) + "\n"
        "## Caption\n\n" + caption + "\n\n"
        "## Negative Prompt\n\nNo fake players. No invented stats. No unapproved headshots. No generic blank headshots. No low-contrast text. No cut-off names. No white panels. No extra teams. No misspelled team names.\n"
    )


def platform_folder(platform: str) -> str:
    p = clean(platform).lower()
    if "story" in p:
        return "ig_stories"
    if "thread" in p:
        return "threads"
    if "feed" in p or "instagram" in p:
        return "ig_feed"
    return "review_only"


def copy_rendered(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], int]:
    if POSTABLE.exists():
        shutil.rmtree(POSTABLE)
    POSTABLE.mkdir(parents=True, exist_ok=True)
    out_rows: List[Dict[str, Any]] = []
    count = 0
    for row in rows:
        src = Path(row.get("output_path") or "")
        if not src.exists():
            continue
        platform = row.get("platform") or "review"
        headline = row.get("headline") or src.stem
        dest_dir = POSTABLE / platform_folder(platform)
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{slug(row.get('packet_id') or headline)}.png"
        shutil.copy2(src, dest)
        count += 1
        out_rows.append({"packet_id": row.get("packet_id") or src.parent.name, "platform": platform, "headline": headline, "source_png": src.as_posix(), "export_png": dest.as_posix(), "review_status": "human_visual_review_required", "reason": "auto-render exported; post only after visual approval"})
    write_csv(EXPORT_MANIFEST, out_rows, EXPORT_FIELDS)
    return out_rows, count


def update_summary(fields: Dict[str, Any]) -> None:
    summary = read_json(SUMMARY)
    summary.update(fields)
    if SUMMARY.parent.exists():
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    for folder in [COPY_DIR, CAROUSEL_DIR, PROMPT_DIR, QA_DIR, CONTEXT_DIR]:
        folder.mkdir(parents=True, exist_ok=True)
    packets = packet_index()
    teams = team_registry()
    _, athletes_by_name, needs_fix = approved_athlete_registry()
    rendered = render_rows()
    exports, exported_count = copy_rendered(rendered)
    copy_rows: List[Dict[str, Any]] = []
    carousel_rows: List[Dict[str, Any]] = []
    qa_rows: List[Dict[str, Any]] = []
    context_rows: List[Dict[str, Any]] = []
    for export in exports:
        packet_id = export["packet_id"]
        merged = dict(packets.get(packet_id, {}))
        merged.setdefault("packet_id", packet_id)
        merged.setdefault("platform", export["platform"])
        merged.setdefault("headline", export["headline"])
        ctx = build_context(merged, teams, athletes_by_name, needs_fix)
        caption, threads, first, story, poll = copy_package(ctx, teams)
        slides = carousel_slides(ctx, teams)
        prompt = prompt_dossier(ctx, caption, slides)
        prompt_path = PROMPT_DIR / f"{slug(packet_id)}.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        carousel_path = CAROUSEL_DIR / f"{slug(packet_id)}_carousel_plan.md"
        carousel_path.write_text("# Carousel Plan\n\n" + "\n".join([f"## Slide {s['slide']}: {s['title']}\n{s['copy']}\n\n{s['visual']}\n" for s in slides]), encoding="utf-8")
        copy_rows.append({"packet_id": packet_id, "platform": ctx["platform"], "headline": ctx["headline"], "content_family": ctx["content_family"], "caption": caption, "threads_post": threads, "first_comment": first, "story_frame_text": story, "poll_question": poll, "hashtags": hashtags(ctx, teams), "context_sources": ctx.get("context_excerpt", "")})
        carousel_rows.append({"packet_id": packet_id, "platform": ctx["platform"], "headline": ctx["headline"], "content_family": ctx["content_family"], "slides": len(slides), "carousel_plan_path": carousel_path.as_posix(), "prompt_dossier_path": prompt_path.as_posix(), "status": "ready_for_manual_or_renderer_build"})
        qa_rows.append({"packet_id": packet_id, "headline": ctx["headline"], "render_status": "exported", "visual_decision": "human_review_required", "reason": "auto-render still requires HSD visual approval", "export_path": export["export_png"]})
        context_rows.append({"packet_id": packet_id, "platform": ctx["platform"], "headline": ctx["headline"], "league": ctx["league"], "content_type": ctx["content_type"], "content_family": ctx["content_family"], "teams": ";".join(ctx.get("teams", [])), "approved_players": ";".join([p.get("athlete_id", "") for p in ctx.get("approved_players", [])]), "needs_fix_players": ";".join(ctx.get("needs_fix_players", [])), "context_quality": ctx["context_quality"], "context_excerpt": ctx["context_excerpt"]})
    write_csv(COPY_DIR / "copy_bank.csv", copy_rows, COPY_FIELDS)
    write_csv(CAROUSEL_DIR / "carousel_manifest.csv", carousel_rows, CAROUSEL_FIELDS)
    write_csv(QA_DIR / "visual_qa_hard_gate.csv", qa_rows, QA_FIELDS)
    write_csv(CONTEXT_DIR / "context_bank.csv", context_rows, CONTEXT_FIELDS)
    (COPY_DIR / "copy_bank.md").write_text("# HSD Copy Bank\n\n" + "\n\n---\n\n".join([f"## {r['headline']}\n\nFamily: `{r['content_family']}`\n\n### IG Caption\n{r['caption']}\n\n### Threads\n{r['threads_post']}\n\n### First comment\n{r['first_comment']}" for r in copy_rows]) + "\n", encoding="utf-8")
    report = {"version": VERSION, "generated_at_utc": now_iso(), "rendered_exports": exported_count, "copy_items": len(copy_rows), "carousel_plans": len(carousel_rows), "prompt_dossiers": len(list(PROMPT_DIR.glob("*.md"))), "context_rows": len(context_rows), "rich_context_rows": len([r for r in context_rows if r.get("context_quality") == "rich"]), "visual_gate_policy": "human_review_required_for_auto_renders", "postable_graphics_dir": POSTABLE.as_posix()}
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text("# Mermaid Production Graphics Director v4.1 Context Engine\n\n" + f"Generated: {report['generated_at_utc']}\n\n" + "## Counts\n\n" + "\n".join([f"- {k}: {v}" for k, v in report.items() if k not in {"version", "generated_at_utc"}]) + "\n\n## Policy\n\n- Auto-rendered PNGs are exported for review, not auto-approved for posting.\n- Captions use packet context when available and avoid headline-only matchup assumptions.\n- Carousel plans are the preferred direction for Tonight in the W and Last Night in the W.\n", encoding="utf-8")
    update_summary({"production_director_version": VERSION, "production_director_rendered_exports": exported_count, "production_director_copy_items": len(copy_rows), "production_director_carousel_plans": len(carousel_rows), "production_director_prompt_dossiers": report["prompt_dossiers"], "production_director_context_rows": len(context_rows), "production_director_rich_context_rows": report["rich_context_rows"]})
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
