from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_hockey_softball_asset_foundation_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_hockey_softball_asset_foundation_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_command_center_module():
    script = REPO / "generate_hsd_operator_command_center_v2.py"
    spec = importlib.util.spec_from_file_location("generate_hsd_operator_command_center_v2", script)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return list(csv.DictReader(handle))


def test_hockey_softball_foundation_generates_review_only_scaffolds(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module.PROJECT_ROOT = tmp_path

    assert module.main() == 0

    report = json.loads((tmp_path / "data/asset_registry/hockey_softball_asset_foundation_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "hockey_softball_asset_foundation_ready"
    assert report["guardrails"] == {
        "paid_apis": False,
        "automatic_downloads": False,
        "auto_approval": False,
        "headshot_png_writes": False,
        "approved_marker_writes": False,
        "publish_ready_movement": False,
        "publishing": False,
    }
    assert {row["sport_family"]: row["team_rows"] for row in report["foundations"]} == {
        "womens_hockey": 12,
        "softball": 6,
    }

    pwhl_teams = read_csv(tmp_path / "data/asset_registry/womens_hockey/pwhl/teams.csv")
    ausl_teams = read_csv(tmp_path / "data/asset_registry/softball/ausl/teams.csv")
    assert len(pwhl_teams) == 12
    assert len(ausl_teams) == 6
    assert "seattle_torrent" in {row["team_id"] for row in pwhl_teams}
    assert "vancouver_goldeneyes" in {row["team_id"] for row in pwhl_teams}
    assert "texas_volts" in {row["team_id"] for row in ausl_teams}
    assert "utah_talons" in {row["team_id"] for row in ausl_teams}

    registry_text = "\n".join(path.read_text(encoding="utf-8") for path in (tmp_path / "data/asset_registry").rglob("*.csv"))
    for forbidden in [
        "publish_ready,true",
        "auto_approval,true",
        "auto_publish,true",
        "move_files,true",
        "paid_apis,true",
        "asset_downloads,true",
        "download_allowed,true",
        "auto_download_allowed,true",
        "render_enabled,true",
    ]:
        assert forbidden not in registry_text
    assert "https://www.thepwhl.com/en/teams/seattle-torrent" in registry_text
    assert "https://theausl.com/volts/" in registry_text
    assert not list(tmp_path.rglob("headshot.png"))
    assert not list(tmp_path.rglob("*.approved"))


def test_hockey_softball_foundation_preserves_human_notes_but_forces_guardrails(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module.PROJECT_ROOT = tmp_path

    assert module.main() == 0

    intake_path = tmp_path / "data/asset_registry/womens_hockey/womens_hockey_athlete_photo_review_intake.csv"
    rows = read_csv(intake_path)
    rows[0]["operator_decision"] = "hold_identity"
    rows[0]["operator_notes"] = "Need a better roster/photo source before using this."
    rows[0]["publish_ready"] = "true"
    rows[0]["auto_approval"] = "true"
    rows[0]["operator_priority"] = "P1"
    with intake_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    assert module.main() == 0
    rerun = read_csv(intake_path)
    assert rerun[0]["operator_decision"] == "hold_identity"
    assert rerun[0]["operator_notes"] == "Need a better roster/photo source before using this."
    assert rerun[0]["operator_priority"] == "P1"
    assert rerun[0]["publish_ready"] == "false"
    assert rerun[0]["auto_approval"] == "false"

    logo_manifest = json.loads((tmp_path / "data/asset_registry/softball/softball_logo_contact_sheet.json").read_text(encoding="utf-8"))
    athlete_manifest = json.loads((tmp_path / "data/asset_registry/softball/softball_athlete_photo_contact_sheet_manifest.json").read_text(encoding="utf-8"))
    assert logo_manifest["downloads_performed"] is False
    assert logo_manifest["approvals_applied"] is False
    assert logo_manifest["publish_ready"] is False
    assert athlete_manifest["headshot_files_written"] is False
    assert athlete_manifest["approved_markers_created"] is False


def test_command_center_surfaces_hockey_softball_asset_foundation(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", str(tmp_path))
    module.PROJECT_ROOT = tmp_path
    assert module.main() == 0

    command_center = load_command_center_module()
    panel = command_center.asset_availability_readiness_panel()

    assert panel["hockey_softball_asset_foundation_status"] == "hockey_softball_asset_foundation_ready"
    assert panel["hockey_softball_asset_foundation_freshness_status"] == "packet_ready"
    assert panel["womens_hockey_logo_contact_sheet_rows"] == 13
    assert panel["womens_hockey_athlete_photo_contact_sheet_rows"] == 12
    assert panel["softball_logo_contact_sheet_rows"] == 7
    assert panel["softball_athlete_photo_contact_sheet_rows"] == 6
    shortcut_labels = {shortcut["label"] for shortcut in panel["file_shortcuts"]}
    assert "Hockey/softball foundation report" in shortcut_labels
    assert "Women's hockey logo contact sheet" in shortcut_labels
    assert "Softball athlete contact sheets" in shortcut_labels
