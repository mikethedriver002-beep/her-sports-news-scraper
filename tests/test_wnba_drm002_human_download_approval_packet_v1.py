from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_drm002_human_download_approval_packet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_drm002_human_download_approval_packet_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_drm002_human_download_approval_packet_builds_review_only_operator_bundle(tmp_path: Path) -> None:
    module = load_module()
    output_dir = tmp_path / "outputs" / "local" / "tmp" / "wnba_drm002_human_download_approval_packet_v1"
    latest_dir = tmp_path / "outputs" / "local" / "latest" / "files" / "wnba_drm002_human_download_approval_packet_v1"

    manifest = module.build_packet(
        intake_csv=REPO / "data" / "asset_registry" / "action_photo_candidates" / "review_only_action_photo_research_return_intake_v1.csv",
        preflight_csv=REPO / "data" / "asset_registry" / "action_photo_candidates" / "review_only_action_photo_quarantine_preflight_v1.csv",
        output_dir=output_dir,
        latest_output_dir=latest_dir,
        head_commit="test-head",
    )

    assert manifest["status"] == "wnba_drm002_human_download_approval_packet_ready"
    assert manifest["candidate_queue_id"] == "DRM002"
    assert manifest["action_photo_status"] == "action_photo_candidate"
    assert manifest["ready_for_human_download_decision"] == "yes"
    assert manifest["download_approved"] == "no"
    assert manifest["review_only"] == "true"
    assert manifest["publish_ready"] == "false"
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publishing"] is False

    manifest_json = json.loads((output_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest_json["repo_head"] == "test-head"

    snapshot_csv = (output_dir / "drm002_authoritative_intake_row_snapshot.csv").read_text(encoding="utf-8")
    assert "DRM002" in snapshot_csv
    assert ",no," in snapshot_csv

    checklist_csv = (output_dir / "drm002_human_download_approval_checklist.csv").read_text(encoding="utf-8")
    assert "ready_for_human_download_decision,yes,ready" in checklist_csv
    assert "download_approved,no,locked_no" in checklist_csv

    report = (output_dir / "drm002_human_download_approval_report.md").read_text(encoding="utf-8")
    assert "review-only operator handoff" in report
    assert "not download approval and not asset approval" in report

    assert (latest_dir / "drm002_human_download_approval_report.md").exists()
