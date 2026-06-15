from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v2.8.5-athlete-registry-review"
OUT_ROOT = Path("outputs/latest")
OUT_GRAPHICS = OUT_ROOT / "rendered_graphics"
OUT_ZIPS = OUT_ROOT / "rendered_zips"
OUT_FILES = OUT_ROOT / "review_files"

COPY_FILES = [
    "rendered_handoff_qa_report.md",
    "rendered_handoff_visual_qa.csv",
    "rendered_handoff_manifest.csv",
    "rendered_handoff_status.csv",
    "rendered_handoff_metadata.json",
    "rendered_handoff_contact_sheet.jpg",
    "assignment_handoff_report.md",
    "assignment_handoff_index.csv",
    "assignment_handoff_status.csv",
    "assignment_handoff_publisher_report.md",
    "assignment_handoff_publisher_manifest.json",
    "manual_workflow_handoff.md",
    "manual_workflow_content_packets.csv",
    "manual_workflow_pack_status.csv",
    "operator_command_center.md",
    "operator_command_center.json",
    "mermaid_upper_echelon_report.md",
    "mermaid_master_content_board.md",
    "mermaid_content_slots_v2.csv",
    "ig_feed_queue_v2.csv",
    "ig_story_queue_v2.csv",
    "threads_queue_v2.csv",
    "data/asset_registry/wnba/teams.csv",
    "data/asset_registry/wnba/team_aliases.csv",
    "data/asset_registry/wnba/team_logos.csv",
    "data/asset_registry/wnba/logo_sources.csv",
    "data/asset_registry/wnba/logo_fetch_report.json",
    "data/asset_registry/wnba/logo_fetch_report.md",
    "data/asset_registry/wnba/logo_gap_upload_manifest.csv",
    "data/asset_registry/wnba/missing_team_logos.csv",
    "data/asset_registry/wnba/athlete_sources.csv",
    "data/asset_registry/wnba/athletes.csv",
    "data/asset_registry/wnba/athlete_aliases.csv",
    "data/asset_registry/wnba/athlete_images.csv",
    "data/asset_registry/wnba/athlete_image_candidates.csv",
    "data/asset_registry/wnba/missing_athlete_images.csv",
    "data/asset_registry/wnba/athlete_registry_report.json",
    "data/asset_registry/wnba/athlete_registry_report.md",
    "data/asset_registry/wnba/roster_entities.csv",
    "data/asset_registry/wnba/roster_names.csv",
    "data/asset_registry/wnba/asset_registry_summary.json",
    "data/asset_registry/wnba/asset_registry_report.md",
    "data/asset_registry/wnba/asset_registry_validation.json",
    "data/asset_registry/wnba/asset_registry_validation_report.md",
    "data/asset_registry/wnba/asset_gap_report.json",
    "data/asset_registry/wnba/asset_gap_report.md",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_csv(path: str | Path) -> List[Dict[str, str]]:
    p = Path(path)
    if not p.exists():
        return []
    try:
        with p.open(newline="", encoding="utf-8", errors="replace") as f:
            return list(csv.DictReader(f))
    except Exception:
        return []


def read_json(path: str | Path) -> Dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def copy_file(src: str | Path, dst_dir: Path, manifest: List[Dict[str, Any]]) -> None:
    p = Path(src)
    if not p.exists() or not p.is_file():
        return
    dst_dir.mkdir(parents=True, exist_ok=True)
    dest = dst_dir / p.name
    shutil.copy2(p, dest)
    manifest.append({"source": p.as_posix(), "dest": dest.as_posix(), "size": p.stat().st_size})


def copy_tree(src: str | Path, dst: Path, manifest: List[Dict[str, Any]]) -> int:
    root = Path(src)
    if not root.exists() or not root.is_dir():
        return 0
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    count = 0
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        rel = p.relative_to(root)
        dest = dst / rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, dest)
        manifest.append({"source": p.as_posix(), "dest": dest.as_posix(), "size": p.stat().st_size})
        count += 1
    return count


def main() -> None:
    if OUT_ROOT.exists():
        shutil.rmtree(OUT_ROOT)
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    manifest: List[Dict[str, Any]] = []
    for name in COPY_FILES:
        copy_file(name, OUT_FILES, manifest)
    graphics_count = copy_tree("rendered_handoff_graphics", OUT_GRAPHICS, manifest)
    zip_count = copy_tree("rendered_handoff_zips", OUT_ZIPS, manifest)

    rendered_status = read_csv("rendered_handoff_status.csv")
    rendered_rows = [r for r in rendered_status if r.get("status") == "rendered"]
    blocked_rows = [r for r in rendered_status if r.get("status") == "blocked"]
    handoff_rows = read_csv("assignment_handoff_index.csv") or read_csv("manual_workflow_content_packets.csv")
    slots = read_csv("mermaid_content_slots_v2.csv")
    missing_logos = read_csv("data/asset_registry/wnba/missing_team_logos.csv")
    team_logos = read_csv("data/asset_registry/wnba/team_logos.csv")
    logo_fetch = read_json("data/asset_registry/wnba/logo_fetch_report.json")
    athlete_report = read_json("data/asset_registry/wnba/athlete_registry_report.json")

    summary = {
        "version": VERSION,
        "generated_at": now_iso(),
        "graphics_files": graphics_count,
        "zip_files": zip_count,
        "rendered_packets": len(rendered_rows),
        "blocked_packets": len(blocked_rows),
        "handoff_packets": len(handoff_rows),
        "content_slots": len(slots),
        "verified_team_logos": len([r for r in team_logos if r.get("file_exists") == "true"]),
        "missing_team_logos": len(missing_logos),
        "logo_sources": logo_fetch.get("sources", 0),
        "logos_downloaded": logo_fetch.get("downloaded", 0),
        "logos_existing": logo_fetch.get("existing", 0),
        "logos_failed": logo_fetch.get("failed", 0),
        "athlete_sources": athlete_report.get("source_count", 0),
        "athlete_sources_ok": athlete_report.get("sources_ok", 0),
        "athletes": athlete_report.get("athletes", 0),
        "athlete_image_candidates": athlete_report.get("image_candidates", 0),
        "approved_athlete_images": athlete_report.get("approved_images", 0),
        "missing_approved_athlete_images": athlete_report.get("missing_approved_images", 0),
        "outputs_root": OUT_ROOT.as_posix(),
    }
    (OUT_ROOT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")

    lines = [
        "# HSD Mermaid Latest Review",
        "",
        f"Generated: {summary['generated_at']}",
        f"Version: Mermaid Render Publish Bridge {VERSION}",
        "",
        "## Counts",
        "",
        f"- rendered packets: {summary['rendered_packets']}",
        f"- blocked packets: {summary['blocked_packets']}",
        f"- handoff packets: {summary['handoff_packets']}",
        f"- content slots: {summary['content_slots']}",
        f"- graphics files copied: {summary['graphics_files']}",
        f"- rendered zip files copied: {summary['zip_files']}",
        f"- verified WNBA team logos: {summary['verified_team_logos']}",
        f"- missing WNBA team logos: {summary['missing_team_logos']}",
        f"- logo sources: {summary['logo_sources']}",
        f"- logos downloaded: {summary['logos_downloaded']}",
        f"- logos existing: {summary['logos_existing']}",
        f"- logos failed: {summary['logos_failed']}",
        f"- athlete sources: {summary['athlete_sources']}",
        f"- athlete sources ok: {summary['athlete_sources_ok']}",
        f"- athletes discovered: {summary['athletes']}",
        f"- athlete image candidates: {summary['athlete_image_candidates']}",
        f"- approved athlete images: {summary['approved_athlete_images']}",
        "",
        "## Review order",
        "",
        "1. `review_files/rendered_handoff_qa_report.md`",
        "2. `review_files/rendered_handoff_visual_qa.csv`",
        "3. `review_files/athlete_registry_report.md`",
        "4. `review_files/athlete_image_candidates.csv`",
        "5. `review_files/logo_fetch_report.md`",
        "6. `review_files/asset_registry_report.md`",
        "7. `review_files/asset_gap_report.md`",
        "8. `review_files/rendered_handoff_contact_sheet.jpg`",
        "9. `rendered_graphics/`",
        "10. `rendered_zips/`",
        "",
        "## Notes",
        "",
        "- This folder is safe to commit for review.",
        "- It does not publish to Instagram or Threads.",
        "- WNBA team logos are required for team-led WNBA graphics.",
        "- Athlete image candidates are review-only and are not used in public graphics automatically.",
        "- Review before posting.",
        "",
    ]
    if blocked_rows:
        lines += ["## Blocked packets", ""]
        for r in blocked_rows:
            lines.append(f"- {r.get('packet_id')}: {r.get('reason')}")
        lines.append("")
    if rendered_rows:
        lines += ["## Rendered packets", ""]
        for r in rendered_rows:
            lines.append(f"- {r.get('packet_id')}: {r.get('headline')}")
        lines.append("")
    (OUT_ROOT / "README.md").write_text("\n".join(lines), encoding="utf-8")
    with (OUT_ROOT / "publish_manifest.csv").open("w", newline="", encoding="utf-8") as f:
        fields = ["source", "dest", "size"]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(manifest)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
