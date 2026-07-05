from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import write_csv, write_json, write_text
from scripts.build_hsd_action_photo_review_deck_ui_v1 import build_packet as build_review_deck_packet


VERSION = "hsd-wnba-fire-gallery-source-scout-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_fire_gallery_source_scout_v1.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SEED_CSV = (
    REPO_ROOT
    / "data"
    / "asset_registry"
    / "action_photo_candidates"
    / "review_only_action_photo_candidate_scout_wnba_fire_photo_gallery_v1.csv"
)
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "tmp" / "wnba_official_source_expansion_highres_v12"
DEFAULT_LATEST_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "latest" / "files" / "wnba_official_source_expansion_highres_v12"

INTAKE_FIELDS = [
    "candidate_queue_id",
    "candidate_photo_url",
    "evidence_url",
    "evidence_summary",
    "identity_anchor_url",
    "source_url",
    "entity_id",
    "rights_class",
    "identity_confidence",
    "intended_review_only_use",
    "notes",
    "operator_verify_required",
    "manual_reviewer",
    "manual_review_status",
    "manual_next_action",
    "download_approved",
    "quarantine_target_hint",
    "review_only",
    "publish_ready",
]
BOARD_FIELDS = [
    "board_rank",
    "source_family_id",
    "candidate_queue_id",
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
    return DEFAULT_OUTPUT_DIR


def resolve_path(path: str | Path) -> Path:
    candidate = Path(path)
    return candidate if candidate.is_absolute() else REPO_ROOT / candidate


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    import csv

    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def write_csv_rows(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    write_csv(path, rows, fields)


def row_score(seed: dict[str, str]) -> tuple[int, str, list[str]]:
    image_url = clean(seed.get("candidate_image_url"))
    flags: list[str] = []
    score = 84
    if image_url.endswith("-scaled.jpg"):
        score += 4
        flags.append("high_res_gallery_frame")
    elif image_url.endswith(".png"):
        score += 2
        flags.append("high_res_gallery_tile")
    if "news-card" in image_url:
        score -= 12
        flags.append("branded_tile_not_action_frame")
    if "home-opener" in image_url:
        flags.append("promo_opener_context")
    tier = "A_primary_source_lead" if score >= 88 else "B_strong_source_lead" if score >= 78 else "C_secondary_source_lead"
    return max(0, min(100, score)), tier, flags or ["gallery_context"]


def build_rows(seed_rows: list[dict[str, str]]) -> tuple[list[dict[str, str]], list[dict[str, str]], int]:
    intake_rows: list[dict[str, str]] = []
    board_rows: list[dict[str, str]] = []
    thumbnail_suffix_count = 0

    for index, seed in enumerate(seed_rows, start=1):
        seed_id = clean(seed.get("seed_id"))
        source_url = clean(seed.get("source_page_url"))
        image_url = clean(seed.get("candidate_image_url"))
        source_label = clean(seed.get("source_label") or "Portland Fire official photo gallery")
        entity_id = clean(seed.get("entity_id") or "wnba_portland_fire_home_opener_gallery_2026_05_09")
        rights_class = clean(seed.get("rights_class") or "official_review_needed")
        confidence = clean(seed.get("identity_confidence") or "medium")
        intended_use = clean(seed.get("intended_review_only_use") or "wnba_source_quality_metadata_only")
        notes = clean(seed.get("notes"))
        score, tier, flags = row_score(seed)
        candidate_id = f"PFG{index:03d}"
        thumbnail_suffix_count += 1 if any(token in image_url.lower() for token in ("-185x148", "-260x190", "-300x78", "-320x180", "-640x360", "-1024x576")) else 0
        shared_notes = (
            f"{notes} "
            "Review-only metadata-first scouting for a public Portland Fire photo gallery; "
            "no downloads, approvals, source auto-enablement, or publish-ready state."
        ).strip()

        intake_rows.append(
            {
                "candidate_queue_id": candidate_id,
                "candidate_photo_url": image_url,
                "evidence_url": source_url,
                "evidence_summary": f"{source_label} with high-resolution public gallery frame metadata.",
                "identity_anchor_url": "https://fire.wnba.com/news",
                "source_url": source_url,
                "entity_id": entity_id,
                "rights_class": rights_class,
                "identity_confidence": confidence,
                "intended_review_only_use": intended_use,
                "notes": shared_notes,
                "operator_verify_required": "yes",
                "manual_reviewer": "",
                "manual_review_status": "not_reviewed",
                "manual_next_action": "Open the Fire gallery frame and confirm the crop still works as a review-only action-photo lead.",
                "download_approved": "no",
                "quarantine_target_hint": clean(seed.get("quarantine_target_hint")),
                "review_only": "true",
                "publish_ready": "false",
            }
        )
        board_rows.append(
            {
                "board_rank": str(index),
                "source_family_id": "wnba_portland_fire_photo_gallery",
                "candidate_queue_id": candidate_id,
                "seed_id": seed_id,
                "entity_id": entity_id,
                "source_type": clean(seed.get("source_type") or "official_team_gallery"),
                "source_url": source_url,
                "candidate_image_url": image_url,
                "image_alt": clean(seed.get("image_alt") or source_label),
                "source_domain": "fire.wnba.com",
                "visual_priority": "P1_visual_review_now" if score >= 88 else "P2_visual_review_soon",
                "candidate_quality_tier": tier,
                "score": str(score),
                "candidate_board_recommendation": "manual_inspect_for_formal_intake",
                "candidate_risk_flags": "|".join(flags),
                "manual_decision_needed": "yes",
                "formal_intake_ready": "no",
                "face_likely_visible": clean(seed.get("face_likely_visible") or "possible"),
                "body_margin_likely": clean(seed.get("body_margin_likely") or "possible"),
                "four_by_five_crop_potential": clean(seed.get("four_by_five_crop_potential") or "possible"),
                "text_safe_negative_space": clean(seed.get("text_safe_negative_space") or "possible"),
                "source_provenance_clarity": "clear",
                "identity_confidence": confidence,
                "operator_fair_use_asserted": "yes",
                "notes": shared_notes,
                "download_approved": "no",
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )

    board_rows.sort(key=lambda row: (-int(row["score"]), row["board_rank"]))
    for new_rank, row in enumerate(board_rows, start=1):
        row["board_rank"] = str(new_rank)
    return intake_rows, board_rows, thumbnail_suffix_count


def render_report(manifest: dict[str, Any]) -> str:
    rows = manifest.get("board_rows", [])
    lines = [
        "# WNBA Fire Gallery Source Scout V1",
        "",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "Review-only metadata-first source scout for the official Portland Fire photo-gallery lane.",
        "",
        "## Summary",
        "",
        f"- Seed rows: `{manifest['seed_row_count']}`",
        f"- Candidate rows: `{manifest['candidate_row_count']}`",
        f"- Deck built: `{manifest['deck_built']}`",
        f"- Latest mirror built: `{manifest['latest_mirror_built']}`",
        f"- High-res gallery frames: `{manifest['high_res_gallery_frame_count']}`",
        f"- Thumbnail suffix count: `{manifest['thumbnail_suffix_count']}`",
        f"- Usefulness verdict: `{manifest['source_family_usefulness_verdict']}`",
        "",
        "## Strongest Rows",
        "",
    ]
    if rows:
        lines.append("| Rank | Candidate | Score | Tier | Image | Source |")
        lines.append("| --- | --- | --- | --- | --- | --- |")
        for row in rows:
            lines.append(
                f"| {row['board_rank']} | {row['candidate_queue_id']} | {row['score']} | {row['candidate_quality_tier']} | {row['candidate_image_url']} | {row['source_url']} |"
            )
    else:
        lines.append("No useful candidate rows were extracted.")
    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- download_approved=no",
            "- publish_ready=false",
            "- asset_downloads=false",
            "- approval_state_change=false",
            "- no paid APIs",
            "- no source auto-enablement",
            "- no publishing",
        ]
    )
    return "\n".join(lines) + "\n"


def mirror_output_tree(source_dir: Path, mirror_dir: Path) -> None:
    mirror_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_dir, mirror_dir, dirs_exist_ok=True)


def build_packet(
    *,
    seed_csv: Path,
    output_dir: Path,
    latest_output_dir: Path = DEFAULT_LATEST_OUTPUT_DIR,
) -> dict[str, Any]:
    seed_rows = read_csv_rows(seed_csv)
    intake_rows, board_rows, thumbnail_suffix_count = build_rows(seed_rows)
    output_dir.mkdir(parents=True, exist_ok=True)
    seed_path = output_dir / "wnba_fire_gallery_source_scout_seed.csv"
    intake_path = output_dir / "wnba_fire_gallery_source_scout_intake.csv"
    board_path = output_dir / "wnba_fire_gallery_source_scout_board.csv"
    report_path = output_dir / "wnba_fire_gallery_source_scout_report.md"
    manifest_path = output_dir / "manifest.json"
    deck_output_dir = output_dir / "review_deck"

    write_csv_rows(seed_path, seed_rows, list(seed_rows[0].keys()) if seed_rows else [])
    write_csv_rows(intake_path, intake_rows, INTAKE_FIELDS)
    write_csv_rows(board_path, board_rows, BOARD_FIELDS)

    high_res_gallery_frame_count = sum(1 for row in board_rows if "high_res_gallery_frame" in row["candidate_risk_flags"])
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_fire_gallery_source_scout_ready" if intake_rows else "wnba_fire_gallery_source_scout_empty",
        "review_only": True,
        "seed_row_count": len(seed_rows),
        "candidate_row_count": len(intake_rows),
        "seed_csv_path": repo_rel(seed_path),
        "intake_csv_path": repo_rel(intake_path),
        "board_csv_path": repo_rel(board_path),
        "report_path": repo_rel(report_path),
        "output_dir": repo_rel(output_dir),
        "latest_output_dir": repo_rel(latest_output_dir),
        "high_res_gallery_frame_count": high_res_gallery_frame_count,
        "thumbnail_suffix_count": thumbnail_suffix_count,
        "source_family_usefulness_verdict": "useful_high_res_official_gallery_family" if board_rows else "not_useful_no_candidate_rows",
        "board_rows": board_rows,
        "intake_rows": intake_rows,
        "guardrails": {
            "review_only": True,
            "download_approved": False,
            "publish_ready": False,
            "asset_downloads": False,
            "approval_state_change": False,
            "no_paid_apis": True,
            "no_source_auto_enablement": True,
            "no_publish_ready_lane": True,
        },
        "deck_built": False,
        "latest_mirror_built": False,
    }

    if intake_rows:
        deck_manifest = build_review_deck_packet(
            board_csv=board_path,
            proof_manifest=output_dir / "empty_proof_manifest.json",
            output_dir=deck_output_dir,
            limit=max(1, len(board_rows)),
            head_commit="",
        )
        manifest["deck_built"] = True
        manifest["deck_manifest_path"] = deck_manifest.get("manifest_path", "")
        manifest["deck_output_dir"] = deck_manifest.get("output_dir", "")
        manifest["deck_status"] = deck_manifest.get("status", "")
        manifest["deck_html_path"] = deck_manifest.get("html_path", "")
        manifest["deck_template_path"] = deck_manifest.get("decision_template_path", "")

    write_text(report_path, render_report(manifest))
    write_json(manifest_path, manifest, sort_keys=True)
    if latest_output_dir:
        mirror_output_tree(output_dir, latest_output_dir)
        manifest["latest_mirror_built"] = True
        write_json(latest_output_dir / "manifest.json", manifest, sort_keys=True)
    write_json(manifest_path, manifest, sort_keys=True)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the Portland Fire official photo-gallery source scout packet.")
    parser.add_argument("--seed-csv", default=DEFAULT_SEED_CSV.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-output-dir", default=DEFAULT_LATEST_OUTPUT_DIR.as_posix())
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = Path(args.output_dir) if args.output_dir else output_root()
    manifest = build_packet(seed_csv=resolve_path(args.seed_csv), output_dir=output_dir, latest_output_dir=resolve_path(args.latest_output_dir))
    print(
        json.dumps(
            {
                "status": manifest["status"],
                "candidate_row_count": manifest["candidate_row_count"],
                "output_dir": output_dir.as_posix(),
                "deck_built": manifest["deck_built"],
                "latest_mirror_built": manifest["latest_mirror_built"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
