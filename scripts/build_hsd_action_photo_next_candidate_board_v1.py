from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-action-photo-next-candidate-board-v1-review-only"
GENERATED_BY = "scripts/build_hsd_action_photo_next_candidate_board_v1.py"
DEFAULT_REMOTE_TRIAGE_CSV = Path(
    "outputs/local/latest/files/action_photo_remote_visual_triage/action_photo_remote_visual_triage.csv"
)
DEFAULT_SCOUT_CSV = Path(
    "outputs/local/latest/files/action_photo_candidate_scout_seed_expansion/action_photo_candidate_intake.csv"
)
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_next_candidate_board_v1")
REPORT_NAME = "action_photo_next_candidate_board_report.md"
CSV_NAME = "action_photo_next_candidate_board.csv"
MANIFEST_NAME = "manifest.json"

FALSE_GUARDRAILS = {
    "asset_downloads": False,
    "approval_state_change": False,
    "approved_marker_writes": False,
    "auto_approval": False,
    "auto_publish": False,
    "download_performed": False,
    "paid_apis": False,
    "protected_asset_moves": False,
    "publish_ready": False,
    "publishing": False,
    "source_auto_enabled": False,
}

ALREADY_PROCESSED_CANDIDATES = {"APCS114"}
GENERIC_FILENAME_TOKENS = {
    "aces",
    "cdn",
    "feat",
    "fever",
    "gallery",
    "game",
    "getty",
    "gray",
    "gsv",
    "image",
    "img",
    "jpeg",
    "jpg",
    "las",
    "nbae",
    "oliphant",
    "png",
    "recap",
    "sea",
    "site",
    "sites",
    "sparks",
    "team",
    "vegas",
    "wnba",
}

CSV_FIELDS = [
    "board_rank",
    "board_id",
    "triage_id",
    "scout_candidate_id",
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
    "formal_intake_required_fields",
    "face_likely_visible",
    "body_margin_likely",
    "four_by_five_crop_potential",
    "text_safe_negative_space",
    "source_provenance_clarity",
    "identity_confidence",
    "operator_fair_use_asserted",
    "operator_decision",
    "operator_notes",
    "download_approved",
    "review_only",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else repo_root() / candidate


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def norm(value: str | None) -> str:
    return (value or "").strip()


def norm_lower(value: str | None) -> str:
    return norm(value).lower()


def truthy_no(value: str | None) -> bool:
    return norm_lower(value) in {"no", "false", "0", ""}


def is_rejected_or_wrong_person(row: dict[str, str]) -> bool:
    status = norm_lower(row.get("manual_review_status"))
    action = norm_lower(row.get("manual_next_action"))
    decision = norm_lower(row.get("manual_visual_decision"))
    notes = norm_lower(row.get("manual_visual_notes"))
    text = " ".join([status, action, decision, notes])
    rejected_markers = ["reject", "wrong-person", "wrong person", "bad grouped", "weak candidate"]
    return any(marker in text for marker in rejected_markers)


def entity_player_tokens(entity_id: str) -> list[str]:
    parts = [part for part in re.split(r"[_\W]+", norm_lower(entity_id)) if part]
    if len(parts) < 2:
        return parts
    return [part for part in parts[-2:] if len(part) >= 3]


def url_filename_tokens(url: str) -> list[str]:
    filename = norm_lower(url).rsplit("/", 1)[-1].rsplit("?", 1)[0]
    stem = filename.rsplit(".", 1)[0]
    return [part for part in re.split(r"[^a-zA-Z]+", stem) if len(part) >= 3]


def filename_identity_signal(row: dict[str, str]) -> str:
    entity_tokens = set(entity_player_tokens(row.get("entity_id", "")))
    filename_tokens = set(url_filename_tokens(row.get("candidate_image_url", "")))
    if not entity_tokens or not filename_tokens:
        return "filename_identity_unverified"
    if entity_tokens & filename_tokens:
        return "filename_identity_match"
    meaningful = {
        token
        for token in filename_tokens
        if token not in GENERIC_FILENAME_TOKENS and token not in entity_tokens and len(token) >= 4
    }
    if meaningful:
        return "filename_identity_mismatch"
    return "filename_identity_unverified"


def score_row(row: dict[str, str], scout_row: dict[str, str] | None) -> int:
    score = 0
    if norm(row.get("visual_priority")).startswith("P1"):
        score += 8
    if norm_lower(row.get("face_likely_visible")) == "likely":
        score += 5
    elif norm_lower(row.get("face_likely_visible")) == "possible":
        score += 2
    if norm_lower(row.get("body_margin_likely")) == "likely":
        score += 4
    elif norm_lower(row.get("body_margin_likely")) == "possible":
        score += 2
    if norm_lower(row.get("four_by_five_crop_potential")) == "possible":
        score += 5
    if norm_lower(row.get("text_safe_negative_space")) == "possible":
        score += 2
    if norm_lower(row.get("source_provenance_clarity")) == "clear":
        score += 3
    if "official" in norm_lower(row.get("source_type")):
        score += 2
    if scout_row and norm_lower(scout_row.get("identity_confidence")) == "high":
        score += 3
    if scout_row and norm_lower(scout_row.get("jersey_text_conflict_risk")) == "high":
        score -= 2
    signal = filename_identity_signal(row)
    if signal == "filename_identity_match":
        score += 7
    elif signal == "filename_identity_mismatch":
        score -= 12
    else:
        score -= 6
    alt = norm_lower(row.get("image_alt"))
    if "gallery" in alt or "score" in alt:
        score -= 1
    return score


def risk_flags(row: dict[str, str], scout_row: dict[str, str] | None) -> list[str]:
    flags: list[str] = []
    signal = filename_identity_signal(row)
    if signal != "filename_identity_match":
        flags.append(signal)
    alt = norm_lower(row.get("image_alt"))
    evidence = norm_lower((scout_row or {}).get("notes_evidence"))
    if "gallery" in alt or "gallery" in evidence:
        flags.append("gallery_row_needs_visual_identity_check")
    if norm_lower(row.get("body_margin_likely")) in {"unclear", ""}:
        flags.append("body_margin_unclear")
    if norm_lower(row.get("face_likely_visible")) != "likely":
        flags.append("face_visibility_not_likely")
    if norm_lower((scout_row or {}).get("jersey_text_conflict_risk")) == "high":
        flags.append("jersey_text_conflict_high")
    if norm_lower((scout_row or {}).get("identity_confidence")) not in {"high", "medium"}:
        flags.append("identity_confidence_needs_check")
    return flags or ["none"]


def quality_tier(score: int, flags: list[str]) -> str:
    if score >= 23 and flags == ["none"]:
        return "A_manual_inspect_first"
    if score >= 21:
        return "A_minus_manual_inspect"
    if score >= 18:
        return "B_review_if_needed"
    return "C_hold"


def recommendation(tier: str, flags: list[str]) -> str:
    if tier.startswith("A"):
        return "manual_inspect_for_formal_intake"
    if "face_visibility_not_likely" in flags:
        return "hold_until_visual_identity_confirms_subject"
    return "reserve_candidate"


def build_board(remote_rows: list[dict[str, str]], scout_rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    scout_by_id = {norm(row.get("scout_candidate_id")): row for row in scout_rows}
    candidates: list[tuple[int, dict[str, str], dict[str, str] | None, list[str]]] = []
    seen: set[str] = set()
    for row in remote_rows:
        scout_id = norm(row.get("scout_candidate_id"))
        if not scout_id or scout_id in seen:
            continue
        if scout_id in ALREADY_PROCESSED_CANDIDATES:
            continue
        scout_row = scout_by_id.get(scout_id)
        if is_rejected_or_wrong_person(row) or (scout_row and is_rejected_or_wrong_person(scout_row)):
            continue
        if not norm(row.get("visual_priority")).startswith("P1"):
            continue
        if not truthy_no(row.get("download_approved")):
            continue
        if norm_lower(row.get("publish_ready")) != "false":
            continue
        score = score_row(row, scout_row)
        flags = risk_flags(row, scout_row)
        candidates.append((score, row, scout_row, flags))
        seen.add(scout_id)

    candidates.sort(
        key=lambda item: (
            -item[0],
            item[3] != ["none"],
            norm(item[1].get("entity_id")),
            norm(item[1].get("scout_candidate_id")),
        )
    )

    board: list[dict[str, str]] = []
    required_fields = (
        "download_approved, source_url, entity_id, rights_class, identity_confidence, "
        "intended_review_only_use, operator_fair_use_asserted"
    )
    rank = 0
    for score, row, scout_row, flags in candidates:
        tier = quality_tier(score, flags)
        if tier == "C_hold":
            continue
        rank += 1
        board.append(
            {
                "board_rank": str(rank),
                "board_id": f"APNB{rank:03d}",
                "triage_id": norm(row.get("triage_id")),
                "scout_candidate_id": norm(row.get("scout_candidate_id")),
                "entity_id": norm(row.get("entity_id")),
                "source_type": norm(row.get("source_type")),
                "source_url": norm(row.get("source_url")),
                "candidate_image_url": norm(row.get("candidate_image_url")),
                "image_alt": norm(row.get("image_alt")),
                "source_domain": norm((scout_row or {}).get("source_domain")),
                "visual_priority": norm(row.get("visual_priority")),
                "candidate_quality_tier": tier,
                "score": str(score),
                "candidate_board_recommendation": recommendation(tier, flags),
                "candidate_risk_flags": "; ".join(flags),
                "manual_decision_needed": "inspect_remote_image_then_choose_approve_reject_or_hold",
                "formal_intake_ready": "no",
                "formal_intake_required_fields": required_fields,
                "face_likely_visible": norm(row.get("face_likely_visible")),
                "body_margin_likely": norm(row.get("body_margin_likely")),
                "four_by_five_crop_potential": norm(row.get("four_by_five_crop_potential")),
                "text_safe_negative_space": norm(row.get("text_safe_negative_space")),
                "source_provenance_clarity": norm(row.get("source_provenance_clarity")),
                "identity_confidence": norm((scout_row or {}).get("identity_confidence")),
                "operator_fair_use_asserted": norm((scout_row or {}).get("operator_fair_use_asserted")) or "yes",
                "operator_decision": "",
                "operator_notes": "",
                "download_approved": "no",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "none",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
        if len(board) >= limit:
            break
    return board


def build_report(manifest: dict[str, Any], board: list[dict[str, str]]) -> str:
    rows = "\n".join(
        [
            "| {rank} | `{candidate}` | {entity} | {tier} | {score} | {flags} | [source]({source}) | [image]({image}) |".format(
                rank=row["board_rank"],
                candidate=row["scout_candidate_id"],
                entity=row["entity_id"],
                tier=row["candidate_quality_tier"],
                score=row["score"],
                flags=row["candidate_risk_flags"],
                source=row["source_url"],
                image=row["candidate_image_url"],
            )
            for row in board
        ]
    )
    if not rows:
        rows = "| - | - | - | - | - | - | - | - |"
    return f"""# Action Photo Next Candidate Board V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This review-only packet converts existing local remote-triage/scout metadata into the next candidate inspection board. It does not download images, approve assets, enable sources, create publish-ready output, or publish.

## What To Do Next

1. Open the direct image/source links for the top rows.
2. Reject wrong-person, group-only, or weak-crop candidates quickly.
3. For one strong candidate, fill the formal intake fields separately before any quarantine-only download workflow.

## Board

| Rank | Candidate | Entity | Tier | Score | Risk flags | Source | Image |
| --- | --- | --- | --- | ---: | --- | --- | --- |
{rows}

## Guardrails

- review_only=true
- download_approved=no for every row
- asset_downloads=false
- approval_state_change=none
- publish_ready=false
- publishing=false
- source_auto_enabled=false
"""


def build_packet(
    *,
    remote_triage_csv: Path,
    scout_csv: Path,
    output_dir: Path,
    head_commit: str = "",
    limit: int = 12,
) -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    remote_triage_csv = remote_triage_csv.resolve(strict=False)
    scout_csv = scout_csv.resolve(strict=False)
    remote_rows = read_csv(remote_triage_csv)
    scout_rows = read_csv(scout_csv)
    board = build_board(remote_rows, scout_rows, limit)

    csv_path = output_dir / CSV_NAME
    manifest_path = output_dir / MANIFEST_NAME
    report_path = output_dir / REPORT_NAME
    write_csv(csv_path, board, CSV_FIELDS)

    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "action_photo_next_candidate_board_ready" if board else "action_photo_next_candidate_board_empty",
        "repo_head": head_commit,
        "remote_triage_csv": remote_triage_csv.as_posix(),
        "scout_csv": scout_csv.as_posix(),
        "output_dir": output_dir.as_posix(),
        "report_path": report_path.as_posix(),
        "csv_path": csv_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "remote_rows_read": len(remote_rows),
        "scout_rows_read": len(scout_rows),
        "board_row_count": len(board),
        "top_candidate_id": board[0]["scout_candidate_id"] if board else "",
        "review_only": True,
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest, board))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only next action-photo candidate board.")
    parser.add_argument("--remote-triage-csv", default=DEFAULT_REMOTE_TRIAGE_CSV.as_posix())
    parser.add_argument("--scout-csv", default=DEFAULT_SCOUT_CSV.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    parser.add_argument("--limit", type=int, default=12)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_packet(
        remote_triage_csv=resolve_path(args.remote_triage_csv),
        scout_csv=resolve_path(args.scout_csv),
        output_dir=resolve_output_dir(args.output_dir or None),
        head_commit=args.head_commit,
        limit=args.limit,
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "board_row_count": manifest["board_row_count"],
                "top_candidate_id": manifest["top_candidate_id"],
            },
            indent=2,
        )
    )
    return 0 if manifest["status"] == "action_photo_next_candidate_board_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
