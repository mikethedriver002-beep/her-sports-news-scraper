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


def is_review_now(row: dict[str, str]) -> bool:
    tier = clean(row.get("source_quality_tier"))
    return tier.startswith("A") or tier.startswith("B")


def deck_input_rows(ranker_rows: list[dict[str, str]], limit: int) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for row in ranker_rows:
        if not is_review_now(row):
            continue
        if lower(row.get("download_approved")) not in {"", "no", "false", "0"}:
            continue
        if lower(row.get("publish_ready")) not in {"", "false"}:
            continue
        rows.append(
            {
                "scout_candidate_id": clean(row.get("scout_candidate_id")),
                "entity_id": clean(row.get("entity_id")),
                "source_type": clean(row.get("source_type")),
                "source_url": clean(row.get("source_url")),
                "candidate_image_url": clean(row.get("candidate_image_url")),
                "image_alt": clean(row.get("image_alt")),
                "source_domain": source_domain(clean(row.get("source_url"))),
                "score": clean(row.get("source_quality_score")),
                "visual_priority": "P1_ranker_manual_review",
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
        )
        if len(rows) >= limit:
            break
    return rows


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a focused swipe review deck from source-quality ranker A/B rows."
    )
    parser.add_argument("--ranker-csv", default=DEFAULT_RANKER_CSV.as_posix())
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
    ranker_rows = read_csv_rows(ranker_csv)
    input_rows = deck_input_rows(ranker_rows, max(1, args.limit))
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
    Path(str(manifest["manifest_path"])).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "deck_item_count": manifest["deck_item_count"],
                "candidate_item_count": manifest["candidate_item_count"],
                "review_now_rows_selected": manifest["review_now_rows_selected"],
                "output_dir": manifest["output_dir"],
            },
            indent=2,
        )
    )
    return 0 if input_rows else 1


if __name__ == "__main__":
    raise SystemExit(main())
