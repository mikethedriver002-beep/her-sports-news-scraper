from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import output_path, run_output_dir, strip_volatile_markdown_lines, write_csv, write_json, write_text


VERSION = "hsd-render-visual-qa-contact-sheet-refresh-v1-review-only"
GENERATED_BY = "scripts/build_hsd_render_visual_qa_contact_sheet_refresh_v1.py"
LATEST_FILES_ROOT = Path("outputs/local/latest/files")
OUT_DIR_REL = Path("render_visual_qa_contact_sheet_refresh")
OUT_README_REL = OUT_DIR_REL / "README.md"
OUT_MD_REL = OUT_DIR_REL / "render_visual_qa_contact_sheet_refresh.md"
OUT_CSV_REL = OUT_DIR_REL / "render_visual_qa_contact_sheet_refresh.csv"
OUT_JSON_REL = OUT_DIR_REL / "manifest.json"

LATEST_RENDER_FILES = [
    {
        "artifact_id": "RVQCR001",
        "artifact_kind": "latest_4x5_render",
        "display_name": "Latest 4:5 render",
        "artifact_path": "render_handoff_top_packet/review_drafts/draft_preview_ig_feed.png",
        "source_note": "Current refreshed 4:5 render after the score-rail and lower-stat updates.",
    },
    {
        "artifact_id": "RVQCR002",
        "artifact_kind": "story_render",
        "display_name": "Story render",
        "artifact_path": "render_handoff_top_packet/review_drafts/draft_preview_story.png",
        "source_note": "Story companion for the same review-only renderer pass.",
    },
    {
        "artifact_id": "RVQCR003",
        "artifact_kind": "square_render",
        "display_name": "Square render",
        "artifact_path": "render_handoff_top_packet/review_drafts/draft_preview_square.png",
        "source_note": "Square companion for the same review-only renderer pass.",
    },
    {
        "artifact_id": "RVQCR004",
        "artifact_kind": "visual_contact_sheet",
        "display_name": "Adobe visual QA contact sheet",
        "artifact_path": "adobe_visual_qa_packet/drafts/draft_preview_visual_contact_sheet.png",
        "source_note": "Review-only contact sheet path for the Adobe QA packet.",
    },
]

SOURCE_CONTEXT_FILES = [
    {
        "artifact_id": "RVQCR005",
        "artifact_kind": "render_handoff_manifest",
        "display_name": "Render handoff manifest",
        "artifact_path": "render_handoff_top_packet/handoff_manifest.json",
        "source_note": "Useful for the top-packet context that produced the current drafts.",
    }
]

REVIEW_NOTES = [
    "Score rail deboxed.",
    "Lower stat rail softened.",
    "Feed-only stat separator changed to middots.",
]

REMAINING_CAVEATS = [
    "The headshot bridge still reads a little roster-card-ish and may need one more pass.",
    "APQ001 quarantine action-photo prototypes remain review-only and must not be approved or moved.",
    "No publishing or publish-ready lane work belongs in this packet.",
]

MANUAL_REVIEW_QUESTIONS = [
    "Hold, revise, or continue to the next renderer lane?",
    "Does the headshot bridge still feel roster-card-ish enough to justify another visual pass?",
    "Are the APQ001 quarantine action-photo prototypes still clearly review-only and untouched?",
]

CONTACT_FIELDS = [
    "question_id",
    "question",
    "decision_options",
    "artifact_id",
    "artifact_kind",
    "display_name",
    "artifact_path",
    "source_exists",
    "source_status",
    "source_note",
    "recent_improvement_note",
    "remaining_caveat",
    "manual_review_question",
    "operator_decision_options",
    "review_only",
    "artifact_only",
    "asset_downloads",
    "image_edits",
    "approval_state_change",
    "approved_marker_writes",
    "publish_ready",
    "publishing",
    "move_files",
    "paid_apis",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def output_rel(path: Path) -> Path:
    if run_output_dir():
        return output_path(path)
    return output_path(LATEST_FILES_ROOT / path)


def input_candidates(path: Path) -> list[Path]:
    candidates: list[Path] = []
    run_root = run_output_dir()
    if run_root:
        candidates.append(run_root / path)
    candidates.append(LATEST_FILES_ROOT / path)
    candidates.append(path)
    return candidates


def find_existing_input(path: Path) -> Path | None:
    for candidate in input_candidates(path):
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return None


def artifact_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for item in [*LATEST_RENDER_FILES, *SOURCE_CONTEXT_FILES]:
        source = find_existing_input(Path(item["artifact_path"]))
        rows.append(
            {
                "question_id": "",
                "question": "",
                "decision_options": "",
                "artifact_id": item["artifact_id"],
                "artifact_kind": item["artifact_kind"],
                "display_name": item["display_name"],
                "artifact_path": item["artifact_path"],
                "source_exists": "true" if source else "false",
                "source_status": "present" if source else "missing",
                "source_note": item["source_note"],
                "recent_improvement_note": " | ".join(REVIEW_NOTES) if item["artifact_kind"] == "latest_4x5_render" else "",
                "remaining_caveat": " | ".join(REMAINING_CAVEATS) if item["artifact_kind"] == "latest_4x5_render" else "",
                "manual_review_question": MANUAL_REVIEW_QUESTIONS[0]
                if item["artifact_kind"] == "latest_4x5_render"
                else "",
                "operator_decision_options": "hold|revise|continue_next_renderer_lane"
                if item["artifact_kind"] == "latest_4x5_render"
                else "",
                "review_only": "true",
                "artifact_only": "true",
                "asset_downloads": "false",
                "image_edits": "false",
                "approval_state_change": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "publishing": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    return rows


def review_question_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for index, question in enumerate(MANUAL_REVIEW_QUESTIONS, start=1):
        rows.append(
            {
                "question_id": f"RVQCRQ{index:03d}",
                "question": question,
                "decision_options": "hold|revise|continue_next_renderer_lane",
                "review_only": "true",
                "artifact_only": "true",
                "asset_downloads": "false",
                "image_edits": "false",
                "approval_state_change": "false",
                "approved_marker_writes": "false",
                "publish_ready": "false",
                "publishing": "false",
                "move_files": "false",
                "paid_apis": "false",
            }
        )
    return rows


def render_readme(payload: dict[str, Any]) -> str:
    artifact_lines = "\n".join(
        f"- `{row['display_name']}` -> `{row['artifact_path']}` ({row['source_status']})" for row in payload["artifact_rows"]
    )
    review_questions = "\n".join(f"- {question}" for question in payload["manual_review_questions"])
    return f"""# HSD Render Visual QA Contact Sheet Refresh

Status: `{payload['status']}`
Version: `{payload['version']}`
Generated: `{payload['generated_at_utc']}`

This is a review-only contact-sheet refresh packet. It surfaces the latest 4:5 renderer draft, the story and square companions, and the Adobe visual QA contact sheet path for human inspection. It does not change renderer behavior, edit images, download assets, approve assets, move files, or publish anything.

## What Changed Most Recently

{chr(10).join(f"- {note}" for note in REVIEW_NOTES)}

## Remaining Review-Only Caveats

{chr(10).join(f"- {note}" for note in REMAINING_CAVEATS)}

## Manual Review Questions

{review_questions}

## Open First

- `{LATEST_RENDER_FILES[0]['artifact_path']}`
- `{LATEST_RENDER_FILES[1]['artifact_path']}`
- `{LATEST_RENDER_FILES[2]['artifact_path']}`
- `{LATEST_RENDER_FILES[3]['artifact_path']}`

## Artifact Rows

{artifact_lines}

## Guardrails

- review-only
- artifact-only
- asset_downloads=false
- image_edits=false
- approval_state_change=false
- approved_marker_writes=false
- publish_ready=false
- publishing=false
- move_files=false
- paid_apis=false
"""


def render_summary_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# HSD Render Visual QA Contact Sheet Refresh Summary",
        "",
        f"Status: `{payload['status']}`",
        f"Generated: `{payload['generated_at_utc']}`",
        "",
        "## Artifact Table",
        "",
        "| Artifact | Path | Source | Note |",
        "| --- | --- | --- | --- |",
    ]
    for row in payload["artifact_rows"]:
        note = row["source_note"]
        if row["artifact_kind"] == "latest_4x5_render":
            note = " | ".join(REVIEW_NOTES)
        lines.append(
            f"| `{row['display_name']}` | `{row['artifact_path']}` | `{row['source_status']}` | {note} |"
        )
    lines.extend(
        [
            "",
            "## Manual Review Questions",
            "",
            *[f"- {question}" for question in payload["manual_review_questions"]],
            "",
            "## Remaining Caveats",
            "",
            *[f"- {note}" for note in REMAINING_CAVEATS],
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- artifact_only=true",
            "- asset_downloads=false",
            "- image_edits=false",
            "- approval_state_change=false",
            "- approved_marker_writes=false",
            "- publish_ready=false",
            "- publishing=false",
            "- move_files=false",
            "- paid_apis=false",
        ]
    )
    return "\n".join(lines)


def build_payload(args: argparse.Namespace) -> dict[str, Any]:
    artifact_rows_list = artifact_rows()
    review_questions = review_question_rows()
    present_count = sum(1 for row in artifact_rows_list if row["source_exists"] == "true")
    missing_count = len(artifact_rows_list) - present_count
    status = "render_visual_qa_contact_sheet_refresh_ready" if present_count else "render_visual_qa_contact_sheet_refresh_reference_missing"

    out_readme = output_rel(OUT_README_REL)
    out_md = output_rel(OUT_MD_REL)
    out_csv = output_rel(OUT_CSV_REL)
    out_json = output_rel(OUT_JSON_REL)

    payload: dict[str, Any] = {
        "version": VERSION,
        "status": status,
        "generated_at_utc": now_iso(),
        "generated_by": GENERATED_BY,
        "repo_head": clean(args.head_commit),
        "output_dir": str(output_rel(OUT_DIR_REL)),
        "readme_path": str(out_readme),
        "summary_md_path": str(out_md),
        "summary_csv_path": str(out_csv),
        "manifest_path": str(out_json),
        "latest_4x5_render_path": LATEST_RENDER_FILES[0]["artifact_path"],
        "story_render_path": LATEST_RENDER_FILES[1]["artifact_path"],
        "square_render_path": LATEST_RENDER_FILES[2]["artifact_path"],
        "contact_sheet_path": LATEST_RENDER_FILES[3]["artifact_path"],
        "render_handoff_manifest_path": SOURCE_CONTEXT_FILES[0]["artifact_path"],
        "artifact_rows": artifact_rows_list,
        "artifact_count": len(artifact_rows_list),
        "present_source_count": present_count,
        "missing_source_count": missing_count,
        "manual_review_questions": MANUAL_REVIEW_QUESTIONS,
        "review_question_rows": review_questions,
        "review_only": True,
        "artifact_only": True,
        "asset_downloads": False,
        "image_edits": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "publishing": False,
        "move_files": False,
        "paid_apis": False,
        "review_notes": REVIEW_NOTES,
        "remaining_caveats": REMAINING_CAVEATS,
        "source_paths": [row["artifact_path"] for row in artifact_rows_list],
    }

    write_csv(out_csv, artifact_rows_list + review_questions, CONTACT_FIELDS, extrasaction="ignore")
    write_text(out_readme, render_readme(payload), normalize=strip_volatile_markdown_lines)
    write_text(out_md, render_summary_markdown(payload), normalize=strip_volatile_markdown_lines)
    write_json(out_json, payload, sort_keys=True)
    return payload


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only render visual QA contact sheet refresh packet.")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    payload = build_payload(parse_args(argv))
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": payload["status"],
                "artifact_count": payload["artifact_count"],
                "present_source_count": payload["present_source_count"],
                "missing_source_count": payload["missing_source_count"],
                "readme_path": payload["readme_path"],
                "summary_md_path": payload["summary_md_path"],
                "summary_csv_path": payload["summary_csv_path"],
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
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
