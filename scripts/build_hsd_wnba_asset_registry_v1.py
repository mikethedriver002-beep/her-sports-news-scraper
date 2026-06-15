from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

ROOT = Path("data/asset_registry/wnba")
TEAMS = ROOT / "teams.csv"
ALIASES = ROOT / "team_aliases.csv"
TEAM_LOGOS = ROOT / "team_logos.csv"
MISSING_TEAM_LOGOS = ROOT / "missing_team_logos.csv"
SUMMARY_JSON = ROOT / "asset_registry_summary.json"
SUMMARY_MD = ROOT / "asset_registry_report.md"
ASSET_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".svg"}
SCAN_ROOTS = [
    Path("assets/leagues/wnba/teams"),
    Path("assets"),
    Path("brand_assets"),
    Path("data/assets/approved"),
    Path("graphics_chat_upload_pack"),
    Path("ig_story_results_upload_pack"),
    Path("hsd_pipeline_lite_review"),
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", clean(value).lower()).strip("_")


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))


def write_csv(path: Path, rows: List[Dict[str, Any]], fields: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def asset_files() -> List[Path]:
    files: List[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in ASSET_EXTS:
                files.append(path)
    return files


def score_asset(team: Dict[str, str], path: Path) -> int:
    low = path.as_posix().lower()
    team_name = clean(team.get("team_name"))
    team_id = clean(team.get("team_id"))
    nick = clean(team.get("nickname"))
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", team_name)]
    score = 0
    if team_id and team_id.lower() in low:
        score += 120
    if slug(team_name).replace("_", "-") in low or slug(team_name) in low:
        score += 105
    if words and all(word in low for word in words):
        score += 85
    if nick and nick.lower() in low:
        score += 40
    if "logo" in low or "primary" in low:
        score += 40
    if "player" in low or "headshot" in low or "cutout" in low or "img_" in low:
        score -= 120
    if "watermark" in low or "brand" in low and "wnba" not in low:
        score -= 80
    return score


def find_logo(team: Dict[str, str], files: List[Path]) -> Optional[Path]:
    preferred = Path("assets/leagues/wnba/teams") / clean(team.get("team_id")) / "logo.png"
    if preferred.exists():
        return preferred
    candidates: List[Tuple[int, int, Path]] = []
    for path in files:
        score = score_asset(team, path)
        if score > 0:
            candidates.append((score, -len(path.as_posix()), path))
    if not candidates:
        return None
    candidates.sort(reverse=True)
    return candidates[0][2]


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    teams = read_csv(TEAMS)
    files = asset_files()
    logo_rows: List[Dict[str, Any]] = []
    missing_rows: List[Dict[str, Any]] = []
    verified = 0
    for team in teams:
        team_id = clean(team.get("team_id"))
        team_name = clean(team.get("team_name"))
        logo_path = find_logo(team, files)
        if logo_path:
            verified += 1
            logo_rows.append({
                "team_id": team_id,
                "asset_type": "primary_logo",
                "file_path": logo_path.as_posix(),
                "file_exists": "true",
                "approved": "true",
                "required": "true",
                "last_verified_utc": now_iso(),
                "source_note": "resolved_by_hsd_wnba_asset_registry_v1",
            })
        else:
            recommended = f"assets/leagues/wnba/teams/{team_id}/logo.png"
            logo_rows.append({
                "team_id": team_id,
                "asset_type": "primary_logo",
                "file_path": recommended,
                "file_exists": "false",
                "approved": "false",
                "required": "true",
                "last_verified_utc": now_iso(),
                "source_note": "missing_required_exact_logo",
            })
            missing_rows.append({
                "team_id": team_id,
                "team_name": team_name,
                "required_asset": "primary_logo",
                "reason": "required exact team logo file not found",
                "recommended_path": recommended,
            })
    write_csv(TEAM_LOGOS, logo_rows, ["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "last_verified_utc", "source_note"])
    write_csv(MISSING_TEAM_LOGOS, missing_rows, ["team_id", "team_name", "required_asset", "reason", "recommended_path"])
    summary = {
        "version": "hsd-wnba-asset-registry-v1",
        "generated_at_utc": now_iso(),
        "teams": len(teams),
        "team_logos_verified": verified,
        "missing_team_logos": len(missing_rows),
        "team_logo_policy": "required_for_team_graphics",
        "scan_roots": [p.as_posix() for p in SCAN_ROOTS],
    }
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = [
        "# HSD WNBA Asset Registry v1",
        "",
        f"Generated: {summary['generated_at_utc']}",
        "",
        "## Counts",
        "",
        f"- teams: {summary['teams']}",
        f"- team logos verified: {summary['team_logos_verified']}",
        f"- missing required team logos: {summary['missing_team_logos']}",
        "",
        "## Missing team logos",
        "",
    ]
    if missing_rows:
        for row in missing_rows:
            lines.append(f"- {row['team_name']} -> `{row['recommended_path']}`")
    else:
        lines.append("- None")
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
