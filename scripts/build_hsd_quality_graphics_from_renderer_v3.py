from __future__ import annotations

import csv
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

VERSION = "v1.1-quality-from-template-renderer-v3"
V3 = Path("outputs/latest/HSD_TEMPLATE_FACTORY/template_renderer_v3")
V3_MANIFEST = V3 / "hsd_template_renderer_v3_manifest.csv"
V3_AUDIT = V3 / "hsd_template_renderer_v3_logo_audit.json"
CONTRACT = Path("results_contract_v2.csv")
OUT = Path("outputs/latest/HSD_QUALITY_GRAPHICS")
MANIFEST = Path("hsd_quality_graphics_manifest.csv")
REPORT = Path("hsd_quality_graphics_report.md")
FIELDS = [
    "event_id",
    "platform",
    "row_kind",
    "headline",
    "variant",
    "player_mode",
    "player_names",
    "player_assets_used",
    "renderer_source",
    "output_path",
    "width",
    "height",
    "used_home_logo",
    "used_away_logo",
    "status",
    "notes",
]


def clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", clean(value).lower())


def slug(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", clean(value).lower()).strip("-") or "item"


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def loaded_teams() -> set[str]:
    try:
        payload = json.loads(V3_AUDIT.read_text(encoding="utf-8"))
    except Exception:
        return set()
    return {
        norm(row.get("team"))
        for row in payload.get("rows", [])
        if row.get("status") == "loaded" and norm(row.get("team"))
    }


def source_index() -> dict[str, dict[str, str]]:
    output: dict[str, dict[str, str]] = {}
    for row in read_csv(CONTRACT):
        for key in ["event_id", "dedupe_key", "event_uid", "canonical_key"]:
            value = clean(row.get(key))
            if value:
                output[value] = row
    return output


def main() -> None:
    source = source_index()
    loaded = loaded_teams()
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir(parents=True, exist_ok=True)
    promoted: list[dict[str, Any]] = []

    for row in read_csv(V3_MANIFEST):
        item_id = clean(row.get("item_id"))
        if item_id.startswith("batch::"):
            continue
        event_id = item_id.split("::", 1)[0]
        src = source.get(event_id, {})
        source_path = Path(clean(row.get("output_path")))
        if not source_path.exists():
            continue
        platform = clean(row.get("platform"))
        variant = clean(row.get("variant")) or "logos_only"
        target_dir = OUT / platform
        target_dir.mkdir(parents=True, exist_ok=True)
        target = target_dir / f"{slug(row.get('headline'))}__{variant}.png"
        shutil.copy2(source_path, target)
        home = clean(src.get("home_team_name") or src.get("home_team_display"))
        away = clean(src.get("away_team_name") or src.get("away_team_display"))
        winner = clean(src.get("winner_team_name") or src.get("winner"))
        loser = clean(src.get("loser_team_name") or src.get("loser"))
        home_logo = norm(home) in loaded or (not home and norm(winner) in loaded)
        away_logo = norm(away) in loaded or (not away and norm(loser) in loaded)
        promoted.append({
            "event_id": event_id,
            "platform": platform,
            "row_kind": clean(src.get("row_kind")) or ("preview" if "tonight_in_the_w" in clean(row.get("template_id")) else "result"),
            "headline": clean(row.get("headline")),
            "variant": variant,
            "player_mode": clean(row.get("player_mode")),
            "player_names": clean(row.get("player_names")),
            "player_assets_used": clean(row.get("player_assets_used")),
            "renderer_source": "template_renderer_v3",
            "output_path": target.as_posix(),
            "width": clean(row.get("width")),
            "height": clean(row.get("height")),
            "used_home_logo": "yes" if home_logo else "no",
            "used_away_logo": "yes" if away_logo else "no",
            "status": "rendered",
            "notes": "Cinematic renderer v3.2 output; Phase 5 visual approval required",
        })

    write_csv(MANIFEST, promoted)
    logos_only = sum(row["variant"] == "logos_only" for row in promoted)
    with_players = sum(row["variant"] == "with_players" for row in promoted)
    REPORT.write_text("\n".join([
        "# HSD Quality Graphics — Renderer v3.2",
        "",
        f"Generated: `{datetime.now(timezone.utc).isoformat()}`",
        f"Version: `{VERSION}`",
        "",
        f"- Promoted: `{len(promoted)}`",
        f"- Logos-only: `{logos_only}`",
        f"- With players: `{with_players}`",
        "- Source: Template Renderer v3.2.",
        "- Human visual approval is required.",
        "",
    ]), encoding="utf-8")
    print(json.dumps({
        "version": VERSION,
        "promoted": len(promoted),
        "logos_only": logos_only,
        "with_players": with_players,
        "quality_dir": OUT.as_posix(),
    }, indent=2))


if __name__ == "__main__":
    main()
