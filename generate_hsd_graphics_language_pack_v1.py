from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-graphics-language-pack-v1.6"

INPUT_RENDER_MANIFEST = "studio_render_manifest_v2.json"
INPUT_PLAYER_REQUIREMENTS = "player_image_requirements.csv"
INPUT_APPROVED_ASSETS = "approved_graphics_assets.csv"

OUT_STYLE_GUIDE = "graphics_copy_style_guide.md"
OUT_DISPLAY_COPY = "graphics_display_copy.csv"
OUT_BANNED_LANGUAGE = "graphics_banned_language.csv"
OUT_ASSET_USAGE_MAP = "graphics_asset_usage_map.csv"
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
    banned = "Verified Final; VERIFIED FINAL; Winner; Loser; Your Take?; Biggest Takeaway; BUNDLE LOCKED FACTS; source-safe context; Do not alter"
    return [
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 1,
            "slide_role": "cover_result_hero",
            "display_headline": "Wings Take L.A.",
            "display_subhead": "Dallas closes out a 104-96 road win",
            "display_kicker": "Final in Los Angeles",
            "score_copy": "DAL 104 · LA 96",
            "cta_copy": "",
            "do_not_render_terms": banned,
            "notes": "Human headline. Do not render verification language. Use two hero player images from the asset usage map only.",
        },
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 2,
            "slide_role": "balanced_scoreboard",
            "display_headline": "Final Score",
            "display_subhead": "Dallas Wings 104 · Los Angeles Sparks 96",
            "display_kicker": "Dallas wins it",
            "score_copy": "104-96",
            "cta_copy": "",
            "do_not_render_terms": banned,
            "notes": "Do not render Winner/Loser labels. Use team names, score, and a small human result line.",
        },
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 3,
            "slide_role": "two_sided_leaders",
            "display_headline": "The Box Score Story",
            "display_subhead": "Dallas leaders on the left. Sparks leaders on the right.",
            "display_kicker": "Top performers",
            "score_copy": "",
            "cta_copy": "",
            "do_not_render_terms": banned,
            "notes": "Two equal columns. No duplicate logo in the margin. No Wings-only performer slide.",
        },
        {
            "bundle_slug": "main-wnba-result",
            "slide_number": 4,
            "slide_role": "filled_cta",
            "display_headline": "What stood out?",
            "display_subhead": "Dallas 104 · Los Angeles 96",
            "display_kicker": "Talk hoops with HSD",
            "score_copy": "Final: 104-96",
            "cta_copy": "Follow Her Sports Daily for more women’s hoops coverage.",
            "do_not_render_terms": banned,
            "notes": "CTA must feel designed and filled. Use score echo, both logos, texture, and one conversation prompt.",
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
            "do_not_render_terms": "Verified Final; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter",
            "notes": "Avoid robotic verification language. Use final scores naturally as result rows.",
        })
    return rows


def banned_language_rows() -> List[Dict[str, str]]:
    return [
        {"term": "Verified Final", "severity": "hard_ban", "replacement": "Final", "reason": "Sounds robotic and database-like on graphics. Keep verification internal only."},
        {"term": "VERIFIED FINAL", "severity": "hard_ban", "replacement": "Final", "reason": "Same as above."},
        {"term": "Winner", "severity": "soft_ban", "replacement": "Dallas wins it / team name", "reason": "Generic label. Use editorial result language instead."},
        {"term": "Loser", "severity": "hard_ban", "replacement": "Los Angeles Sparks / final score", "reason": "Too harsh and not editorial."},
        {"term": "Your Take?", "severity": "soft_ban", "replacement": "What stood out?", "reason": "Less generic CTA."},
        {"term": "Biggest takeaway", "severity": "soft_ban", "replacement": "What stood out in Dallas’ win?", "reason": "More natural sentence."},
        {"term": "BUNDLE LOCKED FACTS", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
        {"term": "source-safe context", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
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
                    "forbidden_usage": "Do not use as a player image. Do not duplicate in random margin or left rail.",
                    "notes": "One clean logo placement per intended zone only.",
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
            "notes": "The graphics chat must preserve exact player-to-file mapping.",
        })
    return rows


def style_guide_md(display_rows: List[Dict[str, str]]) -> str:
    main_rows = [r for r in display_rows if r["bundle_slug"] == "main-wnba-result"]
    return """# HSD Graphics Copy Style Guide v1.6

Generated: {generated}

## Core rule

Keep verification and accuracy-lock language **internal**. Do not render it on the graphic.

The graphic can say:

- Final
- Final Score
- Dallas wins it
- Wings Take L.A.
- What stood out?

The graphic must not say:

- Verified Final
- BUNDLE LOCKED FACTS
- source-safe context
- do not alter
- Loser

## Voice

HSD should sound like a sharp women’s sports desk, not a database export.

Use short active headlines, human sports language, clean score echoes, and confident CTAs.

Avoid robotic verification language, harsh winner/loser tags, generic empty CTAs, and internal QA terms.

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

    write_csv(OUT_DISPLAY_COPY, display_rows, DISPLAY_FIELDS)
    write_csv(OUT_BANNED_LANGUAGE, banned_rows, BANNED_FIELDS)
    write_csv(OUT_ASSET_USAGE_MAP, usage_rows, USAGE_FIELDS)
    Path(OUT_STYLE_GUIDE).write_text(style_guide_md(display_rows), encoding="utf-8")

    Path(OUT_LANGUAGE_MANIFEST).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "outputs": [OUT_STYLE_GUIDE, OUT_DISPLAY_COPY, OUT_BANNED_LANGUAGE, OUT_ASSET_USAGE_MAP],
        "counts": {
            "display_copy_rows": len(display_rows),
            "banned_language_rows": len(banned_rows),
            "asset_usage_rows": len(usage_rows),
        },
    }, indent=2), encoding="utf-8")

    print("Created HSD graphics language pack v1.6")
    print(json.dumps({
        "display_copy_rows": len(display_rows),
        "banned_language_rows": len(banned_rows),
        "asset_usage_rows": len(usage_rows),
    }, indent=2))


if __name__ == "__main__":
    main()
