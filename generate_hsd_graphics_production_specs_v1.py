from __future__ import annotations

import csv
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-graphics-production-specs-v1.6"
INPUT_PROMPTS = os.environ.get("HSD_STUDIO_BUNDLE_PROMPTS", "studio_bundle_prompts_v2.md")
INPUT_RENDER_MANIFEST = os.environ.get("HSD_RENDER_MANIFEST", "studio_render_manifest_v2.json")
INPUT_PLAYER_REQS = os.environ.get("HSD_PLAYER_IMAGE_REQUIREMENTS", "player_image_requirements.csv")
OUT_JSON = "graphics_production_specs.json"
OUT_MD = "graphics_slide_blueprints.md"

MAIN_RESULT_SPARKS_PERFORMERS = [
    "Kelsey Plum (Los Angeles Sparks): PTS 27, AST 6",
    "Ariel Atkins (Los Angeles Sparks): PTS 16",
    "Dearica Hamby (Los Angeles Sparks): PTS 15",
    "Nneka Ogwumike (Los Angeles Sparks): PTS 13, REB 10",
    "Cameron Brink (Los Angeles Sparks): PTS 10",
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


def read_json(path: str) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    return json.loads(p.read_text(encoding="utf-8"))


def read_text(path: str) -> str:
    p = Path(path)
    return p.read_text(encoding="utf-8", errors="replace") if p.exists() else ""


def write_text(path: str, text: str) -> None:
    Path(path).write_text(text, encoding="utf-8")


def prompt_block(prompts: str, heading: str) -> str:
    m = re.search(rf"##\s+{re.escape(heading)}\s*\n(.*?)(?=\n##\s+|\Z)", prompts, re.S)
    return m.group(1).strip() if m else ""


def player_image_status(reqs: List[Dict[str, str]]) -> Dict[str, str]:
    return {clean(r.get("player_name")): clean(r.get("status")) for r in reqs}


def build_main_spec(reqs: List[Dict[str, str]]) -> Dict[str, Any]:
    missing = [r for r in reqs if r.get("bundle_slug") == "main-wnba-result" and r.get("required") == "Yes" and not r.get("approved_asset_id")]
    return {
        "post_slug": "main-wnba-result",
        "bundle_name": "Main WNBA Result",
        "player_images_required": True,
        "missing_required_player_images": [r.get("player_name") for r in missing],
        "decision": "blocked_missing_player_images" if missing else "ready_for_graphics_chat",
        "slide_count": 4,
        "slides": [
            {
                "slide": 1,
                "name": "Result hero with people",
                "must_include": ["Dallas Wings player/person image", "Los Angeles Sparks player/person image", "Dallas Wings logo", "Los Angeles Sparks logo", "Dallas Wings 104", "Los Angeles Sparks 96", "Final in Los Angeles"],
                "layout": "Two-player hero, Dallas left/cyan, Los Angeles right/magenta. Headline centered lower third. Logos small near score, not repeated in margins.",
                "forbidden": ["fake jerseys", "fake numbers", "logo-only cover if player images are present", "empty right or left side"],
            },
            {
                "slide": 2,
                "name": "Balanced final score board",
                "must_include": ["Dallas Wings 104", "Los Angeles Sparks 96", "Dallas wins it", "Final Score", "one Dallas logo", "one Sparks logo"],
                "layout": "Symmetric split scoreboard. Fill both sides equally with score slab, team label, logo, and small context strip. No extra logo floating on the left margin.",
                "forbidden": ["duplicate logo in corner or left rail", "empty side", "tiny robotic verification strip", "cropped score"],
            },
            {
                "slide": 3,
                "name": "Two-sided top performers",
                "must_include": ["Dallas leaders", "Sparks leaders", "Jessica Shepard 22 PTS 15 REB 5 AST 2 STL", "Arike Ogunbowale 30 PTS 6 REB 6 AST", "Paige Bueckers 18 PTS 3 REB 14 AST 1 STL", "Kelsey Plum 27 PTS 6 AST", "Ariel Atkins 16 PTS", "Dearica Hamby 15 PTS"],
                "layout": "Two equal columns. Left column Dallas leaders. Right column Sparks leaders. Use small player photos if uploaded. Use logos only as column headers. No giant logo in the margin.",
                "forbidden": ["Wings-only performer slide", "Sparks side missing", "duplicate logo on left rail", "players assigned to wrong team"],
                "sparks_performers": MAIN_RESULT_SPARKS_PERFORMERS,
            },
            {
                "slide": 4,
                "name": "CTA with filled composition",
                "must_include": ["What stood out?", "Follow Her Sports Daily", "both team logos", "HSD lockup", "Dallas 104 · Los Angeles 96"],
                "layout": "Strong CTA, but not empty. Use both logos in footer, basketball texture, score echo, and one comment prompt.",
                "forbidden": ["huge empty dark area", "logo pair only with no context", "same composition as slide 2"],
            },
        ],
    }


def append_specs_to_prompts(prompts: str, specs: Dict[str, Any]) -> str:
    main = specs["posts"][0]
    spec_text = [
        "",
        "### STRICT HSD SLIDE BLUEPRINT OVERRIDE",
        "",
        f"Player images required: {'YES' if main['player_images_required'] else 'NO'}",
        f"Production decision: {main['decision']}",
    ]
    if main["missing_required_player_images"]:
        spec_text += [
            "",
            "STOP: Missing required player images. Do not generate this carousel until these player/person image files are uploaded or sourced by the free player-image pipeline:",
        ]
        for p in main["missing_required_player_images"]:
            spec_text.append(f"- {p}")
    else:
        spec_text += [
            "",
            "PLAYER IMAGE STATUS: required player/person images are present in the upload pack. Use the uploaded player image files only. Do not generate or invent people.",
        ]
    spec_text += [
        "",
        "DISPLAY COPY LANGUAGE RULES:",
        "- Keep verification language internal. Do not render 'Verified Final' on any slide.",
        "- Use 'Final', 'Final Score', 'Dallas wins it', or 'Wings Take L.A.' instead.",
        "- Do not render 'Winner' or 'Loser' labels. Use team names and natural result language.",
        "- Do not render internal QA phrases such as BUNDLE LOCKED FACTS, source-safe context, or do not alter.",
        "- Use the exact display copy from graphics_display_copy.csv when that file is uploaded.",
        "",
        "Slide-by-slide requirements:",
        "",
    ]
    for s in main["slides"]:
        spec_text += [
            f"SLIDE {s['slide']} - {s['name']}",
            f"Layout: {s['layout']}",
            "Must include: " + "; ".join(s["must_include"]),
            "Forbidden: " + "; ".join(s["forbidden"]),
            "",
        ]
    spec_text += [
        "Global correction from previous output:",
        "- Do not put a duplicate Dallas Wings logo on the left margin of the top performers slide.",
        "- Do not create a Wings-only top performers slide. Sparks performers are required too.",
        "- Keep slide 2 balanced so neither side feels empty.",
        "- Use uploaded player/person images when present. No fake player bodies or fake jersey numbers.",
        "- Do not render the phrase Verified Final; use Final or Final Score.",
        "",
    ]
    addition = "\n".join(spec_text)
    return re.sub(r"(##\s+Main WNBA Result\s*\n)", r"\1" + addition + "\n", prompts, count=1)


def main() -> None:
    prompts = read_text(INPUT_PROMPTS)
    manifest = read_json(INPUT_RENDER_MANIFEST)
    reqs = read_csv(INPUT_PLAYER_REQS)
    specs = {"version": VERSION, "generated_at_utc": now(), "posts": [build_main_spec(reqs)]}
    Path(OUT_JSON).write_text(json.dumps(specs, indent=2), encoding="utf-8")

    lines = ["# HSD Graphics Slide Blueprints", "", f"Generated: {now()}", ""]
    for post in specs["posts"]:
        lines += [f"## {post['bundle_name']}", "", f"Decision: `{post['decision']}`", ""]
        if post["missing_required_player_images"]:
            lines += ["Missing required player images:", ""] + [f"- {p}" for p in post["missing_required_player_images"]] + [""]
        for s in post["slides"]:
            lines += [f"### Slide {s['slide']}: {s['name']}", "", f"Layout: {s['layout']}", "", "Must include:", ""] + [f"- {x}" for x in s["must_include"]] + ["", "Forbidden:", ""] + [f"- {x}" for x in s["forbidden"]] + [""]
    Path(OUT_MD).write_text("\n".join(lines), encoding="utf-8")

    if prompts:
        write_text(INPUT_PROMPTS, append_specs_to_prompts(prompts, specs))

    print("Created HSD graphics production specs")
    print(json.dumps({"posts": len(specs["posts"]), "main_decision": specs["posts"][0]["decision"], "missing_player_images": len(specs["posts"][0]["missing_required_player_images"])}, indent=2))


if __name__ == "__main__":
    main()
