from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import write_csv
from scripts.build_hsd_action_photo_review_deck_ui_v1 import build_packet, resolve_output_dir, resolve_path


VERSION = "hsd-action-photo-ranker-review-deck-v1-review-only"
DEFAULT_RANKER_CSV = Path("outputs/local/latest/files/action_photo_source_quality_ranker_v1/action_photo_source_quality_ranker.csv")
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_ranker_review_deck_v1")
DEFAULT_LIMIT = 12
DECK_INPUT_CSV_NAME = "ranker_review_deck_input.csv"

DECK_INPUT_FIELDS = [
    "scout_candidate_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "image_alt",
    "source_domain",
    "score",
    "visual_priority",
    "candidate_quality_tier",
    "candidate_risk_flags",
    "identity_confidence",
    "face_likely_visible",
    "body_margin_likely",
    "four_by_five_crop_potential",
    "text_safe_negative_space",
    "download_approved",
    "review_only",
    "publish_ready",
    "asset_downloads",
    "approval_state_change",
]


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def clean(value: object) -> str:
    return str(value or "").strip()


def lower(value: object) -> str:
    return clean(value).lower()


def source_domain(url: str) -> str:
    return urlparse(clean(url)).netloc


def decision_key(candidate_id: str, entity_id: str, image_url: str) -> tuple[str, str, str]:
    return (clean(candidate_id), clean(entity_id), clean(image_url).lower())


def decision_exclusion_keys(decision_rows: list[dict[str, str]]) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for row in decision_rows:
        if not clean(row.get("operator_decision")):
            continue
        candidate_id = clean(row.get("candidate_id") or row.get("scout_candidate_id"))
        entity_id = clean(row.get("entity_id"))
        image_url = clean(row.get("image_or_render_url") or row.get("candidate_image_url"))
        if candidate_id and entity_id and image_url:
            keys.add(decision_key(candidate_id, entity_id, image_url))
    return keys


def read_decision_exclusion_keys(paths: list[Path]) -> set[tuple[str, str, str]]:
    keys: set[tuple[str, str, str]] = set()
    for path in paths:
        keys.update(decision_exclusion_keys(read_csv_rows(path)))
    return keys


def ranker_row_decision_key(row: dict[str, str]) -> tuple[str, str, str]:
    return decision_key(
        clean(row.get("scout_candidate_id")),
        clean(row.get("entity_id")),
        clean(row.get("candidate_image_url")),
    )


def is_review_now(row: dict[str, str]) -> bool:
    tier = clean(row.get("source_quality_tier"))
    return tier.startswith("A") or tier.startswith("B") or tier.startswith("C")


def visual_priority(row: dict[str, str]) -> str:
    tier = clean(row.get("source_quality_tier"))
    if tier.startswith("A") or tier.startswith("B"):
        return "P1_ranker_manual_review"
    return "P2_ranker_hold_backup_review"


def eligible_ranker_row(row: dict[str, str], excluded_decision_keys: set[tuple[str, str, str]]) -> bool:
    if not is_review_now(row):
        return False
    if lower(row.get("download_approved")) not in {"", "no", "false", "0"}:
        return False
    if lower(row.get("publish_ready")) not in {"", "false"}:
        return False
    if ranker_row_decision_key(row) in excluded_decision_keys:
        return False
    return True


def source_entity_cluster_key(row: dict[str, str]) -> tuple[str, str]:
    return (clean(row.get("entity_id")), lower(row.get("source_url")))


def to_deck_input_row(row: dict[str, str]) -> dict[str, str]:
    return {
        "scout_candidate_id": clean(row.get("scout_candidate_id")),
        "entity_id": clean(row.get("entity_id")),
        "source_type": clean(row.get("source_type")),
        "source_url": clean(row.get("source_url")),
        "candidate_image_url": clean(row.get("candidate_image_url")),
        "image_alt": clean(row.get("image_alt")),
        "source_domain": source_domain(clean(row.get("source_url"))),
        "score": clean(row.get("source_quality_score")),
        "visual_priority": visual_priority(row),
        "candidate_quality_tier": clean(row.get("source_quality_tier")),
        "candidate_risk_flags": clean(row.get("risk_flags")),
        "identity_confidence": clean(row.get("identity_confidence")),
        "face_likely_visible": clean(row.get("face_likely_visible")),
        "body_margin_likely": clean(row.get("body_margin_likely")),
        "four_by_five_crop_potential": clean(row.get("four_by_five_crop_potential")),
        "text_safe_negative_space": clean(row.get("text_safe_negative_space")),
        "download_approved": "no",
        "review_only": "true",
        "publish_ready": "false",
        "asset_downloads": "false",
        "approval_state_change": "none",
    }


def deck_input_rows(
    ranker_rows: list[dict[str, str]],
    limit: int,
    excluded_decision_keys: set[tuple[str, str, str]] | None = None,
) -> list[dict[str, str]]:
    excluded_decision_keys = excluded_decision_keys or set()
    eligible = [row for row in ranker_rows if eligible_ranker_row(row, excluded_decision_keys)]
    selected: list[dict[str, str]] = []
    selected_row_keys: set[tuple[str, str, str]] = set()
    selected_clusters: set[tuple[str, str]] = set()

    for row in eligible:
        cluster = source_entity_cluster_key(row)
        if cluster in selected_clusters:
            continue
        selected.append(row)
        selected_row_keys.add(ranker_row_decision_key(row))
        selected_clusters.add(cluster)
        if len(selected) >= limit:
            return [to_deck_input_row(item) for item in selected]

    for row in eligible:
        row_key = ranker_row_decision_key(row)
        if row_key in selected_row_keys:
            continue
        selected.append(row)
        selected_row_keys.add(row_key)
        if len(selected) >= limit:
            break

    return [to_deck_input_row(item) for item in selected]


def decision_exclusion_skip_count(
    ranker_rows: list[dict[str, str]],
    excluded_decision_keys: set[tuple[str, str, str]],
) -> int:
    skipped = 0
    for row in ranker_rows:
        if not eligible_ranker_row(row, set()):
            continue
        if ranker_row_decision_key(row) in excluded_decision_keys:
            skipped += 1
    return skipped


def selected_cluster_stats(rows: list[dict[str, str]]) -> dict[str, int]:
    clusters = [source_entity_cluster_key(row) for row in rows]
    unique_clusters = set(clusters)
    return {
        "selected_source_entity_clusters": len(unique_clusters),
        "selected_source_entity_refill_rows": len(rows) - len(unique_clusters),
    }


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a focused swipe review deck from source-quality ranker A/B rows."
    )
    parser.add_argument("--ranker-csv", default=DEFAULT_RANKER_CSV.as_posix())
    parser.add_argument(
        "--exclude-decisions-csv",
        action="append",
        default=[],
        help="Exported review-deck decision CSV to exclude from the next deck. Repeatable.",
    )
    parser.add_argument("--proof-manifest", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = resolve_output_dir(args.output_dir or None)
    output_dir.mkdir(parents=True, exist_ok=True)
    ranker_csv = resolve_path(args.ranker_csv)
    exclude_decision_csvs = [resolve_path(path) for path in args.exclude_decisions_csv]
    excluded_keys = read_decision_exclusion_keys(exclude_decision_csvs)
    ranker_rows = read_csv_rows(ranker_csv)
    input_rows = deck_input_rows(ranker_rows, max(1, args.limit), excluded_keys)
    skipped_by_decisions = decision_exclusion_skip_count(ranker_rows, excluded_keys)
    deck_input_csv = output_dir / DECK_INPUT_CSV_NAME
    write_csv(deck_input_csv, input_rows, DECK_INPUT_FIELDS)

    proof_manifest = resolve_path(args.proof_manifest) if args.proof_manifest else output_dir / "no_renderer_proofs.json"
    manifest = build_packet(
        board_csv=deck_input_csv,
        proof_manifest=proof_manifest,
        output_dir=output_dir,
        limit=max(1, args.limit),
        head_commit=args.head_commit,
    )
    manifest["version_wrapper"] = VERSION
    manifest["source_packet"] = "action_photo_source_quality_ranker_v1"
    manifest["ranker_csv"] = ranker_csv.resolve(strict=False).as_posix()
    manifest["deck_input_csv"] = deck_input_csv.resolve(strict=False).as_posix()
    manifest["ranker_rows_read"] = len(ranker_rows)
    manifest["review_now_rows_selected"] = len(input_rows)
    manifest["excluded_decision_csvs"] = [path.resolve(strict=False).as_posix() for path in exclude_decision_csvs]
    manifest["decision_exclusion_keys_applied"] = len(excluded_keys)
    manifest["ranker_rows_skipped_by_decision_exclusion"] = skipped_by_decisions
    cluster_stats = selected_cluster_stats(input_rows)
    manifest["source_entity_cluster_strategy"] = "first_pass_unique_then_refill"
    manifest["selected_source_entity_clusters"] = cluster_stats["selected_source_entity_clusters"]
    manifest["selected_source_entity_refill_rows"] = cluster_stats["selected_source_entity_refill_rows"]
    Path(str(manifest["manifest_path"])).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    report_path = Path(str(manifest["report_path"]))
    report_path.write_text(
        report_path.read_text(encoding="utf-8")
        + f"""

## Decision Exclusion

- Exported decision CSVs applied: {len(exclude_decision_csvs)}
- Unique decided deck rows excluded: {len(excluded_keys)}
- Ranker rows skipped before deck refill: {skipped_by_decisions}

## Source/Entity Cluster Collapse

- Strategy: first pass selects one card per `entity_id + source_url`; second pass refills duplicates only if the deck still has room.
- Source/entity clusters selected: {cluster_stats["selected_source_entity_clusters"]}
- Refill rows from already-represented clusters: {cluster_stats["selected_source_entity_refill_rows"]}
""",
        encoding="utf-8",
    )
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "deck_item_count": manifest["deck_item_count"],
                "candidate_item_count": manifest["candidate_item_count"],
                "review_now_rows_selected": manifest["review_now_rows_selected"],
                "ranker_rows_skipped_by_decision_exclusion": skipped_by_decisions,
                "output_dir": manifest["output_dir"],
            },
            indent=2,
        )
    )
    return 0 if input_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
