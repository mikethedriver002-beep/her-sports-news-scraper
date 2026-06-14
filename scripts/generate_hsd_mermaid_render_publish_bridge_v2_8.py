from __future__ import annotations

import csv
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

VERSION = "v2.8"
OUT_ROOT = Path("outputs/latest")
OUT_GRAPHICS = OUT_ROOT / "rendered_graphics"
OUT_ZIPS = OUT_ROOT / "rendered_zips"
OUT_FILES = OUT_ROOT / "review_files"

COPY_FILES = [
    "rendered_handoff_qa_report.md",
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

    summary = {
        "version": VERSION,
        "generated_at": now_iso(),
        "graphics_files": graphics_count,
        "zip_files": zip_count,
        "rendered_packets": len(rendered_rows),
        "blocked_packets": len(blocked_rows),
        "handoff_packets": len(handoff_rows),
        "content_slots": len(slots),
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
        "",
        "## Review order",
        "",
        "1. `review_files/rendered_handoff_qa_report.md`",
        "2. `review_files/rendered_handoff_contact_sheet.jpg`",
        "3. `review_files/rendered_handoff_status.csv`",
        "4. `rendered_graphics/`",
        "5. `rendered_zips/`",
        "",
        "## Notes",
        "",
        "- This folder is safe to commit for review.",
        "- It does not publish to Instagram or Threads.",
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
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(manifest)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
