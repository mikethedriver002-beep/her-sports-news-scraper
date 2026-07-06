from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from hsd_run_io import run_output_dir, write_csv, write_json, write_text

try:
    from PIL import Image, ImageDraw
except Exception:  # pragma: no cover
    Image = None  # type: ignore[assignment]
    ImageDraw = None  # type: ignore[assignment]


VERSION = "hsd-wnba-drm002-default-route-handoff-v1-review-only"
GENERATED_BY = "scripts/build_hsd_wnba_drm002_default_route_handoff_v1.py"
TARGET_CANDIDATE_ID = "DRM002"
DEFAULT_ROUTE_VARIANT_ID = "drm002_merge_candidate"
DEFAULT_OUTPUT_DIR = Path("outputs/local/tmp/wnba_drm002_default_route_handoff_v1")
DEFAULT_LATEST_OUTPUT_DIR = Path("outputs/local/latest/files/wnba_drm002_default_route_handoff_v1")
DEFAULT_SOURCE_PACKET_DIR = Path("outputs/local/latest/files/wnba_drm002_photoshop_finish_v4")
MANIFEST_NAME = "manifest.json"
REPORT_NAME = "drm002_default_route_handoff_report.md"
CSV_NAME = "drm002_default_route_handoff.csv"
SHEET_NAME = "drm002_default_route_handoff_sheet.png"
LEAD_COPY_NAME = "drm002_default_route_lead.png"
BUNDLE_NAME = "wnba_drm002_default_route_handoff_v1_bundle.zip"


def load_module(filename: str, name: str):
    script_path = Path(__file__).resolve().with_name(filename)
    spec = importlib.util.spec_from_file_location(name, script_path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


V1 = load_module("build_hsd_wnba_drm002_photoshop_finish_v1.py", "build_hsd_wnba_drm002_photoshop_finish_v1")


def repo_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_path(raw: str | Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else repo_root() / path


def resolve_output_dir(explicit: str | None = None) -> Path:
    if explicit:
        return Path(explicit)
    return run_output_dir() or DEFAULT_OUTPUT_DIR


def mirror_latest(output_dir: Path, latest_dir: Path) -> None:
    if latest_dir.exists():
        shutil.rmtree(latest_dir)
    latest_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(output_dir, latest_dir)


def load_source_manifest(source_packet_dir: Path) -> dict[str, Any]:
    manifest_path = source_packet_dir / MANIFEST_NAME
    if not manifest_path.exists():
        raise FileNotFoundError(f"Missing source packet manifest: {manifest_path}")
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def ensure_source_packet(source_packet_dir: Path, *, timeout_sec: int, head_commit: str = "") -> Path:
    manifest_path = source_packet_dir / MANIFEST_NAME
    if manifest_path.exists():
        return source_packet_dir
    command = [
        sys.executable,
        (repo_root() / "scripts" / "build_hsd_wnba_drm002_photoshop_finish_v4.py").as_posix(),
        "--timeout-sec",
        str(timeout_sec),
    ]
    if head_commit.strip():
        command.extend(["--head-commit", head_commit.strip()])
    completed = subprocess.run(command, cwd=repo_root(), capture_output=True, text=True, timeout=timeout_sec + 60)
    if completed.returncode != 0:
        raise RuntimeError(
            "Unable to generate DRM002 v4 source packet: "
            f"stdout={completed.stdout.strip()} stderr={completed.stderr.strip()}"
        )
    if not manifest_path.exists():
        raise FileNotFoundError(f"Source packet manifest still missing after rebuild: {manifest_path}")
    return source_packet_dir


def find_default_route_row(source_manifest: dict[str, Any]) -> dict[str, Any]:
    best_variant_id = str(source_manifest.get("best_variant_id") or "").strip()
    if best_variant_id and best_variant_id != DEFAULT_ROUTE_VARIANT_ID:
        raise RuntimeError(
            f"Unexpected best_variant_id={best_variant_id}; expected {DEFAULT_ROUTE_VARIANT_ID} for the default DRM002 route."
        )
    rows = source_manifest.get("variant_rows") or []
    for row in rows:
        if str(row.get("variant_id") or "").strip() == DEFAULT_ROUTE_VARIANT_ID:
            return row
    raise RuntimeError(f"{DEFAULT_ROUTE_VARIANT_ID} not found in source packet variant_rows")


def resolve_lead_render_path(source_packet_dir: Path, route_row: dict[str, Any]) -> Path:
    raw = str(route_row.get("render_path") or "").strip()
    if raw:
        candidate = Path(raw)
        if candidate.exists():
            return candidate
    fallback = source_packet_dir / "photoshop_exports" / "variant_01_drm002_merge_candidate.png"
    if fallback.exists():
        return fallback
    raise FileNotFoundError("Default DRM002 lead render is missing from the source packet")


def build_handoff_sheet(output_dir: Path, lead_image_path: Path) -> Path:
    if Image is None or ImageDraw is None:
        raise RuntimeError("Pillow is required for DRM002 default-route handoff sheet generation")

    canvas = Image.new("RGB", (1400, 1600), (11, 13, 18))
    draw = ImageDraw.Draw(canvas)
    title_font = V1.load_font(46, bold=True)
    body_font = V1.load_font(24, bold=False)
    label_font = V1.load_font(20, bold=False)
    badge_font = V1.load_font(18, bold=True)

    draw.text((58, 48), "DRM002 DEFAULT ROUTE HANDOFF", fill=(246, 247, 251), font=title_font)
    draw.text(
        (58, 110),
        "Single downstream route from the local DRM002 quarantine asset. Review-only. No downloads, approvals, or publishing.",
        fill=(184, 192, 205),
        font=body_font,
    )

    with Image.open(lead_image_path) as source:
        lead = source.convert("RGB").resize((972, 1215), Image.Resampling.LANCZOS)
    canvas.paste(lead, (58, 190))
    draw.rectangle((58, 190, 1030, 1405), outline=(237, 239, 244), width=2)

    panel_x0 = 1078
    panel_x1 = 1342
    draw.rounded_rectangle((panel_x0, 190, panel_x1, 1405), radius=16, fill=(20, 24, 31), outline=(56, 65, 80), width=2)
    draw.text((1106, 230), "DEFAULT", fill=(255, 255, 255), font=badge_font)
    lines = [
        "Variant ID",
        "drm002_merge_candidate",
        "",
        "Use this comp only for downstream editorial lanes.",
        "",
        "Do not surface comparison routes in operator-facing handoff copy.",
        "",
        "Guardrails remain review-only all the way through.",
    ]
    y = 290
    for line in lines:
        wrapped = V1.wrap_text(draw, line, label_font, panel_x1 - panel_x0 - 56) if line else [""]
        for wrapped_line in wrapped:
            if wrapped_line:
                draw.text((1106, y), wrapped_line, fill=(220, 226, 236), font=label_font)
            y += 34
        if not line:
            y += 6

    draw.text((58, 1452), "DRM002 // DEFAULT ROUTE ONLY", fill=(245, 246, 249), font=badge_font)
    draw.text((58, 1490), "Route locked for downstream review lanes.", fill=(176, 185, 198), font=label_font)

    path = output_dir / SHEET_NAME
    canvas.save(path)
    return path


def build_report(manifest: dict[str, Any]) -> str:
    return f"""# WNBA DRM002 Default-Route Handoff V1

Status: `{manifest['status']}`
Version: `{manifest['version']}`

This packet is the downstream handoff surface for DRM002 after the v4 finish review. It intentionally exposes one route only: `drm002_merge_candidate`.

It supersedes the broader v4 finish packet for downstream operator-facing use.

## Default Route

- Candidate: `{manifest['candidate_id']}`
- Default variant id: `{manifest['default_variant_id']}`
- Default variant name: `{manifest['default_variant_name']}`
- Why this route: the lead comp is the merge-worthy DRM002 finish and is now the only route that downstream lanes should carry forward.

## Downstream Instruction

- Use the copied lead render in this packet as the single active DRM002 editorial finish.
- Treat the route as review-only.
- Do not introduce alternate-route language into handoff copy, decks, or default operator notes.
- Do not download assets, change approval state, write `.approved` markers, move protected files, mark anything publish-ready, or publish.

## Photoshop Proof From Source Packet

- Source packet status: `{manifest['source_packet_status']}`
- Source packet version: `{manifest['source_packet_version']}`
- Runner verification status: `{manifest['runner_verification_status']}`
- Photoshop used: `{str(manifest['photoshop_used']).lower()}`
- Photoshop version: `{manifest['photoshop_version']}`
- Cleanup verification: `{manifest['photoshop_cleanup_status']}`

## Deliverables

- Lead render copy: `{manifest['default_render_path']}`
- Handoff sheet: `{manifest['handoff_sheet_path']}`
- Handoff CSV: `{manifest['handoff_csv_path']}`
- Bundle zip: `{manifest['bundle_zip_path']}`

## Guardrails

- review_only=true
- asset_downloads=false
- approval_state_change=false
- approved_marker_writes=false
- publish_ready=false
- publishing=false
- source_auto_enabled=false
- paid_apis=false
- protected_asset_moves=false
"""


def build_packet(
    *,
    source_packet_dir: Path,
    output_dir: Path,
    latest_output_dir: Path | None = None,
    head_commit: str = "",
    timeout_sec: int = 150,
) -> dict[str, Any]:
    source_packet_dir = ensure_source_packet(source_packet_dir.resolve(strict=False), timeout_sec=timeout_sec, head_commit=head_commit)
    output_dir = output_dir.resolve(strict=False)
    output_dir.mkdir(parents=True, exist_ok=True)

    source_manifest = load_source_manifest(source_packet_dir)
    route_row = find_default_route_row(source_manifest)
    lead_render_source = resolve_lead_render_path(source_packet_dir, route_row)
    lead_render_copy = output_dir / LEAD_COPY_NAME
    shutil.copy2(lead_render_source, lead_render_copy)

    handoff_sheet_path = build_handoff_sheet(output_dir, lead_render_copy)
    handoff_rows = [
        {
            "candidate_id": TARGET_CANDIDATE_ID,
            "default_variant_id": DEFAULT_ROUTE_VARIANT_ID,
            "default_variant_name": str(route_row.get("variant_name") or ""),
            "default_render_path": lead_render_copy.as_posix(),
            "source_packet_status": str(source_manifest.get("status") or ""),
            "source_packet_version": str(source_manifest.get("version") or ""),
            "review_only": "true",
            "asset_downloads": "false",
            "approval_state_change": "false",
            "approved_marker_writes": "false",
            "publish_ready": "false",
            "publishing": "false",
            "downstream_instruction": "Use drm002_merge_candidate only; keep operator-facing handoff copy single-route.",
        }
    ]
    handoff_csv_path = write_csv(
        output_dir / CSV_NAME,
        handoff_rows,
        [
            "candidate_id",
            "default_variant_id",
            "default_variant_name",
            "default_render_path",
            "source_packet_status",
            "source_packet_version",
            "review_only",
            "asset_downloads",
            "approval_state_change",
            "approved_marker_writes",
            "publish_ready",
            "publishing",
            "downstream_instruction",
        ],
    )

    manifest: dict[str, Any] = {
        "version": VERSION,
        "generated_by": GENERATED_BY,
        "generated_at_utc": V1.now_iso(),
        "status": "wnba_drm002_default_route_handoff_v1_ready",
        "repo_head": head_commit.strip(),
        "candidate_id": TARGET_CANDIDATE_ID,
        "source_packet_dir": source_packet_dir.as_posix(),
        "source_packet_status": str(source_manifest.get("status") or ""),
        "source_packet_version": str(source_manifest.get("version") or ""),
        "source_packet_generated_at_utc": str(source_manifest.get("generated_at_utc") or ""),
        "default_variant_id": DEFAULT_ROUTE_VARIANT_ID,
        "default_variant_name": str(route_row.get("variant_name") or ""),
        "default_render_path": lead_render_copy.as_posix(),
        "handoff_sheet_path": handoff_sheet_path.as_posix(),
        "handoff_csv_path": handoff_csv_path.as_posix(),
        "manifest_path": (output_dir / MANIFEST_NAME).as_posix(),
        "report_path": (output_dir / REPORT_NAME).as_posix(),
        "bundle_zip_path": (output_dir / BUNDLE_NAME).as_posix(),
        "runner_verification_status": str(source_manifest.get("runner_verification_status") or ""),
        "photoshop_used": bool(source_manifest.get("photoshop_used")),
        "photoshop_version": str(source_manifest.get("photoshop_version") or ""),
        "photoshop_cleanup_status": str(source_manifest.get("photoshop_cleanup_status") or ""),
        "review_only": True,
        "asset_downloads": False,
        "approval_state_change": False,
        "approved_marker_writes": False,
        "publish_ready": False,
        "publishing": False,
        "source_auto_enabled": False,
        "paid_apis": False,
        "protected_asset_moves": False,
    }
    write_json(output_dir / MANIFEST_NAME, manifest, sort_keys=True)
    write_text(output_dir / REPORT_NAME, build_report(manifest))

    bundle_path = output_dir / BUNDLE_NAME
    if bundle_path.exists():
        bundle_path.unlink()
    temp_root = output_dir.parent / bundle_path.stem
    temp_zip = temp_root.with_suffix(".zip")
    if temp_zip.exists():
        temp_zip.unlink()
    archive_path = Path(shutil.make_archive(temp_root.as_posix(), "zip", root_dir=output_dir))
    shutil.move(archive_path.as_posix(), bundle_path.as_posix())
    manifest["bundle_zip_path"] = bundle_path.as_posix()
    write_json(output_dir / MANIFEST_NAME, manifest, sort_keys=True)

    if latest_output_dir:
        mirror_latest(output_dir, latest_output_dir.resolve(strict=False))
    return manifest


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a review-only DRM002 default-route handoff packet.")
    parser.add_argument("--source-packet-dir", default=DEFAULT_SOURCE_PACKET_DIR.as_posix())
    parser.add_argument("--output-dir", default="")
    parser.add_argument("--latest-output-dir", default=DEFAULT_LATEST_OUTPUT_DIR.as_posix())
    parser.add_argument("--no-latest", action="store_true")
    parser.add_argument("--head-commit", default="")
    parser.add_argument("--timeout-sec", type=int, default=150)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    latest = None if args.no_latest else resolve_path(args.latest_output_dir)
    manifest = build_packet(
        source_packet_dir=resolve_path(args.source_packet_dir),
        output_dir=resolve_output_dir(args.output_dir or None),
        latest_output_dir=latest,
        head_commit=args.head_commit,
        timeout_sec=args.timeout_sec,
    )
    print(json.dumps({"status": manifest["status"], "default_variant_id": manifest["default_variant_id"]}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
