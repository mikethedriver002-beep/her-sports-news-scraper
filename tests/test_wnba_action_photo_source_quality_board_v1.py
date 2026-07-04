from __future__ import annotations

import csv
import importlib.util
import json
from pathlib import Path

import scripts.guardrail_check as guardrail


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "build_hsd_wnba_action_photo_source_quality_board_v1.py"


def load_module():
    spec = importlib.util.spec_from_file_location("build_hsd_wnba_action_photo_source_quality_board_v1", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return list(csv.DictReader(handle))


def test_wnba_action_photo_source_quality_board_builds_review_only_board(tmp_path: Path, monkeypatch) -> None:
    out_root = tmp_path / "outputs" / "local" / "tmp" / "wnba_source_quality_next_v1"
    monkeypatch.setenv("HSD_RUN_OUTPUT_DIR", out_root.as_posix())

    module = load_module()
    rc = module.main()
    assert rc == 0

    seed_csv = out_root / "wnba_source_quality_next_seed.csv"
    board_csv = out_root / "wnba_source_quality_next_board.csv"
    board_md = out_root / "wnba_source_quality_next_report.md"
    manifest_json = out_root / "manifest.json"

    assert seed_csv.exists()
    assert board_csv.exists()
    assert board_md.exists()
    assert manifest_json.exists()

    rows = read_csv(board_csv)
    assert len(rows) == 6
    assert rows[0]["example_target_id"] == "WFSH001"
    assert rows[0]["source_family_label"] == "WNBA/Fever official galleries and recaps"
    assert rows[0]["source_category"] == "official_league_gallery"
    assert rows[0]["source_quality_tier"] == "A_primary_source_lead"
    assert rows[0]["focus_team_name"] == "Indiana Fever"
    assert rows[0]["focus_player_name"] == "Kelsey Mitchell"
    assert rows[0]["download_approved"] == "no"
    assert rows[0]["review_only"] == "true"
    assert rows[0]["publish_ready"] == "false"
    assert rows[0]["asset_downloads"] == "false"
    assert rows[0]["source_url_or_search_macro"]

    manifest = json.loads(manifest_json.read_text(encoding="utf-8"))
    assert manifest["status"] == "wnba_source_quality_next_board_ready"
    assert manifest["review_only"] is True
    assert manifest["source_family_count"] == 6
    assert manifest["target_row_count"] == 6
    assert manifest["seed_target_id"] == "WFSH001"
    assert manifest["focus_team_name"] == "Indiana Fever"
    assert manifest["focus_player_name"] == "Kelsey Mitchell"
    assert manifest["guardrails"]["download_approved"] is False
    assert manifest["guardrails"]["no_source_auto_enablement"] is True

    report = board_md.read_text(encoding="utf-8")
    assert "WNBA Source Quality Next Board" in report
    assert "Indiana Fever" in report
    assert "Kelsey Mitchell" in report
    assert "WFSH001" in report
    assert "official_league_gallery" in report
    assert "download_approved=no" in report

    assert guardrail.scan_directory(out_root, guardrail.load_guardrails()) == []
