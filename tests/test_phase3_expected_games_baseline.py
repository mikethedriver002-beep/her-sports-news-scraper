from __future__ import annotations

import importlib.util
import json
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "generate_hsd_expected_games_v5.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"


def load_module():
    spec = importlib.util.spec_from_file_location("generate_hsd_expected_games_v5", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase3_expected_games_generator_is_not_observation_derived() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "v5.2-free-public-expected-games-baseline" in text
    assert "source_observations.csv" in text
    assert "not derived from source_observations.csv" in text
    assert "INFILE = Path(\"source_observations.csv\")" not in text
    assert "input_source_type" in text
    assert "free_public_external_schedule_baseline" in text
    assert "uses_source_observations" in text


def test_phase3_expected_games_from_espn_payload() -> None:
    module = load_module()
    payload = {
        "events": [
            {
                "id": "401999999",
                "date": "2026-06-18T23:00Z",
                "competitions": [
                    {
                        "competitors": [
                            {"homeAway": "away", "team": {"displayName": "Indiana Fever"}},
                            {"homeAway": "home", "team": {"displayName": "New York Liberty"}},
                        ]
                    }
                ],
            }
        ]
    }

    rows = module.rows_from_espn_payload(payload)

    assert len(rows) == 1
    row = rows[0]
    assert row["league"] == "WNBA"
    assert row["sport"] == "basketball"
    assert row["away_team"] == "Indiana Fever"
    assert row["home_team"] == "New York Liberty"
    assert row["source_name"] == "espn_wnba_public_schedule"
    assert row["source_role"] == "external_expected_schedule_baseline"
    assert row["expected_key"].startswith("basketball|")


def test_phase3_manual_seed_is_external_expected_source(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    seed = tmp_path / "manual_expected_games.csv"
    seed.write_text(
        "date,league,sport,away_team,home_team,source_event_id,source_url\n"
        "2026-06-18,WNBA,basketball,Atlanta Dream,Chicago Sky,manual-1,manual\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(module, "MANUAL_SEED_FILES", [seed])

    rows, files_used = module.manual_seed_rows()

    assert files_used == [seed.as_posix()]
    assert len(rows) == 1
    assert rows[0]["source_name"] == "manual_reviewed_expected_seed"
    assert rows[0]["source_role"] == "external_expected_schedule_baseline"


def test_phase3_expected_manifest_marks_external_source(tmp_path: Path, monkeypatch) -> None:
    module = load_module()
    monkeypatch.setattr(module, "OUTPUT_FILE", tmp_path / "config" / "hsd_expected_games_v5.csv")
    monkeypatch.setattr(module, "MANIFEST", tmp_path / "expected_games_v5_manifest.json")
    monkeypatch.setattr(module, "REPORT", tmp_path / "expected_games_v5_report.md")
    monkeypatch.setattr(module, "fetch_espn_expected", lambda compact_dates: ([], [{"source_name": "espn_wnba_public_schedule", "date": "20260618", "ok": False, "http_status": 0, "events_found": 0, "expected_rows_emitted": 0, "notes": "test"}]))
    monkeypatch.setattr(module, "manual_seed_rows", lambda: ([module.row_from_game("2026-06-18", "Chicago Sky", "Atlanta Dream", "manual_reviewed_expected_seed", "manual-1", "manual")], ["manual_expected_games.csv"]))

    module.main()

    manifest = json.loads((tmp_path / "expected_games_v5_manifest.json").read_text(encoding="utf-8"))
    output = (tmp_path / "config" / "hsd_expected_games_v5.csv").read_text(encoding="utf-8")

    assert manifest["version"] == "v5.2-free-public-expected-games-baseline"
    assert manifest["input_file"] == "free_public_espn_wnba_scoreboard"
    assert manifest["input_source_type"] == "free_public_external_schedule_baseline"
    assert manifest["observation_derived"] is False
    assert manifest["uses_source_observations"] is False
    assert manifest["expected_games"] == 1
    assert "manual_reviewed_expected_seed" in output


def test_phase3_expected_games_test_is_wired_into_sanity_workflow() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "tests/test_phase3_expected_games_baseline.py" in workflow
