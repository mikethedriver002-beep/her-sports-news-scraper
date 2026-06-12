from __future__ import annotations
import csv, json, os, re, zipfile
from pathlib import Path
from typing import Any, Dict, List, Tuple
from datetime import datetime, timezone

VERSION = "v3.2.16-mermaid-preview-intelligence-v1.0"
CFG_PATH = Path("config/hsd_preview_intelligence_v1.json")
BUNDLE_PATH = Path("studio_bundle_queue.csv")
FOCUS_PATH = Path("preview_player_focus.csv")
MANIFEST_PATH = Path("graphics_chat_upload_manifest.csv")
OUT_REPORT = Path("tonight_preview_intelligence_report.md")
OUT_SLIDE_PLAN = Path("tonight_preview_slide_plan.md")
OUT_PLAYER_LOCK = Path("tonight_preview_player_lock_report.csv")
OUT_STORYLINES = Path("tonight_preview_storylines.csv")
OUT_PROMPT = Path("tonight_preview_graphics_prompt_v2.md")
OUT_STATUS = Path("tonight_preview_pack_status.json")
OUT_GUARD = Path("tonight_preview_guard_report.md")
OUT_LAYOUT = Path("tonight_preview_layout_blueprint.csv")
OUT_OVERRIDE = Path("tonight_preview_graphics_chat_override.txt")


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


def load_cfg() -> Dict[str, Any]:
    if CFG_PATH.exists():
        return json.loads(CFG_PATH.read_text(encoding="utf-8"))
    return {}


def pick_bundle(rows: List[Dict[str, str]]) -> Dict[str, str]:
    for row in rows:
        if clean(row.get("bundle_name")).lower() == "tonight in the w":
            return row
    return rows[0] if rows else {}


def parse_games(bundle: Dict[str, str]) -> List[Tuple[str, str]]:
    source = clean(bundle.get("source_headlines")) or clean(bundle.get("caption_seed")) or clean(bundle.get("bundle_prompt"))
    if not source:
        return []
    games: List[Tuple[str, str]] = []
    candidates = [s.strip() for s in source.split("|") if s.strip()]
    if not candidates:
        candidates = re.findall(r"([A-Za-z .’'À-ÿ-]+?)\s+at\s+([A-Za-z .’'À-ÿ-]+)", source, flags=re.I)
    for item in candidates:
        if isinstance(item, tuple):
            away, home = item
        else:
            m = re.search(r"(.+?)\s+at\s+(.+?)(?:\s+-\s+|$)", item, flags=re.I)
            if not m:
                continue
            away, home = m.group(1), m.group(2)
        away, home = clean(away), clean(home)
        if away and home and (away, home) not in games:
            games.append((away, home))
    return games


def build_focus_map(rows: List[Dict[str, str]]) -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for r in rows:
        team = clean(r.get("team_name"))
        player = clean(r.get("player_name"))
        if not team or not player:
            continue
        out.setdefault(team, []).append(player)
    return out


def build_manifest_sets(rows: List[Dict[str, str]]) -> Tuple[Dict[str, str], Dict[str, str], Dict[str, str]]:
    team_logo_assets: Dict[str, str] = {}
    player_assets: Dict[str, str] = {}
    player_asset_names: Dict[str, str] = {}
    for r in rows:
        entity = clean(r.get("entity_name"))
        etype = clean(r.get("entity_type")).lower()
        path = clean(r.get("png_filename")) or clean(r.get("asset_filename")) or clean(r.get("local_png_path")) or clean(r.get("local_asset_path"))
        if etype == "team":
            team_logo_assets[entity] = path
        elif etype == "player":
            player_assets[entity] = path
            player_asset_names[entity.lower()] = path
    return team_logo_assets, player_assets, player_asset_names


def make_storyline(game_idx: int, away: str, home: str, cfg: Dict[str, Any]) -> Dict[str, str]:
    templates = cfg.get("copy_templates", {})
    hooks = [templates.get("generic_hook_1", "Who sets the tone early?"), templates.get("generic_hook_2", "Which side owns the key moments?"), templates.get("generic_hook_3", "What matters most tonight?")]
    return {
        "game_index": str(game_idx),
        "matchup": f"{away} at {home}",
        "slide_2_label": f"Game {game_idx}",
        "slide_2_hook": hooks[(game_idx - 1) % len(hooks)],
        "slide_2_watch_for": f"Watch how {away} and {home} handle pace, execution, and late-game possessions.",
        "slide_3_fallback_angle": f"Can {away} grab the road spotlight, or does {home} control the matchup at home?",
        "cta_choice": f"{away} at {home}"
    }


def write_player_lock(teams: List[str], focus_map: Dict[str, List[str]], player_assets: Dict[str, str]) -> Dict[str, Any]:
    rows = []
    full_pass = True
    for team in teams:
        requested = focus_map.get(team, [])
        exact = [p for p in requested if p in player_assets]
        status = "PASS" if exact else "FAIL"
        if status != "PASS":
            full_pass = False
        action = "allow_player_slide" if status == "PASS" else "fallback_to_storylines_slide"
        rows.append({
            "team_name": team,
            "requested_focus_players": " | ".join(requested),
            "exact_attached_players": " | ".join(exact),
            "exact_attached_player_count": str(len(exact)),
            "player_gate_status": status,
            "recommended_action": action,
        })
    with OUT_PLAYER_LOCK.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["team_name","requested_focus_players","exact_attached_players","exact_attached_player_count","player_gate_status","recommended_action"])
        w.writeheader()
        if rows:
            w.writerows(rows)
    return {"rows": rows, "full_pass": full_pass}


def write_storylines(games: List[Tuple[str, str]], cfg: Dict[str, Any]) -> List[Dict[str, str]]:
    rows = [make_storyline(i + 1, away, home, cfg) for i, (away, home) in enumerate(games)]
    with OUT_STORYLINES.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()) if rows else ["game_index","matchup","slide_2_label","slide_2_hook","slide_2_watch_for","slide_3_fallback_angle","cta_choice"])
        w.writeheader()
        if rows:
            w.writerows(rows)
    return rows


def write_layout_blueprint(games: List[Tuple[str, str]], slide3_mode: str) -> None:
    rows = [
        {"slide_number": "1", "slide_role": "cover", "required_content": "Title + all games + times compactly", "forbidden_content": "No duplicate long-form slate explanation", "notes": "Event feel, not scoreboard."},
        {"slide_number": "2", "slide_role": "what_to_know_tonight", "required_content": "One short hook per game", "forbidden_content": "Do not repeat full slide-1 slate board", "notes": "Must add value, not duplicate schedule."},
        {"slide_number": "3", "slide_role": slide3_mode, "required_content": "Players if all teams have exact assets, otherwise storyline fallback", "forbidden_content": "No three-team rows for a two-game slate", "notes": "Prefer one player per team or two matchup panels."},
        {"slide_number": "4", "slide_role": "cta", "required_content": "Debate/pick question tied to the slate", "forbidden_content": "No empty filler content", "notes": "Drive comment/reply behavior."},
    ]
    with OUT_LAYOUT.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


def write_slide_plan(games: List[Tuple[str, str]], storylines: List[Dict[str, str]], slide3_mode: str, teams: List[str], cfg: Dict[str, Any]) -> None:
    lines = [
        "# Tonight Preview Slide Plan",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Slide 1 — Cover",
        "- Function: cover",
        "- Keep the slate compactly visible with both matchups and tip times.",
        "- Make it feel like an event, not a flat schedule board.",
        "",
        "## Slide 2 — What to know tonight",
        "- Function: add editorial value",
        "- Do not repeat the full slate board function from Slide 1.",
    ]
    for s in storylines:
        lines += [
            f"- {s['matchup']}: {s['slide_2_hook']} {s['slide_2_watch_for']}",
        ]
    lines += ["", f"## Slide 3 — {'Players to watch' if slide3_mode=='players_to_watch' else 'Storylines to know'}"]
    if slide3_mode == "players_to_watch":
        lines += [
            "- Use one player per team OR two matchup panels.",
            "- Every team in the featured slate must be represented.",
            "- Use exact attached player images only.",
            "- If any team is missing a valid exact player image, this slide must not be player-based.",
        ]
    else:
        lines += [
            "- Do NOT force a player slide.",
            "- Use two matchup panels or two storyline cards instead.",
        ]
        for s in storylines:
            lines += [f"- {s['matchup']}: {s['slide_3_fallback_angle']}"]
    lines += [
        "",
        "## Slide 4 — CTA",
        "- Function: engagement",
        f"- Headline: {cfg.get('copy_templates',{}).get('slide_4_header','Which game are you locked in for?')}",
        f"- Subheadline: {cfg.get('copy_templates',{}).get('slide_4_subheader','Drop your pick before tipoff')}",
        "- Ask for a matchup pick or which game viewers are watching first.",
    ]
    OUT_SLIDE_PLAN.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_prompt(games: List[Tuple[str, str]], storylines: List[Dict[str, str]], slide3_mode: str, team_logo_assets: Dict[str, str], focus_map: Dict[str, List[str]], player_assets: Dict[str, str], cfg: Dict[str, Any]) -> None:
    lines = [
        "# Tonight in the W — Graphics Prompt Override",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Create a premium Her Sports Daily 4-slide 1080x1350 carousel for Tonight in the W.",
        "",
        "Non-negotiable rules:",
        "1. Use only the exact uploaded team logos and exact uploaded player/person images.",
        "2. Do not fetch, substitute, or invent logos or players.",
        "3. Every listed slate game must appear somewhere in the carousel.",
        "4. Slide 2 must not duplicate the function of Slide 1.",
        "5. For player-based slides, every team in the slate must be represented with at least one exact attached player image. If that is not possible, replace the player slide with a storyline slide.",
        "6. Do not create a three-team player grid for a two-game slate.",
        "7. Keep one HSD watermark only, top-left.",
        "8. Improve panel contrast/support treatment for dark logos like Toronto Tempo without changing the official logo itself.",
        "",
        "Featured slate:",
    ]
    for away, home in games:
        lines.append(f"- {away} at {home}")
    lines += ["", "Approved slide structure:", "- Slide 1: Cover with both games and times, event energy.", "- Slide 2: What to know tonight with one value-add hook per game."]
    if slide3_mode == "players_to_watch":
        lines.append("- Slide 3: Players to watch. Use one player per team OR two matchup panels. Every team must be represented.")
        for team in sorted({t for pair in games for t in pair}):
            requested = focus_map.get(team, [])
            exact = [p for p in requested if p in player_assets]
            lines.append(f"  - {team}: exact attached player options: {', '.join(exact) if exact else 'NONE'}")
    else:
        lines.append("- Slide 3: Storylines to know. Do NOT use a player slide because not all slate teams have exact attached player images.")
        for s in storylines:
            lines.append(f"  - {s['matchup']}: {s['slide_3_fallback_angle']}")
    lines += [
        f"- Slide 4: CTA. Headline '{cfg.get('copy_templates',{}).get('slide_4_header','Which game are you locked in for?')}'. Subheadline '{cfg.get('copy_templates',{}).get('slide_4_subheader','Drop your pick before tipoff')}'.",
        "",
        "Exact-logo display notes:",
    ]
    notes = cfg.get("team_logo_display_notes", {})
    for team, note in notes.items():
        if team in {t for pair in games for t in pair}:
            lines.append(f"- {team}: {note}")
    OUT_PROMPT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    OUT_OVERRIDE.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_guard_report(games: List[Tuple[str, str]], slide3_mode: str, player_gate_rows: List[Dict[str, str]]) -> None:
    fail_teams = [r["team_name"] for r in player_gate_rows if r["player_gate_status"] != "PASS"]
    lines = [
        "# Tonight Preview Guard Report",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Slate games detected: {len(games)}",
        f"Teams in slate: {len({t for pair in games for t in pair})}",
        f"Slide 3 mode: {slide3_mode}",
        f"Player gate failing teams: {', '.join(fail_teams) if fail_teams else 'None'}",
        "",
        "Checks:",
        f"- All teams represented for player slide: {'PASS' if not fail_teams else 'FAIL'}",
        f"- Slide substitution required: {'YES' if slide3_mode != 'players_to_watch' else 'NO'}",
        "- Redundancy guard: Slide 2 must be value-add, not a duplicate slate board.",
        "- Logo presentation note: Toronto Tempo requires contrast support without logo substitution.",
        "",
        "Render review focus:",
        "- Ensure Slide 2 is not just the same slate repeated from Slide 1.",
        "- Ensure a 2-game slate does not produce a 3-team player row concept.",
        "- Ensure every team in the slate is represented if a player slide is used.",
        "- Ensure dark logos remain legible without altering the official exact asset.",
    ]
    OUT_GUARD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def make_companion_zip() -> str:
    pack_dir = Path("graphics_chat_upload_pack/tonight-in-the-w")
    out_zip = Path("graphics_chat_upload_pack_zips/tonight-in-the-w_preview-intelligence-v1_companion.zip")
    if not pack_dir.exists():
        return "not_created"
    out_zip.parent.mkdir(parents=True, exist_ok=True)
    # Copy only the new guidance files as a companion, not the whole pack.
    with zipfile.ZipFile(out_zip, "w", zipfile.ZIP_DEFLATED) as z:
        for p in [OUT_PROMPT, OUT_SLIDE_PLAN, OUT_PLAYER_LOCK, OUT_STORYLINES, OUT_GUARD, OUT_LAYOUT, OUT_OVERRIDE]:
            if p.exists():
                z.write(p, arcname=f"preview_intelligence/{p.name}")
    return out_zip.as_posix()


def main() -> None:
    cfg = load_cfg()
    bundle_rows = read_csv(BUNDLE_PATH)
    focus_rows = read_csv(FOCUS_PATH)
    manifest_rows = read_csv(MANIFEST_PATH)
    bundle = pick_bundle(bundle_rows)
    games = parse_games(bundle)
    teams = []
    for away, home in games:
        if away not in teams:
            teams.append(away)
        if home not in teams:
            teams.append(home)
    focus_map = build_focus_map(focus_rows)
    team_logo_assets, player_assets, player_asset_names = build_manifest_sets(manifest_rows)
    player_gate = write_player_lock(teams, focus_map, player_assets)
    slide3_mode = "players_to_watch" if player_gate["full_pass"] else "storylines_to_know"
    storylines = write_storylines(games, cfg)
    write_layout_blueprint(games, slide3_mode)
    write_slide_plan(games, storylines, slide3_mode, teams, cfg)
    write_prompt(games, storylines, slide3_mode, team_logo_assets, focus_map, player_assets, cfg)
    write_guard_report(games, slide3_mode, player_gate["rows"])
    companion_zip = make_companion_zip()
    status = {
        "version": VERSION,
        "games_detected": len(games),
        "teams_detected": teams,
        "slide_2_mode": "what_to_know_tonight",
        "slide_3_mode": slide3_mode,
        "player_gate_full_pass": player_gate["full_pass"],
        "player_gate_fail_teams": [r["team_name"] for r in player_gate["rows"] if r["player_gate_status"] != "PASS"],
        "companion_zip": companion_zip,
        "ready_with_review": True
    }
    OUT_STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")

    lines = [
        "# Tonight Preview Intelligence Report",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Bundle: {clean(bundle.get('bundle_name')) or 'Unknown'}",
        f"Games detected: {len(games)}",
        f"Teams detected: {', '.join(teams) if teams else 'None'}",
        f"Slide 3 mode: {slide3_mode}",
        f"Player gate full pass: {'YES' if player_gate['full_pass'] else 'NO'}",
        "",
        "## Key findings",
        "- Slide 2 should be a value-add editorial slide, not a duplicate slate board.",
        "- Slide 3 must be player-based only if every team in the slate has at least one exact attached player image.",
        "- If any slate team is missing a valid exact player image, Slide 3 should convert to a storylines slide.",
        "- Toronto Tempo needs stronger contrast support because the dark exact logo can get buried on dark panels.",
        "",
        "## Team-by-team player gate",
    ]
    for r in player_gate["rows"]:
        lines.append(f"- {r['team_name']}: {r['player_gate_status']} | exact players: {r['exact_attached_players'] or 'None'}")
    lines += [
        "",
        "## Recommended next render expectations",
        "- Slide 1: cover with event energy.",
        "- Slide 2: what to know tonight, not duplicate schedule.",
        f"- Slide 3: {slide3_mode}.",
        "- Slide 4: stronger CTA tied to the featured slate.",
        "",
        f"Companion zip: {companion_zip}",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(status, indent=2))

if __name__ == "__main__":
    main()
