from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_apq001_manual_review_packet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_apq001_manual_review_packet_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def seed_candidate(run_dir: Path, module, content: bytes = b"fake-apq001-jpeg") -> Path:
    path = run_dir / module.CANDIDATE_SOURCE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return path


def seed_reference_inputs(run_dir: Path) -> None:
    latest = run_dir / "outputs/local/latest/files"
    latest.mkdir(parents=True, exist_ok=True)
    (latest / "review_only_quarantine_download_manifest.json").write_text(
        json.dumps(
            {
                "status": "quarantine_candidate_downloaded_review_only",
                "review_only": True,
                "publish_ready": False,
                "approval_state_change": False,
                "approved_marker_writes": False,
            }
        ),
        encoding="utf-8",
    )
    (latest / "review_only_quarantine_download_report.md").write_text(
        "# Quarantine download\n\nReview-only.\n",
        encoding="utf-8",
    )
    action_root = run_dir / "data/asset_registry/action_photo_candidates"
    action_root.mkdir(parents=True, exist_ok=True)
    (action_root / "review_only_action_photo_quarantine_preflight_v1.json").write_text(
        json.dumps({"status": "action_photo_quarantine_preflight_ready", "asset_downloads": False}),
        encoding="utf-8",
    )
    (action_root / "review_only_action_photo_quarantine_preflight_v1.md").write_text(
        "# Preflight\n\nReview-only.\n",
        encoding="utf-8",
    )
    (action_root / "review_only_action_photo_to_renderer_bridge_v1.json").write_text(
        json.dumps({"status": "action_photo_to_renderer_bridge_ready", "renderer_unblocked": False}),
        encoding="utf-8",
    )
    (action_root / "review_only_action_photo_to_renderer_bridge_v1.md").write_text(
        "# Bridge\n\nRenderer remains blocked.\n",
        encoding="utf-8",
    )


def test_builds_apq001_manual_review_packet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_candidate(run_dir, module)
    seed_reference_inputs(run_dir)

    assert module.main(["--head-commit", "abc123"]) == 0

    packet = run_dir / "apq001_manual_asset_review_packet"
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    readme = (packet / "README.md").read_text(encoding="utf-8")
    manual_rows = read_csv(packet / "manual_asset_review_intake.csv")
    handoff_rows = read_csv(packet / "renderer_handoff_review_checklist.csv")

    assert manifest["version"] == "hsd-apq001-manual-asset-review-packet-v1-review-only"
    assert manifest["status"] == "apq001_manual_asset_review_packet_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["candidate_queue_id"] == "APQ001"
    assert manifest["candidate_packet_path"] == "candidate/apq001_review_only_candidate.jpg"
    assert manifest["required_missing_input_count"] == 0
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["image_edits"] is False
    assert manifest["source_fetching"] is False
    assert manifest["auto_source_enablement"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["new_downloads"] is False
    assert manifest["auto_approval"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["headshot_writes"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["auto_publish"] is False
    assert manifest["publishing"] is False
    assert manifest["move_files"] is False
    assert manifest["paid_apis"] is False

    assert (packet / "candidate" / "apq001_review_only_candidate.jpg").read_bytes() == b"fake-apq001-jpeg"
    assert (packet / "references" / "review_only_quarantine_download_manifest.json").exists()
    assert (packet / "references" / "review_only_quarantine_download_report.md").exists()
    assert (packet / "references" / "review_only_action_photo_quarantine_preflight_v1.json").exists()
    assert (packet / "references" / "review_only_action_photo_quarantine_preflight_v1.md").exists()
    assert (packet / "references" / "review_only_action_photo_to_renderer_bridge_v1.json").exists()
    assert (packet / "references" / "review_only_action_photo_to_renderer_bridge_v1.md").exists()
    assert (packet / "open_packet_in_explorer.ps1").exists()

    assert len(manual_rows) == 1
    assert manual_rows[0]["operator_decision"] == "operator_fill_required"
    assert manual_rows[0]["review_only"] == "true"
    assert manual_rows[0]["publish_ready"] == "false"
    assert manual_rows[0]["approval_state_change"] == "false"
    assert manual_rows[0]["approved_marker_writes"] == "false"

    assert len(handoff_rows) == 5
    assert {row["renderer_handoff_recommendation"] for row in handoff_rows} == {"operator_fill_required"}
    assert all(row["renderer_behavior_change"] == "false" for row in handoff_rows)
    assert all(row["asset_downloads"] == "false" for row in handoff_rows)
    assert "No image edits." in readme
    assert "No .approved marker writes." in readme
    assert "No renderer behavior changes." in readme
    assert "suitable_for_renderer_handoff_review" in readme
    assert "suitable_for_renderer_recheck" in readme


def test_packet_reports_missing_candidate_without_approval_side_effects(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()

    assert module.main([]) == 1

    packet = run_dir / "apq001_manual_asset_review_packet"
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    manual_rows = read_csv(packet / "manual_asset_review_intake.csv")
    handoff_rows = read_csv(packet / "renderer_handoff_review_checklist.csv")

    assert manifest["status"] == "apq001_manual_asset_review_packet_missing_candidate"
    assert manifest["required_missing_input_count"] == 1
    assert manifest["included_file_count"] == 0
    assert manifest["review_only"] is True
    assert manifest["image_edits"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["publish_ready"] is False
    assert len(manual_rows) == 1
    assert len(handoff_rows) == 5


def test_apq001_manual_review_packet_skips_timestamp_only_rewrites(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_candidate(run_dir, module)
    seed_reference_inputs(run_dir)

    assert module.main(["--head-commit", "abc123"]) == 0

    packet = run_dir / "apq001_manual_asset_review_packet"
    manifest_path = packet / "manifest.json"
    readme_path = packet / "README.md"
    first_manifest = manifest_path.read_text(encoding="utf-8")
    first_readme = readme_path.read_text(encoding="utf-8")

    assert module.main(["--head-commit", "abc123"]) == 0

    assert manifest_path.read_text(encoding="utf-8") == first_manifest
    assert readme_path.read_text(encoding="utf-8") == first_readme
