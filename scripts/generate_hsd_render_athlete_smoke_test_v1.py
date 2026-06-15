from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

import generate_hsd_mermaid_render_studio_v3_0 as base_render  # type: ignore
import generate_hsd_mermaid_render_studio_v3_0_2 as approved_render  # type: ignore

SMOKE_ROOT = Path("outputs/latest/review_files/athlete_smoke_test")
PACKET_DIR = SMOKE_ROOT / "packets"
RENDER_DIR = SMOKE_ROOT / "rendered_graphics"
ZIP_DIR = SMOKE_ROOT / "rendered_zips"
STATUS = SMOKE_ROOT / "rendered_handoff_status.csv"
MANIFEST = SMOKE_ROOT / "rendered_handoff_manifest.csv"
VISUAL_QA = SMOKE_ROOT / "rendered_handoff_visual_qa.csv"
REPORT = SMOKE_ROOT / "rendered_handoff_qa_report.md"
CONTACT = SMOKE_ROOT / "rendered_handoff_contact_sheet.jpg"
META = SMOKE_ROOT / "rendered_handoff_metadata.json"
SUMMARY = Path("outputs/latest/summary.json")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def write_smoke_packet() -> Path:
    PACKET_DIR.mkdir(parents=True, exist_ok=True)
    packet = {
        "packet_id": "athlete-smoke-test-approved-headshots",
        "slot": {
            "platform": "IG Feed",
            "headline": "Atlanta Dream beat Chicago Sky",
            "league": "WNBA",
            "content_type": "recap",
            "copy_hook": "Angel Reese and Rhyne Howard give Atlanta a real player-focus test for approved HSD headshots.",
            "first_comment": "Does this player-focus treatment feel ready for live WNBA packets?",
        },
        "public_copy": {
            "platform": "IG Feed",
            "headline": "Atlanta Dream beat Chicago Sky",
            "league": "WNBA",
            "content_type": "recap",
            "hook": "Angel Reese and Rhyne Howard give Atlanta a real player-focus test for approved HSD headshots.",
            "story_frame_text": "Angel Reese. Rhyne Howard. Approved image smoke test.",
            "caption": "Internal HSD render smoke test for approved WNBA athlete images.",
            "first": "Does this player-focus treatment feel ready for live WNBA packets?",
        },
    }
    out = PACKET_DIR / "athlete-smoke-test-approved-headshots.zip"
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("content_packet.json", json.dumps(packet, indent=2))
    return out


def main() -> None:
    if SMOKE_ROOT.exists():
        shutil.rmtree(SMOKE_ROOT)
    SMOKE_ROOT.mkdir(parents=True, exist_ok=True)
    write_smoke_packet()

    base_render.PACKET_DIRS = [PACKET_DIR]
    base_render.OUT_DIR = RENDER_DIR
    base_render.ZIP_DIR = ZIP_DIR
    base_render.STATUS = STATUS
    base_render.MANIFEST = MANIFEST
    base_render.VISUAL_QA = VISUAL_QA
    base_render.REPORT = REPORT
    base_render.CONTACT = CONTACT
    base_render.META = META

    approved_render.main()
    meta = read_json(META)
    summary = read_json(SUMMARY)
    summary.update({
        "athlete_smoke_test_rendered_packets": meta.get("rendered_packets", 0),
        "athlete_smoke_test_blocked_packets": meta.get("blocked_packets", 0),
        "athlete_smoke_test_packets_using_approved_athletes": meta.get("packets_using_approved_athletes", 0),
        "athlete_smoke_test_integrity_status": meta.get("integrity_status", "unknown"),
    })
    if SUMMARY.parent.exists():
        SUMMARY.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    smoke_report = SMOKE_ROOT / "athlete_smoke_test_report.md"
    smoke_report.write_text(
        "# HSD Approved Athlete Render Smoke Test v1\n\n"
        f"Generated: {now_iso()}\n\n"
        "## Expected\n\n"
        "- Render one internal WNBA test packet.\n"
        "- Use only approved athlete headshots.\n"
        "- Keep needs-fix athletes blocked.\n\n"
        "## Result\n\n"
        f"- rendered packets: {meta.get('rendered_packets', 0)}\n"
        f"- blocked packets: {meta.get('blocked_packets', 0)}\n"
        f"- packets using approved athletes: {meta.get('packets_using_approved_athletes', 0)}\n"
        f"- approved athlete images available: {meta.get('approved_athlete_count', 0)}\n"
        f"- needs-fix athletes blocked: {meta.get('needs_fix_athlete_count', 0)}\n"
        f"- integrity status: {meta.get('integrity_status', 'unknown')}\n",
        encoding="utf-8",
    )
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
