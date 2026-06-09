from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-graphics-production-specs-v1.7.1"
INPUT_PROMPTS = os.environ.get("HSD_STUDIO_BUNDLE_PROMPTS", "studio_bundle_prompts_v2.md")
INPUT_PLAYER_REQS = os.environ.get("HSD_PLAYER_IMAGE_REQUIREMENTS", "player_image_requirements.csv")
OUT_JSON = "graphics_production_specs.json"
OUT_MD = "graphics_slide_blueprints.md"
OUT_SANITIZER = "graphics_prompt_sanitizer_rules.md"

MAIN_RESULT_SPARKS_PERFORMERS = [
    "Kelsey Plum (Los Angeles Sparks): 27 PTS, 6 AST",
    "Ariel Atkins (Los Angeles Sparks): 16 PTS",
    "Dearica Hamby (Los Angeles Sparks): 15 PTS",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def read_csv(path: str) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def write_text(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def build_main_spec(reqs: List[Dict[str, str]]) -> Dict[str, Any]:
    missing = [
        r for r in reqs
        if r.get("bundle_slug") == "main-wnba-result" and r.get("required") == "Yes" and not r.get("approved_asset_id")
    ]
    return {
        "post_slug": "main-wnba-result",
        "bundle_name": "Main WNBA Result",
        "player_images_required": True,
        "missing_required_player_images": [r.get("player_name") for r in missing],
        "decision": "blocked_missing_player_images" if missing else "ready_for_graphics_chat",
        "slide_count": 4,
        "language_rules": {
            "must_not_render": [
                "Verified Final",
                "Winner",
                "Loser",
                "BUNDLE LOCKED FACTS",
                "source-safe context",
                "graphics-safe context",
                "Do not alter",
            ],
            "preferred_display_words": [
                "Final",
                "Final Score",
                "Dallas gets the win",
                "What stood out?",
                "Follow Her Sports Daily",
            ],
        },
        "slides": [
            {
                "slide": 1,
                "name": "Result hero with both teams represented",
                "must_include": [
                    "One Dallas player image",
                    "One Sparks player image",
                    "Dallas Wings logo",
                    "Los Angeles Sparks logo",
                    "Dallas 104",
                    "Los Angeles 96",
                ],
                "layout": "Two-player hero, Dallas left/cyan, Sparks right/magenta. Both sides should feel visually full.",
                "forbidden": [
                    "Verified Final",
                    "empty side",
                    "logos-only cover when player images are available",
                    "fake players or fake jerseys",
                ],
            },
            {
                "slide": 2,
                "name": "Balanced final score board",
                "must_include": [
                    "Final Score",
                    "Dallas Wings 104",
                    "Los Angeles Sparks 96",
                    "one Dallas logo",
                    "one Sparks logo",
                ],
                "layout": "Symmetric split scoreboard. Fill both sides equally with team name, score, and logo.",
                "forbidden": [
                    "Winner label",
                    "Loser label",
                    "Verified Final strip",
                    "empty side",
                    "duplicate logo floating in margin",
                ],
            },
            {
                "slide": 3,
                "name": "Two-sided top performers",
                "must_include": [
                    "Dallas leaders",
                    "Sparks leaders",
                    "Jessica Shepard 22 PTS 15 REB 5 AST 2 STL",
                    "Arike Ogunbowale 30 PTS 6 REB 6 AST",
                    "Paige Bueckers 18 PTS 3 REB 14 AST 1 STL",
                    "Kelsey Plum 27 PTS 6 AST",
                    "Ariel Atkins 16 PTS",
                    "Dearica Hamby 15 PTS",
                ],
                "layout": "Two equal columns or stacked two-team comparison. Use Dallas players only on the Dallas side and Sparks players only on the Sparks side.",
                "forbidden": [
                    "Wings-only performer slide",
                    "Sparks side missing",
                    "duplicate giant team logo in the margin",
                    "mixed-up player identities",
                ],
                "sparks_performers": MAIN_RESULT_SPARKS_PERFORMERS,
            },
            {
                "slide": 4,
                "name": "CTA with filled composition",
                "must_include": [
                    "What stood out?",
                    "Follow Her Sports Daily",
                    "Dallas 104",
                    "Los Angeles 96",
                    "both logos",
                ],
                "layout": "Strong CTA with score echo, both logos, HSD branding, and one community prompt.",
                "forbidden": [
                    "dead space",
                    "Verified Final",
                    "generic robotic CTA",
                    "same composition as slide 2",
                ],
            },
        ],
    }


def append_specs_to_prompts(prompts: str, specs: Dict[str, Any]) -> str:
    main = specs["posts"][0]
    spec_text = [
        "",
        "### STRICT HSD SLIDE BLUEPRINT OVERRIDE v1.7",
        "",
        f"Player images required: {'YES' if main['player_images_required'] else 'NO'}",
        f"Production decision: {main['decision']}",
        "",
        "PROMPT SANITIZER RULES:",
        "- Strip internal QA language before writing the final prompt.",
        "- Never render: Verified Final, Winner, Loser, BUNDLE LOCKED FACTS, source-safe context, graphics-safe context, or Do not alter.",
        "- Prefer display language from graphics_display_copy.csv.",
        "- If both team performer data exists, slide 3 must include both teams.",
        "- If approved player images exist, use them. Do not replace with invented people.",
        "",
    ]
    if main["missing_required_player_images"]:
        spec_text += [
            "STOP: Missing required player images. Do not generate this carousel until these files are uploaded or sourced:",
            *[f"- {p}" for p in main["missing_required_player_images"]],
            "",
        ]
    else:
        spec_text += [
            "PLAYER IMAGE STATUS: required player images are present in the upload pack. Use the uploaded player image files only.",
            "",
        ]
    spec_text += ["Slide-by-slide requirements:", ""]
    for s in main["slides"]:
        spec_text += [
            f"SLIDE {s['slide']} - {s['name']}",
            f"Layout: {s['layout']}",
            "Must include: " + "; ".join(s["must_include"]),
            "Forbidden: " + "; ".join(s["forbidden"]),
            "",
        ]
    spec_text += [
        "Global correction rules from prior runs:",
        "- Never render the phrase Verified Final.",
        "- Never label teams as Winner or Loser.",
        "- Slide 2 must feel balanced on both sides.",
        "- Slide 3 must include Sparks performers as well as Dallas performers.",
        "- Do not place a duplicate team logo in an unused margin just to fill space.",
        "",
    ]
    addition = "\n".join(spec_text)
    return re.sub(r"(##\s+Main WNBA Result\s*\n)", r"\1" + addition + "\n", prompts, count=1)


def main() -> None:
    prompts = read_text(INPUT_PROMPTS)
    reqs = read_csv(INPUT_PLAYER_REQS)
    specs = {"version": VERSION, "generated_at_utc": now(), "posts": [build_main_spec(reqs)]}
    Path(OUT_JSON).write_text(json.dumps(specs, indent=2), encoding="utf-8")

    lines = ["# HSD Graphics Slide Blueprints", "", f"Generated: {now()}", ""]
    for post in specs["posts"]:
        lines += [f"## {post['bundle_name']}", "", f"Decision: `{post['decision']}`", ""]
        if post["missing_required_player_images"]:
            lines += ["Missing required player images:", ""] + [f"- {p}" for p in post["missing_required_player_images"]] + [""]
        for s in post["slides"]:
            lines += [
                f"### Slide {s['slide']}: {s['name']}",
                "",
                f"Layout: {s['layout']}",
                "",
                "Must include:",
                "",
            ] + [f"- {x}" for x in s["must_include"]] + ["", "Forbidden:", ""] + [f"- {x}" for x in s["forbidden"]] + [""]
    Path(OUT_MD).write_text("\n".join(lines), encoding="utf-8")

    sanitizer = f"""# HSD Graphics Prompt Sanitizer Rules v1.7

Generated: {now()}

## Purpose

This file defines the last-pass cleanup rules before a graphics-chat prompt is handed off.

## Hard-strip phrases

- Verified Final
- VERIFIED FINAL
- Winner
- Loser
- BUNDLE LOCKED FACTS
- source-safe context
- graphics-safe context
- Do not alter

## Replace with human display copy

- Verified Final -> Final / Final Score
- Winner -> team name or natural result line
- Loser -> opposing team name or natural result line
- Your Take? -> What stood out?
- Biggest takeaway -> What stood out in this one?

## Display copy rule

The graphics chat should render only display language, not internal QA language.
"""
    Path(OUT_SANITIZER).write_text(sanitizer, encoding="utf-8")

    if prompts:
        write_text(INPUT_PROMPTS, append_specs_to_prompts(prompts, specs))

    print("Created HSD graphics production specs v1.7")
    print(json.dumps({"posts": len(specs["posts"]), "main_decision": specs["posts"][0]["decision"]}, indent=2))


if __name__ == "__main__":
    main()
