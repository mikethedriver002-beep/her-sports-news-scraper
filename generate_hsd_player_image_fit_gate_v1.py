from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "hsd-player-image-fit-gate-v1.8"

INPUT_REQS = "player_image_requirements.csv"
INPUT_APPROVED = "approved_graphics_assets.csv"
INPUT_USAGE = "graphics_asset_usage_map.csv"

OUT_CSV = "player_image_fit_gate.csv"
OUT_MD = "player_image_fit_report.md"
OUT_JSON = "player_image_fit_manifest.json"

FIELDS = [
    "bundle_slug", "player_name", "team_name", "approved_asset_id", "fit_status",
    "usage_mode", "risk_level", "risk_reasons", "recommended_crop", "prompt_instruction"
]

CURRENT_TEAM_HINTS = {
    "Dallas Wings": ["dallas", "wings", "wnba", "dal"],
    "Los Angeles Sparks": ["los angeles", "sparks", "wnba", "la sparks", "las"],
    "Minnesota Lynx": ["minnesota", "lynx", "wnba"],
    "Seattle Storm": ["seattle", "storm", "wnba"],
    "Phoenix Mercury": ["phoenix", "mercury", "wnba"],
    "Las Vegas Aces": ["las vegas", "aces", "wnba"],
    "Golden State Valkyries": ["golden state", "valkyries", "wnba"],
    "Portland Fire": ["portland", "fire", "wnba"],
}

NON_CURRENT_TEAM_HINTS = [
    "fenerbahce", "fenerbahçe", "galatasaray", "euroleague", "ncaa", "uconn", "ucla",
    "college", "national team", "olympics", "usa basketball", "fiba", "overseas",
]


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "")).strip()


def slug(v: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", clean(v).lower()).strip()


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


def source_text(row: Dict[str, str], approved_by_id: Dict[str, Dict[str, str]]) -> str:
    aid = row.get("approved_asset_id", "")
    asset = approved_by_id.get(aid, {})
    bits = [
        row.get("player_name", ""),
        row.get("team_name", ""),
        row.get("source_url", ""),
        row.get("local_path", ""),
        row.get("sourcing_method", ""),
        row.get("notes", ""),
        asset.get("source_url", ""),
        asset.get("page_url", ""),
        asset.get("master_path", ""),
        asset.get("web_path", ""),
        asset.get("notes", ""),
    ]
    return slug(" ".join(bits))


def evaluate(row: Dict[str, str], approved_by_id: Dict[str, Dict[str, str]]) -> Dict[str, str]:
    player = clean(row.get("player_name"))
    team = clean(row.get("team_name"))
    aid = clean(row.get("approved_asset_id"))
    txt = source_text(row, approved_by_id)
    risk = []
    usage_mode = "normal_player_photo"
    fit_status = "approved"
    risk_level = "low"

    if not aid:
        fit_status = "blocked_missing_image"
        risk_level = "critical"
        risk.append("missing required player image")
    else:
        team_hints = CURRENT_TEAM_HINTS.get(team, [x for x in slug(team).split() if len(x) > 2])
        if team and not any(slug(h) in txt for h in team_hints):
            risk.append("source does not clearly match current team")
        for bad in NON_CURRENT_TEAM_HINTS:
            if slug(bad) in txt:
                risk.append(f"possible non-current-team/alternate jersey source: {bad}")
        if row.get("sourcing_method", "").lower() in {"wikidata_p18", "wikipedia_pageimage", "duckduckgo_images"}:
            risk.append("public-source image needs visual review")

    if risk and risk_level != "critical":
        risk_level = "medium" if len(risk) <= 2 else "high"
        fit_status = "review"
        usage_mode = "tight_face_crop_only"

    if usage_mode == "tight_face_crop_only":
        crop = "Crop tightly around face/head-and-shoulders. Do not show overseas, college, or wrong-team jersey marks."
        instruction = f"Use {player}'s image only for {player}. Crop tightly if the jersey is not clearly {team}."
    elif fit_status == "blocked_missing_image":
        crop = "Do not use."
        instruction = f"Missing approved image for {player}. Do not substitute another player."
    else:
        crop = "Normal crop is allowed if the image clearly matches the player and team context."
        instruction = f"Use {player}'s image only for {player}."

    return {
        "bundle_slug": clean(row.get("bundle_slug")),
        "player_name": player,
        "team_name": team,
        "approved_asset_id": aid,
        "fit_status": fit_status,
        "usage_mode": usage_mode,
        "risk_level": risk_level,
        "risk_reasons": "; ".join(risk),
        "recommended_crop": crop,
        "prompt_instruction": instruction,
    }


def main() -> None:
    reqs = read_csv(INPUT_REQS)
    approved = read_csv(INPUT_APPROVED)
    approved_by_id = {r.get("approved_asset_id", ""): r for r in approved}
    rows = [evaluate(r, approved_by_id) for r in reqs]

    write_csv(OUT_CSV, rows, FIELDS)

    report = [
        "# HSD Player Image Fit Gate v1.8",
        "",
        f"Generated: {now()}",
        "",
        f"- checked: {len(rows)}",
        f"- approved: {sum(1 for r in rows if r['fit_status'] == 'approved')}",
        f"- review: {sum(1 for r in rows if r['fit_status'] == 'review')}",
        f"- blocked: {sum(1 for r in rows if r['fit_status'].startswith('blocked'))}",
        "",
        "This gate does not prove identity by face recognition. It catches sourcing/team-context risks and gives the graphics chat crop rules to avoid wrong-team jersey exposure.",
        "",
    ]
    for r in rows:
        report += [
            f"## {r['player_name']}",
            "",
            f"- Team: {r['team_name']}",
            f"- Status: **{r['fit_status']}**",
            f"- Usage mode: `{r['usage_mode']}`",
            f"- Risk: {r['risk_level']} | {r['risk_reasons'] or 'none'}",
            f"- Crop rule: {r['recommended_crop']}",
            "",
        ]
    Path(OUT_MD).write_text("\n".join(report), encoding="utf-8")
    Path(OUT_JSON).write_text(json.dumps({
        "version": VERSION,
        "generated_at_utc": now(),
        "counts": {
            "checked": len(rows),
            "approved": sum(1 for r in rows if r["fit_status"] == "approved"),
            "review": sum(1 for r in rows if r["fit_status"] == "review"),
            "blocked": sum(1 for r in rows if r["fit_status"].startswith("blocked")),
        },
        "outputs": [OUT_CSV, OUT_MD, OUT_JSON],
    }, indent=2), encoding="utf-8")

    # The sanitizer and upload pack read player_image_fit_gate.csv directly for crop guidance.

    print("Created HSD Player Image Fit Gate outputs")
    print(json.dumps(json.loads(Path(OUT_JSON).read_text()).get("counts", {}), indent=2))


if __name__ == "__main__":
    main()
