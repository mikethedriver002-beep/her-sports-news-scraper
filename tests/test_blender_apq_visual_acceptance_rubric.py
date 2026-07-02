from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_blender_apq_visual_acceptance_rubric_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_blender_apq_visual_acceptance_rubric_v1", SCRIPT)
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
    before_after_root = repo_root / "outputs" / "local" / "tmp" / "blender_apq_before_after_decision_packet_v1"
    current_root = repo_root / "outputs" / "local" / "tmp" / "blender_apq_clean_editorial_crop_v10"

    write_text(before_after_root / "visual_qa_report.md", "# Before/After\nThis is review-only. APQ001 quarantine-only. Not approved. Not publish-ready.\n")
    write_json(
        before_after_root / "manifest.json",
        {
            "status": "blender_apq_before_after_decision_packet_ready",
            "review_only": True,
            "apq001_quarantine_only": True,
        },
    )
    write_text(before_after_root / "manual_visual_review_intake.csv", "row_kind,row_id\nsource_artifact,SRC001\n")

    write_json(
        current_root / "manifest.json",
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
    for filename in [
        "contact_sheet.png",
        "variant_01_photo_anchor.png",
        "variant_02_score_drama.png",
        "variant_03_clean_editorial.png",
    ]:
        (current_root / filename).write_bytes(b"PNG")


def test_builds_review_only_rubric_with_truth_snapshot(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "blender_apq_visual_acceptance_rubric_v1"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    seed_sources(repo_root)

    assert module.main(["--head-commit", "abc123"]) == 0

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (run_dir / "visual_acceptance_rubric.md").read_text(encoding="utf-8")
    readme = (run_dir / "README.md").read_text(encoding="utf-8")
    rows = read_csv(run_dir / "visual_acceptance_rubric.csv")

    assert manifest["version"] == "hsd-blender-apq-visual-acceptance-rubric-v1-review-only"
    assert manifest["status"] == "blender_apq_visual_acceptance_rubric_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["current_truth"]["baseline_variant_id"] == "variant_03_clean_editorial"
    assert manifest["current_truth"]["baseline_variant_is_strongest"] is True
    assert manifest["current_truth"]["baseline_subject_face_within_frame_intent"] is False
    assert manifest["current_truth"]["baseline_face_edge_clipping_reduced"] is False
    assert manifest["current_truth"]["baseline_minimalist_font_scaling_standardized"] is True
    assert manifest["current_truth"]["baseline_top_spotlight_softened"] is True
    assert manifest["current_truth"]["baseline_review_only_derived_crop"] is True
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
    assert manifest["renderer_behavior_change"] is False
    assert manifest["production_renderer_replacement"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert manifest["auto_publish"] is False
    assert manifest["auto_approval"] is False
    assert [item["category_id"] for item in manifest["decision_categories"]] == [
        "accept_baseline",
        "revise_only_if_better_review_only_crop_exists",
        "pause_for_manual_qa",
        "continue_limited_polish_only_if_fixable_without_new_assets",
    ]
    assert manifest["manual_intake_fields"] == [
        "reviewer_decision",
        "reviewer_notes",
        "blocked_by_source_candidate_limitations",
        "future_lane_recommendation",
    ]
    assert manifest["missing_required_source_paths"] == []

    assert "review-only" in report
    assert "APQ001 quarantine-only" in report
    assert "not approved" in report
    assert "not publish-ready" in report
    assert "variant_03_clean_editorial is the strongest baseline" in report
    assert "still fails the face-safe criterion" in report
    assert "accept_baseline" in report
    assert "pause_for_manual_qa" in report
    assert "review-only, APQ001 quarantine-only" in readme
    assert "reviewer_decision" in readme

    source_rows = [row for row in rows if row["row_kind"] == "source_artifact"]
    decision_rows = [row for row in rows if row["row_kind"] == "decision_category"]
    criterion_rows = [row for row in rows if row["row_kind"] == "criterion"]
    intake_rows = [row for row in rows if row["row_kind"] == "manual_intake_template"]
    assert len(source_rows) == 8
    assert len(decision_rows) == 4
    assert len(criterion_rows) == 8
    assert len(intake_rows) == 1
    assert any(row["row_id"] == "SRC104" and row["current_state"] == "present" for row in source_rows)
    assert any(row["row_id"] == "HB01" and row["current_state"] == "fail" for row in criterion_rows)
    assert any(row["row_id"] == "AD02" and row["current_state"] == "pass" for row in criterion_rows)
    assert all(row["review_only"] == "True" for row in rows)
    assert all(row["apq001_quarantine_only"] == "True" for row in rows)


def test_marks_missing_sources_when_post_v10_truth_is_absent(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    repo_root = tmp_path / "repo"
    run_dir = tmp_path / "outputs" / "local" / "tmp" / "blender_apq_visual_acceptance_rubric_v1"
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    monkeypatch.setattr(module, "repo_root", lambda: repo_root)

    before_after_root = repo_root / "outputs" / "local" / "tmp" / "blender_apq_before_after_decision_packet_v1"
    before_after_root.mkdir(parents=True, exist_ok=True)
    write_text(before_after_root / "visual_qa_report.md", "# Before/After\n")
    write_json(before_after_root / "manifest.json", {"status": "blender_apq_before_after_decision_packet_ready"})
    write_text(before_after_root / "manual_visual_review_intake.csv", "row_kind,row_id\nsource_artifact,SRC001\n")

    assert module.main([]) == 0

    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    report = (run_dir / "visual_acceptance_rubric.md").read_text(encoding="utf-8")
    rows = read_csv(run_dir / "visual_acceptance_rubric.csv")

    assert manifest["status"] == "blender_apq_visual_acceptance_rubric_missing_sources"
    assert manifest["missing_required_source_paths"]
    assert "missing_sources" in report
    assert any(row["row_kind"] == "source_artifact" and row["current_state"] == "missing" for row in rows)
