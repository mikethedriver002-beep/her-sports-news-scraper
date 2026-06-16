from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

VERSION = "v1.2-hsd-graphics-template-factory-law-snapshot"
OUT_DIR = Path("outputs/latest/HSD_TEMPLATE_FACTORY")
MATRIX = OUT_DIR / "template_matrix.csv"
PROMPTS = OUT_DIR / "graphics_production_template_prompts.md"
BRIEF = OUT_DIR / "template_factory_brief.md"
BLUEPRINTS = OUT_DIR / "template_blueprints.json"
PUBLIC_LOGO_RULE = OUT_DIR / "public_logo_rule.md"
LAW_SNAPSHOT = OUT_DIR / "law/HSD_GRAPHICS_LAW_V1.md"
MASTER_PROMPTS_SNAPSHOT = OUT_DIR / "law/HSD_GRAPHICS_TEMPLATE_MASTER_BATCH_PROMPTS_V1.md"
CONFIG_SNAPSHOT_DIR = OUT_DIR / "config_graphics_snapshot"
FIELDS = ["family", "variant", "format", "priority", "purpose", "assets", "must_have", "avoid", "renderer_notes"]

PUBLIC_LOGO_RULE_TEXT = """# HSD Public Logo Rule

For all public-facing Her Sports Daily graphics:

- Use the official compact HSD watermark/bug only.
- Place one bug at top-left.
- Do not use the full HSD + HER SPORTS DAILY lockup on public post templates.
- Do not recreate the logo as editable text.
- Do not add HER SPORTS DAILY wordmark text beside the bug.
- Keep the bug secondary to the content, like a publisher mark.
- Recommended 1080x1350 placement: x 48 px, y 42 px, width 76-84 px.
- Recommended 1080x1920 placement: x 52 px, y 48 px, width 84-96 px.

Spec sheets and internal brand documents may show the full lockup. Public templates may not.
"""

TEMPLATES = [
    ("Tonight in the W", "A", "IG Feed / Threads", "critical", "premium matchup preview", "team logos, optional approved player photos", "big matchup headline, time/TV/context, one strong debate question", "fake jerseys, fake players, tiny schedule tables, large HSD masthead lockups", "two-team hero with logo lockups and optional player lane"),
    ("Tonight in the W", "B", "IG Stories", "critical", "vertical watch guide", "team logos", "fast read, large time, matchup hierarchy, poll space", "crowded dashboards, large HSD masthead lockups", "9:16 safe-zone story with lower poll CTA"),
    ("Tonight in the W", "C", "Carousel Cover", "high", "slate cover", "league/team logos", "3-game or 4-game slate energy", "box-score clutter, large HSD masthead lockups", "cover plus optional per-game slides"),
    ("Last Night in the W", "A", "IG Feed / Threads", "critical", "scoreboard recap", "team logos", "3-5 results, winner emphasis, clean final score hierarchy", "plain spreadsheet tables, large HSD masthead lockups", "stacked editorial scoreboard"),
    ("Last Night in the W", "B", "IG Stories", "critical", "rolling recap", "team logos", "one result per frame or top 3 frames", "tiny team names, large HSD masthead lockups", "story sequence compatible"),
    ("Last Night in the W", "C", "Carousel", "high", "recap carousel", "team logos, approved players when available", "cover, result slides, end-question slide", "overloaded stat panels, large HSD masthead lockups", "multi-slide blueprint"),
    ("Game Recap / Final Score", "A", "IG Feed / Threads", "critical", "single-game final", "team logos", "primary team huge, score huge, secondary team clear, key hook", "grey secondary text too low contrast, large HSD masthead lockups", "premium final-score poster"),
    ("Game Recap / Final Score", "B", "IG Stories", "critical", "story final", "team logos", "score first, primary team first, reply CTA", "tiny captions, large HSD masthead lockups", "9:16 quick final"),
    ("Game Recap / Final Score", "C", "Carousel", "high", "recap package", "team logos, approved player photos", "cover, key performer slide, context slide, end question", "invented stats, large HSD masthead lockups", "needs stat-lock fields"),
    ("Daily Debrief", "A", "IG Carousel", "critical", "multi-sport roundup", "sport/league logos, optional approved images", "3 stories max, broad women’s sports mix", "WNBA-only board, large HSD masthead lockups", "cover plus 3 story slides plus end slide"),
    ("Daily Debrief", "B", "Threads", "high", "text-led visual", "minimal logos", "one visual with 3 headlines", "dense article look, large HSD masthead lockups", "fast summary card"),
    ("Women’s Soccer / NWSL / USWNT", "A", "IG Feed / Threads", "high", "match result or league story", "club/national logos, approved player photos", "global footprint / league context", "wrong crests, fake kits, large HSD masthead lockups", "soccer editorial package"),
    ("Women’s Soccer / NWSL / USWNT", "B", "IG Stories", "high", "matchday story", "logos", "scoreline or callup/roster stat", "crowded roster grids, large HSD masthead lockups", "vertical soccer card"),
    ("LPGA / Golf", "A", "IG Feed / Threads", "high", "winner or leaderboard story", "approved player photo if available, LPGA/event logo if available", "rank/leader/winner hierarchy", "golf score tables that are unreadable, large HSD masthead lockups", "leaderboard editorial card"),
    ("LPGA / Golf", "B", "IG Stories", "medium", "quick leaderboard/winner update", "minimal assets", "player name, event, result, why it matters", "green-on-green low contrast, large HSD masthead lockups", "9:16 golf story"),
    ("Tennis / WTA", "A", "IG Feed / Threads", "high", "match result or tournament story", "approved player photos when available", "player names huge, result/context clean", "fake court photos, large HSD masthead lockups", "tennis editorial match card"),
    ("Tennis / WTA", "B", "IG Stories", "medium", "quick match update", "minimal assets", "winner/result/next opponent if verified", "tiny set score lines, large HSD masthead lockups", "story-first tennis card"),
    ("Player Spotlight", "A", "IG Feed", "high", "star/player moment", "approved real player image required", "player cutout, one claim, one verified stat/context", "fake faces or wrong teams, large HSD masthead lockups", "photo-first hero template"),
    ("Player Spotlight", "B", "Threads", "medium", "conversation starter", "approved player image optional", "strong quote/hook, debate question", "quote without source, large HSD masthead lockups", "fast discourse card"),
    ("Women’s Sports Business / Culture", "A", "IG Feed / Threads", "high", "growth/business story", "logos or text-only", "number/context/headline", "boring corporate chart, large HSD masthead lockups", "premium business editorial card"),
    ("Women’s Sports Business / Culture", "B", "Carousel", "medium", "explainer", "logos, screenshots only if provided/approved", "3-point breakdown", "wall of text, large HSD masthead lockups", "explainer carousel blueprint"),
]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader(); w.writerows(rows)


def prompt_for(row: dict[str, str]) -> str:
    return f"""## {row['family']} - Template {row['variant']} ({row['format']})

Create a premium Her Sports Daily template system for **{row['purpose']}**.

Use HSD style: dark cinematic sports-media background, bold condensed hierarchy, high contrast, modern ESPN/Bleacher Report energy, clean editorial spacing, social-first readability.

Public logo rule: use the official compact HSD watermark/bug only, top-left. Do not use the full HSD + HER SPORTS DAILY lockup on public post templates. Do not recreate the logo as text. Do not add HER SPORTS DAILY beside the bug. The logo should feel like a small publisher mark, not a masthead.

Assets allowed: {row['assets']}.

Must have: {row['must_have']}.

Avoid: {row['avoid']}.

Deliver:
1. One finished template mockup PNG.
2. A blank/editable layout reference PNG.
3. A machine-readable layout spec with canvas size, zones, text hierarchy, logo/photo slots, safe zones, and renderer notes.
4. A short explanation of when to use this template.

Renderer notes: {row['renderer_notes']}.

Non-negotiables: no fake athletes, no fake jerseys, no invented stats, no website URL, compact official HSD bug only top-left, all text inside safe zones.
"""


def copy_if_exists(src: Path, dest: Path) -> None:
    if src.exists() and src.is_file():
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dest)


def copy_config_snapshot() -> None:
    if CONFIG_SNAPSHOT_DIR.exists():
        shutil.rmtree(CONFIG_SNAPSHOT_DIR)
    root = Path("config/graphics")
    if root.exists():
        shutil.copytree(root, CONFIG_SNAPSHOT_DIR)
    copy_if_exists(Path("docs/HSD_GRAPHICS_LAW_V1.md"), LAW_SNAPSHOT)
    copy_if_exists(Path("docs/HSD_GRAPHICS_TEMPLATE_MASTER_BATCH_PROMPTS_V1.md"), MASTER_PROMPTS_SNAPSHOT)


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [{"family": a, "variant": b, "format": c, "priority": d, "purpose": e, "assets": f, "must_have": g, "avoid": h, "renderer_notes": i} for a,b,c,d,e,f,g,h,i in TEMPLATES]
    write_csv(MATRIX, rows)
    BLUEPRINTS.write_text(json.dumps({"version": VERSION, "generated_at_utc": datetime.now(timezone.utc).isoformat(), "public_logo_rule": PUBLIC_LOGO_RULE_TEXT, "templates": rows}, indent=2), encoding="utf-8")
    PROMPTS.write_text("# HSD Graphics Production Template Prompts\n\n" + PUBLIC_LOGO_RULE_TEXT + "\n" + "\n".join(prompt_for(r) for r in rows), encoding="utf-8")
    PUBLIC_LOGO_RULE.write_text(PUBLIC_LOGO_RULE_TEXT, encoding="utf-8")
    copy_config_snapshot()
    BRIEF.write_text("\n".join([
        "# HSD Graphics Template Factory",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        f"Version: `{VERSION}`",
        "",
        "## Purpose",
        "",
        "Stop asking the code renderer to invent taste. Use the Graphics Production chat to create 2-3 approved template families per content type, then convert approved templates into renderer blueprints.",
        "",
        "## Public logo rule",
        "",
        "Public-facing HSD templates use the compact official HSD bug only, top-left. Do not use the full HSD + HER SPORTS DAILY lockup on public graphics. Spec sheets and internal brand documents may use the full lockup.",
        "",
        "## Build order",
        "",
        "1. Final Score / Game Recap",
        "2. Tonight in the W",
        "3. Last Night in the W",
        "4. Daily Debrief",
        "5. NWSL / USWNT / women’s soccer",
        "6. LPGA / golf",
        "7. Tennis / WTA",
        "8. Player Spotlight",
        "9. Women’s sports business / culture",
        "",
        "## Outputs",
        "",
        f"- `{MATRIX.as_posix()}`",
        f"- `{PROMPTS.as_posix()}`",
        f"- `{BLUEPRINTS.as_posix()}`",
        f"- `{PUBLIC_LOGO_RULE.as_posix()}`",
        f"- `{CONFIG_SNAPSHOT_DIR.as_posix()}`",
        f"- `{LAW_SNAPSHOT.as_posix()}`",
        f"- `{MASTER_PROMPTS_SNAPSHOT.as_posix()}`",
        "",
        "## Rule",
        "",
        "The renderer should become a compiler for approved templates, not a designer.",
    ]) + "\n", encoding="utf-8")
    print(json.dumps({"template_factory_rows": len(rows), "out_dir": OUT_DIR.as_posix(), "law_snapshot": LAW_SNAPSHOT.exists()}, indent=2))


if __name__ == "__main__":
    main()
