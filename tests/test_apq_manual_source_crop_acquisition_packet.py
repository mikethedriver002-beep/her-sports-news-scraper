from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_apq_manual_source_crop_acquisition_packet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_apq_manual_source_crop_acquisition_packet_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def seed_sources(repo_root: Path) -> None:
    before_after = repo_root / "outputs" / "local" / "tmp" / "blender_apq_before_after_decision_packet_v1"
    rubric = repo_root / "outputs" / "local" / "tmp" / "blender_apq_visual_acceptance_rubric_v1"
    current = repo_root / "outputs" / "local" / "tmp" / "blender_apq_clean_editorial_crop_v10"

    write_text(before_after / "visual_qa_report.md", "# Review-only before/after\nAPQ001 quarantine-only. Not approved. Not publish-ready.\n")
    write_json(before_after / "manifest.json", {"status": "blender_apq_before_after_decision_packet_ready", "review_only": True, "apq001_quarantine_only": True})
    write_text(before_after / "manual_visual_review_intake.csv", "row_kind,row_id\nsource_artifact,SRC001\n")

    write_text(rubric / "visual_acceptance_rubric.md", "# APQ001 Visual Acceptance Rubric\nreview-only APQ001 quarantine-only not approved not publish-ready\n")
    write_json(rubric / "manifest.json", {"status": "blender_apq_visual_acceptance_rubric_ready", "review_only": True, "apq001_quarantine_only": True})

    write_json(
        current / "manifest.json",
        {
            "status": "blender_apq_composition_variants_ready",
            "review_only": True,
            "apq001_quarantine_only": True,
            "variant_rows": [
                {"variant_id": "variant_01_photo_anchor"},
                {"variant_id": "variant_02_score_drama"},
                {
                    "variant_id": "variant_03_clean_editorial",
                    "lead_direction": "clean_editorial",
                    "subject_face_within_frame_intent": False,
                    "review_only_derived_crop": True,
                    "source_photo_crop_mode": "fit_1080x1350_right_focus",
                    "score_typography_treatment": "open_editorial_type",
                    "minimalist_font_scaling_standardized": True,
                    "top_spotlight_softened": True,
                    "layout_polish_checks": {"face_edge_clipping_reduced": False},
                },
            ],
        },
    )
    write_text(current / "contact_sheet.png", "PNG")
    write_text(current / "variant_03_clean_editorial.png", "PNG")


def test_builds_manual_source_crop_acquisition_packet(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "apq_manual_source_crop_acquisition_v1"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    seed_sources(repo_root)

    assert module.main(["--head-commit", "abc123"]) == 0

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (run_dir / "manual_source_crop_acquisition_packet.md").read_text(encoding="utf-8")
    readme = (run_dir / "README.md").read_text(encoding="utf-8")
    rows = read_csv(run_dir / "manual_source_crop_acquisition_intake.csv")

    assert manifest["version"] == "hsd-apq-manual-source-crop-acquisition-packet-v1-review-only"
    assert manifest["status"] == "apq_manual_source_crop_acquisition_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["review_only"] is True
    assert manifest["apq001_quarantine_only"] is True
    assert manifest["not_approved"] is True
    assert manifest["not_publish_ready"] is True
    assert manifest["asset_downloads"] is False
    assert manifest["download_performed"] is False
    assert manifest["source_auto_enabled"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["asset_approved"] is False
    assert manifest["move_files"] is False
    assert manifest["protected_asset_moves"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["auto_publish"] is False
    assert manifest["auto_approval"] is False
    assert manifest["download_approved_default"] == "no"
    assert manifest["manual_intake_fields"] == [
        "source_url",
        "source_type",
        "entity_id",
        "rights_class",
        "identity_confidence",
        "intended_review_only_use",
        "face_fully_in_frame_expected",
        "wider_frame_available",
        "download_approved",
        "manual_reviewer_notes",
        "reject_reason",
    ]
    assert len(manifest["evidence_items"]) == 4
    assert manifest["evidence_items"][0]["present"] is True
    assert manifest["current_truth"]["baseline_variant_id"] == "variant_03_clean_editorial"
    assert manifest["current_truth"]["baseline_subject_face_within_frame_intent"] is False
    assert manifest["current_truth"]["baseline_face_edge_clipping_reduced"] is False
    assert manifest["current_truth"]["baseline_review_only_derived_crop"] is True

    assert "variant_03_clean_editorial is still the best baseline" in report
    assert "fails the face-safe crop criterion" in report
    assert "APQ001 quarantine-only" in report
    assert "not approved" in report
    assert "not publish-ready" in report
    assert "Do not continue layout micro-polish" in report
    assert "download_approved=no" in readme
    assert "manual-only intake surface" in readme

    assert len(rows) == 1
    row = rows[0]
    assert row["row_kind"] == "manual_intake_template"
    assert row["download_approved"] == "no"
    assert row["review_only"] == "true"
    assert row["apq001_quarantine_only"] == "true"
    assert row["not_approved"] == "true"
    assert row["not_publish_ready"] == "true"
    assert row["asset_downloads"] == "false"
    assert row["download_performed"] == "false"
    assert row["source_auto_enabled"] == "false"
    assert row["approval_state_change"] == "false"
    assert row["asset_approved"] == "false"
    assert row["move_files"] == "false"
    assert row["protected_asset_moves"] == "false"
    assert row["publish_ready"] == "false"
    assert row["publishing"] == "false"
    assert row["auto_publish"] == "false"
    assert row["auto_approval"] == "false"
    assert row["future_lane_recommendation"] == "pause_current_layout_polish_until_better_review_only_crop_exists"


def test_marks_missing_sources_when_evidence_is_absent(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "apq_manual_source_crop_acquisition_v1"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    assert module.main([]) == 0

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "apq_manual_source_crop_acquisition_missing_sources"
    assert manifest["download_approved_default"] == "no"
    assert all(item["present"] is False for item in manifest["evidence_items"])
