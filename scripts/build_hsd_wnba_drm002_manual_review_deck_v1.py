from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text
from scripts.build_hsd_action_photo_review_deck_ui_v1 import build_packet as build_review_deck_packet


VERSION = "hsd-wnba-drm002-manual-review-deck-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_drm002_manual_review_deck_v1.py"
DEFAULT_INTAKE_CSV = Path(
    "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
)
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_drm002_manual_review_deck_v1")
DEFAULT_LATEST_OUTPUT_DIR = Path("outputs/local/latest/files/wnba_drm002_manual_review_deck_v1")
TARGET_CANDIDATE_ID = "DRM002"

BOARD_FIELDS = [
    "board_rank",
    "board_id",
    "scout_candidate_id",
    "candidate_queue_id",
    "entity_id",
    "source_type",
    "source_url",
    "candidate_image_url",
    "candidate_remote_image_url",
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


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def read_csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(newline="", encoding="utf-8", errors="replace") as handle:
        return list(csv.DictReader(handle))


def clean(value: Any) -> str:
    return " ".join(str(value or "").strip().split())


def find_drm002(rows: list[dict[str, str]]) -> dict[str, str]:
    for row in rows:
        if clean(row.get("candidate_queue_id")) == TARGET_CANDIDATE_ID:
            return row
    raise SystemExit(f"{TARGET_CANDIDATE_ID} not found in intake CSV")


def file_uri(path: Path) -> str:
    return path.resolve(strict=False).as_uri()


def placeholder_svg(row: dict[str, str]) -> str:
    source_url = clean(row.get("source_url"))
    candidate_url = clean(row.get("candidate_photo_url"))
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="1080" height="1350" viewBox="0 0 1080 1350">
  <rect width="1080" height="1350" fill="#111418"/>
  <rect x="52" y="52" width="976" height="1246" rx="0" fill="#181c23" stroke="#d8dde6" stroke-width="3"/>
  <text x="88" y="128" fill="#f6f7fb" font-family="Arial, Helvetica, sans-serif" font-size="42" font-weight="700">DRM002 MANUAL REVIEW</text>
  <text x="88" y="184" fill="#b9c0cc" font-family="Arial, Helvetica, sans-serif" font-size="24">Atlanta Dream official recap hero candidate</text>
  <rect x="88" y="236" width="904" height="638" fill="#0d0f13" stroke="#424955" stroke-width="2"/>
  <text x="128" y="326" fill="#f6f7fb" font-family="Arial, Helvetica, sans-serif" font-size="34" font-weight="700">Preview gated</text>
  <text x="128" y="382" fill="#c7ceda" font-family="Arial, Helvetica, sans-serif" font-size="25">The deck starts with this local placeholder.</text>
  <text x="128" y="430" fill="#c7ceda" font-family="Arial, Helvetica, sans-serif" font-size="25">Use the deck button to load the remote preview manually.</text>
  <text x="128" y="506" fill="#7fffd4" font-family="Arial, Helvetica, sans-serif" font-size="24">Source URL</text>
  <foreignObject x="128" y="532" width="808" height="122">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font:23px Arial;color:#f1f5f9;line-height:1.25;word-break:break-word;">{source_url}</div>
  </foreignObject>
  <text x="128" y="704" fill="#7fffd4" font-family="Arial, Helvetica, sans-serif" font-size="24">Candidate image URL metadata</text>
  <foreignObject x="128" y="730" width="808" height="96">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font:23px Arial;color:#f1f5f9;line-height:1.25;word-break:break-word;">{candidate_url}</div>
  </foreignObject>
  <text x="88" y="954" fill="#f6f7fb" font-family="Arial, Helvetica, sans-serif" font-size="30" font-weight="700">Decision Needed</text>
  <foreignObject x="88" y="984" width="884" height="150">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font:25px Arial;color:#c7ceda;line-height:1.45;">Carry forward only if Mike verifies the source, identity context, rights posture, and action-photo fit. A carry-forward decision is not a download approval and not asset approval.</div>
  </foreignObject>
  <foreignObject x="88" y="1190" width="884" height="70">
    <div xmlns="http://www.w3.org/1999/xhtml" style="font:25px Arial;color:#f6f7fb;line-height:1.35;">Review-only. No downloads. No approval-state changes. No publish-ready state.</div>
  </foreignObject>
</svg>
"""


def enhance_review_deck_html(html_path: str | Path, *, remote_preview_url: str) -> None:
    path = Path(html_path)
    html_text = path.read_text(encoding="utf-8")
    if "load-remote-preview" in html_text:
        return
    button_html = (
        '<button id="load-remote-preview" type="button" title="Manually load the remote preview in this browser">'
        "Load Remote Preview</button>"
    )
    html_text = html_text.replace(
        '<a id="source" class="button" target="_blank" rel="noreferrer">Open Source</a>',
        '<a id="source" class="button" target="_blank" rel="noreferrer">Open Source</a>\n'
        f"          {button_html}",
    )
    script = f"""
    const drm002RemotePreviewUrl = {json.dumps(remote_preview_url)};
    const drm002OriginalRender = render;
    render = function() {{
      drm002OriginalRender();
      const loadButton = document.getElementById("load-remote-preview");
      if (loadButton) {{
        loadButton.onclick = function() {{
          const item = active();
          if (!item || item.candidate_id !== "DRM002") return;
          const image = document.getElementById("image");
          image.src = drm002RemotePreviewUrl;
          image.alt = "DRM002 remote preview loaded manually by operator";
          loadButton.textContent = "Remote Preview Loaded";
          loadButton.disabled = true;
        }};
      }}
    }};
"""
    html_text = html_text.replace("    render();\n  </script>", script + "    render();\n  </script>")
    path.write_text(html_text, encoding="utf-8")


def board_row(row: dict[str, str], placeholder_path: Path) -> dict[str, str]:
    return {
        "board_rank": "1",
        "board_id": "WNBA_DRM002_MANUAL_REVIEW",
        "scout_candidate_id": TARGET_CANDIDATE_ID,
        "candidate_queue_id": TARGET_CANDIDATE_ID,
        "entity_id": clean(row.get("entity_id")),
        "source_type": "official_team_recap",
        "source_url": clean(row.get("source_url")),
        "candidate_image_url": file_uri(placeholder_path),
        "candidate_remote_image_url": clean(row.get("candidate_photo_url")),
        "image_alt": "DRM002 Atlanta Dream recap hero candidate; local placeholder used to avoid automatic remote image loading.",
        "source_domain": "dream.wnba.com",
        "visual_priority": "P1_manual_review_now",
        "candidate_quality_tier": "source_intake_ready",
        "score": "",
        "candidate_board_recommendation": (
            "Manual source review card for DRM002. Open the source, verify the hero image and rights/source context, "
            "then export a manual decision CSV from this deck."
        ),
        "candidate_risk_flags": "no_local_proof_image_yet; remote_image_not_loaded_by_deck; human_download_decision_required",
        "manual_decision_needed": "yes",
        "formal_intake_ready": "yes",
        "face_likely_visible": "manual_source_open_required",
        "body_margin_likely": "manual_source_open_required",
        "four_by_five_crop_potential": "manual_source_open_required",
        "text_safe_negative_space": "manual_source_open_required",
        "source_provenance_clarity": "official_team_recap",
        "identity_confidence": clean(row.get("identity_confidence")),
        "operator_fair_use_asserted": "",
        "download_approved": "no",
        "review_only": "true",
        "asset_downloads": "false",
        "approval_state_change": "false",
        "publish_ready": "false",
        "publishing": "false",
    }


def build_report(manifest: dict[str, Any]) -> str:
    return f"""# WNBA DRM002 Manual Review Deck V1

Status: `{manifest['status']}`
Version: `{VERSION}`

This packet gives DRM002 a Tinder-style manual review surface without automatically loading or downloading the remote WNBA image. The card uses a local placeholder and links to the source for human inspection.

## Outputs

- Review deck: `{manifest['review_deck_html']}`
- Manual decision template: `{manifest['manual_decision_template']}`
- Board CSV: `{manifest['board_csv']}`
- Deck manifest: `{manifest['review_deck_manifest']}`

## Blunt Read

- DRM002 now has the right manual-review UX shape.
- It still cannot produce premium Photoshop comps until a human verifies and later approves quarantine-only download review.
- A carry-forward export from this deck is only a manual decision handoff, not download approval.

## Guardrails

- review_only=true
- download_approved=no
- remote_image_loaded_by_deck=false
- asset_downloads=false
- approval_state_change=false
- publish_ready=false
- publishing=false
"""


def mirror_latest(output_dir: Path, latest_dir: Path) -> None:
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(output_dir, latest_dir)


def build_packet(
    *,
    intake_csv: Path,
    output_dir: Path,
    latest_output_dir: Path | None = None,
    head_commit: str = "",
) -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)

    row = find_drm002(read_csv_rows(intake_csv))
    placeholder_path = write_text(output_dir / "drm002_manual_review_placeholder.svg", placeholder_svg(row), if_changed=False)
    board_csv = write_csv(output_dir / "drm002_manual_review_board.csv", [board_row(row, placeholder_path)], BOARD_FIELDS)
    empty_proof_manifest = write_json(output_dir / "empty_proof_manifest.json", {"proof_rows": []}, sort_keys=True)
    review_deck_dir = output_dir / "review_deck"
    deck_manifest = build_review_deck_packet(
        board_csv=board_csv,
        proof_manifest=empty_proof_manifest,
        output_dir=review_deck_dir,
        limit=1,
        head_commit=head_commit,
    )
    remote_preview_url = clean(row.get("candidate_photo_url"))
    enhance_review_deck_html(deck_manifest["html_path"], remote_preview_url=remote_preview_url)
    manifest_path = output_dir / "manifest.json"
    report_path = output_dir / "manual_review_deck_report.md"
    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "wnba_drm002_manual_review_deck_ready",
        "repo_head": head_commit,
        "candidate_queue_id": TARGET_CANDIDATE_ID,
        "intake_csv": intake_csv.as_posix(),
        "output_dir": output_dir.as_posix(),
        "board_csv": board_csv.as_posix(),
        "placeholder_path": placeholder_path.as_posix(),
        "review_deck_html": deck_manifest["html_path"],
        "manual_decision_template": deck_manifest["decision_template_path"],
        "review_deck_manifest": deck_manifest["manifest_path"],
        "report_path": report_path.as_posix(),
        "remote_image_reference": remote_preview_url,
        "remote_preview_mode": "operator_click_to_load_in_browser",
        "remote_image_loaded_by_deck": False,
        "review_only": True,
        "download_approved": "no",
        "asset_downloads": False,
        "approval_state_change": False,
        "publish_ready": False,
        "publishing": False,
    }
    write_json(manifest_path, manifest, sort_keys=True)
    write_text(report_path, build_report(manifest))
    if latest_output_dir:
        mirror_latest(output_dir, latest_output_dir.resolve(strict=False))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a DRM002 review-only Tinder-style manual review deck.")
    parser.add_argument("--intake-csv", default=DEFAULT_INTAKE_CSV.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-output-dir", default=DEFAULT_LATEST_OUTPUT_DIR.as_posix())
    parser.add_argument("--no-latest", action="store_true")
    parser.add_argument("--head-commit", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    latest = None if args.no_latest else resolve_path(args.latest_output_dir)
    manifest = build_packet(
        intake_csv=resolve_path(args.intake_csv),
        output_dir=resolve_output_dir(args.output_dir or None),
        latest_output_dir=latest,
        head_commit=args.head_commit,
    )
    print(json.dumps({"status": manifest["status"], "review_deck_html": manifest["review_deck_html"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
