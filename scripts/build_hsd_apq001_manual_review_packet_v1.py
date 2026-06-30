from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir


VERSION = "hsd-apq001-manual-asset-review-packet-v1-review-only"
GENERATED_BY = "scripts/build_hsd_apq001_manual_review_packet_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
PACKET_DIR_NAME = "apq001_manual_asset_review_packet"
CANDIDATE_ID = "APQ001"
CANDIDATE_SOURCE = Path(
    "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg"
)
CANDIDATE_PACKET_PATH = Path("candidate/apq001_review_only_candidate.jpg")

MANUAL_ASSET_REVIEW_FIELDS = [
    "review_step",
    "candidate_queue_id",
    "candidate_packet_path",
    "quarantine_source_path",
    "identity_match",
    "action_photo_quality",
    "rights_review",
    "crop_fit_square_1x1",
    "crop_fit_feed_4x5",
    "crop_fit_story_9x16",
    "operator_decision",
    "operator_notes",
    "reviewed_by",
    "reviewed_at_local",
    "review_only",
    "publish_ready",
    "approval_state_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "move_files",
    "publishing",
]

RENDERER_HANDOFF_FIELDS = [
    "review_step",
    "candidate_queue_id",
    "candidate_packet_path",
    "renderer_handoff_question",
    "operator_finding",
    "renderer_handoff_recommendation",
    "revision_request",
    "operator_notes",
    "review_only",
    "publish_ready",
    "approval_state_change",
    "renderer_behavior_change",
    "asset_downloads",
    "headshot_writes",
    "approved_marker_writes",
    "move_files",
    "publishing",
]

MANUAL_DECISION_VOCABULARY = [
    "hold_asset_review",
    "needs_rights_or_identity_review",
    "suitable_for_renderer_handoff_review",
]

HANDOFF_RECOMMENDATION_VOCABULARY = [
    "hold_renderer_handoff",
    "needs_crop_or_layout_notes",
    "suitable_for_renderer_recheck",
]

FORBIDDEN_VALUES = [
    "approved",
    "asset_approved",
    "publish_ready",
    "render_ready",
    "renderer_approved",
]

REFERENCE_INPUTS = [
    {
        "source": Path("outputs/local/latest/files/review_only_quarantine_download_manifest.json"),
        "target": Path("references/review_only_quarantine_download_manifest.json"),
        "role": "quarantine_download_manifest",
        "required": False,
    },
    {
        "source": Path("outputs/local/latest/files/review_only_quarantine_download_report.md"),
        "target": Path("references/review_only_quarantine_download_report.md"),
        "role": "quarantine_download_report",
        "required": False,
    },
    {
        "source": Path("data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.json"),
        "target": Path("references/review_only_action_photo_quarantine_preflight_v1.json"),
        "role": "quarantine_preflight_manifest",
        "required": False,
    },
    {
        "source": Path("data/asset_registry/action_photo_candidates/review_only_action_photo_quarantine_preflight_v1.md"),
        "target": Path("references/review_only_action_photo_quarantine_preflight_v1.md"),
        "role": "quarantine_preflight_report",
        "required": False,
    },
    {
        "source": Path("data/asset_registry/action_photo_candidates/review_only_action_photo_to_renderer_bridge_v1.json"),
        "target": Path("references/review_only_action_photo_to_renderer_bridge_v1.json"),
        "role": "to_renderer_bridge_manifest",
        "required": False,
    },
    {
        "source": Path("data/asset_registry/action_photo_candidates/review_only_action_photo_to_renderer_bridge_v1.md"),
        "target": Path("references/review_only_action_photo_to_renderer_bridge_v1.md"),
        "role": "to_renderer_bridge_report",
        "required": False,
    },
]


def clean(value: Any) -> str:
    return str(value or "").strip()


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


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
    candidates.append(rel)
    return candidates


def find_source(relative_path: str | Path) -> Path | None:
    for candidate in source_candidates(relative_path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return None


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


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


def manual_asset_review_rows() -> list[dict[str, str]]:
    return [
        {
            "review_step": "manual_asset_review",
            "candidate_queue_id": CANDIDATE_ID,
            "candidate_packet_path": CANDIDATE_PACKET_PATH.as_posix(),
            "quarantine_source_path": CANDIDATE_SOURCE.as_posix(),
            "identity_match": "operator_fill_required",
            "action_photo_quality": "operator_fill_required",
            "rights_review": "operator_fill_required",
            "crop_fit_square_1x1": "operator_fill_required",
            "crop_fit_feed_4x5": "operator_fill_required",
            "crop_fit_story_9x16": "operator_fill_required",
            "operator_decision": "operator_fill_required",
            "operator_notes": "",
            "reviewed_by": "",
            "reviewed_at_local": "",
            "review_only": "true",
            "publish_ready": "false",
            "approval_state_change": "false",
            "asset_downloads": "false",
            "headshot_writes": "false",
            "approved_marker_writes": "false",
            "move_files": "false",
            "publishing": "false",
        }
    ]


def renderer_handoff_rows() -> list[dict[str, str]]:
    questions = [
        ("identity_context", "Does the image still clearly read as Caitlin Clark / Indiana Fever in context?"),
        ("square_crop_fit", "Can this work as a 1x1 crop without losing face, jersey, or useful court context?"),
        ("feed_crop_fit", "Can this work as a 4x5 feed crop with room for open score typography?"),
        ("story_crop_fit", "Can this work as a 9x16 story crop without crowding top safe zone content?"),
        ("renderer_bridge", "Should a future renderer lane test this candidate as an action-photo bridge only?"),
    ]
    rows: list[dict[str, str]] = []
    for step, question in questions:
        rows.append(
            {
                "review_step": step,
                "candidate_queue_id": CANDIDATE_ID,
                "candidate_packet_path": CANDIDATE_PACKET_PATH.as_posix(),
                "renderer_handoff_question": question,
                "operator_finding": "operator_fill_required",
                "renderer_handoff_recommendation": "operator_fill_required",
                "revision_request": "",
                "operator_notes": "",
                "review_only": "true",
                "publish_ready": "false",
                "approval_state_change": "false",
                "renderer_behavior_change": "false",
                "asset_downloads": "false",
                "headshot_writes": "false",
                "approved_marker_writes": "false",
                "move_files": "false",
                "publishing": "false",
            }
        )
    return rows


def copy_reference_inputs(packet_dir: Path) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    included: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    for item in REFERENCE_INPUTS:
        source = find_source(item["source"])
        if not source:
            missing.append(
                {
                    "path": item["source"].as_posix(),
                    "packet_path": item["target"].as_posix(),
                    "role": clean(item["role"]),
                    "required": str(bool(item["required"])).lower(),
                    "issue": "missing_optional_reference",
                }
            )
            continue
        target = packet_dir / item["target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        included.append(
            {
                "path": item["source"].as_posix(),
                "source_path": str(source),
                "packet_path": item["target"].as_posix(),
                "role": clean(item["role"]),
                "required": str(bool(item["required"])).lower(),
                "bytes": str(target.stat().st_size),
            }
        )
    return included, missing


def copy_candidate(packet_dir: Path) -> tuple[dict[str, str] | None, dict[str, str] | None]:
    source = find_source(CANDIDATE_SOURCE)
    if not source:
        return None, {
            "path": CANDIDATE_SOURCE.as_posix(),
            "packet_path": CANDIDATE_PACKET_PATH.as_posix(),
            "role": "apq001_quarantine_candidate",
            "required": "true",
            "issue": "missing_quarantine_candidate",
        }
    target = packet_dir / CANDIDATE_PACKET_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return (
        {
            "path": CANDIDATE_SOURCE.as_posix(),
            "source_path": str(source),
            "packet_path": CANDIDATE_PACKET_PATH.as_posix(),
            "role": "apq001_quarantine_candidate",
            "required": "true",
            "bytes": str(target.stat().st_size),
            "sha256": sha256_file(target),
        },
        None,
    )


def render_open_packet_script() -> str:
    return """$ErrorActionPreference = "Stop"
$PacketRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Start-Process explorer.exe -ArgumentList $PacketRoot
Write-Host "Opened HSD APQ001 manual asset review packet:"
Write-Host $PacketRoot
Write-Host "Review-only: fill the CSVs, do not move the candidate into renderer or approved folders."
"""


def render_readme(payload: dict[str, Any]) -> str:
    included_lines = "\n".join(f"- `{item['packet_path']}` from `{item['path']}`" for item in payload["included_files"])
    missing_lines = "\n".join(
        f"- `{item['path']}` -> `{item['packet_path']}` ({item['issue']})" for item in payload["missing_inputs"]
    )
    missing_block = missing_lines or "- None"
    return f"""# APQ001 Manual Asset Review Packet

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This packet is for local human review of the APQ001 quarantine-only action-photo candidate. It does not approve the asset, does not edit the image, does not move the file into renderer/headshot/approved folders, and does not publish anything.

## Open

Run:

```powershell
powershell -ExecutionPolicy Bypass -File .\\open_packet_in_explorer.ps1
```

Then inspect `candidate/apq001_review_only_candidate.jpg`.

## Fill These Files

1. `manual_asset_review_intake.csv`
   - Answer identity, quality, rights, and crop-fit fields.
   - Use only: `{", ".join(MANUAL_DECISION_VOCABULARY)}`.

2. `renderer_handoff_review_checklist.csv`
   - Answer whether this candidate is worth a later renderer recheck.
   - Use only: `{", ".join(HANDOFF_RECOMMENDATION_VOCABULARY)}`.

Do not use: `{", ".join(FORBIDDEN_VALUES)}`.

## Guardrails

- Review-only packet.
- No image edits.
- No new downloads.
- No approval state changes.
- No .approved marker writes.
- No headshot, renderer, or approved-folder writes.
- No publish-ready lane.
- No publishing.
- No renderer behavior changes.

## Included Files

{included_lines or "- None"}

## Missing Inputs

{missing_block}

## Next Local Step After Human Review

Paste the filled CSV rows back to Codex. The next repo step should import those filled rows into review-only result artifacts only.
"""


def build_manifest(
    *,
    packet_dir: Path,
    included: list[dict[str, str]],
    missing: list[dict[str, str]],
    head_commit: str,
) -> dict[str, Any]:
    required_missing = [item for item in missing if item.get("required") == "true"]
    return {
        "version": VERSION,
        "status": "apq001_manual_asset_review_packet_ready" if not required_missing else "apq001_manual_asset_review_packet_missing_candidate",
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "repo_head": head_commit,
        "packet_dir": str(packet_dir),
        "candidate_queue_id": CANDIDATE_ID,
        "candidate_source_path": CANDIDATE_SOURCE.as_posix(),
        "candidate_packet_path": CANDIDATE_PACKET_PATH.as_posix(),
        "manual_asset_review_csv": "manual_asset_review_intake.csv",
        "renderer_handoff_review_csv": "renderer_handoff_review_checklist.csv",
        "manual_decision_vocabulary": MANUAL_DECISION_VOCABULARY,
        "renderer_handoff_recommendation_vocabulary": HANDOFF_RECOMMENDATION_VOCABULARY,
        "forbidden_values": FORBIDDEN_VALUES,
        "included_file_count": len(included),
        "missing_input_count": len(missing),
        "required_missing_input_count": len(required_missing),
        "included_files": included,
        "missing_inputs": missing,
        "review_only": True,
        "artifact_only": True,
        "image_edits": False,
        "source_fetching": False,
        "auto_source_enablement": False,
        "asset_downloads": False,
        "new_downloads": False,
        "auto_approval": False,
        "approval_state_change": False,
        "headshot_writes": False,
        "approved_marker_writes": False,
        "renderer_behavior_change": False,
        "publish_ready": False,
        "auto_publish": False,
        "publishing": False,
        "move_files": False,
        "paid_apis": False,
    }


def build_packet(head_commit: str | None = None) -> dict[str, Any]:
    packet_dir = packet_root()
    packet_dir.mkdir(parents=True, exist_ok=True)

    included: list[dict[str, str]] = []
    missing: list[dict[str, str]] = []
    candidate_included, candidate_missing = copy_candidate(packet_dir)
    if candidate_included:
        included.append(candidate_included)
    if candidate_missing:
        missing.append(candidate_missing)
    ref_included, ref_missing = copy_reference_inputs(packet_dir)
    included.extend(ref_included)
    missing.extend(ref_missing)

    write_csv(packet_dir / "manual_asset_review_intake.csv", manual_asset_review_rows(), MANUAL_ASSET_REVIEW_FIELDS)
    write_csv(packet_dir / "renderer_handoff_review_checklist.csv", renderer_handoff_rows(), RENDERER_HANDOFF_FIELDS)
    write_text(packet_dir / "open_packet_in_explorer.ps1", render_open_packet_script())
    payload = build_manifest(
        packet_dir=packet_dir,
        included=included,
        missing=missing,
        head_commit=head_commit or git_head(),
    )
    write_json(packet_dir / "manifest.json", payload)
    write_text(packet_dir / "README.md", render_readme(payload))
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the APQ001 manual asset review / renderer handoff packet.")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    payload = build_packet(head_commit=args.head_commit or None)
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "packet_dir": payload["packet_dir"],
                "included_file_count": payload["included_file_count"],
                "required_missing_input_count": payload["required_missing_input_count"],
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 1 if payload["required_missing_input_count"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
