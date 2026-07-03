from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text


VERSION = "hsd-action-photo-source-quality-ranker-v1-review-only"
GENERATED_BY = "scripts/build_hsd_action_photo_source_quality_ranker_v1.py"
DEFAULT_INPUT_CSVS = [
    Path("outputs/local/latest/files/action_photo_ausl_source_expansion_v1/action_photo_candidate_intake.csv"),
    Path("outputs/local/latest/files/action_photo_pwhl_source_expansion_v1/action_photo_candidate_intake.csv"),
    Path("outputs/local/latest/files/action_photo_official_source_expansion_v3/action_photo_candidate_intake.csv"),
    Path("outputs/local/latest/files/action_photo_wta_lpga_source_expansion_v1/action_photo_candidate_intake.csv"),
    Path("outputs/local/latest/files/action_photo_nwsl_source_expansion_v4/action_photo_candidate_intake.csv"),
]
DEFAULT_REJECT_LOG_CSVS = [
    Path("outputs/local/latest/files/action_photo_recovered_decision_reject_log_v1/recovered_decision_reject_log.csv"),
    Path("outputs/local/latest/files/action_photo_ranker_manual_decision_intake_adapter_v1/rejected_or_held_review_deck_decisions.csv"),
    Path("outputs/local/latest/files/action_photo_ausl_manual_decision_intake_adapter_v1/rejected_or_held_review_deck_decisions.csv"),
]
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_source_quality_ranker_v1")
CSV_NAME = "action_photo_source_quality_ranker.csv"
REPORT_NAME = "action_photo_source_quality_ranker_report.md"
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

CSV_FIELDS = [
    "rank",
    "ranker_id",
    "source_packet",
    "scout_candidate_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "apparent_width",
    "apparent_height",
    "source_quality_score",
    "source_quality_tier",
    "source_quality_recommendation",
    "fast_reject_reason",
    "positive_signals",
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

HIGH_VALUE_TERMS = {
    "action",
    "celebrate",
    "celebrates",
    "complete game shutout",
    "double",
    "doubles",
    "goal",
    "hit",
    "home run",
    "pitch",
    "pitches",
    "scored",
    "scoring",
    "shutout",
    "winner",
}
HERO_URL_TERMS = {
    "articlehero",
    "feature",
    "hero",
    "mobilehero",
    "openingday2026_hero",
}
MOBILE_URL_TERMS = {"_mob", "_mobile", "mobilehero"}
CMS_GRAPHIC_URL_TERMS = {
    "graphic",
    "header",
    "promo",
    "social",
    "template",
    "thumbnail",
}
GROUP_TERMS = {"all six teams", "celebrate", "celebrates", "team", "teams", "group"}
GENERIC_NAME_TOKENS = {
    "action",
    "article",
    "ausl",
    "blaze",
    "candidate",
    "cdn",
    "feature",
    "gallery",
    "game",
    "hero",
    "image",
    "jpg",
    "jpeg",
    "mobile",
    "opening",
    "photo",
    "png",
    "recap",
    "team",
    "webp",
}


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


def camel_spaced(value: str) -> str:
    return re.sub(r"([a-z])([A-Z])", r"\1 \2", value)


def token_set(value: str) -> set[str]:
    spaced = camel_spaced(value)
    return {part.lower() for part in re.split(r"[^A-Za-z0-9]+", spaced) if len(part) >= 3}


def entity_tokens(entity_id: str) -> set[str]:
    parts = [part for part in re.split(r"[_\W]+", lower(entity_id)) if len(part) >= 3]
    if len(parts) <= 2:
        return set(parts)
    return set(parts[-3:])


def image_url_tokens(url: str) -> set[str]:
    filename = clean(url).rsplit("/", 1)[-1].rsplit("?", 1)[0]
    return token_set(filename) - GENERIC_NAME_TOKENS


def image_extension(url: str) -> str:
    filename = clean(url).rsplit("/", 1)[-1].rsplit("?", 1)[0]
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[-1].lower()


def source_packet_name(path: Path) -> str:
    parent = path.parent.name
    if parent and parent != "files":
        return parent
    return path.stem


def int_value(value: object) -> int | None:
    raw = clean(value)
    if not raw:
        return None
    try:
        return int(float(raw))
    except ValueError:
        return None


def landscape_ratio_flag(row: Mapping[str, str]) -> str:
    width = int_value(row.get("apparent_width"))
    height = int_value(row.get("apparent_height"))
    if not width or not height:
        return ""
    if width > height:
        return "landscape_dimensions_weak_4x5"
    if height / width < 1.12:
        return "not_vertical_enough_for_4x5"
    return "vertical_or_unknown_ok"


def named_context_signal(row: Mapping[str, str]) -> str:
    tokens = entity_tokens(clean(row.get("entity_id")))
    text = " ".join(
        [
            lower(row.get("image_alt")),
            lower(row.get("notes_evidence")),
            lower(row.get("candidate_image_url")),
            lower(row.get("source_url")),
        ]
    )
    if tokens and any(token in text for token in tokens):
        return "named_context_match"
    return "named_context_unverified"


def filename_identity_signal(row: Mapping[str, str]) -> str:
    tokens = entity_tokens(clean(row.get("entity_id")))
    image_tokens = image_url_tokens(clean(row.get("candidate_image_url")))
    if tokens and image_tokens and tokens & image_tokens:
        return "image_filename_match"
    if image_tokens:
        return "image_filename_unverified"
    return "missing_image_filename"


def positive_signals(row: Mapping[str, str]) -> list[str]:
    text = lower(row.get("image_alt")) + " " + lower(row.get("notes_evidence"))
    signals: list[str] = []
    for term in sorted(HIGH_VALUE_TERMS):
        if term in text:
            signals.append(f"context:{term}")
    if lower(row.get("source_provenance_clarity")) == "clear":
        signals.append("clear_provenance")
    if "official" in lower(row.get("source_type")):
        signals.append("official_source")
    if lower(row.get("face_likely_visible")) == "likely":
        signals.append("face_likely_metadata")
    if lower(row.get("body_margin_likely")) == "likely":
        signals.append("body_margin_likely")
    if lower(row.get("four_by_five_crop_potential")) in {"possible", "likely"}:
        signals.append("possible_4x5")
    if lower(row.get("text_safe_negative_space")) in {"possible", "likely"}:
        signals.append("text_space_possible")
    if named_context_signal(row) == "named_context_match":
        signals.append("named_context_match")
    if filename_identity_signal(row) == "image_filename_match":
        signals.append("image_filename_match")
    return signals


def risk_flags(row: Mapping[str, str]) -> list[str]:
    flags: list[str] = []
    image_url = lower(row.get("candidate_image_url"))
    filename = image_url.rsplit("/", 1)[-1].rsplit("?", 1)[0]
    text = lower(row.get("image_alt")) + " " + lower(row.get("notes_evidence")) + " " + filename
    extension = image_extension(image_url)

    if any(term in filename for term in HERO_URL_TERMS):
        flags.append("likely_cms_hero_asset")
    if any(term in filename for term in MOBILE_URL_TERMS):
        flags.append("mobile_hero_variant")
    if any(term in filename for term in CMS_GRAPHIC_URL_TERMS):
        flags.append("possible_cms_graphic")
    if "screenshot" in filename:
        flags.append("screenshot_asset")
    if extension == "png" and any(term in filename for term in HERO_URL_TERMS | MOBILE_URL_TERMS | CMS_GRAPHIC_URL_TERMS):
        flags.append("png_cms_layout_asset")
    ratio_flag = landscape_ratio_flag(row)
    if ratio_flag and ratio_flag != "vertical_or_unknown_ok":
        flags.append(ratio_flag)
    if named_context_signal(row) != "named_context_match":
        flags.append("named_context_unverified")
    if filename_identity_signal(row) != "image_filename_match":
        flags.append(filename_identity_signal(row))
    if lower(row.get("body_margin_likely")) in {"", "unclear"}:
        flags.append("body_margin_unclear")
    if lower(row.get("four_by_five_crop_potential")) not in {"possible", "likely"}:
        flags.append("weak_4x5_metadata")
    if any(term in text for term in GROUP_TERMS):
        flags.append("possible_group_or_team_context")
    return flags or ["none"]


def score_row(row: Mapping[str, str]) -> int:
    signals = positive_signals(row)
    flags = risk_flags(row)
    score = 0
    score += 2 * sum(signal.startswith("context:") for signal in signals)
    score += 4 if "clear_provenance" in signals else 0
    score += 3 if "official_source" in signals else 0
    score += 4 if "face_likely_metadata" in signals else 0
    score += 5 if "body_margin_likely" in signals else 0
    score += 5 if "possible_4x5" in signals else 0
    score += 3 if "text_space_possible" in signals else 0
    score += 5 if "named_context_match" in signals else 0
    score += 5 if "image_filename_match" in signals else 0

    penalties = {
        "likely_cms_hero_asset": 10,
        "mobile_hero_variant": 7,
        "possible_cms_graphic": 8,
        "screenshot_asset": 8,
        "png_cms_layout_asset": 8,
        "landscape_dimensions_weak_4x5": 12,
        "not_vertical_enough_for_4x5": 7,
        "named_context_unverified": 6,
        "image_filename_unverified": 4,
        "missing_image_filename": 3,
        "body_margin_unclear": 5,
        "weak_4x5_metadata": 6,
        "possible_group_or_team_context": 4,
    }
    for flag in flags:
        score -= penalties.get(flag, 0)
    return score


def severe_fast_reject_flags(flags: list[str]) -> list[str]:
    severe = [
        flag
        for flag in flags
        if flag
        in {
            "likely_cms_hero_asset",
            "mobile_hero_variant",
            "possible_cms_graphic",
            "screenshot_asset",
            "png_cms_layout_asset",
            "landscape_dimensions_weak_4x5",
        }
    ]
    return severe


def quality_tier(score: int, flags: list[str]) -> str:
    if severe_fast_reject_flags(flags):
        return "D_fast_reject_or_low_priority"
    if score >= 24 and flags == ["none"]:
        return "A_inspect_first"
    if score >= 18:
        return "B_manual_review"
    if score >= 8:
        return "C_hold_backup"
    return "D_fast_reject_or_low_priority"


def recommendation(tier: str, flags: list[str]) -> str:
    if tier.startswith("A"):
        return "inspect_first_for_formal_intake_candidate"
    if tier.startswith("B"):
        return "manual_visual_review"
    if severe_fast_reject_flags(flags):
        return "reject_fast_unless_visual_deck_proves_raw_action"
    return "hold_unless_source_pool_runs_dry"


def fast_reject_reason(flags: list[str]) -> str:
    severe = severe_fast_reject_flags(flags)
    return "; ".join(severe) if severe else ""


def eligible_candidate(row: Mapping[str, str]) -> bool:
    return (
        lower(row.get("fetch_status")) == "candidate_metadata_extracted"
        and bool(clean(row.get("candidate_image_url")))
        and lower(row.get("download_approved")) in {"", "no", "false", "0"}
        and lower(row.get("publish_ready")) in {"", "false"}
    )


def candidate_key(row: Mapping[str, str], candidate_field: str = "scout_candidate_id") -> tuple[str, str]:
    return (clean(row.get(candidate_field)), clean(row.get("entity_id")))


def reject_keys(reject_logs: list[list[dict[str, str]]]) -> set[tuple[str, str]]:
    keys: set[tuple[str, str]] = set()
    for rows in reject_logs:
        for row in rows:
            decision = lower(row.get("decision")) or lower(row.get("operator_decision"))
            manual_next_action = lower(row.get("manual_next_action"))
            if not decision.startswith("reject") and "rejected" not in manual_next_action:
                continue
            candidate_id = clean(row.get("candidate_id")) or clean(row.get("scout_candidate_id"))
            entity_id = clean(row.get("entity_id"))
            if candidate_id and entity_id:
                keys.add((candidate_id, entity_id))
    return keys


def build_ranked_rows(
    input_sets: list[tuple[str, list[dict[str, str]]]],
    limit: int,
    closed_reject_keys: set[tuple[str, str]] | None = None,
) -> list[dict[str, str]]:
    scored: list[tuple[int, str, list[str], list[str], dict[str, str]]] = []
    seen: set[tuple[str, str]] = set()
    rejected = closed_reject_keys or set()
    for packet, rows in input_sets:
        for row in rows:
            if not eligible_candidate(row):
                continue
            if candidate_key(row) in rejected:
                continue
            key = (clean(row.get("scout_candidate_id")), clean(row.get("candidate_image_url")))
            if key in seen:
                continue
            seen.add(key)
            flags = risk_flags(row)
            signals = positive_signals(row)
            score = score_row(row)
            scored.append((score, packet, flags, signals, row))

    scored.sort(
        key=lambda item: (
            item[3] != ["none"] and -len(severe_fast_reject_flags(item[2])),
            item[0],
            "named_context_match" in item[3],
            "image_filename_match" in item[3],
        ),
        reverse=True,
    )

    output: list[dict[str, str]] = []
    for index, (score, packet, flags, signals, row) in enumerate(scored[:limit], start=1):
        tier = quality_tier(score, flags)
        output.append(
            {
                "rank": str(index),
                "ranker_id": f"APSQ{index:03d}",
                "source_packet": packet,
                "scout_candidate_id": clean(row.get("scout_candidate_id")),
                "entity_id": clean(row.get("entity_id")),
                "source_type": clean(row.get("source_type")),
                "source_url": clean(row.get("source_url")),
                "candidate_image_url": clean(row.get("candidate_image_url")),
                "image_alt": clean(row.get("image_alt")),
                "apparent_width": clean(row.get("apparent_width")),
                "apparent_height": clean(row.get("apparent_height")),
                "source_quality_score": str(score),
                "source_quality_tier": tier,
                "source_quality_recommendation": recommendation(tier, flags),
                "fast_reject_reason": fast_reject_reason(flags),
                "positive_signals": "; ".join(signals or ["none"]),
                "risk_flags": "; ".join(flags),
                "manual_decision_needed": "inspect_visual_card_then_reject_hold_or_carry_forward",
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


def build_report(manifest: Mapping[str, Any], rows: list[dict[str, str]]) -> str:
    table = "\n".join(
        "| {rank} | `{candidate}` | {packet} | {tier} | {score} | {reason} | [source]({source}) | [image]({image}) |".format(
            rank=row["rank"],
            candidate=row["scout_candidate_id"],
            packet=row["source_packet"],
            tier=row["source_quality_tier"],
            score=row["source_quality_score"],
            reason=row["fast_reject_reason"] or row["source_quality_recommendation"],
            source=row["source_url"],
            image=row["candidate_image_url"],
        )
        for row in rows[:30]
    )
    if not table:
        table = "| - | - | - | - | - | - | - | - |"
    fast_reject_rows = [row for row in rows if row["source_quality_tier"].startswith("D")]
    fast_reject_table = "\n".join(
        "| {candidate} | {packet} | {reason} | [image]({image}) |".format(
            candidate=row["scout_candidate_id"],
            packet=row["source_packet"],
            reason=row["fast_reject_reason"] or row["risk_flags"],
            image=row["candidate_image_url"],
        )
        for row in fast_reject_rows[:20]
    )
    if not fast_reject_table:
        fast_reject_table = "| - | - | - | - |"
    fast_reject_count = sum(1 for row in rows if row["source_quality_tier"].startswith("D"))
    review_count = sum(1 for row in rows if row["source_quality_tier"].startswith(("A", "B")))
    return f"""# Action Photo Source Quality Ranker V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This review-only packet ranks existing scout metadata for manual visual triage. It is designed to downrank likely CMS hero/mobile/screenshot/landscape assets before Mike spends time swiping through weak cards. It does not download images, approve assets, enable sources, move assets, mark anything publish-ready, or publish.

## Blunt Read

- Rows ranked: {manifest['ranked_row_count']}
- Closed reject keys suppressed: {manifest['closed_reject_keys_applied']}
- Visual-review-now rows: {review_count}
- Fast-reject or low-priority rows: {fast_reject_count}
- Input packets: {', '.join(manifest['input_packets'])}

Use this board as a companion to the swipe review deck: inspect A/B rows first, reject D rows quickly unless the visual deck clearly proves the metadata heuristic wrong.

## Ranked Board

| Rank | Candidate | Packet | Tier | Score | Reason | Source | Image |
| --- | --- | --- | --- | ---: | --- | --- | --- |
{table}

## Fast-Reject / Low-Priority Highlights

These rows should be rejected quickly unless the visual deck proves the metadata heuristic wrong.

| Candidate | Packet | Reason | Image |
| --- | --- | --- | --- |
{fast_reject_table}

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
    input_csvs: list[Path],
    reject_log_csvs: list[Path] | None = None,
    output_dir: Path,
    head_commit: str = "",
    limit: int = 80,
) -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    resolved_inputs = [path.resolve(strict=False) for path in input_csvs]
    resolved_reject_logs = [path.resolve(strict=False) for path in (reject_log_csvs or [])]
    input_sets = [(source_packet_name(path), read_csv_rows(path)) for path in resolved_inputs]
    reject_log_rows = [read_csv_rows(path) for path in resolved_reject_logs if path.exists()]
    closed_rejects = reject_keys(reject_log_rows)
    rows = build_ranked_rows(input_sets, limit, closed_rejects)

    csv_path = output_dir / CSV_NAME
    report_path = output_dir / REPORT_NAME
    manifest_path = output_dir / MANIFEST_NAME
    write_csv(csv_path, rows, CSV_FIELDS)

    tier_counts: dict[str, int] = {}
    for row in rows:
        tier_counts[row["source_quality_tier"]] = tier_counts.get(row["source_quality_tier"], 0) + 1

    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "action_photo_source_quality_ranker_ready" if rows else "action_photo_source_quality_ranker_empty",
        "repo_head": head_commit,
        "input_csvs": [path.as_posix() for path in resolved_inputs],
        "reject_log_csvs": [path.as_posix() for path in resolved_reject_logs],
        "input_packets": [packet for packet, _ in input_sets],
        "input_rows_read": sum(len(input_rows) for _, input_rows in input_sets),
        "closed_reject_keys_applied": len(closed_rejects),
        "ranked_row_count": len(rows),
        "tier_counts": tier_counts,
        "top_candidate_id": rows[0]["scout_candidate_id"] if rows else "",
        "output_dir": output_dir.as_posix(),
        "csv_path": csv_path.as_posix(),
        "report_path": report_path.as_posix(),
        "manifest_path": manifest_path.as_posix(),
        "download_approved_default": "no",
        "review_only": True,
        **FALSE_GUARDRAILS,
    }
    write_csv(csv_path, rows, CSV_FIELDS)
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest, rows))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only action-photo source-quality ranker.")
    parser.add_argument("--input-csv", action="append", default=[], help="Scout intake CSV to rank. Repeatable.")
    parser.add_argument("--reject-log-csv", action="append", default=[], help="Closed reject log CSV to suppress. Repeatable.")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--head-commit", default="")
    parser.add_argument("--limit", type=int, default=80)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    input_csvs = [resolve_path(path) for path in (args.input_csv or [path.as_posix() for path in DEFAULT_INPUT_CSVS])]
    reject_log_csvs = [
        resolve_path(path) for path in (args.reject_log_csv or [path.as_posix() for path in DEFAULT_REJECT_LOG_CSVS])
    ]
    manifest = build_packet(
        input_csvs=input_csvs,
        reject_log_csvs=reject_log_csvs,
        output_dir=resolve_output_dir(args.output_dir or None),
        head_commit=args.head_commit,
        limit=args.limit,
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "ranked_row_count": manifest["ranked_row_count"],
                "top_candidate_id": manifest["top_candidate_id"],
                "tier_counts": manifest["tier_counts"],
            },
            indent=2,
        )
    )
    return 0 if manifest["status"] == "action_photo_source_quality_ranker_ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
