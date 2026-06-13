from __future__ import annotations

import csv
import json
import re
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set

VERSION = "v3.2.17-mermaid-preview-player-lock-v2"

CFG_PATH = Path("config/hsd_preview_player_lock_v2.json")
BUNDLE_QUEUE = Path("studio_bundle_queue.csv")
FOCUS_CSV = Path("preview_player_focus.csv")
UPLOAD_MANIFEST = Path("graphics_chat_upload_manifest.csv")
PACK_STATUS = Path("graphics_upload_pack_status.csv")
DIRECT_HANDOFF = Path("graphics_chat_direct_handoff.md")
PACK_DIR = Path("graphics_chat_upload_pack/tonight-in-the-w")
ZIP_PATH = Path("graphics_chat_upload_pack_zips/tonight-in-the-w_graphics_chat_upload_pack.zip")

OUT_PLAYER_GATE = Path("tonight_preview_player_lock_v2.csv")
OUT_REPORT = Path("tonight_preview_player_lock_v2_report.md")
OUT_STATUS = Path("tonight_preview_player_lock_v2_status.json")
OUT_SAFE_PROMPT = Path("tonight_preview_safe_prompt_v2.md")
OUT_COPY_GUARD = Path("tonight_preview_copy_family_guard.csv")
OUT_MATCHUP_PLAN = Path("tonight_preview_matchup_plan_v2.md")
OUT_ASSET_ACTIONS = Path("tonight_preview_asset_actions_v2.csv")


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


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in rows:
            w.writerow({k: row.get(k, "") for k in fields})


def load_cfg() -> Dict[str, Any]:
    if CFG_PATH.exists():
        return json.loads(CFG_PATH.read_text(encoding="utf-8"))
    return {}


def pick_tonight_bundle() -> Dict[str, str]:
    rows = read_csv(BUNDLE_QUEUE)
    for row in rows:
        if clean(row.get("post_slug")).lower() == "tonight-in-the-w" or clean(row.get("bundle_name")).lower() == "tonight in the w":
            return row
    return rows[0] if rows else {}


def parse_games(bundle: Dict[str, str]) -> List[Tuple[str, str, str]]:
    """Return (away, home, time_label)."""
    text = clean(bundle.get("caption_seed")) or clean(bundle.get("source_headlines")) or clean(bundle.get("bundle_prompt"))
    text = re.sub(r"^Tonight in the W:\s*", "", text, flags=re.I)
    games: List[Tuple[str, str, str]] = []
    for part in [p.strip() for p in text.split("|") if p.strip()]:
        m = re.search(r"(.+?)\s+at\s+(.+?)(?:\s+-\s+(.+))?$", part, flags=re.I)
        if not m:
            continue
        away = clean(m.group(1))
        home = clean(m.group(2))
        time_label = clean(m.group(3)) if m.group(3) else ""
        key = (away.lower(), home.lower())
        if away and home and key not in {(a.lower(), h.lower()) for a, h, _ in games}:
            games.append((away, home, time_label))
    return games


def team_order(games: List[Tuple[str, str, str]]) -> List[str]:
    out: List[str] = []
    for away, home, _ in games:
        for t in [away, home]:
            if t not in out:
                out.append(t)
    return out


def focus_map() -> Dict[str, List[str]]:
    out: Dict[str, List[str]] = {}
    for row in read_csv(FOCUS_CSV):
        team = clean(row.get("team_name"))
        player = clean(row.get("player_name"))
        if team and player:
            out.setdefault(team, []).append(player)
    return out


def manifest_assets() -> Tuple[Dict[str, Dict[str, str]], Dict[str, Dict[str, str]]]:
    team_assets: Dict[str, Dict[str, str]] = {}
    player_assets: Dict[str, Dict[str, str]] = {}
    for row in read_csv(UPLOAD_MANIFEST):
        if clean(row.get("post_slug")).lower() not in {"tonight-in-the-w", ""}:
            continue
        entity = clean(row.get("entity_name"))
        etype = clean(row.get("entity_type")).lower()
        ready = clean(row.get("asset_ready")).lower() == "yes"
        exact = "exact" in clean(row.get("exact_asset_status")).lower() or clean(row.get("exact_asset_status")) == ""
        if not entity or not ready or not exact:
            continue
        if etype == "team":
            team_assets[entity] = row
        elif etype == "player":
            player_assets[entity] = row
    return team_assets, player_assets


def best_file(row: Dict[str, str]) -> str:
    for key in ["local_png_path", "local_asset_path", "png_filename", "asset_filename"]:
        if clean(row.get(key)):
            return clean(row.get(key))
    return ""


def evaluate_player_gate(teams: List[str], fmap: Dict[str, List[str]], passets: Dict[str, Dict[str, str]]) -> Tuple[List[Dict[str, str]], bool, Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    selected: Dict[str, str] = {}
    all_pass = True
    for team in teams:
        requested = fmap.get(team, [])
        exact = [p for p in requested if p in passets]
        chosen = exact[0] if exact else ""
        if not chosen:
            all_pass = False
        status = "PASS" if chosen else "FAIL"
        selected[team] = chosen
        rows.append({
            "team_name": team,
            "requested_players": " | ".join(requested),
            "exact_attached_players": " | ".join(exact),
            "selected_player": chosen,
            "selected_asset": best_file(passets.get(chosen, {})) if chosen else "",
            "player_gate_status": status,
            "reason": "one exact player selected for team" if chosen else "no exact attached player for this slate team",
            "recommended_action": "allow_player_slide" if chosen else "fallback_to_storylines_slide",
        })
    return rows, all_pass, selected


def storylines(games: List[Tuple[str, str, str]]) -> List[Dict[str, str]]:
    hooks = [
        "Who sets the tone before the game settles in?",
        "Which side owns the key possessions late?",
        "Which team controls pace, execution, and shot quality?",
        "Who makes the first statement?",
    ]
    rows: List[Dict[str, str]] = []
    for i, (away, home, time_label) in enumerate(games, start=1):
        rows.append({
            "matchup": f"{away} at {home}",
            "time_label": time_label,
            "hook": hooks[(i - 1) % len(hooks)],
            "storyline": f"{away} and {home} both get a clean spotlight: watch pace, early shot quality, and who handles the fourth-quarter moments.",
        })
    return rows


def copy_family_guard() -> None:
    cfg = load_cfg()
    bans = cfg.get("preview_copy_family_bans", [])
    rows = []
    for phrase in bans:
        rows.append({
            "phrase": phrase,
            "status": "banned_for_preview",
            "replacement": "Use pregame language: watch, matchup, locked in, tipoff, what to know, what matters tonight.",
            "reason": "Previews must not borrow recap/result language.",
        })
    write_csv(OUT_COPY_GUARD, rows, ["phrase", "status", "replacement", "reason"])


def generate_safe_prompt(games: List[Tuple[str, str, str]], rows: List[Dict[str, str]], all_pass: bool, selected: Dict[str, str]) -> str:
    srows = storylines(games)
    lines = [
        "# Tonight in the W — Safe Graphics Prompt v2",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "Create a premium Her Sports Daily 4-slide 1080x1350 carousel for Tonight in the W.",
        "",
        "CRITICAL PLAYER SAFETY LOCK:",
        "- Do not generate, invent, synthesize, redraw, or approximate any player/person image.",
        "- Use only exact uploaded player files that are explicitly named in this prompt.",
        "- Do not put a player in an opponent jersey or wrong team context.",
        "- Do not use a player image for any other player name.",
        "- If the player slide is not explicitly allowed below, do not use player images at all.",
        "",
        "Slate:",
    ]
    for away, home, time_label in games:
        lines.append(f"- {away} at {home}" + (f" — {time_label}" if time_label else ""))
    lines += [
        "",
        "Slide plan:",
        "Slide 1 — Cover: Tonight in the W. Show both games and tip times compactly.",
        "Slide 2 — What to know tonight: one value-add hook per matchup. Do NOT repeat the full slate-board function from Slide 1.",
    ]
    if all_pass:
        lines.append("Slide 3 — Players to watch: use a strict one-player-per-team layout or two matchup panels. Every team must be represented exactly once.")
        for row in rows:
            lines.append(f"- {row['team_name']}: use exact uploaded image for {row['selected_player']} only. Asset: {row['selected_asset']}")
        lines += [
            "Do not add extra players.",
            "Do not create a 3-team row layout.",
            "Do not use any player image not listed above.",
        ]
    else:
        fail_teams = [r["team_name"] for r in rows if r["player_gate_status"] != "PASS"]
        lines += [
            "Slide 3 — Storylines to know: DO NOT use player images or portraits.",
            "Reason: not every slate team has an exact attached player image.",
            f"Teams without exact player coverage: {', '.join(fail_teams)}.",
            "Use two matchup panels or two storyline cards instead.",
        ]
        for s in srows:
            lines.append(f"- {s['matchup']}: {s['hook']} {s['storyline']}")
    lines += [
        "Slide 4 — CTA: Which game are you locked in for? Drop your pick before tipoff.",
        "",
        "Preview copy-family lock:",
        "- Do not use postgame language.",
        "- Do not use: What stood out?, Final, Final Score, Last Night, gets the win, winner, loser, result, results.",
        "- Do not render scores.",
        "",
        "Logo/brand rules:",
        "- Use exact attached team logo files only.",
        "- Do not use text-logo fallbacks.",
        "- Do not alter or redraw logos.",
        "- Use one HSD watermark only, top-left.",
        "- For Toronto Tempo, keep the exact logo but improve the panel contrast/support glow so the dark logo does not get buried.",
    ]
    return "\n".join(lines) + "\n"


def write_matchup_plan(games: List[Tuple[str, str, str]], all_pass: bool) -> None:
    srows = storylines(games)
    lines = [
        "# Tonight Preview Matchup Plan v2",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Slide 1 — Cover",
        "- Cover with both games and times.",
        "",
        "## Slide 2 — What to know tonight",
    ]
    for s in srows:
        lines.append(f"- {s['matchup']}: {s['hook']} {s['storyline']}")
    lines += [
        "",
        "## Slide 3",
        "- Mode: " + ("Players to watch, one player per team." if all_pass else "Storylines to know, no players."),
        "",
        "## Slide 4 — CTA",
        "- Which game are you locked in for?",
        "- Drop your pick before tipoff.",
    ]
    OUT_MATCHUP_PLAN.write_text("\n".join(lines) + "\n", encoding="utf-8")


def disable_player_assets(selected_players: Set[str], all_pass: bool, passets: Dict[str, Dict[str, str]]) -> List[Dict[str, str]]:
    actions: List[Dict[str, str]] = []
    if not PACK_DIR.exists():
        return actions
    disabled_dir = PACK_DIR / "_disabled_player_assets_do_not_upload"
    disabled_dir.mkdir(exist_ok=True)
    for player, row in passets.items():
        keep = all_pass and player in selected_players
        filenames = [clean(row.get("asset_filename")), clean(row.get("png_filename"))]
        paths = []
        for fn in filenames:
            if not fn:
                continue
            paths += list((PACK_DIR / "assets_original").glob(fn))
            paths += list((PACK_DIR / "assets_png_preferred").glob(fn))
        for key in ["local_asset_path", "local_png_path"]:
            p = Path(clean(row.get(key)))
            if p.exists():
                paths.append(p)
        seen = set()
        for p in paths:
            if not p.exists() or p.as_posix() in seen:
                continue
            seen.add(p.as_posix())
            if keep:
                actions.append({"player_name": player, "asset_path": p.as_posix(), "action": "kept_selected_exact_player"})
                continue
            dest = disabled_dir / p.name
            try:
                if p.resolve() != dest.resolve():
                    shutil.move(str(p), str(dest))
                    actions.append({"player_name": player, "asset_path": p.as_posix(), "action": f"disabled_moved_to_{dest.as_posix()}"})
            except Exception as exc:
                actions.append({"player_name": player, "asset_path": p.as_posix(), "action": f"disable_failed_{type(exc).__name__}"})
    write_csv(OUT_ASSET_ACTIONS, actions, ["player_name", "asset_path", "action"])
    return actions


def update_pack_prompt(prompt: str) -> None:
    OUT_SAFE_PROMPT.write_text(prompt, encoding="utf-8")
    if PACK_DIR.exists():
        (PACK_DIR / "00_PROMPT_TO_PASTE.md").write_text(prompt, encoding="utf-8")
        (PACK_DIR / "tonight_preview_safe_prompt_v2.md").write_text(prompt, encoding="utf-8")
        for p in [OUT_PLAYER_GATE, OUT_MATCHUP_PLAN, OUT_COPY_GUARD]:
            if p.exists():
                shutil.copy2(p, PACK_DIR / p.name)


def rebuild_zip() -> str:
    if not PACK_DIR.exists():
        return ""
    ZIP_PATH.parent.mkdir(parents=True, exist_ok=True)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as z:
        for p in PACK_DIR.rglob("*"):
            if p.is_file() and "_disabled_player_assets_do_not_upload" not in p.as_posix():
                z.write(p, p.relative_to(PACK_DIR))
    return ZIP_PATH.as_posix()


def update_pack_status(mode: str, zip_path: str) -> None:
    rows = read_csv(PACK_STATUS)
    changed = False
    for row in rows:
        if clean(row.get("post_slug")).lower() == "tonight-in-the-w":
            row["notes"] = clean(row.get("notes")) + f" Preview Player Lock v2 applied: {mode}. Use safe prompt and rebuilt zip."
            if zip_path:
                row["zip_path"] = zip_path
            changed = True
    if changed and rows:
        write_csv(PACK_STATUS, rows, list(rows[0].keys()))


def update_direct_handoff(prompt: str, mode: str, zip_path: str) -> None:
    header = [
        "# Preview Player Lock v2 Override",
        "",
        f"Mode: `{mode}`",
        f"Safe ZIP: `{zip_path or ZIP_PATH.as_posix()}`",
        "",
        "Use this override for Tonight in the W. It supersedes any older player-slide instructions.",
        "",
        "```text",
        prompt.strip(),
        "```",
        "",
        "---",
        "",
    ]
    old = DIRECT_HANDOFF.read_text(encoding="utf-8", errors="replace") if DIRECT_HANDOFF.exists() else ""
    DIRECT_HANDOFF.write_text("\n".join(header) + old, encoding="utf-8")


def report(games, teams, rows, all_pass, selected, actions, mode, zip_path) -> None:
    fail_teams = [r["team_name"] for r in rows if r["player_gate_status"] != "PASS"]
    lines = [
        "# Tonight Preview Player Lock v2 Report",
        "",
        f"Version: {VERSION}",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"Games detected: {len(games)}",
        f"Teams detected: {', '.join(teams) if teams else 'None'}",
        f"Player slide allowed: {'YES' if all_pass else 'NO'}",
        f"Slide 3 mode: {mode}",
        f"Failing teams: {', '.join(fail_teams) if fail_teams else 'None'}",
        f"Zip rebuilt: {zip_path or 'not rebuilt'}",
        "",
        "## Team player gate",
    ]
    for row in rows:
        lines.append(f"- {row['team_name']}: {row['player_gate_status']} | selected: {row['selected_player'] or 'None'} | requested: {row['requested_players'] or 'None'}")
    lines += ["", "## Asset actions"]
    for a in actions:
        lines.append(f"- {a['player_name']}: {a['action']} — {a['asset_path']}")
    lines += [
        "",
        "## Enforcement",
        "- If player slide is not allowed, all player assets are removed from the upload pack and the prompt forces a no-player storyline slide.",
        "- If player slide is allowed, only the selected one-player-per-team assets remain in the upload pack.",
        "- Preview CTA language is locked away from postgame/result phrasing.",
    ]
    OUT_REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    bundle = pick_tonight_bundle()
    games = parse_games(bundle)
    teams = team_order(games)
    fmap = focus_map()
    team_assets, passets = manifest_assets()
    gate_rows, all_pass, selected = evaluate_player_gate(teams, fmap, passets)
    write_csv(OUT_PLAYER_GATE, gate_rows, ["team_name", "requested_players", "exact_attached_players", "selected_player", "selected_asset", "player_gate_status", "reason", "recommended_action"])
    copy_family_guard()
    mode = "players_to_watch_one_per_team" if all_pass else "storylines_to_know_no_players"
    selected_set = {p for p in selected.values() if p}
    actions = disable_player_assets(selected_set, all_pass, passets)
    prompt = generate_safe_prompt(games, gate_rows, all_pass, selected)
    write_matchup_plan(games, all_pass)
    update_pack_prompt(prompt)
    zip_path = rebuild_zip()
    update_pack_status(mode, zip_path)
    update_direct_handoff(prompt, mode, zip_path)
    report(games, teams, gate_rows, all_pass, selected, actions, mode, zip_path)
    status = {
        "version": VERSION,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "games_detected": len(games),
        "teams_detected": teams,
        "player_slide_allowed": all_pass,
        "slide_3_mode": mode,
        "selected_players": selected,
        "disabled_player_asset_actions": len([a for a in actions if a.get("action", "").startswith("disabled")]),
        "zip_path": zip_path,
        "ready_with_review": True
    }
    OUT_STATUS.write_text(json.dumps(status, indent=2), encoding="utf-8")
    print(json.dumps(status, indent=2))


if __name__ == "__main__":
    main()
