from __future__ import annotations
import csv, json, re
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone

VERSION = "v3.2.15-mermaid-ops-v1.1"
CFG_PATH = Path("config/hsd_story_results_brand_lock_v1.json")
QUEUE_PATH = Path("ig_story_results_queue.csv")
FRAMES_PATH = Path("ig_story_results_frames.md")
PROMPT_PATH = Path("ig_story_results_graphics_prompt.md")
GUARD_PATH = Path("final_score_story_guard_report.md")
CAPTION_PATH = Path("ig_story_caption_bank.md")
POLL_PATH = Path("ig_story_poll_stickers.md")
HEADLINES_CSV = Path("ig_story_results_headlines.csv")
STATUS_JSON = Path("ig_story_results_brand_lock_status.json")


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    try:
        with path.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def pick(row: Dict[str, str], names: List[str]) -> str:
    lower = {k.lower(): v for k, v in row.items()}
    for n in names:
        if clean(lower.get(n.lower())):
            return clean(lower.get(n.lower()))
    return ""


def parse_int(v: str) -> Optional[int]:
    try:
        return int(float(clean(v)))
    except Exception:
        return None


def extract_games(rows: List[Dict[str, str]]) -> List[Dict[str, Any]]:
    games: List[Dict[str, Any]] = []
    seen = set()
    for row in rows:
        winner = pick(row, ["winner_team", "winning_team", "team_a", "team_1", "team1", "home_team", "away_team", "left_team"])
        loser = pick(row, ["loser_team", "losing_team", "team_b", "team_2", "team2", "away_team", "home_team", "right_team", "opponent_team"])
        ws = pick(row, ["winner_score", "winning_score", "team_a_score", "team_1_score", "team1_score", "home_score", "away_score", "left_score"])
        ls = pick(row, ["loser_score", "losing_score", "team_b_score", "team_2_score", "team2_score", "away_score", "home_score", "right_score"])

        # If explicit winner/loser not available, try team1/team2 + score1/score2
        t1 = pick(row, ["team_1", "team1", "home_team", "left_team", "team_a"])
        t2 = pick(row, ["team_2", "team2", "away_team", "right_team", "team_b", "opponent_team"])
        s1 = parse_int(pick(row, ["team_1_score", "team1_score", "home_score", "left_score", "team_a_score"]))
        s2 = parse_int(pick(row, ["team_2_score", "team2_score", "away_score", "right_score", "team_b_score"]))

        if t1 and t2 and s1 is not None and s2 is not None:
            if s1 >= s2:
                winner, loser, ws, ls = t1, t2, str(s1), str(s2)
            else:
                winner, loser, ws, ls = t2, t1, str(s2), str(s1)

        winner, loser, ws, ls = clean(winner), clean(loser), clean(ws), clean(ls)
        if not (winner and loser and ws and ls):
            continue
        key = (winner.lower(), loser.lower(), ws, ls)
        if key in seen:
            continue
        seen.add(key)
        games.append({
            "winner": winner,
            "loser": loser,
            "winner_score": ws,
            "loser_score": ls,
            "headline": f"{winner} beat {loser}",
            "short_winner": short_team_name(winner),
        })
    return games


def short_team_name(team: str) -> str:
    mapping = {
        "Dallas Wings": "Wings",
        "Phoenix Mercury": "Mercury",
        "New York Liberty": "Liberty",
        "Atlanta Dream": "Dream",
        "Las Vegas Aces": "Aces",
        "Portland Fire": "Fire",
        "Indiana Fever": "Fever",
        "Chicago Sky": "Sky",
    }
    return mapping.get(team, team)


def load_cfg() -> Dict[str, Any]:
    if CFG_PATH.exists():
        return json.loads(CFG_PATH.read_text(encoding="utf-8"))
    return {}


def write_headlines_csv(games: List[Dict[str, Any]]) -> None:
    with HEADLINES_CSV.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["frame_index", "frame_type", "headline", "winner", "loser", "winner_score", "loser_score"])
        w.writeheader()
        for i, g in enumerate(games, start=2):
            w.writerow({
                "frame_index": i,
                "frame_type": "game_card",
                "headline": g["headline"],
                "winner": g["winner"],
                "loser": g["loser"],
                "winner_score": g["winner_score"],
                "loser_score": g["loser_score"],
            })


def write_frames_md(games: List[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    lines = [
        "# IG Story Results Frames",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Global rules:",
        "- Use the same official HSD watermark asset on every frame.",
        "- Use the same exact uploaded team logo asset for a team everywhere it appears in the pack.",
        "- Do not switch logo variants across frames.",
        "- Do not use the phrase \"gets the win\". Use the approved headline templates below.",
        "- Keep all frames 1080x1920 and story-safe.",
        "",
        "## Frame 1 — cover",
        "- Headline: Last Night in the W",
        f"- Subhead: {len(games)} final scores from the W",
        "- Kicker: Every game gets a card.",
        "- Layout: stacked scoreboard preview cards with all selected finals visible.",
        "",
    ]
    for idx, g in enumerate(games, start=2):
        lines += [
            f"## Frame {idx} — game_card",
            f"- Headline: {g['headline']}",
            "- Label: FINAL",
            f"- Winner: {g['winner']} {g['winner_score']}",
            f"- Loser: {g['loser']} {g['loser_score']}",
            "- Visual rule: winner row/card gets the primary emphasis, loser row/card gets the secondary emphasis.",
            "",
        ]
    poll_choices = [g["winner"] for g in games[:4]]
    lines += [
        f"## Frame {len(games)+2} — CTA",
        f"- Headline: {cfg.get('cta_rule', {}).get('headline', 'Best win of the night?')}",
        f"- Subheadline: {cfg.get('cta_rule', {}).get('subheadline', 'Tap in with HSD')}",
        f"- Prompt: {cfg.get('cta_rule', {}).get('poll_prompt', 'Vote in the poll or reply with your pick.')}",
        f"- Poll choices: {', '.join(poll_choices)}",
        "- Design rule: leave only a modest, intentional native-Instagram poll-sticker zone. Do not create a giant empty placeholder box.",
        "",
    ]
    FRAMES_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_prompt_md(games: List[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    lines = [
        "# IG Story Results Graphics Prompt",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Create a vertical Instagram Story results pack for Her Sports Daily.",
        "",
        "Non-negotiable brand rules:",
        "1. Use one official HSD watermark only, in the top-left, with identical treatment on every frame.",
        "2. Do not switch between the wordmark watermark and a boxed HSD bug in the same pack.",
        "3. Use the same exact uploaded logo file for each team on every frame where that team appears.",
        "4. Do not redraw, restyle, recolor, or substitute team logos.",
        "5. Keep the same visual system across all frames: dark editorial background, neon accent edge treatment, bold sports-media typography, premium HSD feel.",
        "6. For game-card headlines, do not use \"gets the win\". Use the approved headlines exactly.",
        "7. The CTA frame must feel intentional. Leave only a small to moderate space for an Instagram native poll sticker, not a giant empty panel.",
        "",
        "Frame list:",
        f"- Frame 1 cover: Last Night in the W / {len(games)} final scores from the W / Every game gets a card.",
    ]
    for idx, g in enumerate(games, start=2):
        lines.append(f"- Frame {idx}: Headline \"{g['headline']}\". Show FINAL. Show {g['winner']} {g['winner_score']} and {g['loser']} {g['loser_score']}. Keep logo usage identical to the cover.")
    poll_choices = [short_team_name(g["winner"]) for g in games[:4]]
    lines.append(f"- Frame {len(games)+2}: CTA frame. Headline \"Best win of the night?\". Subheadline \"Tap in with HSD\". Prompt \"Vote in the poll or reply with your pick.\" Suggested poll choices: {', '.join(poll_choices)}.")
    PROMPT_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_caption_bank(games: List[Dict[str, Any]]) -> None:
    lines = [
        "# IG Story Caption Bank",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Story intro",
        f"Last Night in the W. {len(games)} finals. Which result stood out most?",
        "",
    ]
    for g in games:
        lines += [
            f"## {g['headline']}",
            f"{g['winner']} {g['winner_score']}, {g['loser']} {g['loser_score']}.",
            "",
        ]
    CAPTION_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_poll_file(games: List[Dict[str, Any]]) -> None:
    winners = [short_team_name(g["winner"]) for g in games[:4]]
    lines = [
        "# IG Story Poll Stickers",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Question: Best win of the night?",
        f"Choices: {', '.join(winners)}",
        "Sticker placement: lower-middle safe zone, modest size.",
    ]
    POLL_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def update_guard_report(games: List[Dict[str, Any]], cfg: Dict[str, Any]) -> None:
    base = ""
    if GUARD_PATH.exists():
        base = GUARD_PATH.read_text(encoding="utf-8", errors="replace").rstrip() + "\n\n"
    qa_lines = [
        "# Story Results Brand Lock / Polish QA",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Games selected: {len(games)}",
        f"Frame coverage missing: {0 if games else 'unknown'}",
        "",
        "Checks added:",
        "- One official HSD watermark asset must be used on every frame.",
        "- One exact logo asset variant per team per pack.",
        "- No \"gets the win\" headlines.",
        "- CTA frame must not contain a giant empty placeholder zone.",
        "- Winner emphasis vs loser emphasis should be visually consistent on every game card.",
        "",
        "Render review focus:",
        "- Verify Phoenix Mercury uses the same exact logo asset on the cover and the game card.",
        "- Verify the HSD watermark does not switch to a boxed bug on any frame.",
        "- Verify plural team names are not paired with singular phrasing.",
        "- Verify CTA frame feels finished and intentional.",
    ]
    GUARD_PATH.write_text(base + "\n".join(qa_lines) + "\n", encoding="utf-8")


def main() -> None:
    cfg = load_cfg()
    rows = read_csv(QUEUE_PATH)
    games = extract_games(rows)
    write_headlines_csv(games)
    write_frames_md(games, cfg)
    write_prompt_md(games, cfg)
    update_caption_bank(games)
    update_poll_file(games)
    update_guard_report(games, cfg)
    STATUS_JSON.write_text(json.dumps({
        "version": VERSION,
        "games_found": len(games),
        "watermark_lock": True,
        "logo_lock": True,
        "headline_template": "winner beat loser",
        "cta_polish": True,
    }, indent=2), encoding="utf-8")
    print(json.dumps({"version": VERSION, "games_found": len(games)}, indent=2))


if __name__ == "__main__":
    main()
