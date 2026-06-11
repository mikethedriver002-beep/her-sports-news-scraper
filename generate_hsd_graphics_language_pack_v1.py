from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-graphics-language-pack-v2.7-exact-asset-display-safe"

INPUT_RENDER_MANIFEST = "studio_render_manifest_v2.json"
INPUT_PLAYER_REQUIREMENTS = "player_image_requirements.csv"
INPUT_APPROVED_ASSETS = "approved_graphics_assets.csv"
INPUT_PREVIEW_BUILD = "studio_preview_build_v2.json"

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

INTERNAL_BANNED = "Verified Final; VERIFIED FINAL; Winner; Loser; BUNDLE LOCKED FACTS; source-safe context; Do not alter; graphics-safe context"
PREVIEW_BANNED = INTERNAL_BANNED + "; Final Score; final score; score; scores; won; beat; beats; defeated; result; results"


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


def render_bundles(render_manifest: Dict[str, Any]) -> List[Dict[str, Any]]:
    return [b for b in render_manifest.get("bundles", []) if clean(b.get("post_slug") or b.get("bundle_slug"))]


def is_preview_bundle(bundle: Dict[str, Any]) -> bool:
    blob = " ".join([
        clean(bundle.get("post_slug") or bundle.get("bundle_slug")),
        clean(bundle.get("bundle_name")),
        clean(bundle.get("template_name")),
        clean(bundle.get("content_type")),
    ]).lower()
    return any(x in blob for x in ["tonight-in-the-w", "tonight in the w", "preview", "upcoming", "schedule"])


def source_facts_text(bundle: Dict[str, Any]) -> str:
    sf = bundle.get("source_facts", {})
    if isinstance(sf, dict):
        for key in ["caption_context", "source_facts_text", "source_headlines", "accuracy_lock"]:
            val = clean(sf.get(key))
            if val:
                return val
        return clean(json.dumps(sf, ensure_ascii=False))
    return clean(sf)


def preview_matchups() -> List[str]:
    build = read_json(INPUT_PREVIEW_BUILD)
    games = build.get("included_games") or build.get("games") or []
    rows: List[str] = []
    if isinstance(games, list):
        for g in games:
            if not isinstance(g, dict):
                continue
            away = clean(g.get("away_team") or g.get("away") or g.get("visitor_team"))
            home = clean(g.get("home_team") or g.get("home"))
            if away and home:
                rows.append(f"{away} at {home}")
    return rows


def matchups_from_bundle(bundle: Dict[str, Any]) -> List[str]:
    facts = source_facts_text(bundle)
    parts = [clean(x) for x in re.split(r"\s*\|\s*", facts) if clean(x)]
    games = [p for p in parts if " at " in p.lower() or " vs " in p.lower()]
    return games[:8]


def display_copy_for_bundle(bundle: Dict[str, Any]) -> List[Dict[str, str]]:
    slug = clean(bundle.get("post_slug") or bundle.get("bundle_slug"))
    name = clean(bundle.get("bundle_name")) or slug.replace("-", " ").title()
    cta = "Follow Her Sports Daily for more women’s sports coverage."
    if is_preview_bundle(bundle):
        matchups = preview_matchups() or matchups_from_bundle(bundle)
        matchup_text = " | ".join(matchups[:4])
        rows = [
            {
                "bundle_slug": slug,
                "slide_number": 1,
                "slide_role": "preview_cover",
                "display_headline": "Tonight in the W" if "w" in name.lower() else name,
                "display_subhead": "Games worth watching",
                "display_kicker": "WNBA slate preview" if "w" in name.lower() else "Women’s sports preview",
                "score_copy": "",
                "cta_copy": "",
                "do_not_render_terms": PREVIEW_BANNED,
                "notes": "Preview only. Do not render final scores, result language, standings claims, injuries, records, or unsupported stats.",
            },
            {
                "bundle_slug": slug,
                "slide_number": 2,
                "slide_role": "slate_board",
                "display_headline": "The slate",
                "display_subhead": matchup_text or "Today’s matchups",
                "display_kicker": "Four games. One night.",
                "score_copy": "",
                "cta_copy": "",
                "do_not_render_terms": PREVIEW_BANNED,
                "notes": "Use matchup cards with time/team hierarchy. No result language.",
            },
            {
                "bundle_slug": slug,
                "slide_number": 3,
                "slide_role": "player_watch",
                "display_headline": "Players to watch",
                "display_subhead": "Star power across the night",
                "display_kicker": "Names to know",
                "score_copy": "",
                "cta_copy": "",
                "do_not_render_terms": PREVIEW_BANNED,
                "notes": "Use tight face/head-and-shoulders crops only. Omit any player image that feels mismatched.",
            },
            {
                "bundle_slug": slug,
                "slide_number": 4,
                "slide_role": "cta_wrap",
                "display_headline": "Which game are you locked in for?",
                "display_subhead": "Drop your pick before tipoff",
                "display_kicker": "Her Sports Daily",
                "score_copy": "",
                "cta_copy": cta,
                "do_not_render_terms": PREVIEW_BANNED,
                "notes": "Conversation-first CTA. No final-score language.",
            },
        ]
        return rows

    # Generic result/story fallback, only for bundles actually present in render manifest.
    return [{
        "bundle_slug": slug,
        "slide_number": 1,
        "slide_role": "editorial_cover",
        "display_headline": name,
        "display_subhead": "Why it matters",
        "display_kicker": "Her Sports Daily",
        "score_copy": "",
        "cta_copy": cta,
        "do_not_render_terms": INTERNAL_BANNED,
        "notes": "Use only facts provided in the bundle. Do not invent stats, quotes, injuries, records, or rankings.",
    }]


def display_copy(render_manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for b in render_bundles(render_manifest):
        rows.extend(display_copy_for_bundle(b))
    return rows


def banned_language_rows() -> List[Dict[str, str]]:
    return [
        {"term": "Verified Final", "severity": "hard_ban", "replacement": "", "reason": "Keep verification internal only."},
        {"term": "VERIFIED FINAL", "severity": "hard_ban", "replacement": "", "reason": "Keep verification internal only."},
        {"term": "Winner", "severity": "soft_ban", "replacement": "gets the win / beats", "reason": "Too generic for HSD graphics."},
        {"term": "Loser", "severity": "hard_ban", "replacement": "", "reason": "Harsh and uneditorial."},
        {"term": "BUNDLE LOCKED FACTS", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
        {"term": "source-safe context", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
        {"term": "graphics-safe context", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
        {"term": "Do not alter", "severity": "hard_ban", "replacement": "", "reason": "Internal instruction only."},
    ]


def asset_usage_map(player_rows: List[Dict[str, str]], approved_assets: List[Dict[str, str]]) -> List[Dict[str, str]]:
    by_id = {a.get("approved_asset_id"): a for a in approved_assets}
    rows: List[Dict[str, str]] = []

    for asset in approved_assets:
        entity_type = clean(asset.get("entity_type"))
        entity = clean(asset.get("entity_name"))
        if not entity:
            continue
        aid = clean(asset.get("approved_asset_id"))
        local = asset.get("master_path") or asset.get("web_path") or asset.get("source_url", "")
        if entity_type == "team":
            rows.append({
                "bundle_slug": "all_current_bundles",
                "asset_role": "team_logo",
                "entity_name": entity,
                "team_name": entity,
                "approved_asset_id": aid,
                "local_or_source_path": local,
                "allowed_usage": f"Use only as the {entity} logo/team mark.",
                "forbidden_usage": "Do not use as a player image. Do not create duplicate floating logos as filler.",
                "notes": "One intentional logo placement per team zone.",
            })

    for req in player_rows:
        player = clean(req.get("player_name"))
        team = clean(req.get("team_name"))
        slug = clean(req.get("bundle_slug")) or "all_current_bundles"
        if not player:
            continue
        asset = by_id.get(req.get("approved_asset_id", ""), {})
        local = req.get("local_path") or asset.get("master_path") or asset.get("web_path") or asset.get("source_url", "")
        rows.append({
            "bundle_slug": slug,
            "asset_role": "player_photo",
            "entity_name": player,
            "team_name": team,
            "approved_asset_id": req.get("approved_asset_id", ""),
            "local_or_source_path": local,
            "allowed_usage": f"Use this image only for {player}" + (f" ({team})." if team else "."),
            "forbidden_usage": f"Never use this image for any player other than {player}. Never swap with another player. If unsure, omit the photo rather than substituting.",
            "notes": "Public-source player image requires human visual review and tight crop if jersey/context is unclear.",
        })
    return rows


def layout_blueprint_rows(render_manifest: Dict[str, Any]) -> List[Dict[str, str]]:
    rows: List[Dict[str, str]] = []
    for b in render_bundles(render_manifest):
        slug = clean(b.get("post_slug") or b.get("bundle_slug"))
        if is_preview_bundle(b):
            terms = "; ".join(matchups_from_bundle(b)[:4]) or "Tonight in the W"
            rows.append({
                "bundle_slug": slug,
                "slide_number": 1,
                "slide_role": "preview_carousel",
                "required_left_entity": "",
                "required_right_entity": "",
                "required_left_people": "0",
                "required_right_people": "0",
                "must_include_terms": terms,
                "must_not_include_terms": PREVIEW_BANNED,
                "composition_rule": "Premium 4-slide preview carousel with matchup hierarchy, team identity, and player-watch energy.",
                "notes": "No scores, no final/result language, no unsupported stats. Use attached assets only.",
            })
        else:
            rows.append({
                "bundle_slug": slug,
                "slide_number": 1,
                "slide_role": "editorial_carousel",
                "required_left_entity": "",
                "required_right_entity": "",
                "required_left_people": "0",
                "required_right_people": "0",
                "must_include_terms": clean(b.get("bundle_name")),
                "must_not_include_terms": INTERNAL_BANNED,
                "composition_rule": "Premium editorial sports-media layout. Facts exact; style polished.",
                "notes": "Do not invent facts or assets.",
            })
    return rows


def style_guide_md(display_rows: List[Dict[str, str]]) -> str:
    copy_lines = "\n".join(
        f"- {r['bundle_slug']} slide {r['slide_number']}: {r['display_headline']} | {r['display_subhead']}"
        for r in display_rows
    ) or "- No display copy rows generated."
    return f"""# HSD Graphics Copy Style Guide v2.5

Generated: {now()}

## Core rule

Keep verification, source, and accuracy-lock language internal. Do not render workflow language on graphics.

## Preview rule

For preview/Tonight posts, do not render final scores, result language, winner/loser framing, standings claims, injuries, records, or unsupported stats.

Preview graphics can say:

- Tonight in the W
- Games worth watching
- Players to watch
- Which game are you locked in for?

## Result rule

For result posts, use only the verified score and facts in the active bundle. Do not use hardcoded example scores from older packets.

## Voice

HSD should sound like a sharp women’s sports desk, not a database export. Use short active headlines, human sports language, clean hierarchy, and confident CTAs.

## Display copy rows

{copy_lines}

## Asset identity rule

Every player/person image has a one-to-one mapping. Use each attached image only for the named player in `graphics_asset_usage_map.csv`. If a public-source image looks mismatched, omit it instead of improvising.
"""


def main() -> None:
    render_manifest = read_json(INPUT_RENDER_MANIFEST)
    approved_assets = read_csv(INPUT_APPROVED_ASSETS)
    player_req = read_csv(INPUT_PLAYER_REQUIREMENTS)

    display_rows = display_copy(render_manifest)
    banned_rows = banned_language_rows()
    usage_rows = asset_usage_map(player_req, approved_assets)
    blueprint_rows = layout_blueprint_rows(render_manifest)

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

    print("Created HSD graphics language pack v2.5")
    print(json.dumps({
        "display_copy_rows": len(display_rows),
        "banned_language_rows": len(banned_rows),
        "asset_usage_rows": len(usage_rows),
        "layout_blueprint_rows": len(blueprint_rows),
    }, indent=2))


if __name__ == "__main__":
    main()
