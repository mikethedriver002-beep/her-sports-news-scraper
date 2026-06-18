from __future__ import annotations

import importlib.util
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "scripts" / "verify_hsd_wnba_schedule_independent_v5.py"
WORKFLOW = REPO / ".github" / "workflows" / "hsd-v3-repo-state-sanity.yml"


def load_module():
    spec = importlib.util.spec_from_file_location("verify_hsd_wnba_schedule_independent_v5", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_phase3b_verifier_declares_multi_source_free_policy() -> None:
    text = SCRIPT.read_text(encoding="utf-8")
    assert "v5.2-multi-source-wnba-schedule-verification" in text
    assert "wnba_stats_scoreboardv2" in text
    assert "espn_wnba_public_scoreboard_verify" in text
    assert "paid_sources_required" in text
    assert "free_public_schedule_verifier" in text


def test_phase3b_espn_payload_parses_verification_rows() -> None:
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

    rows = []
    for event in payload["events"]:
        date_local = module.local_date_from_iso(event["date"])
        competitors = event["competitions"][0]["competitors"]
        home = next(c["team"]["displayName"] for c in competitors if c["homeAway"] == "home")
        away = next(c["team"]["displayName"] for c in competitors if c["homeAway"] == "away")
        rows.append(module.verification_row(date_local, home, away, "espn_wnba_public_scoreboard_verify", event["id"], "test"))

    assert len(rows) == 1
    assert rows[0]["verification_source"] == "espn_wnba_public_scoreboard_verify"
    assert rows[0]["source_role"] == "free_public_schedule_verifier"
    assert rows[0]["independent_key"].startswith("basketball|")


def test_phase3b_verify_expected_passes_when_one_source_matches() -> None:
    module = load_module()
    expected = [
        {
            "date": "2026-06-18",
            "home_team": "New York Liberty",
            "away_team": "Indiana Fever",
            "expected_key": module.key_for("2026-06-18", "New York Liberty", "Indiana Fever"),
        }
    ]
    independent = [
        module.verification_row("2026-06-18", "New York Liberty", "Indiana Fever", "espn_wnba_public_scoreboard_verify", "401999999", "test")
    ]
    health = [module.source_health("espn_wnba_public_scoreboard_verify", "2026-06-18", True, 200, 1, 1, "ok")]

    rows, summary = module.verify_expected_against_sources(expected, independent, health)

    assert summary["source_available"] is True
    assert summary["verification_inconclusive"] is False
    assert summary["expected_games"] == 1
    assert summary["matched"] == 1
    assert summary["missing_from_independent"] == 0
    assert rows[0]["status"] == "matched"
    assert "espn_wnba_public_scoreboard_verify" in summary["available_sources"]


def test_phase3b_verify_expected_blocks_when_all_sources_unavailable() -> None:
    module = load_module()
    expected = [
        {
            "date": "2026-06-18",
            "home_team": "New York Liberty",
            "away_team": "Indiana Fever",
            "expected_key": module.key_for("2026-06-18", "New York Liberty", "Indiana Fever"),
        }
    ]
    rows, summary = module.verify_expected_against_sources(expected, [], [module.source_health("wnba_stats_scoreboardv2", "2026-06-18", False, 0, 0, 0, "timeout")])

    assert summary["source_available"] is False
    assert summary["verification_inconclusive"] is True
    assert summary["independent_source_unavailable"] == 1
    assert rows[0]["status"] == "independent_source_unavailable"


def test_phase3b_test_is_wired_into_sanity_workflow() -> None:
    workflow = WORKFLOW.read_text(encoding="utf-8")
    assert "tests/test_phase3_independent_verifier_rebuild.py" in workflow
