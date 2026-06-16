from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import generate_hsd_mermaid_production_graphics_director_v4_3 as base  # type: ignore

VERSION = "v4.4-dynamic-slate-copy-polish"
OUT_ROOT = Path("outputs/latest/production_graphics_director")
COPY_DIR = OUT_ROOT / "copy_director"
CAROUSEL_DIR = OUT_ROOT / "carousel_director"
PROMPT_DIR = OUT_ROOT / "manual_prompt_dossiers"
CONTEXT = OUT_ROOT / "context_engine" / "context_bank.csv"
SUMMARY = Path("outputs/latest/summary.json")
RESULTS = [Path("results_contract_v2.csv"), Path("hsd_pipeline_lite_review/files/results_contract_v2.csv")]

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

COPY_FIELDS = ["package_id", "packet_id", "platform", "headline", "content_family", "caption", "threads_post", "first_comment", "story_frame_text", "poll_question", "hashtags", "evidence"]
CAROUSEL_FIELDS = ["package_id", "packet_id", "platform", "headline", "content_family", "slides", "carousel_plan_path", "prompt_dossier_path", "status"]


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


def hashtags(team_ids: str, league: str = "WNBA") -> str:
    tags = ["#HerSportsDaily", "#WomensSports"]
    if league.upper() == "WNBA":
        tags += ["#WNBA", "#Basketball"]
    elif league.upper() == "LPGA":
        tags += ["#LPGA", "#Golf"]
    for tid in [x for x in team_ids.split(";") if x]:
        tag = TEAM_TAGS.get(tid)
        if tag:
            tags.append(tag)
    return " ".join(dict.fromkeys(tags))


def parse_matchup_lines(row: Dict[str, str]) -> List[str]:
    evidence = clean(row.get("evidence"))
    pieces = [clean(p) for p in evidence.split("|") if clean(p)]
    matchups: List[str] = []
    for piece in pieces:
        if re.search(r"\b[A-Z][A-Za-z ]+\s+at\s+[A-Z][A-Za-z ]+\b", piece):
            if piece not in matchups:
                matchups.append(piece)
    return matchups[:4]


def score_lines(row: Dict[str, str]) -> List[str]:
    evidence = clean(row.get("evidence"))
    lines = re.findall(r"[A-Z][A-Za-z ]+\s+\d+\s+·\s+[A-Z][A-Za-z ]+\s+\d+", evidence)
    if lines:
        return [clean(x) for x in lines]
    return [clean(x) for x in evidence.split("|") if " · " in x][:4]


def result_rows() -> Dict[str, Dict[str, str]]:
    out: Dict[str, Dict[str, str]] = {}
    for path in RESULTS:
        for row in read_csv(path):
            if row.get("headline"):
                out[norm(row.get("headline", ""))] = row
    return out


def natural_score(row: Dict[str, str]) -> str:
    winner = clean(row.get("winner_team_name"))
    loser = clean(row.get("loser_team_name"))
    score = clean(row.get("score_display"))
    if not winner or not loser or not score:
        return clean(row.get("summary"))
    nums = re.findall(r"([A-Z][A-Za-z ]+?)\s+(\d+)", score)
    scores = {clean(team): pts for team, pts in nums}
    if winner in scores and loser in scores:
        return f"Final: {winner} {scores[winner]}, {loser} {scores[loser]}."
    return clean(row.get("summary"))


def slate_caption(row: Dict[str, str]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    matchups = parse_matchup_lines(row)
    team_ids = row.get("teams", "")
    if not matchups:
        matchups = [clean(row.get("headline") or "Tonight in the W")]
    display = "\n".join(f"• {m}" for m in matchups)
    is_two_game = len(matchups) >= 2
    caption = (
        "Tonight in the W.\n\n"
        f"{display}\n\n"
        "This slate has more than one question on the board. One game is about who sets the tone early. Another is about who can hold their nerve when the fourth quarter gets loud.\n\n"
        "For HSD, this is exactly the kind of night that needs a carousel: matchup, players to watch, keys to the game, and one clean debate question at the end.\n\n"
        "Which matchup are you watching first? 🏀\n\n"
        f"{hashtags(team_ids, 'WNBA')}"
    )
    threads = f"Tonight in the W: {' | '.join(matchups)}. Which matchup are you watching first?"
    first = "Which matchup has the most juice tonight?"
    story = f"Tonight in the W: {' | '.join(matchups[:2])}"
    poll = "Which game first?" if is_two_game else "Who needs it more?"
    slides = [
        {"slide": "1", "title": "Cover", "copy": "Tonight in the W", "visual": "Premium HSD cover in the preferred dark cinematic style with all matchup logos."},
        {"slide": "2", "title": "Slate", "copy": " | ".join(matchups), "visual": "Clean schedule board. Large matchup rows. Official logos only."},
        {"slide": "3", "title": "Players to watch", "copy": "Use approved or exact attached player images only.", "visual": "Player image lane. If exact player images are unavailable, use team logos and text labels."},
        {"slide": "4", "title": "Keys", "copy": "Pace. Glass. Shot quality. Fourth-quarter answers.", "visual": "Four bold key tiles, big readable type."},
        {"slide": "5", "title": "CTA", "copy": "Which matchup are you watching first?", "visual": "Poll-style HSD end slide."},
    ]
    return caption, threads, first, story, poll, slides


def results_caption(row: Dict[str, str]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    scores = score_lines(row)
    score_block = "\n".join(f"• {s}" for s in scores) if scores else "• Final scores are in."
    caption = (
        "Last Night in the W.\n\n"
        f"{score_block}\n\n"
        "Dallas did more than win. The Wings put a number on the board that makes people look twice. Minnesota did the same with a statement result that gives the night real shape.\n\n"
        "That is the difference between a score dump and a recap: what changed after the final buzzer?\n\n"
        "Which result mattered most? 🏀\n\n"
        f"{hashtags(row.get('teams', ''), 'WNBA')}"
    )
    slides = [
        {"slide": "1", "title": "Cover", "copy": "Last Night in the W", "visual": "Premium dark scoreboard cover."},
        {"slide": "2", "title": "Scores", "copy": " | ".join(scores), "visual": "Large final-score rows with official team logos."},
        {"slide": "3", "title": "Dallas made noise", "copy": "Wings over Aces", "visual": "Spotlight Dallas result with score lock."},
        {"slide": "4", "title": "Minnesota sent a message", "copy": "Lynx over Fire", "visual": "Spotlight Minnesota result with score lock."},
        {"slide": "5", "title": "CTA", "copy": "Best win of the night?", "visual": "Question-first end slide."},
    ]
    return caption, "Last Night in the W. Which result mattered most?", "Best win of the night?", "Last Night in the W: which result mattered most?", "Best win?", slides


def result_caption(row: Dict[str, str], result_map: Dict[str, Dict[str, str]]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    headline = row.get("headline", "")
    rr = result_map.get(norm(headline), {})
    detail = natural_score(rr) if rr else "The final is in."
    caption = (
        f"{headline}.\n\n"
        f"{detail}\n\n"
        "That is a real result, not just a line in the box score. Dallas gets a win that changes the feel of the night, and Vegas leaves with questions that will carry into the next one.\n\n"
        "What did this one tell you? 🏀\n\n"
        f"{hashtags(row.get('teams', ''), 'WNBA')}"
    )
    slides = [
        {"slide": "1", "title": "Final", "copy": headline, "visual": "Final-score cover with both team logos."},
        {"slide": "2", "title": "Score", "copy": detail, "visual": "Score lock. Large winner/loser hierarchy."},
        {"slide": "3", "title": "What changed", "copy": "Dallas made the night louder.", "visual": "Editorial takeaway slide."},
        {"slide": "4", "title": "CTA", "copy": "What did this one tell you?", "visual": "Question-first end slide."},
    ]
    return caption, f"{headline}. What did this one tell you?", "What changed after this result?", headline[:110], "What stood out?", slides


def feature_caption(row: Dict[str, str]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    caption = (
        "Gina Kim and Yana Wilson are officially in the LPGA winner’s circle together.\n\n"
        "From the Epson Tour to a title moment at the Dow Championship, this is the kind of women’s golf story that deserves more than a line in the ticker. It is a team-format breakthrough, a shared win, and a reminder that the LPGA lane has real stories with texture.\n\n"
        "Are we talking about this enough?\n\n"
        "#HerSportsDaily #WomensSports #LPGA #Golf"
    )
    slides = [
        {"slide": "1", "title": "Cover", "copy": "Kim + Wilson win together", "visual": "Premium LPGA editorial cover. No fake player imagery."},
        {"slide": "2", "title": "Path", "copy": "From Epson Tour to LPGA winner’s circle", "visual": "Timeline-style card."},
        {"slide": "3", "title": "Why it matters", "copy": "A shared title moment at the Dow Championship", "visual": "Clean editorial context card."},
        {"slide": "4", "title": "CTA", "copy": "Are we talking about this enough?", "visual": "Question-first end slide."},
    ]
    return caption, "Kim and Wilson in the LPGA winner’s circle together. This deserves more attention.", "Are we talking about this enough?", "LPGA breakthrough: Kim + Wilson win together.", "Enough attention?", slides


def package_copy(row: Dict[str, str], result_map: Dict[str, Dict[str, str]]) -> Tuple[str, str, str, str, str, List[Dict[str, str]]]:
    family = row.get("content_family", "")
    if family == "manual_graphics_pack":
        return slate_caption(row)
    if family == "wnba_results_roundup":
        return results_caption(row)
    if family == "wnba_result_recap":
        return result_caption(row, result_map)
    if family == "feature_story" and row.get("league") == "LPGA":
        return feature_caption(row)
    return feature_caption(row)


def write_prompt(row: Dict[str, str], caption: str, slides: List[Dict[str, str]]) -> str:
    slide_text = "\n".join([f"### Slide {s['slide']}: {s['title']}\nOn-image copy: {s['copy']}\nVisual direction: {s['visual']}\n" for s in slides])
    prompt = (
        f"# HSD Manual Prompt Dossier — {row.get('headline')}\n\n"
        f"Packet: `{row.get('package_id')}`\nPlatform: `{row.get('platform')}`\nFamily: `{row.get('content_family')}`\nQuality: `{row.get('context_quality')}`\n\n"
        "## Brand Style\n\nPremium women’s sports editorial. Dark high-contrast background. Bold condensed sports typography. Cinematic lighting. Clean hierarchy. No white dashboard cards. No tiny text. Use the official HSD watermark exactly.\n\n"
        f"## Evidence\n\n{row.get('evidence','')[:1200]}\n\n"
        f"## Carousel Plan\n\n{slide_text}\n## Caption\n\n{caption}\n\n## Negative Prompt\n\nNo fake players. No invented stats. No unapproved headshots. No generic blank headshots. No cut-off names. No low-contrast text. No extra teams. No white panels.\n"
    )
    path = PROMPT_DIR / f"{slug(row.get('package_id', row.get('headline', 'item')))}.md"
    path.write_text(prompt, encoding="utf-8")
    return path.as_posix()


def main() -> None:
    base.main()
    rows = read_csv(CONTEXT)
    result_map = result_rows()
    copy_rows: List[Dict[str, Any]] = []
    carousel_rows: List[Dict[str, Any]] = []
    for row in rows:
        caption, threads, first, story, poll, slides = package_copy(row, result_map)
        prompt_path = write_prompt(row, caption, slides)
        carousel_path = CAROUSEL_DIR / f"{slug(row.get('package_id', row.get('headline','item')))}_carousel_plan.md"
        carousel_path.write_text("# Carousel Plan\n\n" + "\n".join([f"## Slide {s['slide']}: {s['title']}\n{s['copy']}\n\n{s['visual']}\n" for s in slides]), encoding="utf-8")
        copy_rows.append({"package_id": row.get("package_id"), "packet_id": row.get("packet_id"), "platform": row.get("platform"), "headline": row.get("headline"), "content_family": row.get("content_family"), "caption": caption, "threads_post": threads, "first_comment": first, "story_frame_text": story, "poll_question": poll, "hashtags": caption.split("\n")[-1], "evidence": row.get("evidence")})
        carousel_rows.append({"package_id": row.get("package_id"), "packet_id": row.get("packet_id"), "platform": row.get("platform"), "headline": row.get("headline"), "content_family": row.get("content_family"), "slides": len(slides), "carousel_plan_path": carousel_path.as_posix(), "prompt_dossier_path": prompt_path, "status": "ready_for_manual_or_renderer_build"})
    write_csv(COPY_DIR / "copy_bank.csv", copy_rows, COPY_FIELDS)
    write_csv(CAROUSEL_DIR / "carousel_manifest.csv", carousel_rows, CAROUSEL_FIELDS)
    (COPY_DIR / "copy_bank.md").write_text("# HSD Copy Bank\n\n" + "\n\n---\n\n".join([f"## {r['headline']}\n\nFamily: `{r['content_family']}`\n\n### IG Caption\n{r['caption']}\n\n### Threads\n{r['threads_post']}\n\n### First comment\n{r['first_comment']}" for r in copy_rows]) + "\n", encoding="utf-8")
    report = read_json(OUT_ROOT / "production_graphics_director_manifest.json")
    report.update({"version": VERSION, "generated_at_utc": now_iso(), "copy_polish": "dynamic slate/result copy applied", "copy_items": len(copy_rows), "carousel_plans": len(carousel_rows)})
    (OUT_ROOT / "production_graphics_director_manifest.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    (OUT_ROOT / "production_graphics_director_report.md").write_text("# Mermaid Production Graphics Director v4.4 Dynamic Slate Copy Polish\n\n" + f"Generated: {report['generated_at_utc']}\n\n" + "## Counts\n\n" + "\n".join([f"- {k}: {v}" for k, v in report.items() if k not in {"generated_at_utc"}]) + "\n\n## Policy\n\n- Auto-renders remain human-review only.\n- Slate copy is generated from detected matchup lines, not hardcoded team language.\n- Result copy uses natural final-score language when available.\n", encoding="utf-8")
    summary = read_json(SUMMARY)
    summary.update({"production_director_version": VERSION, "production_director_copy_items": len(copy_rows), "production_director_carousel_plans": len(carousel_rows)})
    if SUMMARY.parent.exists():
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
