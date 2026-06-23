from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REGISTRY = Path("data/asset_registry/wnba/team_logos.csv")
PATCH = Path("data/asset_registry/wnba/phase8a_exact_logo_sources.csv")
OUT_JSON = Path("phase8a_asset_registry_repair_report.json")
OUT_MD = Path("phase8a_asset_registry_repair_report.md")

FIELDS = ["team_id", "asset_type", "file_path", "file_exists", "approved", "required", "last_verified_utc", "source_note"]


def clean(value: Any) -> str:
    return str(value or "").strip()


def read_csv(path: Path) -> List[Dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: List[Dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in FIELDS})


def main() -> int:
    rows = read_csv(REGISTRY)
    patch_rows = {clean(row.get("team_id")): row for row in read_csv(PATCH)}
    changed: List[str] = []
    now = datetime.now(timezone.utc).isoformat()
    by_team = {clean(row.get("team_id")): row for row in rows}
    sparks = patch_rows.get("los_angeles_sparks")
    if sparks:
        target = clean(sparks.get("preferred_path")) or "assets/leagues/wnba/teams/los_angeles_sparks/logo.png"
        path = Path(target)
        existing = by_team.get("los_angeles_sparks")
        if existing:
            if clean(existing.get("file_path")) != target or clean(existing.get("approved")).lower() != "true":
                existing.update({"file_path": target, "file_exists": "true" if path.exists() else clean(existing.get("file_exists")) or "false", "approved": "true", "required": "true", "last_verified_utc": now, "source_note": "phase8a_sparks_exact_logo_repair"})
                changed.append("updated_los_angeles_sparks")
        else:
            rows.append({"team_id": "los_angeles_sparks", "asset_type": "primary_logo", "file_path": target, "file_exists": "true" if path.exists() else "false", "approved": "true" if path.exists() else "false", "required": "true", "last_verified_utc": now, "source_note": "phase8a_sparks_exact_logo_repair"})
            changed.append("inserted_los_angeles_sparks")
        write_csv(REGISTRY, rows)
    report = {"version": "v1.0-phase8a-asset-registry-repair", "generated_at_utc": now, "changed": changed, "registry_path": REGISTRY.as_posix(), "sparks_row_present": "los_angeles_sparks" in {clean(row.get("team_id")) for row in rows}}
    OUT_JSON.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    OUT_MD.write_text("# HSD Phase 8A Asset Registry Repair\n\n" + "\n".join([f"- `{value}`" for value in changed] or ["- No registry changes required"]) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
