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


def write_png(path: Path, size: tuple[int, int], color: tuple[int, int, int]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, "PNG")


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv_file(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def seed_sources(run_dir: Path, module) -> None:
    seeded = {
        "outputs/local/latest/files/blender_apq_visual_qa_packet/visual_qa_contact_sheet.png": ((1080, 562), (18, 32, 48)),
        "outputs/local/latest/files/blender_apq_visual_qa_packet/visual_qa_report.md": None,
        "outputs/local/latest/files/blender_apq_visual_qa_packet/manual_visual_review_intake.csv": None,
        "outputs/local/latest/files/blender_apq_visual_qa_packet/manifest.json": None,
        "outputs/local/latest/files/blender_apq_composition_variants/contact_sheet.png": ((1080, 562), (18, 32, 48)),
        "outputs/local/latest/files/blender_apq_composition_variants/variant_01_photo_anchor.png": ((1080, 1350), (28, 34, 48)),
        "outputs/local/latest/files/blender_apq_composition_variants/variant_02_score_drama.png": ((1080, 1350), (40, 18, 22)),
        "outputs/local/latest/files/blender_apq_composition_variants/variant_03_clean_editorial.png": ((1080, 1350), (26, 30, 36)),
        "outputs/local/latest/files/blender_apq_composition_variants/manifest.json": None,
        "outputs/local/latest/files/blender_apq_composition_variants/manual_variant_review_intake.csv": None,
    }
    for rel, payload in seeded.items():
        path = run_dir / rel
        if payload is None:
            if path.suffix == ".json":
                write_json(
                    path,
                    {
                        "status": "review_only_ready",
                        "render_exit_codes": {"variant_01_photo_anchor": 0, "variant_02_score_drama": 0, "variant_03_clean_editorial": 0},
                    },
                )
            elif path.suffix == ".csv":
                write_csv_file(
                    path,
                    "row_kind,row_id,display_name,artifact_path,source_exists,source_status,review_question,decision_options,operator_decision,operator_notes,review_only,artifact_only,apq001_quarantine_only,asset_downloads,download_performed,image_edits,generated_contact_sheet_allowed,approval_state_change,asset_approved,move_files,protected_asset_moves,renderer_behavior_change,production_renderer_replacement,publish_ready,publishing,auto_publish,auto_approval\n",
                )
            else:
                write_csv_file(path, "review-only artifact\n")
            continue
        size, color = payload
        write_png(path, size, color)


def read_packet_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_builds_review_only_packet_with_contact_sheet(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "blender_apq_visual_qa_packet"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    seed_sources(run_dir, module)

    assert module.main(["--head-commit", "abc123"]) == 0

    packet = run_dir
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    report = (packet / "visual_qa_report.md").read_text(encoding="utf-8")
    readme = (packet / "README.md").read_text(encoding="utf-8")
    rows = read_packet_csv(packet / "manual_visual_review_intake.csv")

    assert manifest["version"] == "hsd-blender-apq-before-after-decision-packet-v1-review-only"
    assert manifest["status"] == "blender_apq_before_after_decision_packet_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["previous_contact_sheet_present"] is True
    assert manifest["current_contact_sheet_present"] is True
    assert manifest["previous_manifest_present"] is True
    assert manifest["current_manifest_present"] is True
    assert manifest["current_manual_review_intake_present"] is True
    assert manifest["current_variant_image_count"] == 3
    assert manifest["reference_artifact_count"] == 10
    assert manifest["reference_image_count"] == 2
    assert manifest["generated_contact_sheet_allowed"] is True
    assert manifest["contact_sheet_created"] is True
    assert manifest["contact_sheet_path"].endswith("visual_qa_contact_sheet.png")
    assert manifest["contact_sheet_source_count"] == 2
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
    assert "Accept variant_03_clean_editorial as the lead direction" in report
    assert "pre-v10 visual QA packet" in report
    assert "current post-v10 composition variants" in report
    assert "pause_for_manual_acceptance_qa" in report
    assert "pre-v10 visual QA surface" in readme
    assert "review-only and artifact-only" in readme

    artifact_rows = [row for row in rows if row["row_kind"] == "source_artifact"]
    generated_rows = [row for row in rows if row["row_kind"] == "generated_artifact"]
    question_rows = [row for row in rows if row["row_kind"] == "question"]
    assert len(artifact_rows) == 10
    assert len(generated_rows) == 1
    assert len(question_rows) == 3
    assert any(row["display_name"] == "Before: pre-v10 visual QA contact sheet" for row in artifact_rows)
    assert any(row["display_name"] == "After: post-v10 current contact sheet" for row in artifact_rows)
    assert any(row["display_name"] == "After: post-v10 variant_03_clean_editorial" for row in artifact_rows)
    assert any(row["display_name"] == "Before: pre-v10 manifest" for row in artifact_rows)
    assert any(row["display_name"] == "After: post-v10 current manual review intake" for row in artifact_rows)
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
    rows = read_packet_csv(packet / "manual_visual_review_intake.csv")

    assert manifest["status"] == "blender_apq_before_after_decision_packet_missing_sources"
    assert manifest["previous_contact_sheet_present"] is False
    assert manifest["current_contact_sheet_present"] is False
    assert manifest["current_manifest_present"] is False
    assert manifest["current_manual_review_intake_present"] is False
    assert manifest["contact_sheet_created"] is False
    assert manifest["generated_contact_sheet_allowed"] is False
    assert manifest["contact_sheet_path"] == ""
    assert manifest["contact_sheet_source_count"] == 0
    assert manifest["missing_primary_artifact_paths"] == [
        "outputs/local/latest/files/blender_apq_visual_qa_packet/visual_qa_contact_sheet.png",
        "outputs/local/latest/files/blender_apq_visual_qa_packet/visual_qa_report.md",
        "outputs/local/latest/files/blender_apq_visual_qa_packet/manual_visual_review_intake.csv",
        "outputs/local/latest/files/blender_apq_visual_qa_packet/manifest.json",
        "outputs/local/latest/files/blender_apq_composition_variants/contact_sheet.png",
        "outputs/local/latest/files/blender_apq_composition_variants/variant_01_photo_anchor.png",
        "outputs/local/latest/files/blender_apq_composition_variants/variant_02_score_drama.png",
        "outputs/local/latest/files/blender_apq_composition_variants/variant_03_clean_editorial.png",
        "outputs/local/latest/files/blender_apq_composition_variants/manifest.json",
        "outputs/local/latest/files/blender_apq_composition_variants/manual_variant_review_intake.csv",
    ]
    assert "No comparison sheet was generated" in report
    assert len([row for row in rows if row["row_kind"] == "question"]) == 3
    assert len([row for row in rows if row["row_kind"] == "source_artifact"]) == 10
    assert all(row["source_status"] == "missing" for row in rows if row["row_kind"] == "source_artifact")
