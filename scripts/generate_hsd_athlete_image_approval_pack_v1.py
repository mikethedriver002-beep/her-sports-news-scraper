from __future__ import annotations

import csv
import json
import os
import shutil
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont

SRC = Path("data/asset_registry/wnba/athlete_image_match_review.csv")
OUT_ROOT = Path("outputs/latest/review_files/athlete_image_approval_pack")
DOWNLOAD_DIR = OUT_ROOT / "downloads"
SHEET_DIR = OUT_ROOT / "contact_sheets"
REPORT_MD = OUT_ROOT / "athlete_image_approval_pack_report.md"
MANIFEST_JSON = OUT_ROOT / "athlete_image_approval_pack_manifest.json"
DOWNLOAD_MANIFEST = OUT_ROOT / "download_manifest.csv"
APPROVAL_CSV = OUT_ROOT / "approval_decisions.csv"
SUMMARY = Path("outputs/latest/summary.json")

SAFE_HEADSHOT_PREFIX = "https://cdn.wnba.com/headshots/wnba/latest/260x190/"
MAX_DOWNLOADS = int(os.environ.get("HSD_ATHLETE_APPROVAL_PACK_MAX", "240"))

DOWNLOAD_FIELDS = ["team_id", "athlete_id", "display_name", "provider_player_id", "image_url", "download_status", "downloaded_file", "bytes", "reason"]
APPROVAL_FIELDS = ["decision", "team_id", "athlete_id", "display_name", "provider_player_id", "downloaded_file", "contact_sheet", "approval_target_path", "reviewer_notes"]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def safe_file_part(value: str) -> str:
    value = str(value or "").lower().strip()
    value = "".join(ch if ch.isalnum() or ch in {"_", "-"} else "_" for ch in value)
    return value.strip("_") or "unknown"


def valid_headshot_url(url: str) -> bool:
    return str(url or "").startswith(SAFE_HEADSHOT_PREFIX) and str(url or "").endswith(".png")


def download_one(row: Dict[str, str]) -> Dict[str, Any]:
    team_id = row.get("team_id", "")
    athlete_id = row.get("athlete_id", "")
    display_name = row.get("display_name", "")
    provider_player_id = row.get("provider_player_id", "")
    image_url = row.get("image_url", "")
    out_dir = DOWNLOAD_DIR / safe_file_part(team_id)
    out_file = out_dir / f"{safe_file_part(athlete_id)}__{safe_file_part(provider_player_id)}.png"
    base = {
        "team_id": team_id,
        "athlete_id": athlete_id,
        "display_name": display_name,
        "provider_player_id": provider_player_id,
        "image_url": image_url,
        "downloaded_file": out_file.as_posix(),
    }
    if not valid_headshot_url(image_url):
        return {**base, "download_status": "blocked", "bytes": 0, "reason": "non-wnba-headshot-url"}
    if out_file.exists() and out_file.stat().st_size > 100:
        return {**base, "download_status": "exists", "bytes": out_file.stat().st_size, "reason": ""}
    try:
        req = urllib.request.Request(image_url, headers={"User-Agent": "HerSportsDailyApprovalPack/1.0"})
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
        if len(data) < 100:
            return {**base, "download_status": "failed", "bytes": 0, "reason": "download too small"}
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file.write_bytes(data)
        return {**base, "download_status": "downloaded", "bytes": len(data), "reason": ""}
    except Exception as exc:
        return {**base, "download_status": "failed", "bytes": 0, "reason": f"{type(exc).__name__}: {exc}"}


def load_font(size: int) -> ImageFont.ImageFont:
    for path in ["/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf"]:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()


def make_contact_sheet(team_id: str, rows: List[Dict[str, Any]]) -> str:
    if not rows:
        return ""
    SHEET_DIR.mkdir(parents=True, exist_ok=True)
    cell_w, cell_h = 320, 320
    cols = 4
    rows_count = (len(rows) + cols - 1) // cols
    sheet = Image.new("RGB", (cell_w * cols, cell_h * rows_count), "white")
    draw = ImageDraw.Draw(sheet)
    font = load_font(18)
    small = load_font(14)
    for idx, row in enumerate(rows):
        x = (idx % cols) * cell_w
        y = (idx // cols) * cell_h
        draw.rectangle([x, y, x + cell_w - 1, y + cell_h - 1], outline=(210, 210, 210), width=2)
        img_path = Path(row.get("downloaded_file", ""))
        if img_path.exists():
            try:
                img = Image.open(img_path).convert("RGB")
                img.thumbnail((260, 190))
                ix = x + (cell_w - img.width) // 2
                sheet.paste(img, (ix, y + 18))
            except Exception:
                draw.text((x + 20, y + 80), "IMAGE ERROR", fill=(0, 0, 0), font=font)
        name = str(row.get("display_name", ""))[:34]
        pid = str(row.get("provider_player_id", ""))
        draw.text((x + 16, y + 222), name, fill=(0, 0, 0), font=font)
        draw.text((x + 16, y + 252), f"ID: {pid}", fill=(40, 40, 40), font=small)
        draw.text((x + 16, y + 274), str(row.get("athlete_id", ""))[:38], fill=(70, 70, 70), font=small)
    out = SHEET_DIR / f"{safe_file_part(team_id)}_contact_sheet.jpg"
    sheet.save(out, quality=88)
    return out.as_posix()


def update_summary(fields: Dict[str, Any]) -> None:
    summary = read_json(SUMMARY)
    summary.update(fields)
    if SUMMARY.parent.exists():
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")


def main() -> None:
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    rows = [r for r in read_csv(SRC) if r.get("status") == "needs_human_approval"][:MAX_DOWNLOADS]
    download_rows = [download_one(r) for r in rows]
    ok_rows = [r for r in download_rows if r.get("download_status") in {"downloaded", "exists"}]
    by_team: Dict[str, List[Dict[str, Any]]] = {}
    for row in ok_rows:
        by_team.setdefault(row.get("team_id", "unknown"), []).append(row)
    sheet_by_team: Dict[str, str] = {}
    for team_id, team_rows in sorted(by_team.items()):
        sheet_by_team[team_id] = make_contact_sheet(team_id, team_rows)
    approval_rows = []
    for row in ok_rows:
        team_id = row.get("team_id", "")
        approval_rows.append({
            "decision": "",
            "team_id": team_id,
            "athlete_id": row.get("athlete_id", ""),
            "display_name": row.get("display_name", ""),
            "provider_player_id": row.get("provider_player_id", ""),
            "downloaded_file": row.get("downloaded_file", ""),
            "contact_sheet": sheet_by_team.get(team_id, ""),
            "approval_target_path": f"assets/leagues/wnba/athletes/{row.get('athlete_id', '')}/headshot.png",
            "reviewer_notes": "",
        })
    write_csv(DOWNLOAD_MANIFEST, download_rows, DOWNLOAD_FIELDS)
    write_csv(APPROVAL_CSV, approval_rows, APPROVAL_FIELDS)
    report = {
        "version": "hsd-athlete-image-approval-pack-v1",
        "generated_at_utc": now_iso(),
        "source_rows": len(rows),
        "downloaded_or_existing": len(ok_rows),
        "failed_or_blocked": len(download_rows) - len(ok_rows),
        "approval_rows": len(approval_rows),
        "contact_sheets": len(sheet_by_team),
        "output_root": OUT_ROOT.as_posix(),
        "download_manifest": DOWNLOAD_MANIFEST.as_posix(),
        "approval_csv": APPROVAL_CSV.as_posix(),
        "sheets": sheet_by_team,
    }
    MANIFEST_JSON.write_text(json.dumps(report, indent=2), encoding="utf-8")
    lines = [
        "# HSD Athlete Image Approval Pack v1",
        "",
        f"Generated: {report['generated_at_utc']}",
        "",
        "## Counts",
        "",
        f"- source match rows: {report['source_rows']}",
        f"- downloaded or existing: {report['downloaded_or_existing']}",
        f"- failed or blocked: {report['failed_or_blocked']}",
        f"- approval rows: {report['approval_rows']}",
        f"- contact sheets: {report['contact_sheets']}",
        "",
        "## Review files",
        "",
        f"- `{APPROVAL_CSV.as_posix()}`",
        f"- `{DOWNLOAD_MANIFEST.as_posix()}`",
        "- `outputs/latest/review_files/athlete_image_approval_pack/contact_sheets/`",
        "",
        "## Usage policy",
        "",
        "- This is a review-only approval pack.",
        "- Nothing here is public-use approved automatically.",
        "- To approve an image later, the reviewed file must be copied to its approval target path and an `.approved` marker must exist.",
    ]
    REPORT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    update_summary({
        "athlete_approval_pack_rows": len(approval_rows),
        "athlete_approval_pack_downloaded": len(ok_rows),
        "athlete_approval_pack_failed_or_blocked": len(download_rows) - len(ok_rows),
        "athlete_approval_pack_contact_sheets": len(sheet_by_team),
    })
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
