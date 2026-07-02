from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

from PIL import Image


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_blender_apq_visual_qa_packet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_blender_apq_visual_qa_packet_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_png(path: Path, color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (900, 1125), color).save(path, "PNG")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_builds_review_only_packet_with_contact_sheet(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "blender_apq_visual_qa_packet"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    current_image = repo_root / "outputs" / "local" / "latest" / "files" / "blender_apq_4x5_prototype" / "blender_apq_4x5_prototype_4x5.png"
    current_manifest = repo_root / "outputs" / "local" / "latest" / "files" / "blender_apq_4x5_prototype" / "blender_apq_4x5_prototype_manifest.json"
    prior_image = repo_root / "outputs" / "local" / "latest" / "files" / "blender_apq_4x5_prototype_v2" / "blender_apq_4x5_prototype_4x5.png"

    write_png(current_image, (18, 32, 48))
    write_png(prior_image, (42, 56, 72))
    write_json(current_manifest, {"status": "prototype_ready_for_review"})

    assert module.main(["--head-commit", "abc123"]) == 0

    packet = run_dir
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    report = (packet / "visual_qa_report.md").read_text(encoding="utf-8")
    readme = (packet / "README.md").read_text(encoding="utf-8")
    rows = read_csv(packet / "manual_visual_review_intake.csv")

    assert manifest["version"] == "hsd-blender-apq-visual-qa-packet-v1-review-only"
    assert manifest["status"] == "blender_apq_visual_qa_packet_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["current_prototype_image_present"] is True
    assert manifest["current_prototype_manifest_present"] is True
    assert manifest["generated_contact_sheet_allowed"] is True
    assert manifest["contact_sheet_created"] is True
    assert manifest["contact_sheet_path"].endswith("visual_qa_contact_sheet.png")
    assert manifest["contact_sheet_source_count"] == 2
    assert manifest["reference_image_count"] == 2
    assert manifest["missing_primary_artifact_paths"] == []
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["apq001_quarantine_only"] is True
    assert manifest["asset_downloads"] is False
    assert manifest["download_performed"] is False
    assert manifest["image_edits"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["asset_approved"] is False
    assert manifest["move_files"] is False
    assert manifest["protected_asset_moves"] is False
    assert manifest["renderer_behavior_change"] is False
    assert manifest["production_renderer_replacement"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["auto_publish"] is False
    assert manifest["auto_approval"] is False

    assert (packet / "visual_qa_contact_sheet.png").exists()
    assert "Does v3 materially reduce noise" in report
    assert "continue_blender_composition_polish" in report
    assert "try_different_crop_framing" in report
    assert "pause_for_external_visual_qa" in report
    assert "review-only and artifact-only" in readme

    artifact_rows = [row for row in rows if row["row_kind"] != "question"]
    question_rows = [row for row in rows if row["row_kind"] == "question"]
    assert len(artifact_rows) == 4
    assert len(question_rows) == 4
    assert any(row["row_kind"] == "generated_artifact" for row in artifact_rows)
    assert any(row["display_name"] == "Current APQ001 Blender 4:5 prototype image" for row in artifact_rows)
    assert any(row["display_name"] == "Current APQ001 Blender prototype manifest" for row in artifact_rows)
    assert any("Reference prototype image" in row["display_name"] for row in artifact_rows)
    assert all(row["review_only"] == "True" for row in rows if row["row_kind"] == "question")


def test_builds_missing_sources_packet_without_contact_sheet(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "blender_apq_visual_qa_packet"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    assert module.main([]) == 0

    packet = run_dir
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    report = (packet / "visual_qa_report.md").read_text(encoding="utf-8")
    rows = read_csv(packet / "manual_visual_review_intake.csv")

    assert manifest["status"] == "blender_apq_visual_qa_packet_missing_sources"
    assert manifest["current_prototype_image_present"] is False
    assert manifest["current_prototype_manifest_present"] is False
    assert manifest["contact_sheet_created"] is False
    assert manifest["generated_contact_sheet_allowed"] is False
    assert manifest["contact_sheet_path"] == ""
    assert manifest["contact_sheet_source_count"] == 0
    assert manifest["missing_primary_artifact_paths"] == [
        "outputs/local/latest/files/blender_apq_4x5_prototype/blender_apq_4x5_prototype_4x5.png",
        "outputs/local/latest/files/blender_apq_4x5_prototype/blender_apq_4x5_prototype_manifest.json",
    ]
    assert "No contact sheet was generated" in report
    assert len([row for row in rows if row["row_kind"] == "question"]) == 4
    assert len([row for row in rows if row["row_kind"] == "source_artifact"]) == 2
    assert all(row["source_status"] == "missing" for row in rows if row["row_kind"] == "source_artifact")
