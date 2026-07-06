from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_drm002_photoshop_finish_v4.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_drm002_photoshop_finish_v4", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_photoshop_jsx_contains_v4_lead_only_controls(tmp_path: Path) -> None:
    module = load_module()
    jsx = module.build_photoshop_jsx(
        source_path=tmp_path / "source.jpg",
        export_dir=tmp_path / "exports",
        working_dir=tmp_path / "working",
        proof_dir=tmp_path / "proof",
        result_path=tmp_path / "working" / "result.json",
    )

    assert "drm002_merge_candidate" in jsx
    assert "drm002_merge_candidate_soft" in jsx
    assert "drm002_merge_candidate_dense" in jsx
    assert "addBottomShadow" in jsx
    assert "RAW|FRICTION" in jsx
    assert "WNBA CASE STUDY" in jsx


def test_v4_report_locks_operator_facing_surface_to_default_route() -> None:
    module = load_module()
    manifest = {
        "status": "wnba_drm002_photoshop_finish_v4_ready",
        "version": "hsd-wnba-drm002-photoshop-finish-v4-review-only",
        "runner_verification_status": "ok",
        "photoshop_used": True,
        "photoshop_version": "26.4.1",
        "photoshop_command": "python scripts/run_hsd_photoshop.py --mode jsx",
        "photoshop_cleanup_status": "clear",
        "contact_sheet_path": "contact_sheet.png",
        "manifest_path": "manifest.json",
        "report_path": "visual_report.md",
        "layer_map_path": "layer_map.md",
        "bundle_zip_path": "bundle.zip",
        "variant_rows": [
            {
                "variant_id": "drm002_merge_candidate",
                "variant_name": "DRM002 Merge Candidate",
                "render_path": "lead.png",
                "decision": "keep",
                "note": "best merge candidate",
            },
            {
                "variant_id": "drm002_merge_candidate_soft",
                "variant_name": "DRM002 Merge Candidate Soft",
                "render_path": "soft.png",
                "decision": "proof_only",
                "note": "proof only",
            },
        ],
    }
    report = module.build_report(manifest)
    assert "Default route: `drm002_merge_candidate`" in report
    assert "Proof-only comparison" not in report
    assert "drm002_merge_candidate_soft" not in report
