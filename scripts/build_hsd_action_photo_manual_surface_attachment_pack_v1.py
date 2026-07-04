from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text

try:
    from PIL import Image
except Exception:  # pragma: no cover - Pillow is expected in the local runtime.
    Image = None  # type: ignore[assignment]


VERSION = "hsd-action-photo-manual-surface-attachment-pack-v1-review-only"
GENERATED_BY = "scripts/build_hsd_action_photo_manual_surface_attachment_pack_v1.py"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/action_photo_manual_surface_attachment_pack_v1")
DEFAULT_LATEST_FILES_ROOT = Path("outputs/local/latest/files")
DEFAULT_SCREENSHOT_DIR = DEFAULT_OUTPUT_DIR / "browser_screenshots"

MANIFEST_NAME = "manifest.json"
INDEX_NAME = "action_photo_manual_surface_attachment_index.csv"
REPORT_NAME = "action_photo_manual_surface_attachment_pack_report.md"
ATTACHMENT_DIR_NAME = "attachments"
THUMBNAIL_DIR_NAME = "thumbnails"
THUMBNAIL_MAX_SIZE = 480


@dataclass(frozen=True)
class AttachmentSpec:
    surface_id: str
    surface_name: str
    source_kind: str
    source_path: Path
    attachment_name: str
    attachment_source_kind: str
    screenshot_source_name: str | None = None
    attachment_note: str = ""


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def resolve_root(raw: str | Path | None, default: Path) -> Path:
    if raw is None or str(raw).strip() == "":
        return default
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def file_uri(path: Path) -> str:
    return path.resolve(strict=False).as_uri()


def require_pillow() -> None:
    if Image is None:
        raise RuntimeError("Pillow is required to create thumbnails for the attachment pack")


def copy_file(source: Path, target: Path) -> Path:
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, target)
    return target


def make_thumbnail(source: Path, target: Path, *, max_size: int = THUMBNAIL_MAX_SIZE) -> Path:
    require_pillow()
    target.parent.mkdir(parents=True, exist_ok=True)
    with Image.open(source) as image:
        thumb = image.copy()
        thumb.thumbnail((max_size, max_size))
        thumb.save(target, "PNG")
    return target


def expected_specs(source_root: Path, screenshot_dir: Path) -> list[AttachmentSpec]:
    return [
        AttachmentSpec(
            surface_id="apcs048_visual_rescue",
            surface_name="APCS048 visual rescue contact sheet",
            source_kind="contact_sheet_png",
            source_path=source_root / "apcs048_visual_rescue_v1" / "contact_sheet.png",
            attachment_name="apcs048_contact_sheet.png",
            attachment_source_kind="literal_png_attachment",
            attachment_note="Attach this literal PNG first in operator email threads.",
        ),
        AttachmentSpec(
            surface_id="manual_surface_index",
            surface_name="Action photo manual surface index",
            source_kind="manual_index_html",
            source_path=source_root / "action_photo_manual_surface_index_v1" / "action_photo_manual_surface_index.html",
            attachment_name="manual_surface_index_screenshot.png",
            attachment_source_kind="browser_screenshot",
            screenshot_source_name="manual_surface_index.png",
            attachment_note="Browser screenshot of the current manual surface index.",
        ),
        AttachmentSpec(
            surface_id="uconn_v6_focus_deck",
            surface_name="UConn v6 focused deck",
            source_kind="focused_deck_html",
            source_path=source_root / "action_photo_review_deck_official_source_expansion_v6" / "action_photo_review_deck.html",
            attachment_name="uconn_v6_focus_deck_screenshot.png",
            attachment_source_kind="browser_screenshot",
            screenshot_source_name="uconn_v6_focus_deck.png",
            attachment_note="Browser screenshot of the current UConn review deck.",
        ),
        AttachmentSpec(
            surface_id="world_rugby_v5_focus_deck",
            surface_name="World Rugby v5 focused deck",
            source_kind="focused_deck_html",
            source_path=source_root / "action_photo_review_deck_official_source_expansion_v5" / "action_photo_review_deck.html",
            attachment_name="world_rugby_v5_focus_deck_screenshot.png",
            attachment_source_kind="browser_screenshot",
            screenshot_source_name="world_rugby_v5_focus_deck.png",
            attachment_note="Browser screenshot of the current World Rugby review deck.",
        ),
        AttachmentSpec(
            surface_id="latest_broad_deck",
            surface_name="Latest broad deck",
            source_kind="ranker_deck_html",
            source_path=source_root / "action_photo_ranker_review_deck_v17" / "action_photo_review_deck.html",
            attachment_name="latest_broad_deck_screenshot.png",
            attachment_source_kind="browser_screenshot",
            screenshot_source_name="latest_broad_deck.png",
            attachment_note="Browser screenshot of the latest broad action-photo deck.",
        ),
    ]


def build_rows(
    specs: list[AttachmentSpec],
    *,
    attachment_dir: Path,
    thumbnail_dir: Path,
    screenshot_dir: Path,
) -> tuple[list[dict[str, str]], list[str], int, int]:
    rows: list[dict[str, str]] = []
    missing_sources: list[str] = []
    attachment_count = 0
    thumbnail_count = 0

    for spec in specs:
        source_exists = spec.source_path.exists()
        source_attachment_path = attachment_dir / spec.attachment_name
        thumbnail_path = thumbnail_dir / spec.attachment_name
        attachment_exists = False
        thumbnail_exists = False
        attachment_source_path = ""

        if spec.surface_id == "apcs048_visual_rescue":
            if source_exists:
                copy_file(spec.source_path, source_attachment_path)
                attachment_exists = True
                attachment_source_path = spec.source_path.as_posix()
                make_thumbnail(source_attachment_path, thumbnail_path)
                thumbnail_exists = True
            else:
                missing_sources.append(spec.source_path.as_posix())
        else:
            if spec.screenshot_source_name:
                screenshot_source = screenshot_dir / spec.screenshot_source_name
                if screenshot_source.exists():
                    copy_file(screenshot_source, source_attachment_path)
                    attachment_exists = True
                    attachment_source_path = screenshot_source.as_posix()
                    make_thumbnail(source_attachment_path, thumbnail_path)
                    thumbnail_exists = True
                else:
                    missing_sources.append(screenshot_source.as_posix())
            else:
                missing_sources.append(spec.source_path.as_posix())

        if attachment_exists:
            attachment_count += 1
        if thumbnail_exists:
            thumbnail_count += 1

        rows.append(
            {
                "surface_id": spec.surface_id,
                "surface_name": spec.surface_name,
                "source_kind": spec.source_kind,
                "source_path": spec.source_path.as_posix(),
                "source_exists": "true" if source_exists else "false",
                "attachment_path": source_attachment_path.as_posix() if attachment_exists else "",
                "attachment_exists": "true" if attachment_exists else "false",
                "thumbnail_path": thumbnail_path.as_posix() if thumbnail_exists else "",
                "thumbnail_exists": "true" if thumbnail_exists else "false",
                "attachment_source_kind": spec.attachment_source_kind,
                "attachment_source_path": attachment_source_path,
                "attachment_note": spec.attachment_note,
                "review_only": "true",
                "asset_downloads": "false",
                "approval_state_change": "false",
                "publish_ready": "false",
                "publishing": "false",
            }
        )

    return rows, missing_sources, attachment_count, thumbnail_count


def build_report(manifest: dict[str, Any], rows: list[dict[str, str]], missing_sources: list[str]) -> str:
    lines = [
        "# Action Photo Manual Surface Attachment Pack V1",
        "",
        f"Status: `{manifest['status']}`",
        f"Version: `{manifest['version']}`",
        f"Generated: `{manifest['generated_at_utc']}`",
        "",
        "This packet is review-only. It copies literal PNG attachments and local browser screenshots for operator email use; it does not download assets, change approval state, move protected files, mark anything publish-ready, or publish anything.",
        "",
        "## Attachment Order",
        "",
        "1. APCS048 contact sheet",
        "2. Manual surface index screenshot",
        "3. UConn v6 focused deck screenshot",
        "4. World Rugby v5 focused deck screenshot",
        "5. Latest broad deck screenshot",
        "",
        "## Attachment Index",
        "",
        "| Surface | Source | Attachment | Thumbnail | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in rows:
        lines.append(
            f"| {row['surface_name']} | `{row['source_path']}` | `{row['attachment_path'] or 'missing'}` | `{row['thumbnail_path'] or 'missing'}` | {row['attachment_note']} |"
        )

    lines.extend(
        [
            "",
            "## Missing Inputs",
            "",
        ]
    )
    if missing_sources:
        for item in missing_sources:
            lines.append(f"- `{item}`")
    else:
        lines.append("- None")

    lines.extend(
        [
            "",
            "## Guardrails",
            "",
            "- review_only=true",
            "- asset_downloads=false",
            "- approval_state_change=false",
            "- publish_ready=false",
            "- publishing=false",
            "- auto_approval=false",
            "- auto_publish=false",
            "- source_auto_enabled=false",
            "- headshot_writes=false",
            "- protected_asset_moves=false",
            "",
        ]
    )
    return "\n".join(lines)


def build_packet(*, output_dir: Path, latest_files_root: Path, screenshot_dir: Path) -> dict[str, Any]:
    output_dir = output_dir.resolve(strict=False)
    latest_files_root = latest_files_root.resolve(strict=False)
    screenshot_dir = screenshot_dir.resolve(strict=False)

    attachment_dir = output_dir / ATTACHMENT_DIR_NAME
    thumbnail_dir = output_dir / THUMBNAIL_DIR_NAME
    attachment_dir.mkdir(parents=True, exist_ok=True)
    thumbnail_dir.mkdir(parents=True, exist_ok=True)

    specs = expected_specs(latest_files_root, screenshot_dir)
    rows, missing_sources, attachment_count, thumbnail_count = build_rows(
        specs,
        attachment_dir=attachment_dir,
        thumbnail_dir=thumbnail_dir,
        screenshot_dir=screenshot_dir,
    )

    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": now_iso(),
        "status": "action_photo_manual_surface_attachment_pack_ready",
        "output_dir": output_dir.as_posix(),
        "latest_files_root": latest_files_root.as_posix(),
        "screenshot_dir": screenshot_dir.as_posix(),
        "attachment_dir": attachment_dir.as_posix(),
        "thumbnail_dir": thumbnail_dir.as_posix(),
        "attachment_count": attachment_count,
        "thumbnail_count": thumbnail_count,
        "missing_source_count": len(missing_sources),
        "missing_sources": missing_sources,
        "review_only": True,
        "asset_downloads": False,
        "approval_state_change": False,
        "publish_ready": False,
        "publishing": False,
        "auto_approval": False,
        "auto_publish": False,
        "source_auto_enabled": False,
        "headshot_writes": False,
        "protected_asset_moves": False,
        "files": rows,
    }

    index_path = write_csv(
        output_dir / INDEX_NAME,
        rows,
        [
            "surface_id",
            "surface_name",
            "source_kind",
            "source_path",
            "source_exists",
            "attachment_path",
            "attachment_exists",
            "thumbnail_path",
            "thumbnail_exists",
            "attachment_source_kind",
            "attachment_source_path",
            "attachment_note",
            "review_only",
            "asset_downloads",
            "approval_state_change",
            "publish_ready",
            "publishing",
        ],
    )
    report_path = write_text(output_dir / REPORT_NAME, build_report(manifest, rows, missing_sources))
    manifest["index_path"] = index_path.as_posix()
    manifest["report_path"] = report_path.as_posix()
    manifest_path = write_json(output_dir / MANIFEST_NAME, manifest, sort_keys=True)

    mirror_dir = latest_files_root / output_dir.name
    mirror_dir.mkdir(parents=True, exist_ok=True)
    for source in output_dir.rglob("*"):
        if source.is_file():
            target = mirror_dir / source.relative_to(output_dir)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
    manifest["mirror_dir"] = mirror_dir.as_posix()
    write_json(manifest_path, manifest, sort_keys=True)
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only attachment pack for current action-photo manual surfaces.")
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-files-root", default=DEFAULT_LATEST_FILES_ROOT.as_posix())
    parser.add_argument("--screenshot-dir", default="")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    output_dir = resolve_output_dir(args.output_dir or None)
    screenshot_dir = Path(args.screenshot_dir) if args.screenshot_dir else output_dir / DEFAULT_SCREENSHOT_DIR.name
    manifest = build_packet(
        output_dir=output_dir,
        latest_files_root=resolve_root(args.latest_files_root, DEFAULT_LATEST_FILES_ROOT),
        screenshot_dir=resolve_root(screenshot_dir, screenshot_dir),
    )
    print(
        json.dumps(
            {
                "version": manifest["version"],
                "status": manifest["status"],
                "attachment_count": manifest["attachment_count"],
                "thumbnail_count": manifest["thumbnail_count"],
                "missing_source_count": manifest["missing_source_count"],
                "output_dir": manifest["output_dir"],
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
