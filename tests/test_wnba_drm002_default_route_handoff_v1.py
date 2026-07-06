from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_drm002_default_route_handoff_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_drm002_default_route_handoff_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_default_route_handoff_builds_single_route_packet(tmp_path: Path) -> None:
    module = load_module()
    source_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_drm002_photoshop_finish_v4"
    exports_dir = source_dir / "photoshop_exports"
    exports_dir.mkdir(parents=True)
    lead_render = exports_dir / "variant_01_drm002_merge_candidate.png"
    Image.new("RGB", (1080, 1350), (25, 35, 45)).save(lead_render)
    source_manifest = {
        "status": "wnba_drm002_photoshop_finish_v4_ready",
        "version": "hsd-wnba-drm002-photoshop-finish-v4-review-only",
        "generated_at_utc": "2026-07-06T21:32:06+00:00",
        "best_variant_id": "drm002_merge_candidate",
        "runner_verification_status": "ok",
        "photoshop_used": True,
        "photoshop_version": "26.4.1",
        "photoshop_cleanup_status": "clear",
        "variant_rows": [
            {
                "variant_id": "drm002_merge_candidate",
                "variant_name": "DRM002 Merge Candidate",
                "render_path": lead_render.as_posix(),
            }
        ],
    }
    (source_dir / "manifest.json").write_text(json.dumps(source_manifest), encoding="utf-8")

    output_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_drm002_default_route_handoff_v1"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_drm002_default_route_handoff_v1"
    manifest = module.build_packet(
        source_packet_dir=source_dir,
        output_dir=output_dir,
        latest_output_dir=latest_dir,
        head_commit="test-head",
        timeout_sec=5,
    )

    assert manifest["status"] == "wnba_drm002_default_route_handoff_v1_ready"
    assert manifest["default_variant_id"] == "drm002_merge_candidate"
    assert manifest["review_only"] is True
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    report_text = Path(manifest["report_path"]).read_text(encoding="utf-8")
    assert "merge_candidate_soft" not in report_text
    assert "merge_candidate_dense" not in report_text
    assert "supersedes the broader v4 finish packet" in report_text

    rows = read_csv(output_dir / "drm002_default_route_handoff.csv")
    assert rows == [
        {
            "candidate_id": "DRM002",
            "default_variant_id": "drm002_merge_candidate",
            "default_variant_name": "DRM002 Merge Candidate",
            "default_render_path": (output_dir / "drm002_default_route_lead.png").as_posix(),
            "source_packet_status": "wnba_drm002_photoshop_finish_v4_ready",
            "source_packet_version": "hsd-wnba-drm002-photoshop-finish-v4-review-only",
            "review_only": "true",
            "asset_downloads": "false",
            "approval_state_change": "false",
            "approved_marker_writes": "false",
            "publish_ready": "false",
            "publishing": "false",
            "downstream_instruction": "Use drm002_merge_candidate only; keep operator-facing handoff copy single-route.",
        }
    ]

    assert (output_dir / "drm002_default_route_handoff_sheet.png").exists()
    assert (output_dir / "wnba_drm002_default_route_handoff_v1_bundle.zip").exists()
    assert (latest_dir / "drm002_default_route_handoff_report.md").exists()
