from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text
from scripts.build_hsd_action_photo_review_deck_ui_v1 import build_packet as build_review_deck_packet


VERSION = "hsd-wnba-unified-swipe-deck-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_unified_swipe_deck_v1.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LATEST_FILES_ROOT = REPO_ROOT / "outputs" / "local" / "latest" / "files"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "tmp" / "wnba_unified_swipe_deck_v1"
DEFAULT_LATEST_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "latest" / "files" / "wnba_unified_swipe_deck_v1"

COMBINED_BOARD_NAME = "wnba_unified_swipe_deck_input.csv"
REPORT_NAME = "wnba_unified_swipe_deck_report.md"
MANIFEST_NAME = "manifest.json"
EMPTY_PROOF_MANIFEST_NAME = "empty_proof_manifest.json"
REVIEW_DECK_DIR_NAME = "review_deck"

BOARD_FIELDS = [
    "board_rank",
    "source_family_id",
    "candidate_queue_id",
    "scout_candidate_id",
    "seed_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "source_domain",
    "visual_priority",
    "candidate_quality_tier",
    "score",
    "candidate_board_recommendation",
    "candidate_risk_flags",
    "manual_decision_needed",
    "formal_intake_ready",
    "face_likely_visible",
    "body_margin_likely",
    "four_by_five_crop_potential",
    "text_safe_negative_space",
    "source_provenance_clarity",
    "identity_confidence",
    "operator_fair_use_asserted",
    "notes",
    "download_approved",
    "review_only",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]


SOURCE_SPECS = [
    {
        "surface_id": "wnba_fever_visual_rank",
        "team": "Fever",
        "path": Path("wnba_fever_visual_rank_v1/wnba_fever_visual_rank_board.csv"),
        "source_order": 1,
    },
    {
        "surface_id": "wnba_storm_visual_rank",
        "team": "Storm",
        "path": Path("wnba_storm_visual_rank_v1/wnba_storm_visual_rank_board.csv"),
        "source_order": 2,
    },
    {
        "surface_id": "wnba_aces_source_scout",
        "team": "Aces",
        "path": Path("wnba_official_team_source_scout_v1/wnba_aces_source_scout_board.csv"),
        "source_order": 3,
    },
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def repo_rel(path: Path) -> str:
    resolved = path.resolve(strict=False)
    try:
        return resolved.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return resolved.as_posix()


def output_root() -> Path:
    raw = clean(run_output_dir() or "")
    return Path(raw).resolve(strict=False) if raw else DEFAULT_OUTPUT_DIR


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def numeric_score(row: dict[str, str]) -> int:
    raw = clean(row.get("visual_rank_score") or row.get("score") or row.get("source_scout_score") or "0")
    try:
        return int(float(raw))
    except ValueError:
        return 0


def source_family(row: dict[str, str], fallback: str) -> str:
    return clean(row.get("source_family_id") or fallback)


def normalize_row(row: dict[str, str], spec: dict[str, Any], rank: int) -> dict[str, str]:
    candidate_id = clean(row.get("candidate_queue_id") or row.get("scout_candidate_id") or row.get("board_id"))
    score = numeric_score(row)
    visual_priority = clean(row.get("visual_review_priority") or row.get("visual_priority"))
    if not visual_priority:
        visual_priority = "P1_visual_review_now" if score >= 94 else "P2_manual_confirm" if score >= 84 else "P3_hold_or_fast_reject"
    quality_tier = clean(row.get("candidate_quality_tier") or row.get("source_scout_tier"))
    if not quality_tier:
        quality_tier = "A_primary_source_lead" if score >= 94 else "B_manual_confirm" if score >= 84 else "C_hold_or_fast_reject"
    notes = clean(row.get("notes"))
    prompt_bits = [
        clean(row.get("carry_forward_prompt")),
        clean(row.get("reject_prompt")),
        clean(row.get("manual_next_action")),
    ]
    prompt_note = " | ".join(bit for bit in prompt_bits if bit)
    if prompt_note:
        notes = f"{notes} | {prompt_note}".strip(" |")
    return {
        "board_rank": str(rank),
        "source_family_id": source_family(row, str(spec["surface_id"])),
        "candidate_queue_id": candidate_id,
        "scout_candidate_id": candidate_id,
        "seed_id": clean(row.get("seed_id")),
        "entity_id": clean(row.get("entity_id")),
        "source_type": clean(row.get("source_type")),
        "source_url": clean(row.get("source_url")),
        "candidate_image_url": clean(row.get("candidate_image_url")),
        "image_alt": clean(row.get("image_alt")),
        "source_domain": clean(row.get("source_domain")),
        "visual_priority": visual_priority,
        "candidate_quality_tier": quality_tier,
        "score": str(score),
        "candidate_board_recommendation": clean(row.get("candidate_board_recommendation") or "manual_inspect_for_formal_intake"),
        "candidate_risk_flags": clean(row.get("candidate_risk_flags") or row.get("identity_honesty") or "none"),
        "manual_decision_needed": "yes",
        "formal_intake_ready": "no",
        "face_likely_visible": clean(row.get("face_likely_visible") or "possible"),
        "body_margin_likely": clean(row.get("body_margin_likely") or "possible"),
        "four_by_five_crop_potential": clean(row.get("four_by_five_crop_potential") or "possible"),
        "text_safe_negative_space": clean(row.get("text_safe_negative_space") or "possible"),
        "source_provenance_clarity": clean(row.get("source_provenance_clarity") or "clear"),
        "identity_confidence": clean(row.get("identity_confidence") or "manual_confirm"),
        "operator_fair_use_asserted": clean(row.get("operator_fair_use_asserted") or "yes"),
        "notes": notes,
        "download_approved": "no",
        "review_only": "true",
        "asset_downloads": "false",
        "approval_state_change": "false",
        "publish_ready": "false",
        "publishing": "false",
    }


def combined_rows(latest_files_root: Path) -> tuple[list[dict[str, str]], dict[str, Any]]:
    gathered: list[tuple[int, int, dict[str, str], dict[str, Any]]] = []
    source_counts: dict[str, int] = {}
    source_paths: dict[str, str] = {}
    for spec in SOURCE_SPECS:
        source_path = latest_files_root / spec["path"]
        rows = read_csv_rows(source_path)
        source_counts[str(spec["surface_id"])] = len(rows)
        source_paths[str(spec["surface_id"])] = source_path.as_posix()
        for original_index, row in enumerate(rows, start=1):
            gathered.append((int(spec["source_order"]), original_index, row, spec))
    gathered.sort(key=lambda item: (item[0], -numeric_score(item[2]), item[1]))
    normalized = [normalize_row(row, spec, rank) for rank, (_, _, row, spec) in enumerate(gathered, start=1)]
    return normalized, {"source_counts": source_counts, "source_paths": source_paths}


def mirror_output_tree(source: Path, destination: Path) -> None:
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)


def render_report(manifest: dict[str, Any]) -> str:
    source_counts = manifest["source_counts"]
    return f"""# WNBA Unified Swipe Deck V1

Status: `{manifest['status']}`
Generated: `{manifest['generated_at_utc']}`

This is the current WNBA-only Tinder-style manual review surface. It wraps the existing action-photo swipe deck UI around Fever, Storm, and Aces candidates so Mike reviews one card at a time instead of juggling tables.

## Counts

- Deck items: `{manifest['deck_item_count']}`
- Fever rows: `{source_counts.get('wnba_fever_visual_rank', 0)}`
- Storm rows: `{source_counts.get('wnba_storm_visual_rank', 0)}`
- Aces rows: `{source_counts.get('wnba_aces_source_scout', 0)}`

## Manual Action

1. Open `review_deck/action_photo_review_deck.html`.
2. Swipe right or click Carry Forward only for strong WNBA action-photo candidates.
3. Swipe left or reject quickly for wrong-person, group-heavy, bad-crop, graphic-looking, or visually weak rows.
4. Export the decision CSV from the deck.

## Guardrails

- review_only=true
- download_approved=no
- asset_downloads=false
- approval_state_change=false
- publish_ready=false
- publishing=false
- no new downloads
- no source auto-enablement
"""


def build_packet(*, latest_files_root: Path, output_dir: Path, latest_output_dir: Path | None = DEFAULT_LATEST_OUTPUT_DIR, limit: int = 50) -> dict[str, Any]:
    latest_files_root = latest_files_root.resolve(strict=False)
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, source_meta = combined_rows(latest_files_root)
    if not rows:
        raise ValueError(f"No WNBA rows found under {latest_files_root}")
    rows = rows[: max(1, limit)]

    board_path = output_dir / COMBINED_BOARD_NAME
    report_path = output_dir / REPORT_NAME
    manifest_path = output_dir / MANIFEST_NAME
    empty_proof_manifest = output_dir / EMPTY_PROOF_MANIFEST_NAME
    review_deck_dir = output_dir / REVIEW_DECK_DIR_NAME

    write_csv(board_path, rows, BOARD_FIELDS)
    write_json(empty_proof_manifest, {"proof_rows": []}, sort_keys=True)
    deck_manifest = build_review_deck_packet(
        board_csv=board_path,
        proof_manifest=empty_proof_manifest,
        output_dir=review_deck_dir,
        limit=len(rows),
        head_commit="",
    )
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_unified_swipe_deck_ready",
        "review_only": True,
        "latest_files_root": latest_files_root.as_posix(),
        "output_dir": output_dir.as_posix(),
        "combined_board_csv_path": repo_rel(board_path),
        "report_path": repo_rel(report_path),
        "manifest_path": repo_rel(manifest_path),
        "deck_output_dir": repo_rel(review_deck_dir),
        "deck_html_path": deck_manifest.get("html_path", ""),
        "deck_decision_template_path": deck_manifest.get("decision_template_path", ""),
        "deck_manifest_path": deck_manifest.get("manifest_path", ""),
        "deck_item_count": deck_manifest.get("deck_item_count", len(rows)),
        "candidate_item_count": deck_manifest.get("candidate_item_count", len(rows)),
        "renderer_proof_item_count": deck_manifest.get("renderer_proof_item_count", 0),
        "browser_storage_key": deck_manifest.get("browser_storage_key", ""),
        "source_counts": source_meta["source_counts"],
        "source_paths": source_meta["source_paths"],
        "download_approved": False,
        "asset_downloads": False,
        "approval_state_change": False,
        "publish_ready": False,
        "publishing": False,
        "source_auto_enabled": False,
        "latest_mirror_built": False,
    }
    write_text(report_path, render_report(manifest))
    write_json(manifest_path, manifest, sort_keys=True)
    if latest_output_dir:
        latest_output_dir = latest_output_dir.resolve(strict=False)
        mirror_output_tree(output_dir, latest_output_dir)
        manifest["latest_mirror_built"] = True
        write_json(manifest_path, manifest, sort_keys=True)
        write_json(latest_output_dir / MANIFEST_NAME, manifest, sort_keys=True)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build one WNBA-only Tinder-style swipe deck from current WNBA source boards.")
    parser.add_argument("--latest-files-root", default=DEFAULT_LATEST_FILES_ROOT.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-output-dir", default=DEFAULT_LATEST_OUTPUT_DIR.as_posix())
    parser.add_argument("--limit", type=int, default=50)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else output_root()
    latest_output_dir = Path(args.latest_output_dir) if args.latest_output_dir else DEFAULT_LATEST_OUTPUT_DIR
    manifest = build_packet(
        latest_files_root=Path(args.latest_files_root),
        output_dir=output_dir,
        latest_output_dir=latest_output_dir,
        limit=args.limit,
    )
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "deck_item_count": manifest["deck_item_count"],
                "deck_html_path": manifest["deck_html_path"],
                "output_dir": output_dir.as_posix(),
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
