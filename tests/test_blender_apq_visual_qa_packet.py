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
        "outputs/local/latest/files/blender_apq_composition_variants/contact_sheet.png": ((1080, 562), (18, 32, 48)),
        "outputs/local/latest/files/blender_apq_composition_variants/variant_01_photo_anchor.png": ((1080, 1350), (28, 34, 48)),
        "outputs/local/latest/files/blender_apq_composition_variants/variant_02_score_drama.png": ((1080, 1350), (40, 18, 22)),
        "outputs/local/latest/files/blender_apq_composition_variants/variant_03_clean_editorial.png": ((1080, 1350), (26, 30, 36)),
    }
    for rel, (size, color) in seeded.items():
        write_png(run_dir / rel, size, color)

    write_json(
        run_dir / "outputs" / "local" / "latest" / "files" / "blender_apq_composition_variants" / "manifest.json",
        {"status": "review_only_ready", "render_exit_codes": {"variant_01_photo_anchor": 0, "variant_02_score_drama": 0, "variant_03_clean_editorial": 0}},
    )
    write_csv_file(
        run_dir / "outputs" / "local" / "latest" / "files" / "blender_apq_composition_variants" / "manual_variant_review_intake.csv",
        "row_kind,row_id,display_name,artifact_path,source_exists,source_status,review_question,decision_options,operator_decision,operator_notes,review_only,artifact_only,apq001_quarantine_only,asset_downloads,download_performed,image_edits,generated_contact_sheet_allowed,approval_state_change,asset_approved,move_files,protected_asset_moves,renderer_behavior_change,production_renderer_replacement,publish_ready,publishing,auto_publish,auto_approval\n"
        "source_artifact,APQBVQ001,Current Blender/APQ contact sheet,outputs/local/latest/files/blender_apq_composition_variants/contact_sheet.png,True,present,Open this contact sheet first and judge the current post-#471 direction at a glance.,,,,,True,True,True,False,False,False,False,False,False,False,False,False,False,False,False,False\n"
        "question,APQBVQQ001,Does variant_01_photo_anchor now feel worth continuing as the lead Blender/APQ direction?,,,,,,yes|mostly|no|unclear,,,,True,True,True,False,False,False,False,False,False,False,False,False,False,False,False\n",
    )


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

    assert manifest["version"] == "hsd-blender-apq-visual-qa-packet-v1-review-only"
    assert manifest["status"] == "blender_apq_visual_qa_packet_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["current_contact_sheet_present"] is True
    assert manifest["current_manifest_present"] is True
    assert manifest["current_manual_review_intake_present"] is True
    assert manifest["current_variant_image_count"] == 3
    assert manifest["generated_contact_sheet_allowed"] is True
    assert manifest["contact_sheet_created"] is True
    assert manifest["contact_sheet_path"].endswith("visual_qa_contact_sheet.png")
    assert manifest["contact_sheet_source_count"] == 3
    assert manifest["reference_image_count"] == 3
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
    assert "variant_01_photo_anchor now feel worth continuing" in report
    assert "full-photo scrim direction" in report
    assert "pause_for_external_visual_qa" in report
    assert "current post-#471 Blender/APQ composition variants" in readme
    assert "review-only and artifact-only" in readme

    artifact_rows = [row for row in rows if row["row_kind"] == "source_artifact"]
    generated_rows = [row for row in rows if row["row_kind"] == "generated_artifact"]
    question_rows = [row for row in rows if row["row_kind"] == "question"]
    assert len(artifact_rows) == 6
    assert len(generated_rows) == 1
    assert len(question_rows) == 3
    assert any(row["display_name"] == "Current Blender/APQ contact sheet" for row in artifact_rows)
    assert any(row["display_name"] == "variant_01_photo_anchor" for row in artifact_rows)
    assert any(row["display_name"] == "variant_02_score_drama" for row in artifact_rows)
    assert any(row["display_name"] == "variant_03_clean_editorial" for row in artifact_rows)
    assert any(row["display_name"] == "Current Blender/APQ manifest" for row in artifact_rows)
    assert any(row["display_name"] == "Current manual review intake" for row in artifact_rows)
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

    assert manifest["status"] == "blender_apq_visual_qa_packet_missing_sources"
    assert manifest["current_contact_sheet_present"] is False
    assert manifest["current_manifest_present"] is False
    assert manifest["current_manual_review_intake_present"] is False
    assert manifest["contact_sheet_created"] is False
    assert manifest["generated_contact_sheet_allowed"] is False
    assert manifest["contact_sheet_path"] == ""
    assert manifest["contact_sheet_source_count"] == 0
    assert manifest["missing_primary_artifact_paths"] == [
        "outputs/local/latest/files/blender_apq_composition_variants/contact_sheet.png",
        "outputs/local/latest/files/blender_apq_composition_variants/variant_01_photo_anchor.png",
        "outputs/local/latest/files/blender_apq_composition_variants/variant_02_score_drama.png",
        "outputs/local/latest/files/blender_apq_composition_variants/variant_03_clean_editorial.png",
        "outputs/local/latest/files/blender_apq_composition_variants/manifest.json",
        "outputs/local/latest/files/blender_apq_composition_variants/manual_variant_review_intake.csv",
    ]
    assert "No contact sheet was generated" in report
    assert len([row for row in rows if row["row_kind"] == "question"]) == 3
    assert len([row for row in rows if row["row_kind"] == "source_artifact"]) == 6
    assert all(row["source_status"] == "missing" for row in rows if row["row_kind"] == "source_artifact")
