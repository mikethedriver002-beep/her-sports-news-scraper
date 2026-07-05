from __future__ import annotations

import argparse
import csv
import hashlib
import mimetypes
import json
import shutil
import subprocess
import tempfile
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Iterable
from urllib.error import URLError
from urllib.parse import urlparse
from urllib.request import Request, url2pathname, urlopen

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text
from scripts.build_hsd_action_photo_review_deck_ui_v1 import build_packet as build_review_deck_packet


VERSION = "hsd-wnba-unified-swipe-deck-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_unified_swipe_deck_v1.py"
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LATEST_FILES_ROOT = REPO_ROOT / "outputs" / "local" / "latest" / "files"
DEFAULT_MANUAL_DECISIONS_CSV = DEFAULT_LATEST_FILES_ROOT / "wnba_manual_decision_batch_v1" / "normalized_review_deck_decisions.csv"
DEFAULT_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "tmp" / "wnba_unified_swipe_deck_v1"
DEFAULT_LATEST_OUTPUT_DIR = REPO_ROOT / "outputs" / "local" / "latest" / "files" / "wnba_unified_swipe_deck_v1"
PREVIEW_CACHE_DIR_NAME = "preview_cache"
MAX_PREVIEW_CACHE_BYTES = 10 * 1024 * 1024

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
    "candidate_image_remote_url",
    "preview_cache_path",
    "preview_cache_status",
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
    "preview_cache_only",
    "candidate_downloads",
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


def read_decision_rows(path: Path) -> list[dict[str, str]]:
    return read_csv_rows(path)


def numeric_score(row: dict[str, str]) -> int:
    raw = clean(row.get("visual_rank_score") or row.get("score") or row.get("source_scout_score") or "0")
    try:
        return int(float(raw))
    except ValueError:
        return 0


def source_family(row: dict[str, str], fallback: str) -> str:
    return clean(row.get("source_family_id") or fallback)


def decision_group_key(row: dict[str, str]) -> tuple[str, str]:
    candidate_id = clean(row.get("candidate_id") or row.get("candidate_queue_id") or row.get("scout_candidate_id") or row.get("board_id"))
    return candidate_id.lower(), clean(row.get("entity_id")).lower()


def file_url_to_path(parsed) -> Path:
    raw_path = url2pathname(parsed.path)
    if sys.platform.startswith("win") and raw_path.startswith(("/", "\\")) and len(raw_path) > 3 and raw_path[2] == ":":
        raw_path = raw_path.lstrip("/\\")
    if parsed.netloc:
        if raw_path.startswith("\\\\") or raw_path.startswith("//"):
            pass
        else:
            raw_path = f"//{parsed.netloc}{raw_path}"
    return Path(raw_path)


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
        "candidate_image_remote_url": clean(row.get("candidate_image_remote_url") or row.get("candidate_image_url")),
        "preview_cache_path": clean(row.get("preview_cache_path")),
        "preview_cache_status": clean(row.get("preview_cache_status") or "remote_pending"),
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
        "preview_cache_only": "true",
        "candidate_downloads": "false",
        "asset_downloads": "false",
        "approval_state_change": "false",
        "publish_ready": "false",
        "publishing": "false",
    }


def preview_cache_extension(remote_url: str) -> str:
    parsed = urlparse(remote_url)
    suffix = Path(parsed.path).suffix.lower()
    if suffix == ".jpeg":
        return ".jpg"
    if suffix in {".jpg", ".png", ".gif", ".webp"}:
        return suffix
    guessed, _ = mimetypes.guess_type(parsed.path)
    if guessed == "image/png":
        return ".png"
    if guessed == "image/webp":
        return ".webp"
    if guessed == "image/gif":
        return ".gif"
    return ".jpg"


def fetch_preview_bytes(remote_url: str, timeout_seconds: int = 20) -> bytes:
    parsed = urlparse(remote_url)
    if parsed.scheme == "file":
        local_path = file_url_to_path(parsed)
        if local_path.stat().st_size > MAX_PREVIEW_CACHE_BYTES:
            raise ValueError(f"Preview cache source exceeds {MAX_PREVIEW_CACHE_BYTES} bytes: {remote_url}")
        return local_path.read_bytes()
    request = Request(remote_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            content_length = response.headers.get("Content-Length")
            if content_length and content_length.isdigit() and int(content_length) > MAX_PREVIEW_CACHE_BYTES:
                raise ValueError(f"Preview cache source exceeds {MAX_PREVIEW_CACHE_BYTES} bytes: {remote_url}")
            payload = response.read(MAX_PREVIEW_CACHE_BYTES + 1)
            if len(payload) > MAX_PREVIEW_CACHE_BYTES:
                raise ValueError(f"Preview cache source exceeds {MAX_PREVIEW_CACHE_BYTES} bytes: {remote_url}")
            return payload
    except (URLError, OSError, ValueError):
        curl = shutil.which("curl.exe") or shutil.which("curl")
        if not curl:
            raise
        with tempfile.NamedTemporaryFile(prefix="wnba_preview_cache_", suffix=preview_cache_extension(remote_url), delete=False) as temp_handle:
            temp_file = Path(temp_handle.name)
        try:
            subprocess.run(
                [
                    curl,
                    "--fail",
                    "--location",
                    "--silent",
                    "--show-error",
                    "--max-time",
                    str(timeout_seconds),
                    "--max-filesize",
                    str(MAX_PREVIEW_CACHE_BYTES),
                    "--output",
                    temp_file.as_posix(),
                    remote_url,
                ],
                check=True,
                capture_output=True,
                text=True,
            )
            if temp_file.exists():
                payload = temp_file.read_bytes()
                if len(payload) > MAX_PREVIEW_CACHE_BYTES:
                    raise ValueError(f"Preview cache source exceeds {MAX_PREVIEW_CACHE_BYTES} bytes: {remote_url}")
                return payload
        finally:
            if temp_file.exists():
                try:
                    temp_file.unlink()
                except OSError:
                    pass
    raise ValueError(f"Unable to fetch preview bytes for {remote_url}")


def preview_cache_path(cache_dir: Path, row: dict[str, str]) -> Path:
    basis = "|".join(
        [
            clean(row.get("candidate_queue_id")),
            clean(row.get("entity_id")),
            clean(row.get("candidate_image_remote_url") or row.get("candidate_image_url")),
        ]
    )
    suffix = preview_cache_extension(clean(row.get("candidate_image_remote_url") or row.get("candidate_image_url")))
    return cache_dir / f"{hashlib.sha256(basis.encode('utf-8')).hexdigest()[:20]}{suffix}"


def materialize_preview_cache(
    rows: list[dict[str, str]],
    cache_dir: Path,
    *,
    fetcher: Callable[[str], bytes] = fetch_preview_bytes,
) -> list[dict[str, str]]:
    cache_dir.mkdir(parents=True, exist_ok=True)
    materialized: list[dict[str, str]] = []
    for row in rows:
        remote_url = clean(row.get("candidate_image_remote_url") or row.get("candidate_image_url"))
        cached_row = dict(row)
        cached_row["candidate_image_remote_url"] = remote_url
        if not remote_url:
            cached_row["preview_cache_status"] = "missing_remote_url"
            cached_row["preview_cache_path"] = ""
            cached_row["candidate_image_url"] = ""
            materialized.append(cached_row)
            continue
        target = preview_cache_path(cache_dir, cached_row)
        if not target.exists():
            target.write_bytes(fetcher(remote_url))
        cached_row["preview_cache_path"] = target.resolve(strict=False).as_posix()
        cached_row["candidate_image_url"] = target.resolve(strict=False).as_uri()
        cached_row["preview_cache_status"] = "cached"
        materialized.append(cached_row)
    return materialized


def combined_rows(
    latest_files_root: Path,
    *,
    manual_decisions_csv: Path,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
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
    decision_rows = read_decision_rows(manual_decisions_csv)
    suppressed_keys = {decision_group_key(row) for row in decision_rows if decision_group_key(row) != ("", "")}
    kept_rows = [row for row in normalized if decision_group_key(row) not in suppressed_keys]
    return kept_rows, {
        "source_counts": source_counts,
        "source_paths": source_paths,
        "manual_decisions_csv": manual_decisions_csv.as_posix(),
        "manual_decision_rows": len(decision_rows),
        "suppressed_reviewed_candidates": len(normalized) - len(kept_rows),
    }


def mirror_output_tree(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    skipped: list[str] = []
    for path in source.rglob("*"):
        relative = path.relative_to(source)
        target = destination / relative
        try:
            if path.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, target)
        except (PermissionError, OSError):
            skipped.append(relative.as_posix())
    if skipped:
        raise PermissionError(f"Skipped {len(skipped)} mirrored path(s): {', '.join(skipped[:5])}")


def render_empty_deck(manifest: dict[str, Any]) -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>WNBA Unified Swipe Deck</title>
  <style>
    body {{
      margin: 0;
      min-height: 100vh;
      background: #0b0f16;
      color: #f4f6fa;
      font: 16px/1.5 Arial, Helvetica, sans-serif;
      display: grid;
      place-items: center;
      padding: 32px;
    }}
    .panel {{
      max-width: 760px;
      border: 1px solid #2a3342;
      background: #121824;
      padding: 28px;
      box-shadow: 0 28px 70px rgba(0, 0, 0, 0.35);
    }}
    h1 {{
      margin: 0 0 10px;
      font-size: clamp(28px, 5vw, 42px);
    }}
    p {{ color: #aeb8c6; }}
    code {{ color: #f7d58b; }}
  </style>
</head>
<body>
  <section class="panel">
    <h1>No WNBA swipe cards remain</h1>
    <p>The latest normalized manual decisions suppressed every reviewed candidate, so this run intentionally produced an empty review deck.</p>
    <p>Preview cache is review-only under <code>{manifest["preview_cache_dir"]}</code>, and the next useful artifact is the manual decision batch packet at <code>{manifest["manual_decisions_csv"]}</code>.</p>
  </section>
</body>
</html>
"""


def render_report(manifest: dict[str, Any]) -> str:
    source_counts = manifest["source_counts"]
    mirror_errors = manifest.get("latest_mirror_errors") or []
    mirror_section = ""
    if mirror_errors:
        mirror_section = "\n## Latest Mirror\n\n- Status: partial\n- Errors: " + "; ".join(mirror_errors) + "\n"
    return f"""# WNBA Unified Swipe Deck V1

Status: `{manifest['status']}`
Generated: `{manifest['generated_at_utc']}`

This is the current WNBA-only Tinder-style manual review surface. It wraps the existing action-photo swipe deck UI around Fever, Storm, and Aces candidates so Mike reviews one card at a time instead of juggling tables.

## Counts

- Deck items: `{manifest['deck_item_count']}`
- Suppressed reviewed candidates: `{manifest['suppressed_reviewed_candidates']}`
- Fever rows: `{source_counts.get('wnba_fever_visual_rank', 0)}`
- Storm rows: `{source_counts.get('wnba_storm_visual_rank', 0)}`
- Aces rows: `{source_counts.get('wnba_aces_source_scout', 0)}`
- Manual decision rows read: `{manifest['manual_decision_rows']}`

## Manual Action

1. Open `review_deck/action_photo_review_deck.html`.
2. Swipe right or click Carry Forward only for strong WNBA action-photo candidates.
3. Swipe left or reject quickly for wrong-person, group-heavy, bad-crop, graphic-looking, or visually weak rows.
4. Export the decision CSV from the deck.

If the deck is empty, that is expected after processing the latest reviewed WNBA decisions. This is the empty review deck, and the useful artifact is the manual decision batch packet.

{mirror_section}

## Guardrails

- review_only=true
- download_approved=no
- preview_cache_only=true
- candidate_downloads=false
- asset_downloads=false
- approval_state_change=false
- publish_ready=false
- publishing=false
- no new downloads
- no source auto-enablement
"""


def build_packet(
    *,
    latest_files_root: Path,
    output_dir: Path,
    latest_output_dir: Path | None = DEFAULT_LATEST_OUTPUT_DIR,
    manual_decisions_csv: Path = DEFAULT_MANUAL_DECISIONS_CSV,
    limit: int = 50,
    preview_fetcher: Callable[[str], bytes] = fetch_preview_bytes,
) -> dict[str, Any]:
    latest_files_root = latest_files_root.resolve(strict=False)
    manual_decisions_csv = manual_decisions_csv.resolve(strict=False)
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)
    rows, source_meta = combined_rows(latest_files_root, manual_decisions_csv=manual_decisions_csv)
    rows = rows[: max(0, limit)]
    preview_cache_dir = output_dir / PREVIEW_CACHE_DIR_NAME
    rows = materialize_preview_cache(rows, preview_cache_dir, fetcher=preview_fetcher) if rows else []

    board_path = output_dir / COMBINED_BOARD_NAME
    report_path = output_dir / REPORT_NAME
    manifest_path = output_dir / MANIFEST_NAME
    empty_proof_manifest = output_dir / EMPTY_PROOF_MANIFEST_NAME
    review_deck_dir = output_dir / REVIEW_DECK_DIR_NAME

    write_csv(board_path, rows, BOARD_FIELDS)
    write_json(empty_proof_manifest, {"proof_rows": []}, sort_keys=True)
    if rows:
        deck_manifest = build_review_deck_packet(
            board_csv=board_path,
            proof_manifest=empty_proof_manifest,
            output_dir=review_deck_dir,
            limit=len(rows),
            head_commit="",
        )
    else:
        review_deck_dir.mkdir(parents=True, exist_ok=True)
        html_path = review_deck_dir / "action_photo_review_deck.html"
        decision_path = review_deck_dir / "manual_decision_export_template.csv"
        deck_manifest_path = review_deck_dir / "manifest.json"
        deck_report_path = review_deck_dir / "action_photo_review_deck_report.md"
        write_text(
            html_path,
            render_empty_deck(
                {
                    "preview_cache_dir": preview_cache_dir.as_posix(),
                    "manual_decisions_csv": manual_decisions_csv.as_posix(),
                }
            ),
        )
        write_csv(
            decision_path,
            [],
            [
                "deck_item_id",
                "item_kind",
                "candidate_id",
                "entity_id",
                "source_url",
                "image_or_render_url",
                "operator_decision",
                "operator_notes",
                "manual_reviewer",
                "reviewed_at_utc",
                "formal_intake_next_action",
                "review_only",
                "download_approved",
                "asset_downloads",
                "approval_state_change",
                "publish_ready",
                "publishing",
            ],
        )
        deck_manifest = {
            "status": "action_photo_review_deck_ui_ready",
            "html_path": html_path.as_posix(),
            "decision_template_path": decision_path.as_posix(),
            "manifest_path": deck_manifest_path.as_posix(),
            "report_path": deck_report_path.as_posix(),
            "candidate_item_count": 0,
            "renderer_proof_item_count": 0,
            "deck_item_count": 0,
            "browser_storage_key": "",
            "cross_deck_decision_recovery": True,
            "review_only": True,
            "download_approved_default": "no",
        }
        write_json(deck_manifest_path, deck_manifest, sort_keys=True)
        write_text(deck_report_path, "Empty review deck produced after suppressing all reviewed WNBA candidates.\n")
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_unified_swipe_deck_ready",
        "review_only": True,
        "latest_files_root": latest_files_root.as_posix(),
        "manual_decisions_csv": manual_decisions_csv.as_posix(),
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
        "manual_decision_rows": source_meta["manual_decision_rows"],
        "suppressed_reviewed_candidates": source_meta["suppressed_reviewed_candidates"],
        "preview_cache_dir": preview_cache_dir.as_posix(),
        "preview_cache_only": True,
        "candidate_downloads": False,
        "download_approved": False,
        "asset_downloads": False,
        "approval_state_change": False,
        "publish_ready": False,
        "publishing": False,
        "source_auto_enabled": False,
        "latest_mirror_built": False,
        "latest_mirror_errors": [],
    }
    write_text(report_path, render_report(manifest))
    write_json(manifest_path, manifest, sort_keys=True)
    if latest_output_dir:
        latest_output_dir = latest_output_dir.resolve(strict=False)
        mirror_errors: list[str] = []
        try:
            mirror_output_tree(output_dir, latest_output_dir)
            manifest["latest_mirror_built"] = True
        except Exception as exc:
            mirror_errors.append(str(exc))
        manifest["latest_mirror_errors"] = mirror_errors
        write_text(report_path, render_report(manifest))
        write_json(manifest_path, manifest, sort_keys=True)
        write_json(latest_output_dir / MANIFEST_NAME, manifest, sort_keys=True)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build one WNBA-only Tinder-style swipe deck from current WNBA source boards.")
    parser.add_argument("--latest-files-root", default=DEFAULT_LATEST_FILES_ROOT.as_posix())
    parser.add_argument("--manual-decisions-csv", default=DEFAULT_MANUAL_DECISIONS_CSV.as_posix())
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
        manual_decisions_csv=Path(args.manual_decisions_csv),
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
