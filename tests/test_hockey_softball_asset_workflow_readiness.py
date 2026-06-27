from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
FOUNDATION_SCRIPT = REPO / "scripts" / "generate_hsd_hockey_softball_asset_foundation_v1.py"
HELPER_SCRIPT = REPO / "scripts" / "prepare_hsd_hockey_softball_source_review_intake_v1.py"
WORKFLOW_SCRIPT = REPO / "scripts" / "report_hsd_hockey_softball_asset_workflow_readiness_v1.py"


def load_module(script: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_command_center_module():
    return load_module(REPO / "generate_hsd_operator_command_center_v2.py", "generate_hsd_operator_command_center_v2")


def seed_hockey_softball_review_packet(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))

    foundation = load_module(FOUNDATION_SCRIPT, "generate_hsd_hockey_softball_asset_foundation_v1")
    foundation.PROJECT_ROOT = tmp_path
    assert foundation.main() == 0

    helper = load_module(HELPER_SCRIPT, "prepare_hsd_hockey_softball_source_review_intake_v1")
    monkeypatch.setattr(
        "sys.argv",
        [
            "prepare_hsd_hockey_softball_source_review_intake_v1.py",
            "--reviewed-by",
            "Mike",
            "--reviewed-at-local",
            "2026-06-27 11:00 local",
        ],
    )
    assert helper.main() == 0


def test_hockey_softball_asset_workflow_readiness_reports_review_only_clarity(tmp_path: Path, monkeypatch) -> None:
    seed_hockey_softball_review_packet(tmp_path, monkeypatch)
    workflow = load_module(WORKFLOW_SCRIPT, "report_hsd_hockey_softball_asset_workflow_readiness_v1")

    assert workflow.main() == 0

    report_path = tmp_path / "data/asset_registry/hockey_softball_asset_workflow_readiness_report.json"
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["status"] == "hockey_softball_asset_workflow_readiness_ready"
    assert report["guardrails"] == {
        "paid_apis": False,
        "automatic_downloads": False,
        "auto_approval": False,
        "approval_state_changes": False,
        "headshot_png_writes": False,
        "approved_marker_writes": False,
        "publish_ready_movement": False,
        "publishing": False,
    }
    assert report["totals"]["workflow_rows"] == 74
    assert report["totals"]["logo_contact_rows"] == 20
    assert report["totals"]["athlete_candidate_rows"] == 54
    assert report["totals"]["proposed_headshot_path_refs"] == 54
    assert report["totals"]["proposed_approved_marker_path_refs"] == 54
    assert report["totals"]["local_candidate_files_present"] == 0
    assert report["totals"]["approved_marker_files_present"] == 0
    assert report["totals"]["unsafe_intake_rows"] == 0

    hockey_board = (tmp_path / "data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md").read_text(encoding="utf-8")
    softball_board = (tmp_path / "data/asset_registry/softball/softball_asset_workflow_board.md").read_text(encoding="utf-8")
    assert "## Review Order" in hockey_board
    assert "proposed manual target paths only" in hockey_board
    assert "PWHL San Jose" in hockey_board
    assert "Athletes Unlimited Softball League" in softball_board
    assert "proposed manual marker paths only" in softball_board
    assert not list(tmp_path.rglob("headshot.png"))
    assert not list(tmp_path.rglob("*.approved"))


def test_command_center_surfaces_hockey_softball_asset_workflow_readiness(tmp_path: Path, monkeypatch) -> None:
    seed_hockey_softball_review_packet(tmp_path, monkeypatch)
    workflow = load_module(WORKFLOW_SCRIPT, "report_hsd_hockey_softball_asset_workflow_readiness_v1")
    assert workflow.main() == 0

    command_center = load_command_center_module()
    panel = command_center.asset_availability_readiness_panel()

    assert panel["hockey_softball_asset_workflow_status"] == "hockey_softball_asset_workflow_readiness_ready"
    assert panel["hockey_softball_asset_workflow_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_asset_workflow_rows"] == 74
    assert panel["womens_hockey_asset_workflow_rows"] == 49
    assert panel["softball_asset_workflow_rows"] == 25
    assert panel["womens_hockey_proposed_headshot_path_refs"] == 36
    assert panel["softball_proposed_headshot_path_refs"] == 18
    assert panel["womens_hockey_athlete_photo_source_review_slot_rows"] == 36
    assert panel["softball_athlete_photo_source_review_slot_rows"] == 18
    shortcut_labels = {shortcut["label"] for shortcut in panel["file_shortcuts"]}
    assert "Hockey/softball asset workflow readiness" in shortcut_labels
    assert "Women's hockey asset workflow board" in shortcut_labels
    assert "Softball asset workflow board" in shortcut_labels


def test_command_center_tolerates_missing_or_empty_hockey_softball_asset_workflow_report(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    command_center = load_command_center_module()

    missing_panel = command_center.asset_availability_readiness_panel()
    assert missing_panel["hockey_softball_asset_workflow_status"] == ""
    assert missing_panel["hockey_softball_asset_workflow_generated_at"] == ""
    assert missing_panel["hockey_softball_asset_workflow_freshness_status"] == "packet_missing"

    report_dir = tmp_path / "data" / "asset_registry"
    report_dir.mkdir(parents=True)
    (report_dir / "hockey_softball_asset_workflow_readiness_report.md").write_text("# Empty workflow\n", encoding="utf-8")
    (report_dir / "hockey_softball_asset_workflow_readiness_report.json").write_text(
        json.dumps({"status": "workflow_empty", "generated_at_utc": "2026-06-27T15:00:00+00:00", "summaries": None}),
        encoding="utf-8",
    )

    empty_panel = command_center.asset_availability_readiness_panel()
    assert empty_panel["hockey_softball_asset_workflow_status"] == "workflow_empty"
    assert empty_panel["hockey_softball_asset_workflow_generated_at"] == "2026-06-27T15:00:00+00:00"
    assert empty_panel["hockey_softball_asset_workflow_freshness_status"] == "packet_empty"
