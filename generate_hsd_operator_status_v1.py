from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

OUT = Path("operator_status.md")

def read_csv(path: str):
    p = Path(path)
    if not p.exists():
        return []
    with p.open(newline="", encoding="utf-8", errors="replace") as f:
        return list(csv.DictReader(f))

def main():
    packs = read_csv("graphics_upload_pack_status.csv")
    ready = [p for p in packs if p.get("upload_pack_status") in {"ready", "ready_with_review"}]
    blocked = [p for p in packs if p.get("upload_pack_status") not in {"ready", "ready_with_review"}]
    reqs = read_csv("player_image_requirements.csv")
    fake_preview_people = [r for r in reqs if "preview" in r.get("bundle_slug", "") and r.get("player_name")]
    status = "GO" if ready and not fake_preview_people else "REVIEW"
    lines = [
        "# HSD Operator Status",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"## Status: {status}",
        "",
        f"- Ready upload packs: {len(ready)}",
        f"- Blocked upload packs: {len(blocked)}",
        f"- Preview player/person false positives: {len(fake_preview_people)}",
        "",
    ]
    if ready:
        lines += ["## Ready to send to graphics chat", ""]
        for p in ready:
            lines.append(f"- {p.get('bundle_name')} | {p.get('upload_pack_status')} | `{p.get('zip_path')}`")
        lines.append("")
    if fake_preview_people:
        lines += ["## Fix before posting", ""]
        for r in fake_preview_people:
            lines.append(f"- Preview false person: {r.get('player_name')} in {r.get('bundle_slug')}")
        lines.append("")
    OUT.write_text("\n".join(lines), encoding="utf-8")
    print("Created operator_status.md")

if __name__ == "__main__":
    main()
