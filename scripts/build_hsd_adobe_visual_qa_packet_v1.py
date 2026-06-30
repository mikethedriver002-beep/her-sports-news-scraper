from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir


VERSION = "hsd-adobe-visual-qa-packet-v1-review-only"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
PACKET_DIR_NAME = "adobe_visual_qa_packet"
GENERATED_BY = "scripts/build_hsd_adobe_visual_qa_packet_v1.py"

WORKSHEET_FIELDS = [
    "format",
    "crop_fit",
    "title_safety",
    "score_rail_dashboard_violation",
    "lower_stat_strip_violation",
    "logo_readiness",
    "action_photo_suitability",
    "operator_decision",
    "revision_request",
    "operator_notes",
]

WORKSHEET_FORMATS = [
    "ig_feed_4x5",
    "ig_story_9x16",
    "square_1x1",
    "contact_sheet",
]

DECISION_VOCABULARY = [
    "hold",
    "revise",
    "approve_for_manual_next_step",
]

FORBIDDEN_DECISION_VALUES = [
    "approved",
    "publish_ready",
    "render_ready",
]

DRAFT_INPUTS = [
    {
        "source": "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png",
        "target": "drafts/draft_preview_ig_feed.png",
        "role": "ig_feed_4x5_draft",
    },
    {
        "source": "render_handoff_top_packet/review_drafts/draft_preview_story.png",
        "target": "drafts/draft_preview_story.png",
        "role": "ig_story_9x16_draft",
    },
    {
        "source": "render_handoff_top_packet/review_drafts/draft_preview_square.png",
        "target": "drafts/draft_preview_square.png",
        "role": "square_1x1_draft",
    },
    {
        "source": "render_handoff_top_packet/review_drafts/draft_preview_visual_contact_sheet.png",
        "target": "drafts/draft_preview_visual_contact_sheet.png",
        "role": "visual_contact_sheet",
    },
]

REFERENCE_INPUTS = [
    {
        "source": "render_handoff_top_packet/handoff_manifest.json",
        "target": "references/handoff_manifest.json",
        "role": "render_handoff_manifest",
    },
    {
        "source": "manual_visual_qa_manifest.json",
        "target": "references/manual_visual_qa_manifest.json",
        "role": "manual_visual_qa_manifest",
    },
    {
        "source": "manual_visual_qa_checklist.csv",
        "target": "references/manual_visual_qa_checklist.csv",
        "role": "manual_visual_qa_checklist",
    },
    {
        "source": "render_visual_revision_plan.md",
        "target": "references/render_visual_revision_plan.md",
        "role": "render_visual_revision_plan",
    },
    {
        "source": "render_visual_delta_report.md",
        "target": "references/render_visual_delta_report.md",
        "role": "render_visual_delta_report",
    },
    {
        "source": "render_next_level_editorial_qa.md",
        "target": "references/render_next_level_editorial_qa.md",
        "role": "render_next_level_editorial_qa",
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return str(value or "").strip()


def git_head() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "--short", "HEAD"], text=True).strip()
    except Exception:
        return "unknown"


def packet_root() -> Path:
    if run_output_dir():
        return output_path(PACKET_DIR_NAME).resolve()
    return output_path(LATEST_FILES_ROOT / PACKET_DIR_NAME).resolve()


def source_candidates(relative_path: str | Path) -> list[Path]:
    rel = Path(relative_path)
    candidates: list[Path] = []
    run_root = run_output_dir()
    if run_root:
        candidates.append(run_root / rel)
    candidates.append(LATEST_FILES_ROOT / rel)
    candidates.append(rel)
    return candidates


def find_source(relative_path: str | Path) -> Path | None:
    for candidate in source_candidates(relative_path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return None


def expected_inputs() -> list[dict[str, str]]:
    return [*DRAFT_INPUTS, *REFERENCE_INPUTS]


def worksheet_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for format_name in WORKSHEET_FORMATS:
        rows.append(
            {
                "format": format_name,
                "crop_fit": "operator_fill_required",
                "title_safety": "operator_fill_required",
                "score_rail_dashboard_violation": "operator_fill_required",
                "lower_stat_strip_violation": "operator_fill_required",
                "logo_readiness": "operator_fill_required",
                "action_photo_suitability": "operator_fill_required",
                "operator_decision": "operator_fill_required",
                "revision_request": "",
                "operator_notes": "",
            }
        )
    return rows


def write_csv(path: Path, rows: Iterable[dict[str, str]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def write_json(path: Path, payload: Any) -> None:
    write_text(path, json.dumps(payload, indent=2, sort_keys=True))


def copy_required_inputs(packet_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    included: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    for item in expected_inputs():
        source_rel = item["source"]
        packet_rel = item["target"]
        source = find_source(source_rel)
        if not source:
            missing.append(
                {
                    "path": source_rel,
                    "packet_path": packet_rel,
                    "role": item["role"],
                    "issue": "missing_required_input",
                }
            )
            continue
        target = packet_dir / packet_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        included.append(
            {
                "path": source_rel,
                "source_path": str(source),
                "packet_path": packet_rel,
                "role": item["role"],
                "bytes": str(target.stat().st_size),
            }
        )
    return included, missing


def render_open_packet_script() -> str:
    return """$ErrorActionPreference = "Stop"
$PacketRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process explorer.exe -ArgumentList $PacketRoot
Write-Host "Opened HSD Adobe visual QA packet:"
Write-Host $PacketRoot
Write-Host "Optional manual step: open this same folder from Adobe Bridge or Photoshop. This script does not edit images or change approval state."
"""


def render_readme(payload: dict[str, Any]) -> str:
    included_lines = "\n".join(f"- `{item['packet_path']}` from `{item['path']}`" for item in payload["included_files"])
    missing_lines = "\n".join(f"- `{item['path']}` -> `{item['packet_path']}`" for item in payload["missing_required_inputs"])
    missing_block = missing_lines or "- None"
    return f"""# HSD Adobe-Assisted Manual Visual QA Packet

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This packet is a review-only local folder for human visual inspection in Adobe Bridge, Photoshop, or Explorer. It copies the current render drafts, contact sheet, handoff manifest, visual QA checklist, and revision references into one place.

## Open

From this folder, run:

```powershell
powershell -ExecutionPolicy Bypass -File .\\open_packet_in_explorer.ps1
```

Then open `drafts/` in Adobe Bridge or Photoshop if you want the Adobe review view.

## Review Questions

For each row in `manual_adobe_visual_qa_intake.csv`, answer these exact questions:

- `crop_fit`: Does the crop fit the format without awkward subject, score, or text clipping?
- `title_safety`: Is the story headline clear of the top safe zone?
- `score_rail_dashboard_violation`: Does the score rail look like dashboard boxes?
- `lower_stat_strip_violation`: Is the lower stat strip too heavy or boxed?
- `logo_readiness`: Is the WNBA/team logo treatment ready for manual next step, or does it need manual logo review?
- `action_photo_suitability`: Would an action photo improve this draft once quarantine/manual review clears?
- `operator_decision`: Use only `hold`, `revise`, or `approve_for_manual_next_step`.
- `revision_request`: Write the concrete visual revision needed.
- `operator_notes`: Add any human Adobe-review notes.

Never enter `approved`, `publish_ready`, or `render_ready` in the operator decision.

## Files To Inspect

- `drafts/draft_preview_ig_feed.png`
- `drafts/draft_preview_story.png`
- `drafts/draft_preview_square.png`
- `drafts/draft_preview_visual_contact_sheet.png`

## Reference Files

{included_lines}

## Missing Required Inputs

{missing_block}

## After Review

Leave the filled worksheet at `manual_adobe_visual_qa_intake.csv`. The next importer lane will read that CSV and create review-only result artifacts. Until that importer exists, rerun only this packet builder if the render drafts or QA references change:

```powershell
.\\.venv\\Scripts\\python.exe scripts\\build_hsd_adobe_visual_qa_packet_v1.py
```

## Guardrails

- Review-only artifact packet.
- No paid APIs.
- No source fetching.
- No automatic downloads.
- No image edits.
- No asset approval.
- No approval-state changes.
- No headshot writes.
- No .approved marker writes.
- No publish-ready lane.
- No publishing.
"""


def build_packet(args: argparse.Namespace) -> dict[str, Any]:
    packet_dir = packet_root()
    packet_dir.mkdir(parents=True, exist_ok=True)
    (packet_dir / "drafts").mkdir(parents=True, exist_ok=True)
    (packet_dir / "references").mkdir(parents=True, exist_ok=True)

    included, missing = copy_required_inputs(packet_dir)
    worksheet_path = packet_dir / "manual_adobe_visual_qa_intake.csv"
    open_script_path = packet_dir / "open_packet_in_explorer.ps1"
    readme_path = packet_dir / "README.md"
    manifest_path = packet_dir / "manifest.json"

    write_csv(worksheet_path, worksheet_rows(), WORKSHEET_FIELDS)
    write_text(open_script_path, render_open_packet_script())

    payload: dict[str, Any] = {
        "version": VERSION,
        "status": "adobe_visual_qa_packet_ready" if not missing else "adobe_visual_qa_packet_missing_required_inputs",
        "generated_at_utc": now_iso(),
        "generated_by": GENERATED_BY,
        "repo_head": clean(args.head_commit) or git_head(),
        "packet_dir": str(packet_dir),
        "manifest_path": str(manifest_path),
        "readme_path": str(readme_path),
        "open_packet_script": str(open_script_path),
        "manual_intake_csv": str(worksheet_path),
        "worksheet_fields": WORKSHEET_FIELDS,
        "worksheet_rows": len(WORKSHEET_FORMATS),
        "operator_decision_vocabulary": DECISION_VOCABULARY,
        "forbidden_decision_values": FORBIDDEN_DECISION_VALUES,
        "required_inputs": expected_inputs(),
        "included_files": included,
        "included_file_count": len(included),
        "missing_required_inputs": missing,
        "missing_required_input_count": len(missing),
        "review_only": True,
        "artifact_only": True,
        "paid_apis": False,
        "source_fetching": False,
        "auto_source_enablement": False,
        "asset_downloads": False,
        "image_edits": False,
        "auto_approval": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "auto_publish": False,
        "publishing": False,
        "move_files": False,
    }
    write_text(readme_path, render_readme(payload))
    write_json(manifest_path, payload)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only Adobe-assisted manual visual QA packet.")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_packet(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "packet_dir": payload["packet_dir"],
                "included_file_count": payload["included_file_count"],
                "missing_required_input_count": payload["missing_required_input_count"],
                "manual_intake_csv": payload["manual_intake_csv"],
                "review_only": True,
                "asset_downloads": False,
                "image_edits": False,
                "approval_state_change": False,
                "publish_ready": False,
                "publishing": False,
            },
            indent=2,
        )
    )
    return 1 if payload["missing_required_inputs"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
