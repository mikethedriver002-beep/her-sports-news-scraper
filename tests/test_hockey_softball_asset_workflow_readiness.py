from __future__ import annotations

import importlib.util
import csv
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
    assert report["totals"]["action_queue_rows"] == 74
    assert report["totals"]["source_candidate_only_rows"] == 74
    assert report["totals"]["local_asset_present_rows"] == 0
    assert report["action_queue"] == {
        "md": "data/asset_registry/hockey_softball_asset_review_action_queue.md",
        "csv": "data/asset_registry/hockey_softball_asset_review_action_queue.csv",
        "json": "data/asset_registry/hockey_softball_asset_review_action_queue.json",
        "rows": 74,
    }

    action_queue_path = tmp_path / "data/asset_registry/hockey_softball_asset_review_action_queue.json"
    action_queue = json.loads(action_queue_path.read_text(encoding="utf-8"))
    assert action_queue["status"] == "hockey_softball_asset_review_action_queue_ready"
    assert action_queue["rows"] == 74
    assert action_queue["source_candidate_only_rows"] == 74
    assert action_queue["local_asset_present_rows"] == 0
    athlete_row = next(row for row in action_queue["action_rows"] if row["asset_domain"] == "athlete_photo")
    assert athlete_row["review_state"] == "source_candidate_only_local_asset_missing"
    assert athlete_row["local_asset_present"] == "no"
    assert athlete_row["current_source_reviewed"] == "no"
    assert athlete_row["current_identity_status"] == "no"
    assert "reviewed_by; reviewed_at_local" in athlete_row["fields_to_keep_blank_until_review"]
    assert "identity_verified=no until named athlete evidence" in athlete_row["fields_that_must_remain_hold"]
    assert "fill only source-review fields" in athlete_row["next_human_action"]
    logo_row = next(row for row in action_queue["action_rows"] if row["asset_domain"] == "logo")
    assert logo_row["review_state"] == "source_candidate_only_local_logo_missing"
    assert logo_row["board_to_open"].endswith("_logo_contact_sheet.md")
    assert logo_row["intake_to_fill"].endswith("_logo_review_intake.csv")
    csv_path = tmp_path / "data/asset_registry/hockey_softball_asset_review_action_queue.csv"
    with csv_path.open(newline="", encoding="utf-8") as handle:
        csv_rows = list(csv.DictReader(handle))
    assert len(csv_rows) == 74
    assert list(csv_rows[0].keys()) == workflow.ACTION_QUEUE_FIELDS
    assert csv_rows[0]["fields_to_keep_blank_until_review"] == "reviewed_by; reviewed_at_local; source_url_to_record"

    hockey_board = (tmp_path / "data/asset_registry/womens_hockey/womens_hockey_asset_workflow_board.md").read_text(encoding="utf-8")
    softball_board = (tmp_path / "data/asset_registry/softball/softball_asset_workflow_board.md").read_text(encoding="utf-8")
    action_queue_board = (tmp_path / "data/asset_registry/hockey_softball_asset_review_action_queue.md").read_text(encoding="utf-8")
    assert "## How To Work This Queue" in action_queue_board
    assert "fields_to_keep_blank_until_review" in action_queue_board
    assert "no automatic downloads" in action_queue_board
    assert "## Review Order" in hockey_board
    assert "## Next Human Action" in hockey_board
    assert "hockey_softball_asset_review_action_queue.md" in hockey_board
    assert "proposed manual target paths only" in hockey_board
    assert "PWHL San Jose" in hockey_board
    assert "Athletes Unlimited Softball League" in softball_board
    assert "proposed manual marker paths only" in softball_board
    assert not list(tmp_path.rglob("headshot.png"))
    assert not list(tmp_path.rglob("*.approved"))


def test_action_queue_source_only_count_uses_local_asset_presence() -> None:
    workflow = load_module(WORKFLOW_SCRIPT, "report_hsd_hockey_softball_asset_workflow_readiness_v1")
    rows = [
        {
            "sport_label": "Women's Hockey",
            "asset_domain": "athlete_photo",
            "display_name": "Marker-only row",
            "priority": "A01",
            "review_state": "approved_marker_present_manual_audit_required",
            "board_to_open": "team-board.md",
            "contact_sheet_to_open": "contact.csv",
            "intake_to_fill": "intake.csv",
            "source_url": "https://example.com/source",
            "local_asset_path": "assets/example/headshot.png",
            "local_asset_present": "no",
            "fields_to_fill_after_manual_review": "source_reviewed",
            "fields_to_keep_blank_until_review": "reviewed_by; reviewed_at_local",
            "fields_that_must_remain_hold": "identity_verified=no; publish_ready=false",
            "next_human_action": "Hold until a local asset exists.",
        }
    ]

    board = workflow.render_action_queue(rows, "2026-06-27T15:00:00+00:00")

    assert "- Source-candidate-only rows: `1`" in board
    assert "- Local asset present rows: `0`" in board


def test_command_center_surfaces_hockey_softball_asset_workflow_readiness(tmp_path: Path, monkeypatch) -> None:
    seed_hockey_softball_review_packet(tmp_path, monkeypatch)
    workflow = load_module(WORKFLOW_SCRIPT, "report_hsd_hockey_softball_asset_workflow_readiness_v1")
    assert workflow.main() == 0

    command_center = load_command_center_module()
    panel = command_center.asset_availability_readiness_panel()

    assert panel["hockey_softball_asset_workflow_status"] == "hockey_softball_asset_workflow_readiness_ready"
    assert panel["hockey_softball_asset_workflow_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_asset_workflow_rows"] == 74
    assert panel["hockey_softball_asset_review_action_queue_status"] == "hockey_softball_asset_review_action_queue_ready"
    assert panel["hockey_softball_asset_review_action_queue_freshness_status"] == "packet_ready"
    assert panel["hockey_softball_asset_review_action_queue_rows"] == 74
    assert panel["hockey_softball_asset_review_action_queue_source_candidate_only_rows"] == 74
    assert panel["hockey_softball_asset_review_action_queue_local_asset_present_rows"] == 0
    assert panel["womens_hockey_asset_workflow_rows"] == 49
    assert panel["softball_asset_workflow_rows"] == 25
    assert panel["womens_hockey_proposed_headshot_path_refs"] == 36
    assert panel["softball_proposed_headshot_path_refs"] == 18
    assert panel["womens_hockey_athlete_photo_source_review_slot_rows"] == 36
    assert panel["softball_athlete_photo_source_review_slot_rows"] == 18
    shortcut_labels = {shortcut["label"] for shortcut in panel["file_shortcuts"]}
    assert "Hockey/softball asset workflow readiness" in shortcut_labels
    assert "Hockey/softball asset review action queue" in shortcut_labels
    assert "Women's hockey asset workflow board" in shortcut_labels
    assert "Softball asset workflow board" in shortcut_labels


def test_command_center_tolerates_missing_or_empty_hockey_softball_asset_workflow_and_action_queue_reports(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    command_center = load_command_center_module()

    missing_panel = command_center.asset_availability_readiness_panel()
    assert missing_panel["hockey_softball_asset_workflow_status"] == ""
    assert missing_panel["hockey_softball_asset_workflow_generated_at"] == ""
    assert missing_panel["hockey_softball_asset_workflow_freshness_status"] == "packet_missing"
    assert missing_panel["hockey_softball_asset_review_action_queue_status"] == ""
    assert missing_panel["hockey_softball_asset_review_action_queue_generated_at"] == ""
    assert missing_panel["hockey_softball_asset_review_action_queue_freshness_status"] == "packet_missing"

    report_dir = tmp_path / "data" / "asset_registry"
    report_dir.mkdir(parents=True)
    (report_dir / "hockey_softball_asset_workflow_readiness_report.md").write_text("# Empty workflow\n", encoding="utf-8")
    (report_dir / "hockey_softball_asset_workflow_readiness_report.json").write_text(
        json.dumps({"status": "workflow_empty", "generated_at_utc": "2026-06-27T15:00:00+00:00", "summaries": None}),
        encoding="utf-8",
    )
    (report_dir / "hockey_softball_asset_review_action_queue.md").write_text("# Empty action queue\n", encoding="utf-8")
    (report_dir / "hockey_softball_asset_review_action_queue.json").write_text(
        json.dumps({"status": "action_queue_empty", "generated_at_utc": "2026-06-27T15:05:00+00:00", "action_rows": None}),
        encoding="utf-8",
    )

    empty_panel = command_center.asset_availability_readiness_panel()
    assert empty_panel["hockey_softball_asset_workflow_status"] == "workflow_empty"
    assert empty_panel["hockey_softball_asset_workflow_generated_at"] == "2026-06-27T15:00:00+00:00"
    assert empty_panel["hockey_softball_asset_workflow_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_asset_review_action_queue_status"] == "action_queue_empty"
    assert empty_panel["hockey_softball_asset_review_action_queue_generated_at"] == "2026-06-27T15:05:00+00:00"
    assert empty_panel["hockey_softball_asset_review_action_queue_freshness_status"] == "packet_empty"
    assert empty_panel["hockey_softball_asset_review_action_queue_rows"] == 0
