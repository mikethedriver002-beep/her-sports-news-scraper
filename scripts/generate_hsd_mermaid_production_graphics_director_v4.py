from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

VERSION = "v4.0-production-graphics-director"
OUT_ROOT = Path("outputs/latest/production_graphics_director")
POSTABLE = Path("outputs/latest/POSTABLE_GRAPHICS")
COPY_DIR = OUT_ROOT / "copy_director"
CAROUSEL_DIR = OUT_ROOT / "carousel_director"
PROMPT_DIR = OUT_ROOT / "manual_prompt_dossiers"
QA_DIR = OUT_ROOT / "visual_qa_hard_gate"
EXPORT_MANIFEST = OUT_ROOT / "postable_export_manifest.csv"
REPORT_MD = OUT_ROOT / "production_graphics_director_report.md"
REPORT_JSON = OUT_ROOT / "production_graphics_director_manifest.json"
SUMMARY = Path("outputs/latest/summary.json")

RENDER_MANIFESTS = [
    Path("outputs/latest/review_files/rendered_handoff_manifest.csv"),
    Path("rendered_handoff_manifest.csv"),
]
RENDER_STATUS = [
    Path("outputs/latest/review_files/rendered_handoff_status.csv"),
    Path("rendered_handoff_status.csv"),
]
SLOT_FILES = [
    Path("manual_workflow_content_packets.csv"),
    Path("assignment_handoff_index.csv"),
    Path("mermaid_content_slots_v2.csv"),
]
TEAM_LOGOS = Path("data/asset_registry/wnba/team_logos.csv")
TEAMS = Path("data/asset_registry/wnba/teams.csv")
ATHLETES = Path("data/asset_registry/wnba/athletes.csv")
ATHLETE_IMAGES = Path("data/asset_registry/wnba/athlete_images.csv")
ATHLETE_NEEDS_FIX = Path("data/asset_registry/wnba/athlete_image_needs_fix.csv")

EXPORT_FIELDS = ["packet_id", "platform", "headline", "source_png", "export_png", "review_status", "reason"]
COPY_FIELDS = ["packet_id", "platform", "headline", "caption", "threads_post", "first_comment", "story_frame_text", "poll_question", "hashtags"]
CAROUSEL_FIELDS = ["packet_id", "platform", "headline", "slides", "carousel_plan_path", "prompt_dossier_path", "status"]
QA_FIELDS = ["packet_id", "headline", "render_status", "visual_decision", "reason", "export_path"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "item"


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


def first_existing_csv(paths: List[Path]) -> List[Dict[str, str]]:
    for path in paths:
        rows = read_csv(path)
        if rows:
            return rows
    return []


def team_maps() -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    names = {}
    city = {}
    nick = {}
    for row in read_csv(TEAMS):
        tid = row.get("team_id", "")
        if tid:
            names[tid] = clean(row.get("team_name") or tid.replace("_", " ").title())
            city[tid] = clean(row.get("city"))
            nick[tid] = clean(row.get("nickname"))
    return names, city, nick


def extract_matchup(headline: str, team_names: Dict[str, str]) -> Tuple[str, str, str, str]:
    h = clean(headline)
    for sep in [" at ", " vs ", " versus "]:
        if sep in h.lower():
            parts = re.split(sep, h, flags=re.I, maxsplit=1)
            if len(parts) == 2:
                return clean(parts[0]), clean(parts[1]), "preview", sep.strip()
    if " beat " in h.lower():
        parts = re.split(r"\s+beat\s+", h, flags=re.I, maxsplit=1)
        if len(parts) == 2:
            return clean(parts[0]), clean(parts[1]), "result", "beat"
    return "", "", "feature", ""


def platform_folder(platform: str) -> str:
    p = clean(platform).lower()
    if "story" in p:
        return "ig_stories"
    if "thread" in p:
        return "threads"
    if "feed" in p or "instagram" in p:
        return "ig_feed"
    return "review_only"


def hashtags(league: str, headline: str) -> str:
    base = ["#HerSportsDaily", "#WomensSports"]
    if clean(league).upper() == "WNBA" or " W" in headline or "Sparks" in headline or "Valkyries" in headline:
        base += ["#WNBA", "#Basketball"]
    if "Sparks" in headline:
        base.append("#LASparks")
    if "Valkyries" in headline or "Golden State" in headline:
        base.append("#GoldenStateValkyries")
    return " ".join(dict.fromkeys(base))


def game_caption(headline: str, league: str) -> Tuple[str, str, str, str, str]:
    away, home, kind, _ = extract_matchup(headline, {})
    if kind == "preview" and away and home:
        hook = "Who needs this one more? 👀"
        caption = (
            f"{away} at {home}.\n\n"
            f"{hook}\n\n"
            f"{away} comes into the window looking for a road statement, and this is the kind of matchup where the first run can change the whole tone of the night. They need clean possessions, pressure on the glass, and enough shot-making to keep the building from getting comfortable.\n\n"
            f"{home} gets it at home, with a chance to protect the floor and turn the late window into a statement. If they control the pace, make the extra pass, and force {away} to work late in the clock, this one can get loud fast.\n\n"
            f"One matchup. One tone-setter.\n\n"
            f"Do you trust the road punch, or the home response? 🏀\n\n"
            f"{hashtags(league, headline)}"
        )
        threads = f"{away} at {home}. Who needs this one more? Road punch or home response? 🏀"
        story = f"{away} at {home}. Who controls the first run?"
        poll = "Who needs this one more?"
        first = "Road statement or home-court hold? Drop your pick."
        return caption, threads, first, story, poll
    if kind == "result" and away and home:
        caption = (
            f"{away} gets the win over {home}.\n\n"
            f"This is the kind of result that changes the temperature of the night. The scoreboard gives us the final, but the bigger question is what travels from this one: confidence, pressure, or a new problem for the next opponent.\n\n"
            f"What stood out most from this result? 🏀\n\n"
            f"{hashtags(league, headline)}"
        )
        return caption, f"{away} beats {home}. What stood out most?", "What did you take from this one?", f"{away} gets the win. What changed?", "What stood out most?"
    caption = (
        f"{headline}\n\n"
        f"This is the kind of women’s sports story that deserves more than a scroll-by. The context matters, the names matter, and the moment has a chance to travel if people are actually paying attention.\n\n"
        f"What part of this story are you watching closest?\n\n"
        f"{hashtags(league, headline)}"
    )
    return caption, headline[:260], "What are you watching here?", headline[:110], "What stood out?"


def overlay_copy(headline: str) -> List[str]:
    away, home, kind, _ = extract_matchup(headline, {})
    if kind == "preview" and away and home:
        return ["TONIGHT IN THE W", f"{away} at {home}", "Who controls the first run?", "Keys: pace • glass • late-clock shot-making"]
    if "last night in the w" in headline.lower():
        return ["LAST NIGHT IN THE W", "The results that moved the night", "Biggest win? Best finish? Most important answer?"]
    return [headline, "Why it matters", "What changes next?"]


def carousel_slides(headline: str, league: str) -> List[Dict[str, str]]:
    away, home, kind, _ = extract_matchup(headline, {})
    if kind == "preview" and away and home:
        return [
            {"slide": "1", "title": "Cover", "copy": f"{away} at {home}", "visual": "Premium Tonight in the W cover. Big typography, both team logos, dark arena-lighting background."},
            {"slide": "2", "title": "Why it matters", "copy": "Road statement or home-court hold?", "visual": "Editorial text slide with subtle team-color split and one key matchup question."},
            {"slide": "3", "title": "Players to watch", "copy": "Star power, pace-setters, and late-game decision makers.", "visual": "Use approved player headshots only when available; otherwise use team logos and silhouette placeholders marked review-only."},
            {"slide": "4", "title": "Keys to the game", "copy": "Pace. Glass. Shot quality. Turnovers.", "visual": "Four key tiles with icon-style treatments, no tiny text."},
            {"slide": "5", "title": "Poll", "copy": "Who needs this one more?", "visual": "Big CTA with two team logo buttons and HSD branding."},
        ]
    if "last night in the w" in headline.lower():
        return [
            {"slide": "1", "title": "Cover", "copy": "Last Night in the W", "visual": "Premium scoreboard cover with bold title and neon/gold accents."},
            {"slide": "2", "title": "Scores", "copy": "Every final, clean and readable.", "visual": "Team logo scoreboard rows with large final scores."},
            {"slide": "3", "title": "Biggest win", "copy": "Which result moved the night?", "visual": "One result gets a full-card spotlight."},
            {"slide": "4", "title": "Player standout", "copy": "Use approved headshot only if verified.", "visual": "Approved player headshot, stat slots, and short takeaway."},
            {"slide": "5", "title": "Poll", "copy": "Best win of the night?", "visual": "Audience engagement frame."},
        ]
    return [
        {"slide": "1", "title": "Cover", "copy": headline, "visual": "Bold HSD editorial cover."},
        {"slide": "2", "title": "Context", "copy": "Why this story matters.", "visual": "Magazine-style explainer card."},
        {"slide": "3", "title": "What’s next", "copy": "The question that travels from here.", "visual": "CTA card with HSD branding."},
    ]


def prompt_dossier(packet_id: str, platform: str, headline: str, league: str, caption: str, slides: List[Dict[str, str]]) -> str:
    overlay = overlay_copy(headline)
    slide_lines = []
    for s in slides:
        slide_lines.append(f"### Slide {s['slide']}: {s['title']}\nOn-image copy: {s['copy']}\nVisual direction: {s['visual']}\n")
    return (
        f"# HSD Manual Prompt Dossier — {headline}\n\n"
        f"Packet ID: `{packet_id}`\n"
        f"Platform: `{platform}`\n"
        f"League: `{league}`\n\n"
        "## Brand Style\n\n"
        "Create a premium Her Sports Daily women’s sports graphic. Use a cinematic black/dark navy background, neon edge lighting, team-color accents, bold condensed sports typography, visible HSD watermark/logo, high contrast, and clean spacing. Avoid generic Canva templates. Avoid white panels unless explicitly used as tiny text labels.\n\n"
        "## Exact On-Image Copy Options\n\n"
        + "\n".join(f"- {x}" for x in overlay)
        + "\n\n## Carousel Plan\n\n"
        + "\n".join(slide_lines)
        + "\n## Caption\n\n"
        + caption
        + "\n\n## Negative Prompt\n\n"
        "No fake players. No invented stats. No low-contrast white-on-white text. No cut-off names. No generic blank headshots. No overstuffed small text. No misspelled team names. No extra logos.\n"
    )


def collect_rendered() -> List[Dict[str, str]]:
    rows = first_existing_csv(RENDER_MANIFESTS)
    if rows:
        return rows
    out = []
    for p in Path("outputs/latest/rendered_graphics").rglob("*.png"):
        out.append({"packet_id": p.parent.name, "platform": "review", "headline": p.stem.replace("-", " ").title(), "output_path": p.as_posix()})
    return out


def copy_rendered(rows: List[Dict[str, str]]) -> Tuple[List[Dict[str, Any]], int]:
    if POSTABLE.exists():
        shutil.rmtree(POSTABLE)
    POSTABLE.mkdir(parents=True, exist_ok=True)
    out_rows: List[Dict[str, Any]] = []
    count = 0
    for row in rows:
        src = Path(row.get("output_path") or row.get("source_png") or "")
        if not src.exists():
            continue
        platform = row.get("platform") or "review"
        headline = row.get("headline") or src.stem
        folder = platform_folder(platform)
        dest_dir = POSTABLE / folder
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest = dest_dir / f"{slug(row.get('packet_id') or headline)}.png"
        shutil.copy2(src, dest)
        count += 1
        out_rows.append({
            "packet_id": row.get("packet_id") or src.parent.name,
            "platform": platform,
            "headline": headline,
            "source_png": src.as_posix(),
            "export_png": dest.as_posix(),
            "review_status": "human_visual_review_required",
            "reason": "auto-render exported; post only after visual approval",
        })
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
    for d in [COPY_DIR, CAROUSEL_DIR, PROMPT_DIR, QA_DIR]:
        d.mkdir(parents=True, exist_ok=True)
    render_rows = collect_rendered()
    export_rows, exported_count = copy_rendered(render_rows)
    copy_rows: List[Dict[str, Any]] = []
    carousel_rows: List[Dict[str, Any]] = []
    qa_rows: List[Dict[str, Any]] = []
    for item in export_rows:
        packet_id = item["packet_id"]
        platform = item["platform"]
        headline = item["headline"]
        league = "WNBA" if any(x in headline.lower() for x in ["sparks", "valkyries", "wings", "aces", "lynx", "last night in the w"]) else ""
        caption, threads, first, story, poll = game_caption(headline, league)
        slides = carousel_slides(headline, league)
        prompt = prompt_dossier(packet_id, platform, headline, league, caption, slides)
        prompt_path = PROMPT_DIR / f"{slug(packet_id)}.md"
        prompt_path.write_text(prompt, encoding="utf-8")
        carousel_path = CAROUSEL_DIR / f"{slug(packet_id)}_carousel_plan.md"
        carousel_path.write_text("# Carousel Plan\n\n" + "\n".join([f"## Slide {s['slide']}: {s['title']}\n{s['copy']}\n\n{s['visual']}\n" for s in slides]), encoding="utf-8")
        copy_rows.append({"packet_id": packet_id, "platform": platform, "headline": headline, "caption": caption, "threads_post": threads, "first_comment": first, "story_frame_text": story, "poll_question": poll, "hashtags": hashtags(league, headline)})
        carousel_rows.append({"packet_id": packet_id, "platform": platform, "headline": headline, "slides": len(slides), "carousel_plan_path": carousel_path.as_posix(), "prompt_dossier_path": prompt_path.as_posix(), "status": "ready_for_manual_or_renderer_build"})
        qa_rows.append({"packet_id": packet_id, "headline": headline, "render_status": "exported", "visual_decision": "human_review_required", "reason": "v4 director does not auto-post current renderer output", "export_path": item["export_png"]})
    write_csv(COPY_DIR / "copy_bank.csv", copy_rows, COPY_FIELDS)
    write_csv(CAROUSEL_DIR / "carousel_manifest.csv", carousel_rows, CAROUSEL_FIELDS)
    write_csv(QA_DIR / "visual_qa_hard_gate.csv", qa_rows, QA_FIELDS)
    (COPY_DIR / "copy_bank.md").write_text("# HSD Copy Bank\n\n" + "\n\n---\n\n".join([f"## {r['headline']}\n\n### IG Caption\n{r['caption']}\n\n### Threads\n{r['threads_post']}\n\n### First comment\n{r['first_comment']}" for r in copy_rows]) + "\n", encoding="utf-8")
    report = {
        "version": VERSION,
        "generated_at_utc": now_iso(),
        "rendered_exports": exported_count,
        "copy_items": len(copy_rows),
        "carousel_plans": len(carousel_rows),
        "prompt_dossiers": len(list(PROMPT_DIR.glob("*.md"))),
        "visual_gate_policy": "human_review_required_for_auto_renders",
        "postable_graphics_dir": POSTABLE.as_posix(),
    }
    REPORT_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    REPORT_MD.write_text(
        "# Mermaid Production Graphics Director v4.0\n\n"
        f"Generated: {report['generated_at_utc']}\n\n"
        "## Counts\n\n"
        f"- rendered exports: {exported_count}\n"
        f"- copy items: {len(copy_rows)}\n"
        f"- carousel plans: {len(carousel_rows)}\n"
        f"- prompt dossiers: {report['prompt_dossiers']}\n"
        f"- postable graphics folder: `{POSTABLE.as_posix()}`\n\n"
        "## Policy\n\n"
        "- Auto-rendered PNGs are exported for review, not auto-approved for posting.\n"
        "- Captions and prompt dossiers are production-oriented drafts and should be reviewed before posting.\n"
        "- Carousel plans are the preferred direction for Tonight in the W and Last Night in the W.\n",
        encoding="utf-8",
    )
    update_summary({
        "production_director_version": VERSION,
        "production_director_rendered_exports": exported_count,
        "production_director_copy_items": len(copy_rows),
        "production_director_carousel_plans": len(carousel_rows),
        "production_director_prompt_dossiers": report["prompt_dossiers"],
    })
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
