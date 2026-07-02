from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_blender_apq_scene_payload_contract_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_blender_apq_scene_payload_contract_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True), encoding="utf-8")


def write_csv(path: Path, rows: list[dict[str, str]], fields: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def seed_inputs(run_dir: Path) -> None:
    write_json(
        run_dir / "apq001_action_photo_composition_review" / "manifest.json",
        {
            "version": "hsd-apq001-action-photo-composition-review-v1-review-only",
            "status": "apq001_action_photo_composition_review_ready",
            "candidate_path": (
                "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/"
                "apq001_review_only_candidate.jpg"
            ),
            "review_only": True,
            "artifact_only": True,
            "asset_approved": False,
            "approval_state_change": False,
            "asset_downloads": False,
            "move_files": False,
            "publish_ready": False,
            "publishing": False,
            "renderer_behavior_change": False,
        },
    )
    (run_dir / "apq001_action_photo_composition_review" / "composition_review.md").write_text(
        "# APQ001 Action-Photo Composition Review\n\nReview-only comparison packet.\n",
        encoding="utf-8",
    )
    write_csv(
        run_dir / "apq001_action_photo_composition_review" / "manual_composition_intake.csv",
        [
            {
                "question_id": "APQ001-CR01",
                "review_focus": "subject_readability",
                "question": "Is face and action context readable?",
                "review_only": "true",
                "artifact_only": "true",
                "asset_approved": "false",
                "approval_state_change": "false",
                "asset_downloads": "false",
                "move_files": "false",
                "publish_ready": "false",
                "publishing": "false",
            },
            {
                "question_id": "APQ001-CR02",
                "review_focus": "crop_notes",
                "question": "What crop notes should a later prototype use?",
                "review_only": "true",
                "artifact_only": "true",
                "asset_approved": "false",
                "approval_state_change": "false",
                "asset_downloads": "false",
                "move_files": "false",
                "publish_ready": "false",
                "publishing": "false",
            },
        ],
        [
            "question_id",
            "review_focus",
            "question",
            "review_only",
            "artifact_only",
            "asset_approved",
            "approval_state_change",
            "asset_downloads",
            "move_files",
            "publish_ready",
            "publishing",
        ],
    )
    write_json(
        run_dir / "blender_renderer_smoke" / "blender_renderer_smoke_manifest.json",
        {
            "version": "hsd-blender-renderer-smoke-v1-review-only",
            "status": "blender_renderer_smoke_rendered",
            "review_only": True,
            "artifact_only": True,
            "publish_ready": False,
            "approval_state_change": False,
            "asset_downloads": False,
            "move_files": False,
            "publishing": False,
            "production_renderer_replacement": False,
        },
    )
    write_json(
        run_dir / "blender_renderer_smoke" / "scene_payload.json",
        {
            "version": "hsd-blender-renderer-smoke-v1-review-only",
            "review_only": True,
            "artifact_only": True,
            "render": {"width": 1080, "height": 1350, "engine": "CYCLES", "samples": 8},
            "camera": {"location": [0.0, -7.9, 2.8], "target": [0.0, 0.0, -0.45], "lens": 42.0},
            "lights": [{"type": "area", "location": [-2.4, -3.8, 4.6], "energy": 2200.0, "size": 5.5}],
        },
    )


def test_builds_review_only_contract_from_apq_and_blender_inputs(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_inputs(run_dir)

    assert module.main([]) == 0

    out = run_dir / "blender_apq_scene_payload_contract"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    schema = json.loads((out / "scene_payload_schema.json").read_text(encoding="utf-8"))
    sample = json.loads((out / "sample_apq001_scene_payload.json").read_text(encoding="utf-8"))
    intake_rows = read_csv(out / "manual_contract_review_intake.csv")
    readme = (out / "README.md").read_text(encoding="utf-8")

    assert manifest["version"] == "hsd-blender-apq-scene-payload-contract-v1-review-only"
    assert manifest["schema_version"] == "blender_apq_scene_payload_contract.v1"
    assert manifest["status"] == "blender_apq_scene_payload_contract_ready"
    assert manifest["source_missing_count"] == 0
    assert manifest["sample_validation_issue_count"] == 0
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["apq001_quarantine_only"] is True
    for key, expected in module.FALSE_GUARDRAILS.items():
        assert manifest[key] is expected

    assert schema["properties"]["schema_version"]["const"] == "blender_apq_scene_payload_contract.v1"
    assert "canvas" in schema["required"]
    assert "source_context" in schema["required"]
    assert "action_photo_slot" in schema["required"]
    assert "blender_scene" in schema["required"]
    assert "burn_in" in schema["required"]
    assert "guardrails" in schema["required"]

    assert module.validate_sample_payload(sample) == []
    assert sample["review_only"] is True
    assert sample["artifact_only"] is True
    assert sample["canvas"]["width"] == 1080
    assert sample["canvas"]["height"] == 1350
    assert sample["canvas"]["aspect_ratio"] == "4:5"
    assert sample["source_context"]["quarantine_only"] is True
    assert sample["source_context"]["approved_input"] is False
    assert sample["source_context"]["source_status"]["manual_composition_intake_rows"] == 2
    assert sample["action_photo_slot"]["quarantine_path"].startswith(module.QUARANTINE_ROOT)
    assert sample["action_photo_slot"]["asset_approved"] is False
    assert "crop_notes" in sample["action_photo_slot"]
    assert "focus_notes" in sample["action_photo_slot"]
    assert "face_readability" in sample["action_photo_slot"]
    assert "action_readability" in sample["action_photo_slot"]
    assert sample["score_context"]["status"] == "placeholder_not_renderer_bound"
    assert sample["headline_context"]["status"] == "placeholder_not_renderer_bound"
    assert sample["blender_scene"]["renderer_invocation"] == "not_in_scope_contract_only"
    assert sample["blender_scene"]["camera"]["lens"] == 42.0
    assert sample["blender_scene"]["lights"][0]["type"] == "area"
    assert sample["blender_scene"]["stage_primitives"][0]["source"] == "action_photo_slot.quarantine_path"
    assert sample["burn_in"]["required"] is True
    assert "REVIEW ONLY" in sample["burn_in"]["text"]
    for key, expected in module.FALSE_GUARDRAILS.items():
        assert sample["guardrails"][key] is expected

    assert len(intake_rows) == 4
    assert all(row["review_only"] == "true" for row in intake_rows)
    assert all(row["artifact_only"] == "true" for row in intake_rows)
    assert all(row["apq001_quarantine_only"] == "true" for row in intake_rows)
    assert all(row["asset_approved"] == "false" for row in intake_rows)
    assert all(row["approval_state_change"] == "false" for row in intake_rows)
    assert all(row["asset_downloads"] == "false" for row in intake_rows)
    assert all(row["download_performed"] == "false" for row in intake_rows)
    assert all(row["move_files"] == "false" for row in intake_rows)
    assert all(row["publish_ready"] == "false" for row in intake_rows)
    assert all(row["publishing"] == "false" for row in intake_rows)
    assert all(row["production_renderer_replacement"] == "false" for row in intake_rows)
    assert all(row["renderer_behavior_change"] == "false" for row in intake_rows)
    assert all(row["paid_apis"] == "false" for row in intake_rows)

    artifact_text = json.dumps({"manifest": manifest, "sample": sample}, sort_keys=True).lower()
    assert "publish-ready" not in readme.lower()
    assert "ready to publish" not in artifact_text
    assert '"asset_approved": true' not in artifact_text
    assert '"approval_state_change": true' not in artifact_text
    assert '"asset_downloads": true' not in artifact_text
    assert '"move_files": true' not in artifact_text
    assert '"publishing": true' not in artifact_text
    assert "does not call blender" in readme.lower()


def test_missing_optional_source_artifacts_degrade_gracefully(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()

    assert module.main([]) == 0

    out = run_dir / "blender_apq_scene_payload_contract"
    manifest = json.loads((out / "manifest.json").read_text(encoding="utf-8"))
    sample = json.loads((out / "sample_apq001_scene_payload.json").read_text(encoding="utf-8"))
    intake_rows = read_csv(out / "manual_contract_review_intake.csv")

    assert manifest["status"] == "blender_apq_scene_payload_contract_ready_with_missing_optional_inputs"
    assert manifest["source_missing_count"] == 5
    assert manifest["sample_validation_issue_count"] == 0
    assert (out / "scene_payload_schema.json").exists()
    assert (out / "sample_apq001_scene_payload.json").exists()
    assert (out / "README.md").exists()
    assert sample["source_context"]["source_status"]["apq_manifest_present"] is False
    assert sample["source_context"]["source_status"]["manual_composition_intake_rows"] == 0
    assert sample["action_photo_slot"]["quarantine_path"].startswith(module.QUARANTINE_ROOT)
    assert sample["action_photo_slot"]["asset_approved"] is False
    assert sample["blender_scene"]["renderer_invocation"] == "not_in_scope_contract_only"
    assert module.validate_sample_payload(sample) == []
    assert len(intake_rows) == 4
    assert all(row["publish_ready"] == "false" for row in intake_rows)
    assert all(row["approval_state_change"] == "false" for row in intake_rows)


def test_sample_validator_rejects_renderer_or_asset_escalation() -> None:
    module = load_module()
    sample = module.make_sample_payload(
        statuses={
            "apq_manifest": {"path": "apq001_action_photo_composition_review/manifest.json", "present": False},
            "composition_review": {"path": "apq001_action_photo_composition_review/composition_review.md", "present": False},
            "manual_composition_intake": {"path": "apq001_action_photo_composition_review/manual_composition_intake.csv", "present": False},
            "blender_smoke_manifest": {"path": "blender_renderer_smoke/blender_renderer_smoke_manifest.json", "present": False},
            "blender_smoke_payload": {"path": "blender_renderer_smoke/scene_payload.json", "present": False},
        },
        apq_manifest={},
        blender_manifest={},
        blender_payload={},
        manual_rows=[],
        composition_review="",
    )

    sample["action_photo_slot"]["asset_approved"] = True
    sample["guardrails"]["publishing"] = True
    sample["blender_scene"]["renderer_invocation"] = "render_now"

    issues = module.validate_sample_payload(sample)
    issue_pairs = {(issue["field"], issue["issue"]) for issue in issues}
    assert ("action_photo_slot.asset_approved", "must_be_false") in issue_pairs
    assert ("guardrails.publishing", "guardrail_must_remain_false") in issue_pairs
    assert ("blender_scene.renderer_invocation", "renderer_must_not_be_invoked") in issue_pairs


def test_infer_quarantine_path_writes_repo_relative_path_for_absolute_source() -> None:
    module = load_module()
    absolute_path = (
        "D:/HSD Github Repo CLone/her-sports-news-scraper/data/assets/quarantine/review_only_candidates/"
        "action_photo_candidates/wnba/apq001/apq001_review_only_candidate.jpg"
    )

    assert module.infer_quarantine_path({"candidate_path": absolute_path}) == (
        "data/assets/quarantine/review_only_candidates/action_photo_candidates/wnba/apq001/"
        "apq001_review_only_candidate.jpg"
    )
