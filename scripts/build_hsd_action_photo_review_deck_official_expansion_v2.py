from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts.build_hsd_action_photo_review_deck_ui_v1 import build_packet, resolve_output_dir, resolve_path


VERSION = "hsd-action-photo-review-deck-official-expansion-v2-review-only"
DEFAULT_OFFICIAL_EXPANSION_CSV = Path(
    "outputs/local/latest/files/action_photo_official_source_expansion_v3/action_photo_candidate_intake.csv"
)
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_review_deck_official_expansion_v2")
DEFAULT_LIMIT = 36


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build a local review-only action-photo deck from the official-source expansion candidates."
    )
    parser.add_argument("--board-csv", default=DEFAULT_OFFICIAL_EXPANSION_CSV.as_posix())
    parser.add_argument("--proof-manifest", default="")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--limit", type=int, default=DEFAULT_LIMIT)
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = resolve_output_dir(args.output_dir or None)
    proof_manifest = resolve_path(args.proof_manifest) if args.proof_manifest else output_dir / "no_renderer_proofs.json"
    manifest = build_packet(
        board_csv=resolve_path(args.board_csv),
        proof_manifest=proof_manifest,
        output_dir=output_dir,
        limit=max(1, args.limit),
        head_commit=args.head_commit,
    )
    manifest["version_wrapper"] = VERSION
    manifest["source_packet"] = "action_photo_official_source_expansion_v3"
    Path(str(manifest["manifest_path"])).write_text(json.dumps(manifest, indent=2, sort_keys=True), encoding="utf-8")
    print(
        json.dumps(
            {
                "version": VERSION,
                "status": manifest["status"],
                "deck_item_count": manifest["deck_item_count"],
                "candidate_item_count": manifest["candidate_item_count"],
                "output_dir": manifest["output_dir"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
