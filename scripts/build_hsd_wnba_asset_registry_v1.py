from __future__ import annotations

import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, UnidentifiedImageError

ROOT = Path("data/asset_registry/wnba")
TEAMS = ROOT / "teams.csv"
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


def slug(value: str, sep: str = "_") -> str:
    return re.sub(r"[^a-z0-9]+", sep, clean(value).lower()).strip(sep)


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


def asset_decodable(path: Path) -> bool:
    if not path.exists() or not path.is_file() or path.stat().st_size <= 100:
        return False
    if path.suffix.lower() == ".svg":
        try:
            text = path.read_text(encoding="utf-8", errors="ignore").lower()
        except Exception:
            return False
        if "<svg" not in text:
            return False
        try:
            import cairosvg
            cairosvg.svg2png(url=path.as_posix(), bytestring=None, output_width=64, output_height=64)
        except TypeError:
            pass
        except Exception:
            return False
        return True
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            image.convert("RGBA")
        return True
    except (UnidentifiedImageError, OSError, ValueError, SyntaxError):
        return False


def asset_files() -> List[Path]:
    files: List[Path] = []
    for root in SCAN_ROOTS:
        if not root.exists():
            continue
        for path in root.rglob("*"):
            if path.is_file() and path.suffix.lower() in ASSET_EXTS and asset_decodable(path):
                files.append(path)
    return files


def identity_match(team: Dict[str, str], path: Path) -> bool:
    low = path.as_posix().lower()
    team_id = clean(team.get("team_id"))
    team_name = clean(team.get("team_name"))
    slug_under = slug(team_name, "_")
    slug_dash = slug(team_name, "-")
    words = [w.lower() for w in re.findall(r"[A-Za-z0-9]+", team_name)]
    if team_id and (team_id.lower() in low or team_id.replace("_", "-").lower() in low):
        return True
    if slug_under and slug_under in low:
        return True
    if slug_dash and slug_dash in low:
        return True
    if len(words) >= 2 and all(word in low for word in words):
        return True
    return False


def score_asset(team: Dict[str, str], path: Path) -> int:
    if not asset_decodable(path) or not identity_match(team, path):
        return -999
    low = path.as_posix().lower()
    score = 100
    if "logo" in low:
        score += 40
    if "primary" in low:
        score += 20
    if path.suffix.lower() == ".png":
        score += 12
    if path.suffix.lower() == ".svg":
        score += 8
    if "player" in low or "headshot" in low or "cutout" in low or "img_" in low:
        score -= 160
    if "watermark" in low:
        score -= 160
    return score


def find_logo(team: Dict[str, str], files: List[Path]) -> Optional[Path]:
    preferred = Path("assets/leagues/wnba/teams") / clean(team.get("team_id")) / "logo.png"
    if asset_decodable(preferred):
        return preferred
    preferred_svg = preferred.with_suffix(".svg")
    if asset_decodable(preferred_svg):
        return preferred_svg
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
        if logo_path and asset_decodable(logo_path):
            verified += 1
            logo_rows.append({"team_id": team_id, "asset_type": "primary_logo", "file_path": logo_path.as_posix(), "file_exists": "true", "approved": "true", "image_decodable": "true", "required": "true", "last_verified_utc": now_iso(), "source_note": "strict_exact_identity_match_image_decodable"})
        else:
            recommended = f"assets/leagues/wnba/teams/{team_id}/logo.png"
            logo_rows.append({"team_id": team_id, "asset_type": "primary_logo", "file_path": recommended, "file_exists": "false", "approved": "false", "image_decodable": "false", "required": "true", "last_verified_utc": now_iso(), "source_note": "missing_required_exact_decodable_logo"})
            missing_rows.append({"team_id": team_id, "team_name": team_name, "required_asset": "primary_logo", "reason": "required exact team logo file not found or not image-decodable", "recommended_path": recommended})
    write_csv(TEAM_LOGOS, logo_rows, ["team_id", "asset_type", "file_path", "file_exists", "approved", "image_decodable", "required", "last_verified_utc", "source_note"])
    write_csv(MISSING_TEAM_LOGOS, missing_rows, ["team_id", "team_name", "required_asset", "reason", "recommended_path"])
    summary = {"version": "hsd-wnba-asset-registry-v1.2-strict-decodable", "generated_at_utc": now_iso(), "teams": len(teams), "team_logos_verified": verified, "missing_team_logos": len(missing_rows), "team_logo_policy": "required_exact_identity_match_image_decodable", "scan_roots": [p.as_posix() for p in SCAN_ROOTS]}
    SUMMARY_JSON.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    lines = ["# HSD WNBA Asset Registry v1.2", "", f"Generated: {summary['generated_at_utc']}", "", "## Counts", "", f"- teams: {summary['teams']}", f"- team logos verified: {summary['team_logos_verified']}", f"- missing required team logos: {summary['missing_team_logos']}", "", "## Missing team logos", ""]
    lines += [f"- {row['team_name']} -> `{row['recommended_path']}`" for row in missing_rows] if missing_rows else ["- None"]
    SUMMARY_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
