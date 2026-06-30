from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_adobe_visual_qa_packet_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_adobe_visual_qa_packet_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def seed_required_inputs(run_dir: Path, module) -> dict[str, bytes]:
    seeded: dict[str, bytes] = {}
    for item in module.expected_inputs():
        path = run_dir / item["source"]
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.suffix == ".png":
            content = f"fake image bytes for {item['source']}".encode("utf-8")
            path.write_bytes(content)
            seeded[item["target"]] = content
        elif path.suffix == ".json":
            path.write_text(json.dumps({"status": "review_only_ready", "publish_ready": False}), encoding="utf-8")
        elif path.suffix == ".csv":
            path.write_text("check_id,status\nqa001,hold\n", encoding="utf-8")
        else:
            path.write_text("# Review-only reference\n\nNo publishing.\n", encoding="utf-8")
    return seeded


def test_builds_review_only_adobe_visual_qa_packet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seeded_bytes = seed_required_inputs(run_dir, module)

    assert module.main(["--head-commit", "abc123"]) == 0

    packet = run_dir / "adobe_visual_qa_packet"
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    readme = (packet / "README.md").read_text(encoding="utf-8")
    intake_rows = read_csv(packet / "manual_adobe_visual_qa_intake.csv")

    assert manifest["version"] == "hsd-adobe-visual-qa-packet-v1-review-only"
    assert manifest["status"] == "adobe_visual_qa_packet_ready"
    assert manifest["repo_head"] == "abc123"
    assert manifest["included_file_count"] == len(module.expected_inputs())
    assert manifest["missing_required_input_count"] == 0
    assert manifest["worksheet_fields"] == module.WORKSHEET_FIELDS
    assert manifest["operator_decision_vocabulary"] == ["hold", "revise", "approve_for_manual_next_step"]
    assert manifest["forbidden_decision_values"] == ["approved", "publish_ready", "render_ready"]
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["paid_apis"] is False
    assert manifest["source_fetching"] is False
    assert manifest["auto_source_enablement"] is False
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["auto_approval"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["headshot_writes"] is False
    assert manifest["approved_marker_writes"] is False
    assert manifest["publish_ready"] is False
    assert manifest["auto_publish"] is False
    assert manifest["publishing"] is False
    assert manifest["move_files"] is False

    assert (packet / "open_packet_in_explorer.ps1").exists()
    assert (packet / "drafts" / "draft_preview_ig_feed.png").read_bytes() == seeded_bytes["drafts/draft_preview_ig_feed.png"]
    assert (packet / "drafts" / "draft_preview_story.png").read_bytes() == seeded_bytes["drafts/draft_preview_story.png"]
    assert (packet / "drafts" / "draft_preview_square.png").read_bytes() == seeded_bytes["drafts/draft_preview_square.png"]
    assert (packet / "drafts" / "draft_preview_visual_contact_sheet.png").read_bytes() == seeded_bytes[
        "drafts/draft_preview_visual_contact_sheet.png"
    ]
    assert (packet / "references" / "handoff_manifest.json").exists()
    assert (packet / "references" / "manual_visual_qa_manifest.json").exists()
    assert (packet / "references" / "manual_visual_qa_checklist.csv").exists()
    assert (packet / "references" / "render_visual_revision_plan.md").exists()
    assert (packet / "references" / "render_visual_delta_report.md").exists()
    assert (packet / "references" / "render_next_level_editorial_qa.md").exists()

    assert [row["format"] for row in intake_rows] == ["ig_feed_4x5", "ig_story_9x16", "square_1x1", "contact_sheet"]
    assert all(row["operator_decision"] == "operator_fill_required" for row in intake_rows)
    assert all(row["revision_request"] == "" for row in intake_rows)
    assert all(row["operator_notes"] == "" for row in intake_rows)
    assert "score_rail_dashboard_violation" in readme
    assert "Use only `hold`, `revise`, or `approve_for_manual_next_step`." in readme
    assert "No automatic downloads." in readme
    assert "No .approved marker writes." in readme


def test_packet_reports_missing_inputs_without_approval_side_effects(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    first_input = module.expected_inputs()[0]
    path = run_dir / first_input["source"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b"only one draft exists")

    assert module.main([]) == 1

    packet = run_dir / "adobe_visual_qa_packet"
    manifest = json.loads((packet / "manifest.json").read_text(encoding="utf-8"))
    intake_rows = read_csv(packet / "manual_adobe_visual_qa_intake.csv")

    assert manifest["status"] == "adobe_visual_qa_packet_missing_required_inputs"
    assert manifest["included_file_count"] == 1
    assert manifest["missing_required_input_count"] == len(module.expected_inputs()) - 1
    assert manifest["asset_downloads"] is False
    assert manifest["image_edits"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert len(intake_rows) == 4


def test_adobe_visual_qa_packet_skips_timestamp_only_rewrites(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run" / "files"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    module = load_module()
    seed_required_inputs(run_dir, module)

    assert module.main(["--head-commit", "abc123"]) == 0
    packet = run_dir / "adobe_visual_qa_packet"
    manifest_path = packet / "manifest.json"
    readme_path = packet / "README.md"
    first_manifest = manifest_path.read_text(encoding="utf-8")
    first_readme = readme_path.read_text(encoding="utf-8")

    assert module.main(["--head-commit", "abc123"]) == 0

    assert manifest_path.read_text(encoding="utf-8") == first_manifest
    assert readme_path.read_text(encoding="utf-8") == first_readme
