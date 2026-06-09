from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-graphics-language-pack-v1.7.1"

INPUT_RENDER_MANIFEST = "studio_render_manifest_v2.json"
INPUT_PLAYER_REQUIREMENTS = "player_image_requirements.csv"
INPUT_APPROVED_ASSETS = "approved_graphics_assets.csv"

OUT_STYLE_GUIDE = "graphics_copy_style_guide.md"
OUT_DISPLAY_COPY = "graphics_display_copy.csv"
OUT_BANNED_LANGUAGE = "graphics_banned_language.csv"
OUT_ASSET_USAGE_MAP = "graphics_asset_usage_map.csv"
OUT_LAYOUT_BLUEPRINT = "graphics_layout_blueprint.csv"
OUT_LANGUAGE_MANIFEST = "graphics_language_manifest.json"

DISPLAY_FIELDS = [
    "bundle_slug", "slide_number", "slide_role", "display_headline", "display_subhead",
    "display_kicker", "score_copy", "cta_copy", "do_not_render_terms", "notes"
]
BANNED_FIELDS = ["term", "severity", "replacement", "reason"]
USAGE_FIELDS = [
    "bundle_slug", "asset_role", "entity_name", "team_name", "approved_asset_id",
    "local_or_source_path", "allowed_usage", "forbidden_usage", "notes"
]
LAYOUT_FIELDS = [
    "bundle_slug", "slide_number", "slide_role", "required_left_entity", "required_right_entity",
    "required_left_people", "required_right_people", "must_include_terms", "must_not_include_terms",
    "composition_rule", "notes"
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: str, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}


def main_wnba_display_copy() -> List[Dict[str, str]]:
    banned = "Verified Final; VERIFIED FINAL; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context"
    return [
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 1,
            "slide_role": "cover_result_hero",
            "display_headline": "Dallas Wings Beat Los Angeles Sparks",
            "display_subhead": "Dallas handles L.A., 104-96",
            "display_kicker": "Final in Los Angeles",
            "score_copy": "104-96",
            "cta_copy": "",
            "do_not_render_terms": banned,
            "notes": "Use one hero player from each team when available. Headline should feel editorial, not robotic.",
        },
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 2,
            "slide_role": "balanced_scoreboard",
            "display_headline": "Final Score",
            "display_subhead": "Dallas Wings 104, Los Angeles Sparks 96",
            "display_kicker": "Dallas gets the win",
            "score_copy": "Dallas 104 · Sparks 96",
            "cta_copy": "",
            "do_not_render_terms": banned,
            "notes": "Do not render Winner/Loser or Verified Final. Use a balanced two-sided scoreboard with both teams equally present.",
        },
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 3,
            "slide_role": "two_team_performers",
            "display_headline": "Top Performers",
            "display_subhead": "Dallas leaders and Sparks leaders from the same game",
            "display_kicker": "The box score story",
            "score_copy": "",
            "cta_copy": "",
            "do_not_render_terms": banned,
            "notes": "Two equal sides. Dallas performers on one side, Sparks performers on the other. No one-team-only layout.",
        },
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 4,
            "slide_role": "cta_wrap",
            "display_headline": "What stood out?",
            "display_subhead": "Dallas 104, Los Angeles 96",
            "display_kicker": "Join the conversation",
            "score_copy": "Final: 104-96",
            "cta_copy": "Follow Her Sports Daily for more women’s sports coverage.",
            "do_not_render_terms": banned,
            "notes": "Use a filled CTA slide with one prompt and both logos. Avoid empty dead space.",
        },
    ]


def generic_display_copy(render_manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    rows = main_wnba_display_copy()
    for b in render_manifest.get("bundles", []):
        slug = clean(b.get("post_slug"))
        if not slug or slug == "main-wnba-result":
            continue
        name = clean(b.get("bundle_name")) or slug.replace("-", " ").title()
        rows.append({
            "bundle_slug": slug,
            "slide_number": 1,
            "slide_role": "bundle_cover",
            "display_headline": name,
            "display_subhead": "Results worth knowing.",
            "display_kicker": "Around women’s sports",
            "score_copy": "",
            "cta_copy": "Follow Her Sports Daily for more women’s sports coverage.",
            "do_not_render_terms": "Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context",
            "notes": "Avoid robotic verification language. Use natural sports-editor phrasing.",
        })
    return rows


def banned_language_rows() -> List[Dict[str, str]]:
    return [
        {"term": "Verified Final", "severity": "hard_ban", "replacement": "Final / Final Score", "reason": "Keep verification internal only. Display language must sound editorial."},
        {"term": "VERIFIED FINAL", "severity": "hard_ban", "replacement": "Final / Final Score", "reason": "Keep verification internal only. Display language must sound editorial."},
        {"term": "Winner", "severity": "soft_ban", "replacement": "Dallas gets the win / Dallas beats L.A.", "reason": "Too generic for HSD graphics."},
        {"term": "Loser", "severity": "hard_ban", "replacement": "Los Angeles Sparks / Sparks fall", "reason": "Harsh and uneditorial."},
        {"term": "Your Take?", "severity": "soft_ban", "replacement": "What stood out?", "reason": "More natural CTA language."},
        {"term": "Biggest takeaway", "severity": "soft_ban", "replacement": "What stood out in this one?", "reason": "Avoid repetitive robotic CTA copy."},
        {"term": "BUNDLE LOCKED FACTS", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
        {"term": "source-safe context", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
        {"term": "graphics-safe context", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
        {"term": "Do not alter", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
    ]


def asset_usage_map(player_rows: List[Dict[str, str]], approved_assets: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_id = {a.get("approved_asset_id"): a for a in approved_assets}
    rows: List[Dict[str, str]] = []

    for team in ["Dallas Wings", "Los Angeles Sparks"]:
        for asset in approved_assets:
            if asset.get("entity_name") == team:
                rows.append({
                    "bundle_slug": "main-wnba-result",
                    "asset_role": "team_logo",
                    "entity_name": team,
                    "team_name": team,
                    "approved_asset_id": asset.get("approved_asset_id", ""),
                    "local_or_source_path": asset.get("master_path") or asset.get("web_path") or asset.get("source_url", ""),
                    "allowed_usage": f"Use only as the {team} logo.",
                    "forbidden_usage": "Do not use as a player image. Do not place duplicate floating logos in unused corners or margins.",
                    "notes": "One intentional logo placement per zone only.",
                })

    for req in player_rows:
        if req.get("bundle_slug") != "main-wnba-result":
            continue
        player = req.get("player_name", "")
        team = req.get("team_name", "")
        asset = by_id.get(req.get("approved_asset_id", ""), {})
        local = req.get("local_path") or asset.get("master_path") or asset.get("web_path") or asset.get("source_url", "")
        rows.append({
            "bundle_slug": "main-wnba-result",
            "asset_role": "player_photo",
            "entity_name": player,
            "team_name": team,
            "approved_asset_id": req.get("approved_asset_id", ""),
            "local_or_source_path": local,
            "allowed_usage": f"Use this image only for {player} ({team}).",
            "forbidden_usage": f"Never use this image for any player other than {player}. Never swap with another player. If unsure, omit the photo rather than substituting.",
            "notes": "Player-to-file mapping is strict.",
        })
    return rows


def layout_blueprint_rows() -> List[Dict[str, str]]:
    banned_terms = "Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context"
    return [
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 1,
            "slide_role": "cover_result_hero",
            "required_left_entity": "Dallas Wings",
            "required_right_entity": "Los Angeles Sparks",
            "required_left_people": "1",
            "required_right_people": "1",
            "must_include_terms": "Dallas Wings; Los Angeles Sparks; 104; 96",
            "must_not_include_terms": banned_terms,
            "composition_rule": "Balanced split cover. If player images exist, use one Dallas player and one Sparks player.",
            "notes": "No empty side. Do not make this a logos-only cover when approved player photos are present.",
        },
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 2,
            "slide_role": "balanced_scoreboard",
            "required_left_entity": "Dallas Wings",
            "required_right_entity": "Los Angeles Sparks",
            "required_left_people": "0",
            "required_right_people": "0",
            "must_include_terms": "Final Score; Dallas Wings; Los Angeles Sparks; 104; 96",
            "must_not_include_terms": banned_terms,
            "composition_rule": "Scores and team identity should be visually balanced left and right. Do not label teams as Winner or Loser.",
            "notes": "Both sides must feel equally full.",
        },
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 3,
            "slide_role": "two_team_performers",
            "required_left_entity": "Dallas Wings",
            "required_right_entity": "Los Angeles Sparks",
            "required_left_people": "2",
            "required_right_people": "2",
            "must_include_terms": "Jessica Shepard; Arike Ogunbowale; Paige Bueckers; Kelsey Plum; Ariel Atkins; Dearica Hamby",
            "must_not_include_terms": banned_terms,
            "composition_rule": "Two-column performer comparison. Left column Dallas. Right column Sparks.",
            "notes": "No one-team-only layout. No giant duplicate margin logo.",
        },
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 4,
            "slide_role": "cta_wrap",
            "required_left_entity": "Dallas Wings",
            "required_right_entity": "Los Angeles Sparks",
            "required_left_people": "0",
            "required_right_people": "0",
            "must_include_terms": "Follow Her Sports Daily; What stood out?; 104; 96",
            "must_not_include_terms": banned_terms,
            "composition_rule": "CTA should feel filled and purposeful. Include both logos and a conversation prompt.",
            "notes": "Avoid dead space and generic filler copy.",
        },
    ]


def style_guide_md(display_rows: List[Dict[str, str]]) -> str:
    main_rows = [r for r in display_rows if r["bundle_slug"] == "main-wnba-result"]
    return """# HSD Graphics Copy Style Guide v1.7

Generated: {generated}

## Core rule

Keep verification and accuracy-lock language **internal**. Do not render it on the graphic.

The graphic can say:

- Final
- Final Score
- Dallas gets the win
- Dallas Wings Beat Los Angeles Sparks
- What stood out?

The graphic must not say:

- Verified Final
- Winner
- Loser
- BUNDLE LOCKED FACTS
- source-safe context
- graphics-safe context
- do not alter

## Voice

HSD should sound like a sharp women’s sports desk, not a database export.

Use short active headlines, human sports language, clean score echoes, and confident CTAs.

Avoid robotic verification language, harsh winner/loser tags, and internal QA terms.

## Separation of concerns

- `graphics_display_copy.csv` is the **display layer**. Only this language is meant to appear on graphics.
- `graphics_banned_language.csv` is the **guardrail layer**. These terms should be stripped from prompts and final graphics.
- `graphics_asset_usage_map.csv` is the **identity layer**. Every player image has a strict one-to-one mapping.
- `graphics_layout_blueprint.csv` is the **composition layer**. It tells the graphics chat what each slide must contain.

## Main WNBA display copy

{copy_lines}

## Asset identity rule

Every player/person image has a one-to-one mapping. The graphics chat must use each image only for the named player in `graphics_asset_usage_map.csv`.
""".format(
        generated=now(),
        copy_lines="\n".join(f"- Slide {r['slide_number']}: {r['display_headline']} | {r['display_subhead']} | {r['score_copy']}" for r in main_rows),
    )


def main() -> None:
    render_manifest = read_json(INPUT_RENDER_MANIFEST)
    approved_assets = read_csv(INPUT_APPROVED_ASSETS)
    player_req = read_csv(INPUT_PLAYER_REQUIREMENTS)

    display_rows = generic_display_copy(render_manifest)
    banned_rows = banned_language_rows()
    usage_rows = asset_usage_map(player_req, approved_assets)
    blueprint_rows = layout_blueprint_rows()

    write_csv(OUT_DISPLAY_COPY, display_rows, DISPLAY_FIELDS)
    write_csv(OUT_BANNED_LANGUAGE, banned_rows, BANNED_FIELDS)
    write_csv(OUT_ASSET_USAGE_MAP, usage_rows, USAGE_FIELDS)
    write_csv(OUT_LAYOUT_BLUEPRINT, blueprint_rows, LAYOUT_FIELDS)
    Path(OUT_STYLE_GUIDE).write_text(style_guide_md(display_rows), encoding="utf-8")

    Path(OUT_LANGUAGE_MANIFEST).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "outputs": [OUT_STYLE_GUIDE, OUT_DISPLAY_COPY, OUT_BANNED_LANGUAGE, OUT_ASSET_USAGE_MAP, OUT_LAYOUT_BLUEPRINT],
        "counts": {
            "display_copy_rows": len(display_rows),
            "banned_language_rows": len(banned_rows),
            "asset_usage_rows": len(usage_rows),
            "layout_blueprint_rows": len(blueprint_rows),
        },
    }, indent=2), encoding="utf-8")

    print("Created HSD graphics language pack v1.7")
    print(json.dumps({
        "display_copy_rows": len(display_rows),
        "banned_language_rows": len(banned_rows),
        "asset_usage_rows": len(usage_rows),
        "layout_blueprint_rows": len(blueprint_rows),
    }, indent=2))


if __name__ == "__main__":
    main()
