from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import generate_hsd_mermaid_production_graphics_director_v4_4 as base  # type: ignore

VERSION = "v4.5-post-ready-copy-gate"
OUT_ROOT = Path("outputs/latest/production_graphics_director")
COPY_DIR = OUT_ROOT / "copy_director"
CAROUSEL_DIR = OUT_ROOT / "carousel_director"
PROMPT_DIR = OUT_ROOT / "manual_prompt_dossiers"
CONTEXT = OUT_ROOT / "context_engine" / "context_bank.csv"
SUMMARY = Path("outputs/latest/summary.json")
RESULTS = [Path("results_contract_v2.csv"), Path("hsd_pipeline_lite_review/files/results_contract_v2.csv")]

COPY_FIELDS = ["package_id", "packet_id", "platform", "headline", "content_family", "caption", "threads_post", "first_comment", "story_frame_text", "poll_question", "hashtags", "evidence"]
CAROUSEL_FIELDS = ["package_id", "packet_id", "platform", "headline", "content_family", "slides", "carousel_plan_path", "prompt_dossier_path", "status"]

TEAM_TAGS = {
    "connecticut_sun": "#ConnecticutSun",
    "toronto_tempo": "#TorontoTempo",
    "los_angeles_sparks": "#LASparks",
    "seattle_storm": "#SeattleStorm",
    "golden_state_valkyries": "#GoldenStateValkyries",
    "dallas_wings": "#DallasWings",
    "las_vegas_aces": "#LasVegasAces",
    "minnesota_lynx": "#MinnesotaLynx",
    "portland_fire": "#PortlandFire",
}
TEAM_NAMES = {
    "connecticut_sun": "Connecticut Sun",
    "toronto_tempo": "Toronto Tempo",
    "los_angeles_sparks": "Los Angeles Sparks",
    "seattle_storm": "Seattle Storm",
    "golden_state_valkyries": "Golden State Valkyries",
    "dallas_wings": "Dallas Wings",
    "las_vegas_aces": "Las Vegas Aces",
    "minnesota_lynx": "Minnesota Lynx",
    "portland_fire": "Portland Fire",
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(v).lower()).strip("-") or "item"


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


def dedupe(items: List[str]) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    for item in items:
        value = clean(item)
        key = norm(value)
        if value and key not in seen:
            seen.add(key)
            out.append(value)
    return out


def matchups(row: Dict[str, str]) -> List[str]:
    evidence = clean(row.get("evidence"))
    pieces = [clean(x) for x in evidence.split("|") if clean(x)]
    out: List[str] = []
    for piece in pieces:
        if len(piece) > 80 or "prompt" in piece.lower() or "attached" in piece.lower():
            continue
        if re.search(r"\bat\b", piece, flags=re.I) and re.search(r"[A-Za-z]", piece):
            if " at " in piece.lower():
                out.append(piece)
    return dedupe(out)[:4]


def detect_team_ids(text: str) -> List[str]:
    blob = norm(text)
    ids: List[str] = []
    for team_id, name in TEAM_NAMES.items():
        if norm(name) in blob and team_id not in ids:
            ids.append(team_id)
    return ids


def team_ids_for_row(row: Dict[str, str]) -> List[str]:
    ids: List[str] = []
    for matchup in matchups(row):
        for tid in detect_team_ids(matchup):
            if tid not in ids:
                ids.append(tid)
    for tid in [x for x in row.get("teams", "").split(";") if x]:
        if tid not in ids:
            ids.append(tid)
    return ids


def tag_string(team_ids: List[str], league: str) -> str:
    tags = ["#HerSportsDaily", "#WomensSports"]
    if league.upper() == "LPGA":
        tags += ["#LPGA", "#Golf"]
    else:
        tags += ["#WNBA", "#Basketball"]
    for tid in team_ids:
        if tid in TEAM_TAGS:
            tags.append(TEAM_TAGS[tid])
    return " ".join(dict.fromkeys(tags))


def score_lines(row: Dict[str, str]) -> List[str]:
    evidence = clean(row.get("evidence"))
    scores = re.findall(r"[A-Z][A-Za-z ]+\s+\d+\s+·\s+[A-Z][A-Za-z ]+\s+\d+", evidence)
    more = [clean(x) for x in evidence.split("|") if " · " in x]
    return dedupe(scores + more)[:6]


def result_map() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for path in RESULTS:
        for row in read_csv(path):
            if row.get("headline"):
                out[norm(row.get("headline", ""))] = row
    return out


def natural_final(row: Dict[str, str], headline: str) -> str:
    winner = clean(row.get("winner_team_name"))
    loser = clean(row.get("loser_team_name"))
    score = clean(row.get("score_display"))
    if winner and loser and score:
        nums = re.findall(r"([A-Z][A-Za-z ]+?)\s+(\d+)", score)
        score_map = {clean(team): pts for team, pts in nums}
        if winner in score_map and loser in score_map:
            return f"Final: {winner} {score_map[winner]}, {loser} {score_map[loser]}."
    return clean(row.get("summary")) or headline


def result_copy(row: Dict[str, str], rm: Dict[str, Dict[str, str]]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    headline = row.get("headline", "")
    detail = natural_final(rm.get(norm(headline), {}), headline)
    team_ids = team_ids_for_row(row)
    caption = (
        f"{headline}.\n\n"
        f"{detail}\n\n"
        "This was not just a box-score result. It changes the next conversation around rhythm, pressure, and who gets to carry momentum forward.\n\n"
        "What did this one tell you? 🏀\n\n"
        f"{tag_string(team_ids, 'WNBA')}"
    )
    slides = [
        {"slide": "1", "title": "Final", "copy": headline, "visual": "Final-score cover with official team logos."},
        {"slide": "2", "title": "Score", "copy": detail, "visual": "Large final score. Winner hierarchy clear."},
        {"slide": "3", "title": "What changed", "copy": "Momentum changed after the final.", "visual": "Editorial takeaway slide."},
        {"slide": "4", "title": "CTA", "copy": "What did this one tell you?", "visual": "Question-first HSD end slide."},
    ]
    return caption, f"{headline}. What did this one tell you?", "What changed after this result?", headline[:110], "What stood out?", slides


def results_roundup_copy(row: Dict[str, str]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    scores = score_lines(row)
    team_ids = team_ids_for_row(row)
    score_block = "\n".join(f"• {x}" for x in scores) if scores else "• Final scores are in."
    caption = (
        "Last Night in the W.\n\n"
        f"{score_block}\n\n"
        "The scores tell you who handled business. The bigger story is what each result changes: momentum, pressure, and the next conversation around the league.\n\n"
        "Which result mattered most? 🏀\n\n"
        f"{tag_string(team_ids, 'WNBA')}"
    )
    slides = [
        {"slide": "1", "title": "Cover", "copy": "Last Night in the W", "visual": "Premium dark scoreboard cover."},
        {"slide": "2", "title": "Scores", "copy": " | ".join(scores), "visual": "Large score rows with official team logos."},
        {"slide": "3", "title": "What changed", "copy": "The scoreboard shifted the conversation.", "visual": "Editorial takeaway slide."},
        {"slide": "4", "title": "CTA", "copy": "Best win of the night?", "visual": "Question-first HSD end slide."},
    ]
    return caption, "Last Night in the W. Which result mattered most?", "Best win of the night?", "Last Night in the W: which result mattered most?", "Best win?", slides


def slate_copy(row: Dict[str, str]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    slate = matchups(row) or [row.get("headline", "Tonight in the W")]
    team_ids = team_ids_for_row(row)
    slate_block = "\n".join(f"• {x}" for x in slate)
    caption = (
        "Tonight in the W.\n\n"
        f"{slate_block}\n\n"
        "The slate has a simple question: who sets the tone early, and who has the late answer when the game tightens up?\n\n"
        "Which matchup are you watching first? 🏀\n\n"
        f"{tag_string(team_ids, 'WNBA')}"
    )
    slides = [
        {"slide": "1", "title": "Cover", "copy": "Tonight in the W", "visual": "Premium HSD cover in the preferred dark cinematic style."},
        {"slide": "2", "title": "Slate", "copy": " | ".join(slate), "visual": "Clean matchup board with official logos."},
        {"slide": "3", "title": "What to watch", "copy": "First run. Pace. Fourth-quarter answers.", "visual": "Three editorial watch tiles."},
        {"slide": "4", "title": "Keys", "copy": "Pace. Glass. Shot quality. Late-clock answers.", "visual": "Four bold key tiles."},
        {"slide": "5", "title": "CTA", "copy": "Which matchup are you watching first?", "visual": "Poll-style HSD end slide."},
    ]
    return caption, f"Tonight in the W: {' | '.join(slate)}. Which matchup are you watching first?", "Which matchup has the most juice tonight?", f"Tonight in the W: {' | '.join(slate[:2])}", "Which game first?", slides


def preview_copy(row: Dict[str, str]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    headline = clean(row.get("headline") or "Tonight in the W")
    team_ids = team_ids_for_row(row)
    caption = (
        f"{headline}.\n\n"
        "Who needs this one more? 👀\n\n"
        "This matchup is about pace, shot quality, and who handles the pressure possessions late. The first run matters, but the fourth-quarter answer matters more.\n\n"
        "Road statement or home hold? Drop your pick before tip. 🏀\n\n"
        f"{tag_string(team_ids, 'WNBA')}"
    )
    slides = [
        {"slide": "1", "title": "Cover", "copy": headline, "visual": "Premium HSD matchup cover with official logos."},
        {"slide": "2", "title": "Stakes", "copy": "Road statement vs home hold", "visual": "Two-sided stakes slide."},
        {"slide": "3", "title": "Keys", "copy": "Pace. Shot quality. Late possessions.", "visual": "Three clean key tiles."},
        {"slide": "4", "title": "CTA", "copy": "Who needs this one more?", "visual": "Question-first end slide."},
    ]
    return caption, f"{headline}. Who needs this one more? 👀", "Road statement or home hold? Drop your pick.", f"{headline}. Who owns the window?", "Who needs this one more?", slides


def feature_copy(row: Dict[str, str]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    caption = (
        "Gina Kim and Yana Wilson are officially in the LPGA winner’s circle together.\n\n"
        "From the Epson Tour to a title moment at the Dow Championship, this is the kind of women’s golf story that deserves more than a line in the ticker. It is a team-format breakthrough, a shared win, and a reminder that the LPGA lane has real stories with texture.\n\n"
        "Are we talking about this enough?\n\n"
        "#HerSportsDaily #WomensSports #LPGA #Golf"
    )
    slides = [
        {"slide": "1", "title": "Cover", "copy": "Kim + Wilson win together", "visual": "Premium LPGA editorial cover."},
        {"slide": "2", "title": "Path", "copy": "From Epson Tour to LPGA winner’s circle", "visual": "Timeline-style context card."},
        {"slide": "3", "title": "Why it matters", "copy": "A shared title moment at the Dow Championship", "visual": "Clean editorial context card."},
        {"slide": "4", "title": "CTA", "copy": "Are we talking about this enough?", "visual": "Question-first end slide."},
    ]
    return caption, "Kim and Wilson in the LPGA winner’s circle together. This deserves more attention.", "Are we talking about this enough?", "LPGA breakthrough: Kim + Wilson win together.", "Enough attention?", slides


def package_copy(row: Dict[str, str], rm: Dict[str, Dict[str, str]]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    family = row.get("content_family", "")
    content_type = row.get("content_type", "")
    league = row.get("league", "")
    if family == "wnba_result_recap":
        return result_copy(row, rm)
    if family == "wnba_results_roundup":
        return results_roundup_copy(row)
    if family == "wnba_game_preview" or (league.upper() == "WNBA" and "preview" in content_type.lower()):
        return preview_copy(row)
    if family == "manual_graphics_pack":
        return slate_copy(row)
    return feature_copy(row)


def prompt_text(row: Dict[str, str], caption: str, slides: List[Dict[str, str]]) -> str:
    slide_text = "\n".join([f"### Slide {s['slide']}: {s['title']}\nOn-image copy: {s['copy']}\nVisual direction: {s['visual']}\n" for s in slides])
    return f"# HSD Manual Prompt Dossier — {row.get('headline')}\n\nPacket: `{row.get('package_id')}`\nPlatform: `{row.get('platform')}`\nFamily: `{row.get('content_family')}`\nQuality: `{row.get('context_quality')}`\n\n## Brand Style\n\nPremium women’s sports editorial. Dark high-contrast background. Bold condensed sports typography. Cinematic lighting. Clean hierarchy. No white dashboard cards. No tiny text. Use the official HSD watermark exactly.\n\n## Evidence\n\n{row.get('evidence','')[:1200]}\n\n## Carousel Plan\n\n{slide_text}\n## Caption\n\n{caption}\n\n## Negative Prompt\n\nNo fake players. No invented stats. No unapproved headshots. No generic blank headshots. No cut-off names. No low-contrast text. No extra teams. No white panels.\n"


def main() -> None:
    base.main()
    rows = read_csv(CONTEXT)
    rm = result_map()
    seen: set[Tuple[str, str]] = set()
    publish_seen: set[Tuple[str, str]] = set()
    copy_rows: List[Dict[str, Any]] = []
    carousel_rows: List[Dict[str, Any]] = []
    publish_lines = ["# HSD Post-Ready Copy", "", f"Generated: {now_iso()}", ""]
    for row in rows:
        key = (row.get("content_family", ""), norm(row.get("headline", "")))
        if key in seen and row.get("content_family") == "wnba_result_recap":
            continue
        seen.add(key)
        caption, threads, first, story, poll, slides = package_copy(row, rm)
        prompt_path = PROMPT_DIR / f"{slug(row.get('package_id', row.get('headline', 'item')))}.md"
        prompt_path.write_text(prompt_text(row, caption, slides), encoding="utf-8")
        carousel_path = CAROUSEL_DIR / f"{slug(row.get('package_id', row.get('headline','item')))}_carousel_plan.md"
        carousel_path.write_text("# Carousel Plan\n\n" + "\n".join([f"## Slide {s['slide']}: {s['title']}\n{s['copy']}\n\n{s['visual']}\n" for s in slides]), encoding="utf-8")
        copy_rows.append({"package_id": row.get("package_id"), "packet_id": row.get("packet_id"), "platform": row.get("platform"), "headline": row.get("headline"), "content_family": row.get("content_family"), "caption": caption, "threads_post": threads, "first_comment": first, "story_frame_text": story, "poll_question": poll, "hashtags": caption.split("\n")[-1], "evidence": row.get("evidence")})
        carousel_rows.append({"package_id": row.get("package_id"), "packet_id": row.get("packet_id"), "platform": row.get("platform"), "headline": row.get("headline"), "content_family": row.get("content_family"), "slides": len(slides), "carousel_plan_path": carousel_path.as_posix(), "prompt_dossier_path": prompt_path.as_posix(), "status": "ready_for_manual_or_renderer_build"})
        if key not in publish_seen:
            publish_lines += [f"## {row.get('headline')}", "", "### Instagram caption", caption, "", "### Threads", threads, "", "### First comment", first, "", "---", ""]
            publish_seen.add(key)
    write_csv(COPY_DIR / "copy_bank.csv", copy_rows, COPY_FIELDS)
    write_csv(CAROUSEL_DIR / "carousel_manifest.csv", carousel_rows, CAROUSEL_FIELDS)
    (COPY_DIR / "copy_bank.md").write_text("# HSD Copy Bank\n\n" + "\n\n---\n\n".join([f"## {r['headline']}\n\nFamily: `{r['content_family']}`\n\n### IG Caption\n{r['caption']}\n\n### Threads\n{r['threads_post']}\n\n### First comment\n{r['first_comment']}" for r in copy_rows]) + "\n", encoding="utf-8")
    (COPY_DIR / "post_ready_copy.md").write_text("\n".join(publish_lines), encoding="utf-8")
    report = read_json(OUT_ROOT / "production_graphics_director_manifest.json")
    report.update({"version": VERSION, "generated_at_utc": now_iso(), "copy_gate": "deduped_scores_story_and_preview_rows", "copy_items": len(copy_rows), "carousel_plans": len(carousel_rows), "post_ready_copy": (COPY_DIR / "post_ready_copy.md").as_posix()})
    (OUT_ROOT / "production_graphics_director_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT_ROOT / "production_graphics_director_report.md").write_text("# Mermaid Production Graphics Director v4.5 Post-Ready Copy Gate\n\n" + f"Generated: {report['generated_at_utc']}\n\n" + "## Counts\n\n" + "\n".join([f"- {k}: {v}" for k, v in report.items() if k not in {"generated_at_utc"}]) + "\n\n## Policy\n\n- Auto-renders remain human-review only.\n- Copy bank is deduped for human publishing.\n- Score lines are deduped.\n- Preview copy stays WNBA-specific and cannot fall through to LPGA feature copy.\n- Slate hashtags include all detected teams.\n", encoding="utf-8")
    summary = read_json(SUMMARY)
    summary.update({"production_director_version": VERSION, "production_director_copy_items": len(copy_rows), "production_director_carousel_plans": len(carousel_rows), "production_director_post_ready_copy": (COPY_DIR / "post_ready_copy.md").as_posix()})
    if SUMMARY.parent.exists():
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
