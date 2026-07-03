from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-action-photo-pwhl-shortlist-board-v1-review-only"
GENERATED_BY = "scripts/build_hsd_action_photo_pwhl_shortlist_board_v1.py"
DEFAULT_INPUT_CSV = Path("outputs/local/latest/files/action_photo_pwhl_source_expansion_v1/action_photo_candidate_intake.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_pwhl_shortlist_board_v1")
CSV_NAME = "action_photo_pwhl_shortlist_board.csv"
REPORT_NAME = "action_photo_pwhl_shortlist_board_report.md"
MANIFEST_NAME = "manifest.json"

CSV_FIELDS = [
    "shortlist_rank",
    "shortlist_id",
    "scout_candidate_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "score",
    "quality_tier",
    "shortlist_recommendation",
    "scoring_reasons",
    "risk_flags",
    "manual_decision_needed",
    "formal_intake_ready",
    "face_likely_visible",
    "body_margin_likely",
    "four_by_five_crop_potential",
    "text_safe_negative_space",
    "source_provenance_clarity",
    "identity_confidence",
    "download_approved",
    "review_only",
    "asset_downloads",
    "approval_state_change",
    "publish_ready",
    "publishing",
]

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

HIGH_VALUE_TERMS = {
    "captured",
    "clinch",
    "clinched",
    "goal",
    "goals",
    "overtime",
    "playoff",
    "playoffs",
    "recorded",
    "scored",
    "scores",
    "shines",
    "shutout",
    "snipes",
    "victory",
    "win",
    "winner",
    "wins",
}

GROUP_RISK_TERMS = {"team", "channels", "press conferences", "post-game coverage", "fans"}


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


def clean(value: object) -> str:
    return str(value or "").strip()


def lower(value: object) -> str:
    return clean(value).lower()


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def entity_name_tokens(entity_id: str) -> set[str]:
    parts = [part for part in re.split(r"[_\W]+", lower(entity_id)) if len(part) >= 3]
    return set(parts[-3:])


def image_url_tokens(url: str) -> set[str]:
    filename = lower(url).rsplit("/", 1)[-1].rsplit("?", 1)[0]
    return {part for part in re.split(r"[^a-z0-9]+", filename) if len(part) >= 3}


def named_context_signal(row: Mapping[str, str]) -> str:
    tokens = entity_name_tokens(clean(row.get("entity_id")))
    text = lower(row.get("image_alt")) + " " + lower(row.get("notes_evidence")) + " " + lower(row.get("source_url"))
    if tokens and any(token in text for token in tokens):
        return "named_context_match"
    return "named_context_unverified"


def image_filename_signal(row: Mapping[str, str]) -> str:
    tokens = entity_name_tokens(clean(row.get("entity_id")))
    image_tokens = image_url_tokens(clean(row.get("candidate_image_url")))
    if tokens and image_tokens and tokens & image_tokens:
        return "image_filename_match"
    if image_tokens:
        return "image_filename_unverified"
    return "missing_image_filename"


def scoring_reasons(row: Mapping[str, str]) -> list[str]:
    reasons: list[str] = []
    text = lower(row.get("image_alt")) + " " + lower(row.get("notes_evidence"))
    for term in sorted(HIGH_VALUE_TERMS):
        if term in text:
            reasons.append(f"context:{term}")
    if "cloudinary.com/pwhl" in lower(row.get("candidate_image_url")):
        reasons.append("pwhl_cloudinary_image")
    if lower(row.get("source_provenance_clarity")) == "clear":
        reasons.append("clear_provenance")
    if "official" in lower(row.get("source_type")):
        reasons.append("official_source")
    if lower(row.get("four_by_five_crop_potential")) == "possible":
        reasons.append("possible_4x5")
    if lower(row.get("face_likely_visible")) == "likely":
        reasons.append("face_likely_metadata")
    signal = named_context_signal(row)
    if signal == "named_context_match":
        reasons.append(signal)
    filename_signal = image_filename_signal(row)
    if filename_signal == "image_filename_match":
        reasons.append(filename_signal)
    return reasons


def risk_flags(row: Mapping[str, str]) -> list[str]:
    flags: list[str] = []
    text = lower(row.get("image_alt")) + " " + lower(row.get("notes_evidence"))
    if named_context_signal(row) != "named_context_match":
        flags.append("named_context_unverified")
    if image_filename_signal(row) != "image_filename_match":
        flags.append(image_filename_signal(row))
    if lower(row.get("body_margin_likely")) in {"", "unclear"}:
        flags.append("body_margin_unclear")
    if lower(row.get("text_safe_negative_space")) not in {"possible", "likely"}:
        flags.append("negative_space_unclear")
    if any(term in text for term in GROUP_RISK_TERMS):
        flags.append("possible_group_or_press_context")
    return flags or ["none"]


def score_row(row: Mapping[str, str]) -> int:
    score = 0
    reasons = scoring_reasons(row)
    flags = risk_flags(row)
    score += 3 * sum(reason.startswith("context:") for reason in reasons)
    if "pwhl_cloudinary_image" in reasons:
        score += 5
    if "clear_provenance" in reasons:
        score += 4
    if "official_source" in reasons:
        score += 3
    if "possible_4x5" in reasons:
        score += 3
    if "face_likely_metadata" in reasons:
        score += 3
    if "named_context_match" in reasons:
        score += 5
    if "image_filename_match" in reasons:
        score += 4
    if "named_context_unverified" in flags:
        score -= 4
    if "body_margin_unclear" in flags:
        score -= 2
    if "possible_group_or_press_context" in flags:
        score -= 2
    return score


def quality_tier(score: int, flags: list[str]) -> str:
    if score >= 32 and flags == ["none"]:
        return "A_manual_inspect_first"
    if score >= 22 and "named_context_unverified" not in flags:
        return "B_visual_review_now"
    if score >= 16:
        return "C_hold_or_backup"
    return "D_reject_fast"


def recommendation(tier: str, flags: list[str]) -> str:
    if tier.startswith("A"):
        return "manual_inspect_for_formal_intake"
    if tier.startswith("B"):
        return "manual_visual_review_first"
    if "named_context_unverified" in flags:
        return "inspect_identity_context_before_download_intake"
    return "reserve_candidate"


def board_rows(input_rows: list[Mapping[str, str]], limit: int) -> list[dict[str, str]]:
    candidates = [
        row
        for row in input_rows
        if lower(row.get("fetch_status")) == "candidate_metadata_extracted" and clean(row.get("candidate_image_url"))
    ]
    scored: list[tuple[int, list[str], list[str], Mapping[str, str]]] = []
    for row in candidates:
        flags = risk_flags(row)
        reasons = scoring_reasons(row)
        scored.append((score_row(row), flags, reasons, row))
    scored.sort(key=lambda item: (item[0], "named_context_match" in item[2], "image_filename_match" in item[2]), reverse=True)

    output: list[dict[str, str]] = []
    for index, (score, flags, reasons, row) in enumerate(scored[:limit], start=1):
        tier = quality_tier(score, flags)
        output.append(
            {
                "shortlist_rank": str(index),
                "shortlist_id": f"PWHS{index:03d}",
                "scout_candidate_id": clean(row.get("scout_candidate_id")),
                "entity_id": clean(row.get("entity_id")),
                "source_type": clean(row.get("source_type")),
                "source_url": clean(row.get("source_url")),
                "candidate_image_url": clean(row.get("candidate_image_url")),
                "image_alt": clean(row.get("image_alt")),
                "score": str(score),
                "quality_tier": tier,
                "shortlist_recommendation": recommendation(tier, flags),
                "scoring_reasons": "|".join(reasons) or "metadata_only",
                "risk_flags": "|".join(flags),
                "manual_decision_needed": "yes",
                "formal_intake_ready": "no",
                "face_likely_visible": clean(row.get("face_likely_visible")),
                "body_margin_likely": clean(row.get("body_margin_likely")),
                "four_by_five_crop_potential": clean(row.get("four_by_five_crop_potential")),
                "text_safe_negative_space": clean(row.get("text_safe_negative_space")),
                "source_provenance_clarity": clean(row.get("source_provenance_clarity")),
                "identity_confidence": clean(row.get("identity_confidence")),
                "download_approved": "no",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "none",
                "publish_ready": "false",
                "publishing": "false",
            }
        )
    return output


def render_report(rows: list[Mapping[str, str]], manifest: Mapping[str, object]) -> str:
    lines = [
        "# PWHL Action Photo Shortlist Board V1",
        "",
        "This board ranks review-only PWHL action-photo metadata candidates for manual visual triage. It does not download images, approve assets, change approval state, create approved markers, mark publish-ready, or publish.",
        "",
        f"- Version: `{VERSION}`",
        f"- Source intake: `{manifest['source_intake_csv']}`",
        f"- Shortlist rows: `{len(rows)}`",
        f"- A-tier rows: `{sum(1 for row in rows if clean(row.get('quality_tier')).startswith('A'))}`",
        "",
        "## Shortlist",
        "",
        "| Rank | Candidate | Entity | Score | Tier | Recommendation | Risks |",
        "| --- | --- | --- | ---: | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            "| {rank} | {candidate} | {entity} | {score} | {tier} | {recommendation} | {risks} |".format(
                rank=clean(row.get("shortlist_rank")),
                candidate=clean(row.get("scout_candidate_id")),
                entity=clean(row.get("entity_id")),
                score=clean(row.get("score")),
                tier=clean(row.get("quality_tier")),
                recommendation=clean(row.get("shortlist_recommendation")),
                risks=clean(row.get("risk_flags")),
            )
        )
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- download_approved=no",
            "- asset_downloads=false",
            "- approval_state_change=none",
            "- publish_ready=false",
            "- publishing=false",
        ]
    )
    return "\n".join(lines) + "\n"


def build_packet(*, input_csv: Path, output_dir: Path, head_commit: str = "", limit: int = 24) -> dict[str, object]:
    resolved_input = resolve_path(input_csv)
    out_dir = resolve_output_dir(str(output_dir))
    out_dir.mkdir(parents=True, exist_ok=True)
    rows = board_rows(read_csv_rows(resolved_input), max(1, limit))
    csv_path = write_csv(out_dir / CSV_NAME, rows, CSV_FIELDS)
    manifest_path = out_dir / MANIFEST_NAME
    report_path = out_dir / REPORT_NAME
    manifest: dict[str, object] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "action_photo_pwhl_shortlist_board_ready",
        "repo_head": head_commit,
        "source_intake_csv": resolved_input.as_posix(),
        "output_dir": out_dir.as_posix(),
        "csv_path": csv_path.as_posix(),
        "report_path": report_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "shortlist_row_count": len(rows),
        "a_tier_rows": sum(1 for row in rows if clean(row.get("quality_tier")).startswith("A")),
        "csv_fields": CSV_FIELDS,
        "review_only": True,
        "download_approved_default": "no",
        **FALSE_GUARDRAILS,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, render_report(rows, manifest))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only PWHL action-photo shortlist board.")
    parser.add_argument("--input-csv", default=DEFAULT_INPUT_CSV.as_posix())
    parser.add_argument("--output-dir", default=DEFAULT_OUTPUT_DIR.as_posix())
    parser.add_argument("--head-commit", default="")
    parser.add_argument("--limit", type=int, default=24)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    manifest = build_packet(
        input_csv=Path(args.input_csv),
        output_dir=Path(args.output_dir),
        head_commit=args.head_commit,
        limit=args.limit,
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "shortlist_row_count": manifest["shortlist_row_count"],
                "a_tier_rows": manifest["a_tier_rows"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
