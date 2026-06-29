from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import generate_hsd_operator_command_center_v2 as command_center


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_action_photo_handoff_draft_copy_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_action_photo_handoff_draft_copy_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def seed_latest_bundle(run_dir: Path) -> None:
    prompt = run_dir / "data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_prompt_v1.md"
    source_map = run_dir / "data/asset_registry/action_photo_candidates/review_only_action_photo_sport_entity_source_map_board_v1.md"
    packet = run_dir / "data/asset_registry/action_photo_candidates/review_only_action_photo_candidate_research_packet_v1.md"
    return_intake = run_dir / "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv"
    for path in [prompt, source_map, packet]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("# review-only artifact\n", encoding="utf-8")
    return_intake.write_text("entity_id,source_url,download_approved\nplayer_1,,no\n", encoding="utf-8")

    bundle_dir = run_dir / "action_photo_external_research_bundles/packet-check"
    bundle_prompt = bundle_dir / "files/data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_prompt_v1.md"
    bundle_prompt.parent.mkdir(parents=True, exist_ok=True)
    bundle_prompt.write_text("# bundled prompt\n", encoding="utf-8")
    packet_manifest = bundle_dir / "packet_manifest.json"
    packet_manifest.write_text(
        json.dumps(
            {
                "status": "action_photo_external_research_bundle_ready",
                "review_only": True,
                "email_sending": False,
                "gmail_payload_created": False,
                "automatic_downloads": False,
                "approval_state_change": False,
            }
        ),
        encoding="utf-8",
    )
    (bundle_dir / "README.md").write_text("# Bundle README\n\nReview-only bundle.\n", encoding="utf-8")
    latest = run_dir / "action_photo_external_research_bundle_latest.json"
    latest.write_text(
        json.dumps(
            {
                "status": "action_photo_external_research_bundle_ready",
                "bundle_dir": str(bundle_dir),
                "zip_path": str(bundle_dir.with_suffix(".zip")),
                "manifest_path": str(packet_manifest),
                "readme_path": str(bundle_dir / "README.md"),
                "review_only": True,
                "artifact_only": True,
                "email_sending": False,
                "automatic_downloads": False,
                "approval_state_change": False,
                "publish_ready": False,
                "publishing": False,
            }
        ),
        encoding="utf-8",
    )


def test_generates_local_paste_ready_handoff_copy_without_gmail_side_effects(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "run"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    seed_latest_bundle(run_dir)
    module = load_module()

    assert module.main([]) == 0

    md = (run_dir / "action_photo_external_research_handoff_draft_copy.md").read_text(encoding="utf-8")
    txt = (run_dir / "action_photo_external_research_handoff_draft_copy.txt").read_text(encoding="utf-8")
    manifest = json.loads((run_dir / "action_photo_external_research_handoff_draft_copy.json").read_text(encoding="utf-8"))

    assert manifest["status"] == "action_photo_external_research_handoff_draft_copy_ready"
    assert manifest["subject"] == "HSD review-only action-photo research handoff"
    assert manifest["review_only"] is True
    assert manifest["artifact_only"] is True
    assert manifest["email_sending"] is False
    assert manifest["gmail_api_calls"] is False
    assert manifest["gmail_draft_creation"] is False
    assert manifest["gmail_payload_created"] is False
    assert manifest["recipient_auto_send"] is False
    assert manifest["attachments_sent"] is False
    assert manifest["automatic_downloads"] is False
    assert manifest["source_fetching"] is False
    assert manifest["source_scraping"] is False
    assert manifest["source_auto_enablement"] is False
    assert manifest["approval_state_change"] is False
    assert manifest["publish_ready"] is False
    assert manifest["publishing"] is False
    assert "does not send email, create Gmail drafts, call the Gmail API" in md
    assert "No email sending, Gmail API calls, Gmail draft creation" in txt
    assert str(run_dir / "action_photo_external_research_bundle_latest.json") in txt
    assert str(run_dir / "action_photo_external_research_bundles/packet-check/packet_manifest.json") in txt
    assert str(run_dir / "action_photo_external_research_bundles/packet-check/files/data/asset_registry/action_photo_candidates/review_only_action_photo_external_research_packet_prompt_v1.md") in txt
    assert str(run_dir / "data/asset_registry/action_photo_candidates/review_only_action_photo_research_return_intake_v1.csv") in txt
    assert "gmail_payload" not in manifest
    assert "recipients" not in manifest
    assert "attachments" not in manifest


def test_handoff_draft_helper_uses_no_send_fetch_download_or_approval_modules() -> None:
    source = SCRIPT.read_text(encoding="utf-8").lower()

    for forbidden in [
        "smtplib",
        "googleapiclient",
        "requests",
        "urllib",
        "selenium",
        "playwright",
        "send_message",
        "create_draft",
        "users.messages.send",
        "users.drafts.create",
    ]:
        assert forbidden not in source


def test_command_center_surfaces_action_photo_handoff_draft_artifacts() -> None:
    artifact_paths = {path for _, _, path in command_center.ARTIFACTS}

    assert "action_photo_external_research_handoff_draft_copy.md" in artifact_paths
    assert "action_photo_external_research_handoff_draft_copy.txt" in artifact_paths
    assert "action_photo_external_research_handoff_draft_copy.json" in artifact_paths
    assert "action_photo_external_research_bundle_latest.json" in artifact_paths
    assert command_center.RUN_COMMANDS["action_photo_external_research_handoff_draft_copy.md"].endswith(
        "scripts\\generate_hsd_action_photo_handoff_draft_copy_v1.py"
    )


def test_command_center_surfaces_latest_action_photo_bundle_packet_files(tmp_path: Path, monkeypatch) -> None:
    run_dir = tmp_path / "run"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(run_dir))
    seed_latest_bundle(run_dir)

    by_path = {entry["path"]: entry for entry in command_center.artifact_entries()}

    readme_path = "action_photo_external_research_bundles/packet-check/README.md"
    packet_manifest_path = "action_photo_external_research_bundles/packet-check/packet_manifest.json"
    assert by_path[readme_path]["title"] == "Action-photo external research bundle README"
    assert by_path[readme_path]["exists"] is True
    assert by_path[packet_manifest_path]["title"] == "Action-photo external research bundle packet manifest"
    assert by_path[packet_manifest_path]["exists"] is True
